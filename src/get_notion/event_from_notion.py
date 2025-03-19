from notion_client import Client
from datetime import datetime, timedelta
import pytz

def fetch_event_from_notion(custom_date, USER_NOTION_TOKEN, USER_DATABASE_ID, timezone_offset=8, include_completed=False):
    notion = Client(auth=USER_NOTION_TOKEN)
    print("\nFetching events from Notion...\n")
    
    try:
        user_tz = pytz.FixedOffset(timezone_offset * 60)
        utc = pytz.utc
        
        # Date range setup
        today_start = datetime.combine(custom_date, datetime.min.time()).replace(tzinfo=user_tz)
        today_end = today_start + timedelta(days=1)
        future_date = custom_date + timedelta(days=30)
        current_time = datetime.now(user_tz)

        results = notion.databases.query(
            database_id=USER_DATABASE_ID,
            filter={
                "property": "Date",
                "date": {"is_not_empty": True}
            }
        )

        events = {"in_progress": [], "tomorrow": [], "upcoming": [], "completed": []}

        for row in results.get("results", []):
            try:
                date_prop = row['properties'].get('Date', {}).get('date', {})
                if not date_prop:
                    continue

                # UTC-based parsing
                start_utc = datetime.fromisoformat(date_prop['start'].replace('Z', '+00:00')).astimezone(utc)
                end_utc = datetime.fromisoformat(date_prop['end'].replace('Z', '+00:00')).astimezone(utc) if date_prop.get('end') else None
                
                # Local time conversion
                start_local = start_utc.astimezone(user_tz)
                end_local = end_utc.astimezone(user_tz) if end_utc else None

                event = {
                    'Name': ''.join([t['text']['content'] for t in row['properties']['Name'].get('title', [])]),
                    'Start': start_local.strftime('%Y-%m-%d %H:%M'),
                    'End': end_local.strftime('%Y-%m-%d %H:%M') if end_local else 'N/A',
                    'Location': (row['properties']
                        .get('Location', {})
                        .get('rich_text', [{}])[0]
                        .get('text', {})
                        .get('content', 'No location')),
                    'Status': 'Completed' if end_local and end_local < current_time else 'In Progress'
                }

                # Date comparisons using local dates
                event_date = start_local.date()
                if event_date == custom_date:
                    events["in_progress"].append(event)
                elif event_date == custom_date + timedelta(days=1):
                    events["tomorrow"].append(event)
                elif custom_date + timedelta(days=2) <= event_date <= future_date:
                    events["upcoming"].append(event)
                elif include_completed and end_local and end_local.date() == custom_date:
                    events["completed"].append(event)

            except Exception as e:
                print(f"Skipping event: {str(e)}")
                continue

        return events

    except Exception as e:
        print(f"Event Error: {str(e)}")
        return {k: [] for k in ["in_progress", "tomorrow", "upcoming", "completed"]}