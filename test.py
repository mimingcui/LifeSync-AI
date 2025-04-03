import pytz
from datetime import datetime
from src.send_email.format_email import format_email
from src.get_notion.task_from_notion import fetch_tasks_from_notion  # Updated path
from src.send_email.email_notifier import send_email
from src.ai_operations.ai_morning_advice import email_advice_with_ai
from src.get_weather import get_weather_forecast  
from src.get_env.env_from_notion import get_user_env_vars

def safe_get(dictionary, *keys, default=None):
    """Safely retrieve nested values from dictionaries/lists"""
    current = dictionary
    for key in keys:
        try:
            current = current[key]
        except (KeyError, TypeError, IndexError):
            return default
    return current

# Get the current time in UTC
utc_now = datetime.now(pytz.utc)

try:
    user_data = get_user_env_vars()
except Exception as e:
    print(f"Failed to get user data: {str(e)}")
    exit(1)

for user_id in user_data:
    try:
        # Validate required configuration
        required_keys = [
            "USER_NOTION_TOKEN", "USER_DATABASE_ID", "GPT_VERSION",
            "PRESENT_LOCATION", "USER_NAME", "USER_CAREER",
            "SCHEDULE_PROMPT", "TIME_ZONE", "EMAIL_RECEIVER", "EMAIL_TITLE"
        ]
        
        if any(key not in user_data[user_id] for key in required_keys):
            print(f"Skipping user {user_id} - missing configuration")
            continue

        config = user_data[user_id]
        time_zone_offset = int(config["TIME_ZONE"])
        
        present_location = config["PRESENT_LOCATION"]

        
        # Convert UTC time to user's local time
        user_tz = pytz.FixedOffset(time_zone_offset * 60)
        local_time = utc_now.astimezone(user_tz)
        custom_date = local_time.date()

        print(f"\nProcessing {config['USER_NAME']} ({local_time})")

        # Fetch tasks with safe fallback
        tasks = fetch_tasks_from_notion(
            custom_date,
            config["USER_NOTION_TOKEN"],
            config["USER_DATABASE_ID"],
            time_zone_offset
        ) or {}

        
        # Get weather data
        forecast_data = get_weather_forecast(present_location, time_zone_offset)

        data = {
            "weather": forecast_data,  # Direct dictionary access
            "today_tasks": tasks.get("today_due", []),
            "in_progress_tasks": tasks.get("in_progress", []),
            "future_tasks": tasks.get("future", [])
        }

        # Generate advice
        advice = email_advice_with_ai(
            data,
            config["GPT_VERSION"],
            config["PRESENT_LOCATION"],
            config["USER_CAREER"],
            local_time,
            config["SCHEDULE_PROMPT"]
        )

        # Format and send email
        email_body = format_email(advice, config["USER_NAME"], "Morning Brief")
        send_email(
            body=email_body,
            email_receiver=config["EMAIL_RECEIVER"],
            email_title=config["EMAIL_TITLE"],
            timeoffset=time_zone_offset
        )

        print("✅ Email processed successfully")

    except Exception as e:
        print(f"Failed to process user {user_id}: {str(e)}")
        continue
