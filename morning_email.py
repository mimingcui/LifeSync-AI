# Remove event imports and references
from src.get_notion.task_from_notion import fetch_tasks_from_notion  # Keep only this
# Remove: from src.get_notion.event_from_notion import fetch_event_from_notion

# Modify required keys (remove USER_EVENT_DATABASE_ID)
required_keys = [
    "USER_NOTION_TOKEN", "USER_DATABASE_ID",  # Keep these
    "GPT_VERSION", "PRESENT_LOCATION", "USER_NAME", 
    "USER_CAREER", "SCHEDULE_PROMPT", "TIME_ZONE",
    "EMAIL_RECEIVER", "EMAIL_TITLE"
]

# Remove event fetching block
# Delete this entire block:
# try:
#     events = fetch_event_from_notion(...)
# except...

# Modify data preparation (remove event references):
data = {
    "weather": safe_get(forecast_data, "today", default={}),
    "today_tasks": safe_get(tasks, "today_due", default=[]),
    "in_progress_tasks": safe_get(tasks, "in_progress", default=[]),
    "future_tasks": safe_get(tasks, "future", default=[])
}