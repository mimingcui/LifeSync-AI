# morning_email.py
import re
import pytz
from datetime import datetime
from src.send_email.format_email import format_email
from src.get_notion.task_from_notion import fetch_tasks_from_notion
from src.send_email.email_notifier import send_email
from src.ai_operations.ai_morning_advice import email_advice_with_ai
from src.get_weather import get_weather_forecast
from src.get_env.env_from_notion import get_user_env_vars

# --- Add this FIRST ---
def safe_get(dictionary, *keys, default=None):
    """Safely retrieve nested values from dictionaries/lists"""
    current = dictionary
    for key in keys:
        try:
            current = current[key]
        except (KeyError, TypeError, IndexError):
            return default
    return current
# ----------------------

def validate_user_config(user_data):
    """Validate user configurations"""
    valid_users = [uid for uid in user_data if uid != "MISSING_USER_ID"]
    if not valid_users:
        raise SystemExit("Error: No valid user configurations found")

def send_morning_digest():
    utc_now = datetime.now(pytz.utc)
    
    try:
        user_data = get_user_env_vars()
    except Exception as e:
        raise SystemExit(f"Config Error: {str(e)}")

    validate_user_config(user_data)

    for user_id in user_data:
        if user_id == "MISSING_USER_ID":
            print("Configuration Error:")
            print("1. Check USER_ID in Notion")
            print("2. Verify TIME_ZONE format")
            raise SystemExit("Invalid configuration")

        try:
            user_info = user_data[user_id]
            
            # Timezone handling
            time_zone_offset = int(user_info["TIME_ZONE"].strip())
            local_time = utc_now.astimezone(
                pytz.FixedOffset(time_zone_offset * 60)
            )
            custom_date = local_time.date()

            # Fetch data using safe_get
            tasks = fetch_tasks_from_notion(
                custom_date,
                user_info["USER_NOTION_TOKEN"],
                user_info["USER_DATABASE_ID"],
                time_zone_offset
            )

            forecast_data = get_weather_forecast(
                user_info["PRESENT_LOCATION"],
                time_zone_offset
            )

            # --- This is where safe_get is used ---
            data = {
                "weather": safe_get(forecast_data, "today", default={}),
                "today_tasks": safe_get(tasks, "today_due", default=[]),
                "in_progress_tasks": safe_get(tasks, "in_progress", default=[]),
                "future_tasks": safe_get(tasks, "future", default=[])
            }

            # Rest of email logic...
            
        except Exception as e:
            print(f"Error processing {user_id}: {str(e)}")
            continue

if __name__ == "__main__":
    send_morning_digest()