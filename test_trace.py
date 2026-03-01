from src.risk_model import predict
import logging
logging.basicConfig(level=logging.DEBUG)

def trace_seattle():
    lat = 47.6062
    lon = -122.3321
    # mimic smoke_test.py calling /v1/analyze for Seattle
    print("Tracing predict for Seattle...")
    # I will call predict and it will print the logger.info CALC block if I uncomment it in the real code, or I can just see the output.
    # To see internal vars, let's just run predict.
    score = predict(lat, lon, rainfall_mm=0.0, soil_type='loam', ndvi=0.08, soil_moisture=0.15, is_burn_zone=False)
    print(f"Final Score: {score}")
    
trace_seattle()
