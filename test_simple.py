import os
from notion_client import Client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # This loads your .env file

NOTION_TOKEN = os.getenv("ENV_NOTION_TOKEN")
DATABASE_ID = os.getenv("ENV_DATABASE_ID")

# Initialize client with proper error handling
try:
    notion = Client(auth=NOTION_TOKEN)
    
    def fetch_users():
        try:
            response = notion.databases.query(database_id=DATABASE_ID)
            print("\n=== NOTION API RESPONSE ===")
            print(f"Results count: {len(response['results'])}")
            for result in response['results']:
                user_id = result.get('properties', {}).get('USER_ID', {}).get('title', [{}])[0].get('plain_text', 'MISSING')
                print(f"\nUser ID: {user_id}")
                print("Properties:", result.get('properties').keys())
        except Exception as e:
            print(f"\n🚨 Error fetching data: {str(e)}")
            print("Verify your NOTION_TOKEN and DATABASE_ID are correct")
            print(f"Current DB ID: {DATABASE_ID}")

    if __name__ == "__main__":
        fetch_users()

except Exception as e:
    print(f"\n🔥 Failed to initialize Notion client: {str(e)}")
    print("Check your NOTION_TOKEN environment variable")