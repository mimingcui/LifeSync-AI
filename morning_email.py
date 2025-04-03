import re
import pytz
from datetime import datetime
from src.send_email.format_email import format_email
from src.get_notion.task_from_notion import fetch_tasks_from_notion
from src.send_email.email_notifier import send_email
from src.ai_operations.ai_morning_advice import email_advice_with_ai
from src.get_weather import get_weather_forecast  
from src.get_env.env_from_notion import get_user_env_vars
from src.get_notion.event_from_notion import fetch_event_from_notion

def safe_get(dictionary, *keys, default=None):
    """Safely retrieve nested dictionary values."""
    for key in keys:
        try:
            dictionary = dictionary[key]
        except (KeyError, TypeError):
            return default
    return dictionary

def validate_user_config(user_data):
    """Ensure at least one valid user configuration exists"""
    valid_users = [uid for uid in user_data if uid != "MISSING_USER_ID"]
    
    if not valid_users:
        raise SystemExit("⛔ CRITICAL ERROR: No valid user configurations found. "
                         "Check Notion database for USER_ID and TIME_ZONE values.")

def send_morning_digest():
    utc_now = datetime.now(pytz.utc)
    user_data = get_user_env_vars()
    validate_user_config(user_data)

    for user_id in user_data:
        if user_id == "MISSING_USER_ID":
            print(f"⛔ Configuration Error - Fix these issues:")
            print(f"1. Ensure USER_ID is a 'Title' property in Notion")
            print(f"2. Verify TIME_ZONE is set (e.g., '-4')")
            print(f"3. Check integration has database access")
            raise SystemExit("Critical configuration error - see details above")
        
        try:
            user_info = user_data[user_id]
            required_keys = [
                "USER_NOTION_TOKEN", "USER_DATABASE_ID", "USER_EVENT_DATABASE_ID",
                "GPT_VERSION", "PRESENT_LOCATION", "USER_NAME", "USER_CAREER",
                "SCHEDULE_PROMPT", "TIME_ZONE", "EMAIL_RECEIVER", "EMAIL_TITLE"
            ]
            
            for key in required_keys:
                if key not in user_info:
                    raise ValueError(f"Missing required key: {key}")
            
            # Process time zone
            time_zone_str = user_info["TIME_ZONE"].strip()
            if not re.match(r"^[+-]?\d+$", time_zone_str):
                print(f"⚠️ Invalid TIME_ZONE '{time_zone_str}' for {user_id}. Using UTC.")
                time_zone_offset = 0
            else:
                time_zone_offset = int(time_zone_str)
            
            tz_str = f'Etc/GMT{"+" if time_zone_offset < 0 else "-"}{abs(time_zone_offset)}'
            local_time = utc_now.astimezone(pytz.timezone(tz_str))
            custom_date = local_time.date()
            print(f"\nProcessing {user_id} ({user_info['USER_NAME']})")
            print(f"Local time: {local_time}")
            
            # Fetch data with error handling
            try:
                tasks = fetch_tasks_from_notion(
                    custom_date,
                    user_info["USER_NOTION_TOKEN"],
                    user_info["USER_DATABASE_ID"],
                    time_zone_offset,
                    include_completed=False
                )
            except Exception as e:
                print(f"❌ Failed to fetch tasks: {str(e)}")
                tasks = {}

            try:
                events = fetch_event_from_notion(
                    custom_date,
                    user_info["USER_NOTION_TOKEN"],
                    user_info["USER_EVENT_DATABASE_ID"],
                    time_zone_offset,
                    include_completed=False
                )
            except Exception as e:
                print(f"❌ Failed to fetch events: {str(e)}")
                events = {}

            try:
                forecast_data = get_weather_forecast(
                    user_info["PRESENT_LOCATION"],
                    time_zone_offset
                )
            except Exception as e:
                print(f"❌ Weather API error: {str(e)}")
                forecast_data = {}
            
            # Prepare data with fallback values
            data = {
                "weather": safe_get(forecast_data, "today", default={}),
                "today_tasks": safe_get(tasks, "today_due", default=[]),
                "in_progress_tasks": safe_get(tasks, "in_progress", default=[]),
                "future_tasks": safe_get(tasks, "future", default=[]),
                "in_progress_events": safe_get(events, "in_progress", default=[]),
                "future_events": safe_get(events, "upcoming", default=[])
            }
            
            # Generate AI advice
            try:
                advice = email_advice_with_ai(
                    data,
                    user_info["GPT_VERSION"],
                    user_info["PRESENT_LOCATION"],
                    user_info["USER_CAREER"],
                    local_time,
                    user_info["SCHEDULE_PROMPT"]
                )
                print("AI Advice generated successfully")
            except Exception as e:
                print(f"❌ AI advice generation failed: {str(e)}")
                advice = "No advice generated due to system error"
            
            # Prepare and send email
            email_body = format_email(
                advice, 
                user_info["USER_NAME"], 
                "日程早报",  # Morning Brief
                "morning"
            )
            
            try:
                send_email(
                    body=email_body,
                    email_receiver=user_data[user_id]["EMAIL_RECEIVER"],
                    email_title=user_data[user_id]["EMAIL_TITLE"],
                    timeoffset=time_zone_offset
                )
            except KeyError as e:
                print(f"⚠️ Missing email configuration for user {user_id}: {str(e)}")
            except ValueError as e:
                print(f"⚠️ Invalid email configuration: {str(e)}")
            except Exception as e:
                print(f"🔥 Unexpected error sending email: {str(e)}")
            
        except Exception as e:
            print(f"🔥 Critical error processing {user_id}: {str(e)}")
            continue
    
    print("\nMorning email processing completed")

if __name__ == "__main__":
    send_morning_digest()
