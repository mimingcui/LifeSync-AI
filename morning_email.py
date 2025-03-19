import pytz
from datetime import datetime
from src.send_email.format_email import format_email
from src.get_notion.task_from_notion import fetch_tasks_from_notion
from src.send_email.email_notifier import send_email
from src.ai_operations.ai_morning_advice import email_advice_with_ai
from src.get_weather import get_weather_forecast  # Fixed typo 'wheather' to 'weather'
from src.get_env.env_from_notion import get_user_env_vars
from src.get_notion.event_from_notion import fetch_event_from_notion

def send_morning_digest():
    utc_now = datetime.now(pytz.utc)
    user_data = get_user_env_vars()

    for user_id, config in user_data.items():
        try:
            # Validate required fields
            required_keys = ["USER_NOTION_TOKEN", "USER_DATABASE_ID", "USER_EVENT_DATABASE_ID",
                            "GPT_VERSION", "PRESENT_LOCATION", "USER_NAME", 
                            "USER_CAREER", "SCHEDULE_PROMPT", "TIME_ZONE",
                            "EMAIL_RECEIVER", "EMAIL_TITLE"]
            
            if any(key not in config for key in required_keys):
                print(f"⚠️ Skipping user {user_id} - missing required config")
                continue

            # Timezone handling
            time_zone_offset = int(config["TIME_ZONE"])
            try:
                tz = pytz.timezone(f'Etc/GMT{"+" if time_zone_offset < 0 else "-"}{abs(time_zone_offset)}')
            except pytz.UnknownTimeZoneError:
                tz = pytz.UTC

            local_time = utc_now.astimezone(tz)
            custom_date = local_time.date()
            print(f"\nProcessing {config['USER_NAME']} in {tz.zone}")

            # Fetch data with error handling
            try:
                tasks = fetch_tasks_from_notion(
                    custom_date,
                    config["USER_NOTION_TOKEN"],
                    config["USER_DATABASE_ID"],
                    time_zone_offset,
                    include_completed=False
                )
                events = fetch_event_from_notion(
                    custom_date,
                    config["USER_NOTION_TOKEN"],
                    config["USER_EVENT_DATABASE_ID"],
                    time_zone_offset,
                    include_completed=False
                )
                forecast_data = get_weather_forecast(
                    config["PRESENT_LOCATION"],
                    time_zone_offset
                )
            except Exception as e:
                print(f"⚠️ Data fetch failed for {user_id}: {str(e)}")
                continue

            # Safely prepare data
            data = {
                "weather": forecast_data.get('today', {}),
                "today_tasks": tasks.get("today_due", []),
                "in_progress_tasks": tasks.get("in_progress", []),
                "future_tasks": tasks.get("future", []),
                "in_progress_events": events.get("in_progress", []),
                "future_events": events.get("upcoming", [])
            }

            # Generate advice
            try:
                advice = email_advice_with_ai(
                    data,
                    config["GPT_VERSION"],
                    config["PRESENT_LOCATION"],
                    config["USER_CAREER"],
                    local_time,
                    config["SCHEDULE_PROMPT"]
                )
            except Exception as e:
                print(f"⚠️ AI advice failed for {user_id}: {str(e)}")
                advice = "Could not generate advice - system error"

            # Prepare and send email
            email_body = format_email(
                advice, 
                config["USER_NAME"], 
                "日程晨报"  # Morning Brief
            )
            
            send_email(
                body=email_body,
                to_email=config["EMAIL_RECEIVER"],
                subject=config["EMAIL_TITLE"],
                timeoffset=time_zone_offset
            )

        except Exception as e:
            print(f"🔥 Critical error processing {user_id}: {str(e)}")
            continue

if __name__ == "__main__":
    send_morning_digest()