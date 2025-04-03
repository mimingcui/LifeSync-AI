import os
import re
import pytz
from datetime import datetime
from typing import Dict, Any, List, Union

def safe_get(dictionary, *keys, default=None):
    """Safely retrieve nested values from dictionaries/lists."""
    current = dictionary
    for key in keys:
        try:
            current = current[key]
        except (KeyError, IndexError, TypeError):
            return default
    return current

# ----- Configuration -----
def validate_config(user_config: Dict) -> None:
    """Validate required configuration keys"""
    required_keys = {
        "USER_NOTION_TOKEN", "USER_DATABASE_ID",
        "GPT_VERSION", "PRESENT_LOCATION", "USER_NAME",
        "USER_CAREER", "SCHEDULE_PROMPT", "TIME_ZONE",
        "EMAIL_RECEIVER", "EMAIL_TITLE"
    }
    
    missing = required_keys - user_config.keys()
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")

# ----- Data Fetching -----
def fetch_user_data(config: Dict) -> Dict:
    """Fetch user data from Notion with error wrapping"""
    try:
        from src.get_env.env_from_notion import get_user_env_vars
        return get_user_env_vars()
    except ImportError as e:
        raise RuntimeError(f"Import error: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Data fetch failed: {str(e)}") from e

def fetch_weather_data(location: str, tz_offset: int) -> Dict:
    """Get weather data with error handling"""
    try:
        from src.get_weather import get_weather_forecast
        return get_weather_forecast(location, tz_offset)
    except Exception as e:
        print(f"Weather API error: {str(e)}")
        return {}

def fetch_tasks(config: Dict, date: datetime.date, tz_offset: int) -> Dict:
    """Fetch tasks from Notion with error handling"""
    try:
        from src.get_notion.task_from_notion import fetch_tasks_from_notion
        return fetch_tasks_from_notion(
            date,
            config["USER_NOTION_TOKEN"],
            config["USER_DATABASE_ID"],
            tz_offset
        )
    except Exception as e:
        print(f"Task fetch error: {str(e)}")
        return {}

# ----- Email Processing -----
def generate_email_content(data: Dict, config: Dict) -> str:
    """Generate email body with AI advice"""
    try:
        from src.ai_operations.ai_morning_advice import email_advice_with_ai
        return email_advice_with_ai(
            data,
            config["GPT_VERSION"],
            config["PRESENT_LOCATION"],
            config["USER_CAREER"],
            datetime.now(pytz.utc).astimezone(
                pytz.FixedOffset(int(config["TIME_ZONE"]) * 60)
        ),
        config["SCHEDULE_PROMPT"]
        )
    except Exception as e:
        print(f"AI generation error: {str(e)}")
        return "Could not generate email content"

def send_digest_email(content: str, config: Dict) -> None:
    """Send email with error handling"""
    try:
        from src.send_email.email_notifier import send_email
        send_email(
            body=content,
            email_receiver=config["EMAIL_RECEIVER"],
            email_title=config["EMAIL_TITLE"],
            timeoffset=int(config["TIME_ZONE"])
        )
        print("✅ Email sent successfully")
    except Exception as e:
        print(f"Email sending failed: {str(e)}")

# ----- Main Workflow -----
def main() -> None:
    """Main execution flow"""
    print("🚀 Starting morning digest process")
    
    try:
        # Initialize core components
        utc_now = datetime.now(pytz.utc)
        print(f"UTC Time: {utc_now.isoformat()}")

        # Fetch and validate configurations
        print("\n🔧 Loading configurations...")
        user_data = fetch_user_data()
        validate_config(user_data)

        for user_id, config in user_data.items():
            if user_id == "MISSING_USER_ID":
                print("⚠️ Skipping invalid user configuration")
                continue

            print(f"\n👤 Processing user: {config['USER_NAME']}")
            
            try:
                # Calculate local time
                tz_offset = int(config["TIME_ZONE"].strip())
                local_time = utc_now.astimezone(
                    pytz.FixedOffset(tz_offset * 60)
                )
                print(f"⏰ Local time: {local_time.strftime('%Y-%m-%d %H:%M')}")

                # Fetch external data
                print("\n🌤️ Fetching weather data...")
                weather = fetch_weather_data(
                    config["PRESENT_LOCATION"],
                    tz_offset
                )

                print("\n📋 Fetching tasks...")
                tasks = fetch_tasks(
                    config,
                    local_time.date(),
                    tz_offset
                )

                # Prepare AI input
                ai_data = {
                    "weather": safe_get(weather, "today", default={}),
                    "today_tasks": safe_get(tasks, "today_due", default=[]),
                    "in_progress_tasks": safe_get(tasks, "in_progress", default=[]),
                    "future_tasks": safe_get(tasks, "future", default=[])
                }

                # Generate and send email
                print("\n💡 Generating email content...")
                email_body = generate_email_content(ai_data, config)
                
                print("\n📨 Sending email...")
                send_digest_email(email_body, config)

            except Exception as e:
                print(f"❌ Error processing user {user_id}: {str(e)}")
                continue

        print("\n🎉 Morning digest process completed successfully")

    except Exception as e:
        print(f"🔥 Critical failure: {str(e)}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()