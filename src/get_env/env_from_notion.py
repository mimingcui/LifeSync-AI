import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()  # ✅ ensure .env is loaded even when called by another script

def get_user_env_vars():
    token = os.getenv("ENV_NOTION_TOKEN")
    db_id = os.getenv("ENV_DATABASE_ID")

    try:
        notion = Client(auth=token)
        response = notion.databases.query(database_id=db_id)
        # parse and return config
        return {
            result["properties"]["USER_ID"]["title"][0]["plain_text"]: {
                key: result["properties"][key]["rich_text"][0]["plain_text"]
                if "rich_text" in result["properties"][key]
                else "MISSING"
                for key in result["properties"]
            }
            for result in response["results"]
        }

    except Exception as e:
        print(f"❌ Error fetching user data from Notion: {str(e)}")
        return {}
