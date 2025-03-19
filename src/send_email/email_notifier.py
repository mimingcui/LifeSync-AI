import re
import pytz
import requests
from datetime import datetime
from config import MAILGUN_API_KEY, MAILGUN_DOMAIN  # Make sure these are properly configured

def send_email(body, email_receiver, email_title, timeoffset):
    """Send email through Mailgun API with proper validation and error handling"""
    print("Attempting to send email...")
    
    try:
        # Validate required parameters
        if not all([email_receiver, email_title, MAILGUN_API_KEY, MAILGUN_DOMAIN]):
            raise ValueError("Missing required email parameters or Mailgun credentials")

        # Clean email body
        cleaned_body = re.sub(r'```(?:html)?', '', body)

        # Calculate local time
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        timezone_str = f'Etc/GMT{"+" if timeoffset < 0 else "-"}{abs(timeoffset)}'
        local_timezone = pytz.timezone(timezone_str)
        local_now = utc_now.astimezone(local_timezone)
        custom_date = local_now.strftime('%Y-%m-%d')

        # Prepare email data
        data = {
            "from": f"LifeSync-AI <mailgun@{MAILGUN_DOMAIN}>",
            "to": [email_receiver.strip()],  # Ensure email is properly formatted
            "subject": f"{email_title} {custom_date}",
            "html": cleaned_body
        }

        # Send request to Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data=data
        )

        # Handle response
        if response.status_code == 200:
            print(f"✅ Email successfully sent to {email_receiver}")
        else:
            print(f"⚠️ Mailgun API Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"🔥 Critical email error: {str(e)}")
        raise  # Re-raise exception to handle in calling code
