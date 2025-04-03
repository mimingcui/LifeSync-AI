# Modify property access to handle empty lists
def get_user_env_vars():
    try:
        notion = Client(auth=os.environ.get("NOTION_TOKEN"))
        db_id = os.environ.get("USER_ENV_DATABASE_ID")
        
        if not db_id:
            raise ValueError("USER_ENV_DATABASE_ID environment variable not set")

        results = notion.databases.query(db_id)
        
        if not results.get("results"):
            raise ValueError("No entries found in user config database")

        user_data = {}
        for page in results["results"]:
            try:
                props = page.get('properties', {})
                
                # Safe USER_ID extraction
                user_id = "".join(
                    t["text"]["content"] 
                    for t in props.get("USER_ID", {}).get("title", [])
                ) or "MISSING_USER_ID"

                # Safe property access with empty list handling
                def get_rich_text(content):
                    rich_text = props.get(content, {}).get("rich_text", [])
                    return rich_text[0]["text"]["content"] if rich_text else ""

                user_config = {
                    "USER_NOTION_TOKEN": get_rich_text("USER_NOTION_TOKEN"),
                    "USER_DATABASE_ID": get_rich_text("USER_DATABASE_ID"),
                    "TIME_ZONE": get_rich_text("TIME_ZONE"),
                    "PRESENT_LOCATION": get_rich_text("PRESENT_LOCATION"),
                    "USER_NAME": get_rich_text("USER_NAME"),
                    "USER_CAREER": get_rich_text("USER_CAREER"),
                    "EMAIL_RECEIVER": get_rich_text("EMAIL_RECEIVER"),
                    "EMAIL_TITLE": get_rich_text("EMAIL_TITLE"),
                    "GPT_VERSION": get_rich_text("GPT_VERSION"),
                    "SCHEDULE_PROMPT": get_rich_text("SCHEDULE_PROMPT")
                }

                if all(user_config.values()):  # Only add complete configs
                    user_data[user_id] = user_config
                    
            except Exception as e:
                print(f"Skipping invalid entry: {str(e)}")
                continue

        return user_data

    except Exception as e:
        print(f"Environment Error: {str(e)}")
        return {}