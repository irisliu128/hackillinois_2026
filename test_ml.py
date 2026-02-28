import sys
from pathlib import Path

# Add src to python path
src_path = Path("c:/Users/senda/Downloads/hackIllinoisProject/hackillinois_2026/src").resolve()
sys.path.append(str(src_path.parent))

from src.risk_model import predict

try:
    # Test coordinates for Kolkata, India (as requested in task: 22.57, 88.36)
    score = predict(22.57, 88.36)
    print(f"Risk score for (22.57, 88.36): {score}")
    assert 0 <= score <= 1
    print("Test passed: Risk score is in range [0, 1]")
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()
