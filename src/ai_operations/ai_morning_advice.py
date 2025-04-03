# morning_email.py
import re
import pytz
from datetime import datetime
from send_email.format_email import format_email
from get_notion.task_from_notion import fetch_tasks_from_notion
from send_email.email_notifier import send_email
from ai_operations.ai_morning_advice import email_advice_with_ai
from get_weather import get_weather_forecast
from get_env.env_from_notion import get_user_env_vars

def safe_get(dictionary, *keys, default=None):
    """Safely retrieve nested dictionary values"""
    current = dictionary
    for key in keys:
        try:
            current = current[key]
        except (KeyError, TypeError, IndexError):
            return default
    return current

def validate_user_config(user_data):
    """Ensure valid user configurations exist"""
    valid_users = [uid for uid in user_data if uid != "MISSING_USER_ID"]
    
    if not valid_users:
        raise SystemExit("CRITICAL ERROR: No valid user configurations found. Check Notion database.")

def send_morning_digest():
    utc_now = datetime.now(pytz.utc)
    
    try:
        print("Fetching user configurations...")
        user_data = get_user_env_vars()
    except Exception as e:
        raise SystemExit(f"Failed to fetch user environment variables: {str(e)}")

    validate_user_config(user_data)

    for user_id in user_data:
        if user_id == "MISSING_USER_ID":
            print("Configuration Error - Fix these issues:")
            print("1. Ensure USER_ID exists in Notion")
            print("2. Verify TIME_ZONE is set")
            print("3. Check integration permissions")
            raise SystemExit("Critical configuration error")

        try:
            user_info = user_data[user_id]
            required_keys = [
                "USER_NOTION_TOKEN", "USER_DATABASE_ID",
                "GPT_VERSION", "PRESENT_LOCATION", "USER_NAME", "USER_CAREER",
                "SCHEDULE_PROMPT", "TIME_ZONE", "EMAIL_RECEIVER", "EMAIL_TITLE"
            ]
            
            # Validate required keys
            missing_keys = [key for key in required_keys if key not in user_info]
            if missing_keys:
                raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")

            # Process time zone
            try:
                time_zone_offset = int(user_info["TIME_ZONE"].strip())
            except ValueError:
                print(f"Invalid TIME_ZONE value, using UTC")
                time_zone_offset = 0

            tz_str = f'Etc/GMT{"+" if time_zone_offset < 0 else "-"}{abs(time_zone_offset)}'
            local_time = utc_now.astimezone(pytz.timezone(tz_str))
            custom_date = local_time.date()
            
            print(f"\nProcessing {user_id} ({user_info['USER_NAME']})")
            print(f"Local time: {local_time}")

            # Fetch data with error handling
            tasks = {}
            try:
                print("Fetching tasks...")
                tasks = fetch_tasks_from_notion(
                    custom_date,
                    user_info["USER_NOTION_TOKEN"],
                    user_info["USER_DATABASE_ID"],
                    time_zone_offset
                )
            except Exception as e:
                print(f"Task fetch error: {str(e)}")

            forecast_data = {}
            try:
                print("Fetching weather...")
                forecast_data = get_weather_forecast(
                    user_info["PRESENT_LOCATION"],
                    time_zone_offset
                )
            except Exception as e:
                print(f"Weather API error: {str(e)}")

            # Prepare data with safe defaults
            data = {
                "weather": safe_get(forecast_data, "today", default={}),
                "today_tasks": safe_get(tasks, "today_due", default=[]),
                "in_progress_tasks": safe_get(tasks, "in_progress", default=[]),
                "future_tasks": safe_get(tasks, "future", default=[])
            }

            # Generate advice
            try:
                print("Generating AI advice...")
                advice = email_advice_with_ai(
                    data,
                    user_info["GPT_VERSION"],
                    user_info["PRESENT_LOCATION"],
                    user_info["USER_CAREER"],
                    local_time,
                    user_info["SCHEDULE_PROMPT"]
                )
            except Exception as e:
                print(f"AI advice error: {str(e)}")
                advice = "No AI advice generated"

            # Prepare and send email
            try:
                print("Sending email...")
                send_email(
                    body=format_email(advice, user_info["USER_NAME"], "Morning Digest"),
                    email_receiver=user_info["EMAIL_RECEIVER"],
                    email_title=user_info["EMAIL_TITLE"],
                    timeoffset=time_zone_offset
                )
            except Exception as e:
                print(f"Email send error: {str(e)}")

        except Exception as e:
            print(f"Error processing user {user_id}: {str(e)}")
            continue

    print("\nMorning email processing completed")

if __name__ == "__main__":
    send_morning_digest()