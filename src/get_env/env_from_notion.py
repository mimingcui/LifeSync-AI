from notion_client import Client
from config import ENV_NOTION_TOKEN, ENV_DATABASE_ID

def get_user_env_vars():
    print("get users' enviroments' variables")
    # 查询数据库
    notion = Client(auth=ENV_NOTION_TOKEN)
    response = notion.databases.query(ENV_DATABASE_ID)

    # DEBUG: Print raw Notion response
    print("\n⚠️ DEBUG - RAW NOTION RESPONSE:")
    import json
    print(json.dumps(response, indent=2, default=str))

    # 存储用户环境变量的字典
    user_env_vars = {}

    # 遍历每个页面（数据库中的行）
    for page in response.get("results", []):
        user_id = (
            page.get('properties', {})
               .get('USER_ID', {})
               .get('title', [{}])[0]  # Default empty dict if no title
               .get('text', {})
               .get('content', 'MISSING_USER_ID')  # Fallback value
        )
        
        if not user_id:
            user_id = (
                page.get('properties', {})
                   .get('USER_ID', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            )
        
        if not user_id:
            print(f"⛔ MALFORMED ENTRY: {page['id']}")
            print("Required properties missing:")
            print(json.dumps(page['properties'], indent=2))
            raise SystemExit("Fix Notion database configuration")
            
        # 假设数据库中有如下属性
        user_env_vars[user_id] = {
            "USER_NAME": (
                page.get('properties', {})
                   .get('USER_NAME', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "USER_CAREER": (
                page.get('properties', {})
                   .get('USER_CAREER', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "PRESENT_LOCATION": (
                page.get('properties', {})
                   .get('PRESENT_LOCATION', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "SCHEDULE_PROMPT": (
                page.get('properties', {})
                   .get('SCHEDULE_PROMPT', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "GPT_VERSION": (
                page.get('properties', {})
                   .get('GPT_VERSION', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "USER_NOTION_TOKEN": (
                page.get('properties', {})
                   .get('USER_NOTION_TOKEN', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "USER_DATABASE_ID": (
                page.get('properties', {})
                   .get('USER_DATABASE_ID', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "USER_EVENT_DATABASE_ID": (
                page.get('properties', {})
                   .get('USER_EVENT_DATABASE_ID', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "EMAIL_RECEIVER": (
                page.get('properties', {})
                   .get('EMAIL_RECEIVER', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "TIME_ZONE": (
                page.get('properties', {})
                   .get('TIME_ZONE', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
            "EMAIL_TITLE": (
                page.get('properties', {})
                   .get('EMAIL_TITLE', {})
                   .get('rich_text', [{}])[0]
                   .get('text', {})
                   .get('content', '')
            ),
        }
    print("Enviroments' variables fetched.")
    # print(user_env_vars)
    return user_env_vars

# # 假设已经运行了 get_user_env_vars 函数并保存了返回值
# user_data = get_user_env_vars()

# # 指定用户ID
# user_id = "user123"

# # 检查是否有这个用户的数据
# if user_id in user_data:
#     # 获取特定用户的用户名
#     username = user_data[user_id]["USERNAME"]
#     # 获取特定用户的时区
#     time_zone = user_data[user_id]["TIME_ZONE"]
    
#     print(f"Username for {user_id}: {username}")
#     print(f"Time Zone for {user_id}: {time_zone}")
# else:
#     print(f"No data available for user ID: {user_id}")
