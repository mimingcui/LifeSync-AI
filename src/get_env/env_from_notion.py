from notion_client import Client
from config import ENV_NOTION_TOKEN, ENV_DATABASE_ID
import json

def safe_get_property(prop, prop_type, default=''):
    """Safely retrieve property values from Notion response"""
    try:
        items = prop.get(prop_type, [{}])
        if not items or not items[0].get('text', {}).get('content'):
            return default
        return items[0]['text']['content']
    except (IndexError, KeyError):
        return default

def get_user_env_vars():
    print("Fetching user environment variables...")
    notion = Client(auth=ENV_NOTION_TOKEN)
    
    try:
        response = notion.databases.query(ENV_DATABASE_ID)
    except Exception as e:
        print(f"⛔ Database query failed: {str(e)}")
        return {}

    user_env_vars = {}

    # Debug raw response (uncomment if needed)
    # print("\n⚠️ DEBUG - RAW NOTION RESPONSE:")
    # print(json.dumps(response, indent=2, default=str))

    for page in response.get("results", []):
        props = page.get('properties', {})
        
        # Get USER_ID from title or rich_text
        user_id = safe_get_property(props.get('USER_ID', {}), 'title', 'MISSING_USER_ID')
        if user_id == 'MISSING_USER_ID':
            user_id = safe_get_property(props.get('USER_ID', {}), 'rich_text', 'MISSING_USER_ID')
        
        if user_id == 'MISSING_USER_ID':
            print(f"⏭️ Skipping entry with missing USER_ID (Page ID: {page['id']})")
            continue

        # Validate required fields
        required_fields = {
            'USER_NOTION_TOKEN': safe_get_property(props.get('USER_NOTION_TOKEN', {}), 'rich_text'),
            'USER_DATABASE_ID': safe_get_property(props.get('USER_DATABASE_ID', {}), 'rich_text')
        }
        
        if not all(required_fields.values()):
            print(f"⏭️ Skipping user {user_id} - missing required fields")
            continue

        # Build user config
        user_config = {
            "USER_NAME": safe_get_property(props.get('USER_NAME', {}), 'rich_text'),
            "USER_CAREER": safe_get_property(props.get('USER_CAREER', {}), 'rich_text'),
            "PRESENT_LOCATION": safe_get_property(props.get('PRESENT_LOCATION', {}), 'rich_text'),
            "SCHEDULE_PROMPT": safe_get_property(props.get('SCHEDULE_PROMPT', {}), 'rich_text'),
            "GPT_VERSION": safe_get_property(props.get('GPT_VERSION', {}), 'rich_text'),
            "EMAIL_RECEIVER": safe_get_property(props.get('EMAIL_RECEIVER', {}), 'rich_text'),
            "TIME_ZONE": safe_get_property(props.get('TIME_ZONE', {}), 'rich_text'),
            "EMAIL_TITLE": safe_get_property(props.get('EMAIL_TITLE', {}), 'rich_text'),
            **required_fields
        }

        # Optional: Event database ID (only if needed)
        if 'USER_EVENT_DATABASE_ID' in props:
            user_config["USER_EVENT_DATABASE_ID"] = safe_get_property(
                props.get('USER_EVENT_DATABASE_ID', {}), 'rich_text'
            )

        user_env_vars[user_id] = user_config

    print("✅ Environment variables fetched successfully")
    return user_env_vars