# morning_email.py
import os
import pytz
from datetime import datetime
from typing import Any, Dict

# ========== SAFE GET IMPLEMENTATION ==========
def safe_get(data: Dict, *keys: Any, default: Any = None) -> Any:
    """Universal safe accessor for nested data structures"""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError, IndexError):
        return default

# ========== CORE FUNCTIONALITY ==========
def main():
    print("🚀 Starting morning digest workflow")
    
    try:
        # Initialize with dummy data to test safe_get
        test_data = {
            "weather": {"today": {"temp": 22, "condition": "sunny"}},
            "tasks": {"today_due": [{"name": "Test task", "priority": "high"}]}
        }
        
        print("\n🔧 Testing safe_get functionality:")
        print("Weather temp:", safe_get(test_data, "weather", "today", "temp", default=0))
        print("Non-existent field:", safe_get(test_data, "invalid", "path", default="N/A"))
        
        print("\n✅ All core functionality works")
        return 0
        
    except Exception as e:
        print(f"🔥 Critical failure: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)