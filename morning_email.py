def safe_get(dictionary, *keys, default=None):
    """Safely retrieve nested values from dictionaries/lists"""
    current = dictionary
    for key in keys:
        try:
            current = current[key]
        except (KeyError, TypeError, IndexError):
            return default
    return current


import re
import pytz
from datetime import datetime
from src.send_email.format_email import format_email
from src.get_notion.task_from_notion import fetch_tasks_from_notion
from src.send_email.email_notifier import send_email
from src.ai_operations.ai_morning_advice import email_advice_with_ai
from src.get_weather import get_weather_forecast
from src.get_env.env_from_notion import get_user_env_vars


def validate_user_config(user_data):
    """Validate at least one valid user configuration exists"""
    valid_users = [uid for uid in user_data if uid != "MISSING_USER_ID"]
    if not valid_users:
        raise SystemExit("CRITICAL ERROR: No valid user configurations found")

def send_morning_digest():
    utc_now = datetime.now(pytz.utc)
    
    try:
        print("🔍 Fetching user configurations...")
        user_data = get_user_env_vars()
    except Exception as e:
        raise SystemExit(f"Failed to fetch configurations: {str(e)}")

    validate_user_config(user_data)

    for user_id in user_data:
        if user_id == "MISSING_USER_ID":
            print("Invalid configuration detected")
            print("1. Check USER_ID in Notion")
            print("2. Verify TIME_ZONE format")
            raise SystemExit("Configuration error")

        try:
            user_info = user_data[user_id]
            
            # Validate required fields
            required_keys = [
                "USER_NOTION_TOKEN", "USER_DATABASE_ID",
                "GPT_VERSION", "PRESENT_LOCATION", "USER_NAME",
                "USER_CAREER", "SCHEDULE_PROMPT", "TIME_ZONE",
                "EMAIL_RECEIVER", "EMAIL_TITLE"
            ]
            
            missing_keys = [key for key in required_keys if key not in user_info]
            if missing_keys:
                raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")

            # Process timezone
            try:
                time_zone_offset = int(user_info["TIME_ZONE"].strip())
            except ValueError:
                print("⚠️ Invalid TIME_ZONE, using UTC")
                time_zone_offset = 0

            user_tz = pytz.FixedOffset(time_zone_offset * 60)
            local_time = utc_now.astimezone(user_tz)
            custom_date = local_time.date()

            print(f"\nProcessing {user_id} ({user_info['USER_NAME']})")
            print(f"Local time: {local_time.strftime('%Y-%m-%d %H:%M')}")

            # Fetch tasks
            tasks = {}
            try:
                print("📋 Fetching tasks...")
                tasks = fetch_tasks_from_notion(
                    custom_date,
                    user_info["USER_NOTION_TOKEN"],
                    user_info["USER_DATABASE_ID"],
                    time_zone_offset
                )
            except Exception as e:
                print(f"❌ Task fetch error: {str(e)}")
                tasks = {}

            # Get weather
            forecast_data = {}
            try:
                print("🌤️ Fetching weather...")
                forecast_data = get_weather_forecast(
                    user_info["PRESENT_LOCATION"],
                    time_zone_offset
                )
            except Exception as e:
                print(f"❌ Weather error: {str(e)}")

            # Prepare AI data
            data = {
                "weather": safe_get(forecast_data, "today", default={}),
                "today_tasks": safe_get(tasks, "today_due", default=[]),
                "in_progress_tasks": safe_get(tasks, "in_progress", default=[]),
                "future_tasks": safe_get(tasks, "future", default=[])
            }

            # Generate advice
            try:
                print("💡 Generating AI advice...")
                advice = email_advice_with_ai(
                    data,
                    user_info["GPT_VERSION"],
                    user_info["PRESENT_LOCATION"],
                    user_info["USER_CAREER"],
                    local_time,
                    user_info["SCHEDULE_PROMPT"]
                )
            except Exception as e:
                print(f"❌ AI error: {str(e)}")
                advice = "Could not generate advice"

            # Send email
            try:
                print("📨 Sending email...")
                send_email(
                    body=format_email(advice, user_info["USER_NAME"], "Morning Digest"),
                    email_receiver=user_info["EMAIL_RECEIVER"],
                    email_title=user_info["EMAIL_TITLE"],
                    timeoffset=time_zone_offset
                )
                print("✅ Email sent successfully")
            except Exception as e:
                print(f"❌ Email error: {str(e)}")

        except Exception as e:
            print(f"⚠️ Error processing {user_id}: {str(e)}")
            continue

    print("\n✅ Morning digest process completed")

if __name__ == "__main__":
    send_morning_digest()
