import sys
import os
sys.path.append(os.getcwd())

try:
    print("Attempting imports...")
    from routers import competitors_router
    from routers import dashboard_router
    from routers import alerts_router
    print("Routers imported successfully.")
    
    from main import app
    print("App imported successfully.")
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
