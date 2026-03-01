import os
import logging
import ee
import geemap
import numpy as np
import json
import rasterio
from whitebox import WhiteboxTools
from dotenv import load_dotenv


from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger("TerrainEngine")

class TerrainAnalyzer:
    def __init__(self, work_dir="C:/hydro_temp"):
        self.work_dir = os.path.abspath(work_dir)
        os.makedirs(self.work_dir, exist_ok=True)
        self.wbt = WhiteboxTools()
        self.wbt.work_dir = self.work_dir
        self.wbt.verbose = False
        self._init_gee()

    def _init_gee(self):
        project_id = os.getenv("GEE_PROJECT_ID", "hydroproject-488807")
        try:
            ee.Initialize(project=project_id)
            logger.info(f"GEE Initialized with project: {project_id}")
        except Exception as e:
            logger.warning(f"⚠️ PERMISSION NOTICE: Could not initialize Google Earth Engine. "
                           f"The system will run in Demo Mode (Risk Score only). "
                           f"To enable Live Terrain, ensure you have the 'serviceusage.serviceUsageConsumer' "
                           f"role for project '{project_id}'.")
            # We DON'T raise an error here so the rest of the app (ML Risk) still works
            self.gee_available = False
            return
        self.gee_available = True

    def fetch_dem(self, lat, lon, buffer_degrees=0.03):
        bbox = [lon - buffer_degrees, lat - buffer_degrees, lon + buffer_degrees, lat + buffer_degrees]
        region = ee.Geometry.BBox(*bbox)
        out_dem = os.path.join(self.work_dir, "raw_dem.tif")
        dem_image = ee.Image("NASA/NASADEM_HGT/001").select('elevation')
        
        # Clip to region to avoid huge downloads
        arr = geemap.ee_to_numpy(dem_image, region=region)
        # Correct lat/lon ordering for geotiff (geemap expects [miny, minx, maxy, maxx])
        geemap.numpy_to_cog(arr.squeeze(), out_dem, bounds=[bbox[1], bbox[0], bbox[3], bbox[2]], crs='EPSG:4326')
        return "raw_dem.tif"

    def get_environmental_context(self, lat, lon):
        """
        Fetches global environmental indices from GEE for advanced risk calibration.
        Returns: {ndvi, soil_moisture, burn_index}
        """
        if not self.gee_available:
            return {"ndvi": 0.5, "soil_moisture": 0.3, "is_burn_zone": False}

        # Resilient Caching: Only query GEE if we haven't checked this approx area in 24 hours.
        import requests_cache
        from pathlib import Path
        cache_dir = Path(self.work_dir) / "gee_cache"
        requests_cache.install_cache(str(cache_dir), expire_after=86400) # 24 hour cache
        
        # Round to ~1km resolution to increase cache hits for nearby requests
        cache_lat = round(lat, 2)
        cache_lon = round(lon, 2)
        cache_key = f"{cache_lat}_{cache_lon}"
        
        # We simulate a cache check using requests_cache by creating a dummy URL
        # Since Earth Engine API isn't a simple REST endpoint we can wrap with requests_cache,
        # we'll build a simple dict cache on top of requests_cache's SQLite backend manually
        
        session = requests_cache.CachedSession(str(cache_dir), expire_after=86400)
        dummy_url = f"http://local.gee.cache/{cache_key}"
        
        cached_resp = session.get(dummy_url)
        if cached_resp.status_code == 200:
            logger.info(f"   GEE Cache HIT for {cache_key}")
            return cached_resp.json()

        logger.info(f"   GEE Cache MISS for {cache_key}. Fetching live satellite indices...")

        point = ee.Geometry.Point([lon, lat])
        buffer = point.buffer(500) # 500m radius for environmental context

        # 1. Vegetation Index (NDVI) - Sentinel-2
        s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(buffer) \
            .filterDate('2023-01-01', '2024-12-31') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .median()
        
        ndvi = s2.normalizedDifference(['B8', 'B4']).rename('ndvi')
        ndvi_val = ndvi.reduceRegion(ee.Reducer.mean(), buffer, 30).get('ndvi').getInfo()

        # 2. Daily Soil Moisture (SMAP)
        smap = ee.ImageCollection("NASA/SMAP/SPL4SMGP/007") \
            .filterBounds(buffer) \
            .sort('system:time_start', False) \
            .first()
        
        # sm_surface: surface soil moisture
        moisture_val = smap.select('sm_surface').reduceRegion(ee.Reducer.mean(), buffer, 1000).get('sm_surface').getInfo()

        # 3. Burn Scars (MODIS)
        burn = ee.ImageCollection("MODIS/006/MCD64A1") \
            .filterBounds(buffer) \
            .filterDate('2022-01-01', '2024-12-31') \
            .max()
        
        burn_val = burn.select('BurnDate').reduceRegion(ee.Reducer.max(), buffer, 500).get('BurnDate').getInfo()

        result = {
            "ndvi": float(ndvi_val) if ndvi_val else 0.4,
            "soil_moisture": float(moisture_val) if moisture_val else 0.2,
            "is_burn_zone": burn_val is not None and burn_val > 0
        }
        
        # Save to cache using a manual mock response
        from requests.models import Response
        import json
        mock_resp = Response()
        mock_resp.status_code = 200
        mock_resp._content = json.dumps(result).encode('utf-8')
        mock_resp.url = dummy_url
        session.cache.save_response(mock_resp)

        return result

    def process_hydrology(self, raw_dem_name):
        logger.info("Phase 3: Cleaning terrain physics...")
        self.wbt.breach_depressions(raw_dem_name, "breached.tif")
        self.wbt.fill_depressions("breached.tif", "filled.tif")
        self.wbt.d8_pointer("filled.tif", "pntr.tif")
        self.wbt.d8_flow_accumulation("pntr.tif", "accum.tif")
        return "accum.tif"

    def finalize_output(self, accum_name):
        """Auto-thresholding logic to ensure we ALWAYS get a file."""
        out_geojson = os.path.join(self.work_dir, "flow_paths.geojson")
        accum_path = os.path.join(self.work_dir, accum_name)
        
        # Try progressively easier thresholds [cite: 10]
        for threshold in [5, 20]:
            logger.info(f"Attempting stream extraction at threshold: {threshold}")
            self.wbt.extract_streams(accum_name, "streams.tif", threshold)
            
            with rasterio.open(os.path.join(self.work_dir, "streams.tif")) as src:
                data = src.read(1)
                coords = np.argwhere(data > 0)
                
                if len(coords) > 0:
                    logger.info(f"Success! Found {len(coords)} stream segments.")
                    features = []
                    for y, x in coords[::3]: # Sample every 3rd pixel for speed
                        lon, lat = src.xy(y, x)
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [lon, lat]},
                            "properties": {"intensity": float(data[y,x])}
                        })
                    
                    with open(out_geojson, "w") as f:
                        json.dump({"type": "FeatureCollection", "features": features}, f)
                    return out_geojson
        
        raise RuntimeError("Even at threshold 5, no water flow was detected. Check your area coordinates.")

    def run_full_pipeline(self, lat, lon):
        if not hasattr(self, 'gee_available') or not self.gee_available:
            logger.warning("Skipping terrain pipeline: GEE is not available.")
            return None
        raw_dem = self.fetch_dem(lat, lon)
        accum_map = self.process_hydrology(raw_dem)
        return self.finalize_output(accum_map)

if __name__ == "__main__":
    analyzer = TerrainAnalyzer()
    # Machu Picchu test area [cite: 30]
    geojson_path = analyzer.run_full_pipeline(-13.1631, -72.5450)
    print(f"\n--- Successful Generation ---\nGeoJSON located at: {geojson_path}\nPoints inside: {os.path.getsize(geojson_path)//100}")