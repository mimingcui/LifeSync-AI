from notion_client import Client
import os

def get_user_env_vars():
    """Fetch user configs from Notion with robust error handling"""
    try:
        notion = Client(auth=os.environ.get("ENV_NOTION_TOKEN"))
        db_id = os.environ.get("ENV_DATABASE_ID")
        
        if not db_id:
            raise ValueError("🚨 ENV_DATABASE_ID environment variable missing")

        print(f"🔄 Querying Notion database: {db_id}")
        response = notion.databases.query(db_id)
        
        # Critical check for empty database
        if not response.get("results"):
            raise ValueError("🚨 Database is empty or integration lacks access")

        user_data = {}
        
        for page in response["results"]:
            try:
                props = page.get('properties', {})
                
                # 1. Safely extract USER_ID
                user_id = "".join(
                    t["text"]["content"] 
                    for t in props.get("USER_ID", {}).get("title", [])
                ) or "MISSING_USER_ID"
                
                if user_id == "MISSING_USER_ID":
                    print("⚠️ Skipping entry with missing USER_ID")
                    continue

                # 2. Safe property access with empty-list protection
                def safe_rich_text(prop_name):
                    items = props.get(prop_name, {}).get("rich_text", [])
                    return items[0]["text"]["content"] if items else ""
                
                # 3. Validate critical fields
                config = {
                    "USER_NOTION_TOKEN": safe_rich_text("USER_NOTION_TOKEN"),
                    "USER_DATABASE_ID": safe_rich_text("USER_DATABASE_ID"),
                    "TIME_ZONE": safe_rich_text("TIME_ZONE"),
                    "PRESENT_LOCATION": safe_rich_text("PRESENT_LOCATION"),
                    "EMAIL_RECEIVER": safe_rich_text("EMAIL_RECEIVER")
                }
                
                # 4. Skip incomplete configs
                if not all(config.values()):
                    print(f"🚨 Incomplete config for user {user_id}")
                    continue

                user_data[user_id] = config
                
            except Exception as e:
                print(f"⚠️ Skipping invalid page: {str(e)}")
                continue

        return user_data

    except Exception as e:
        print(f"🔥 CRITICAL FAILURE: {str(e)}")
        return {}f