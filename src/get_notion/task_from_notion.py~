from notion_client import Client
from datetime import datetime, timedelta
import pytz
import json

def fetch_tasks_from_notion(custom_date, USER_NOTION_TOKEN, USER_DATABASE_ID, timezone_offset=8, include_completed=False):
    notion = Client(auth=USER_NOTION_TOKEN)
    print("\nFetching tasks from Notion...\n")

    try:
        # Debug database schema
        db = notion.databases.retrieve(USER_DATABASE_ID)
        print("Task Database Properties:", json.dumps(db.get('properties', {}), indent=2))

        # Timezone handling
        user_tz = pytz.FixedOffset(timezone_offset * 60)
        utc = pytz.utc

        # Date range calculation
        today_start = datetime.combine(custom_date, datetime.min.time()).replace(tzinfo=user_tz)
        today_end = today_start + timedelta(days=1)

        # Convert to UTC for Notion query
        today_start_utc = today_start.astimezone(utc)
        today_end_utc = today_end.astimezone(utc)

        # Query with UTC dates
        results = notion.databases.query(
            database_id=USER_DATABASE_ID,
            filter={
                "property": "Date",
                "date": {
                    "on_or_after": today_start_utc.isoformat(),
                    "before": today_end_utc.isoformat()
                }
            }
        )

        tasks = {"today_due": [], "in_progress": [], "future": [], "completed": []}

        for row in results.get("results", []):
            try:
                # Extract date property
                date_prop = row.get('properties', {}).get('Date', {}).get('date', {})
                if not date_prop:
                    print("Skipping task: No date property")
                    continue

                # Parse start and end dates with UTC conversion
                start_utc = datetime.fromisoformat(date_prop['start'].replace('Z', '+00:00')).astimezone(utc)
                end_utc = datetime.fromisoformat(date_prop['end'].replace('Z', '+00:00')).astimezone(utc) if date_prop.get('end') else None

                # Convert to user timezone
                start_local = start_utc.astimezone(user_tz)
                end_local = end_utc.astimezone(user_tz) if end_utc else None

                # Extract other properties safely
                urgency = row.get('properties', {}).get('Urgency', {}).get('select', {}).get('name', 'NA')

                description = (
                    row.get('properties', {}).get('Description', {}).get('rich_text', [{}])[0]
                    .get('text', {}).get('content', '')
                ).replace('\n', ' ').strip()

                # Fix: Correct task name extraction
                name = ''.join(
                    t.get('text', {}).get('content', '') 
                    for t in row.get('properties', {}).get('Name', {}).get('title', [])
                ).strip()

                task = {
                    'Name': name or "Untitled",
                    'Start': start_local.strftime('%Y-%m-%d %H:%M'),
                    'End': end_local.strftime('%Y-%m-%d %H:%M') if end_local else 'N/A',
                    'Urgency': urgency,
                    'Completed': row.get('properties', {}).get('Complete', {}).get('checkbox', False)
                }

                # Classification logic
                if task['Completed']:
                    if include_completed:
                        tasks["completed"].append(task)
                else:
                    if end_local and end_local.date() == custom_date:
                        tasks["today_due"].append(task)
                    elif start_local.date() <= custom_date:
                        tasks["in_progress"].append(task)
                    elif start_local.date() > custom_date:
                        tasks["future"].append(task)

            except Exception as e:
                print(f"Skipping task due to error: {str(e)}")
                continue

        return tasks

    except Exception as e:
        print(f"Task Error: {str(e)}")
        return {k: [] for k in ["today_due", "in_progress", "future", "completed"]}
