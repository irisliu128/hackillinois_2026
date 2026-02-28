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

    def fetch_dem(self, lat, lon, buffer_degrees=0.05):
        bbox = [lon - buffer_degrees, lat - buffer_degrees, lon + buffer_degrees, lat + buffer_degrees]
        region = ee.Geometry.BBox(*bbox)
        out_dem = os.path.join(self.work_dir, "raw_dem.tif")
        dem_image = ee.Image("NASA/NASADEM_HGT/001").select('elevation')
        arr = geemap.ee_to_numpy(dem_image, region=region)
        geemap.numpy_to_cog(arr.squeeze(), out_dem, bounds=[bbox[1], bbox[0], bbox[3], bbox[2]], crs='EPSG:4326')
        return "raw_dem.tif"

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