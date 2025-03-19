from notion_client import Client
from datetime import datetime, timedelta
import pytz

def safe_get(data, *keys, default=None):
    """Safely retrieve nested values from dictionaries"""
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError, IndexError):
            return default
    return data

def fetch_tasks_from_notion(custom_date, USER_NOTION_TOKEN, USER_DATABASE_ID, timezone_offset=8, include_completed=False):
    """
    Enhanced version with comprehensive error handling
    """
    notion = Client(auth=USER_NOTION_TOKEN)
    print("\nFetching tasks from Notion...\n")
    
    try:
        # Timezone handling
        tz = pytz.FixedOffset(timezone_offset * 60)
        today = custom_date
        tomorrow = today + timedelta(days=1)
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=tz)
        today_end = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=tz)

        # Query with safe property name
        filter_conditions = {
            "and": [
                {
                    "property": "Date",  # Make sure this matches Notion's property name exactly
                    "date": {"is_not_empty": True}
                }
            ]
        }

        # Safe database query
        try:
            results = notion.databases.query(
                database_id=USER_DATABASE_ID,
                filter=filter_conditions
            )
        except Exception as query_error:
            print(f"Database query failed: {str(query_error)}")
            return empty_task_structure()

        tasks = empty_task_structure()
        future_date = today + timedelta(days=30)

        for row in results.get("results", []):
            try:
                # Safe property access
                date_prop = safe_get(row, 'properties', 'Date', 'date', default={})
                last_edited_time = parse_datetime(
                    safe_get(row, 'last_edited_time'), 
                    tz
                )

                # Date handling
                start_datetime = parse_datetime(
                    safe_get(date_prop, 'start'), 
                    tz
                )
                end_datetime = parse_datetime(
                    safe_get(date_prop, 'end'), 
                    tz
                )

                # Task details
                task = {
                    'Name': extract_title(row),
                    'Description': extract_description(row),
                    'Urgency Level': safe_get(
                        row, 'properties', '紧急程度', 'select', 'name', 
                        default='NA'
                    ),
                    'Start Time': format_datetime(start_datetime),
                    'End Time': format_datetime(end_datetime),
                    'Completed': safe_get(
                        row, 'properties', 'Complete', 'checkbox', 
                        default=False
                    ),
                    'Last Edited': format_datetime(last_edited_time),
                    'Status': 'Completed' if safe_get(
                        row, 'properties', 'Complete', 'checkbox', 
                        default=False
                    ) else 'In Progress'
                }

                # Categorize tasks
                categorize_task(task, tasks, today, future_date, today_start, today_end, include_completed)

            except Exception as row_error:
                print(f"Error processing task row: {str(row_error)}")
                continue

        print("Tasks fetched successfully with error handling.")
        return tasks

    except Exception as e:
        print(f"Critical error in task processing: {str(e)}")
        return empty_task_structure()

# Helper functions
def empty_task_structure():
    return {
        "today_due": [],
        "in_progress": [],
        "future": [],
        "completed": []
    }

def parse_datetime(dt_str, tz):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00')).astimezone(tz)
    except ValueError:
        return None

def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M') if dt else 'N/A'

def extract_title(row):
    title_parts = safe_get(row, 'properties', 'Name', 'title', default=[])
    return ''.join([safe_get(p, 'text', 'content', default='') for p in title_parts]) or 'NA'

def extract_description(row):
    rich_text = safe_get(row, 'properties', 'Description', 'rich_text', default=[])
    description = ''.join([safe_get(p, 'text', 'content', default='') for p in rich_text])
    return description.replace('\n', ' ').replace('\xa0', ' ').strip() or 'NA'

def categorize_task(task, tasks, today, future_date, today_start, today_end, include_completed):
    if task['Completed']:
        if include_completed and today_start <= parse_datetime(task['Last Edited'], today_start.tzinfo) < today_end:
            tasks["completed"].append(task)
        return
    
    end_date = parse_datetime(task['End Time'], today_start.tzinfo).date() if task['End Time'] != 'N/A' else None
    start_date = parse_datetime(task['Start Time'], today_start.tzinfo).date() if task['Start Time'] != 'N/A' else None

    if end_date == today:
        tasks["today_due"].append(task)
    elif start_date and start_date <= today and (not end_date or end_date > today):
        tasks["in_progress"].append(task)
    elif start_date and today < start_date <= future_date:
        tasks["future"].append(task)
