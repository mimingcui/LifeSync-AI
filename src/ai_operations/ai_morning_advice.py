import openai
from zhipuai import ZhipuAI
from config import AI_API_KEY
from src.ai_operations.ai_iterator import iterator
import re

def email_advice_with_ai(data, ai_version, present_location, user_career, local_time, schedule_prompt=""):
    print("\nGenerating morning advice...")
    try:
        # Task-focused prompt information
        prompt_info = f"""
        1. Core Information:
        - Weather: {data['weather']}
        - User Career: {user_career}
        - Location: {present_location}
        - Current Time: {local_time}
        - Schedule Preferences: {schedule_prompt}

        2. Today's Tasks:
        - Urgent (Due Today): {data['today_tasks']}
        - In Progress: {data['in_progress_tasks']}
        - Future Tasks: {data['future_tasks']}
        - Priority Levels: High/Medium/Low
        - Remaining Days: From task properties
        - ETA Status: From task checkboxes
        """

        # Analysis prompt for iterator
        analysis_prompt = f"""
        Analyze today's schedule based on:
        1. Priority (High > Medium > Low)
        2. Remaining days (<=1 day = urgent)
        3. ETA status (checkbox)
        4. Schedule preferences: {schedule_prompt}
        
        Output format:
        - Top 3 prioritized tasks
        - Time allocation suggestions
        - ETA risk assessment
        """

        ai_analysis = iterator(analysis_prompt, ai_version)

        # HTML template with task properties
        html_template = f"""
        <div class="container">
            <div class="header">
                <h1>Morning Brief - {local_time.strftime('%A, %B %d')}</h1>
                <div class="weather">
                    <h3>🌤️ Weather Advisory</h3>
                    <p>{data['weather'].get('summary', 'No weather data')}</p>
                    <p>Temperature: {data['weather'].get('temp', 'N/A')}°C</p>
                </div>
            </div>

            <div class="priority-tasks">
                <h2>🔥 Critical Tasks</h2>
                <ul>
                    {{% for task in today_tasks %}}
                    <li class="priority-{{{{ task['Priority'].lower() }}}}">
                        <div class="task-header">
                            <h3>{{{{ task['Name'] }}}}</h3>
                            <span class="eta-badge">{{{{ '✅ On Track' if task['ETA'] else '⚠️ Behind Schedule' }}}}</span>
                        </div>
                        <div class="task-details">
                            <p>Priority: {{{{ task['Priority'] }}}}</p>
                            <p>Days Remaining: {{{{ task['RemainingDays'] }}}}</p>
                            <p>{{{{ task.get('Description', '') }}}}</p>
                        </div>
                    </li>
                    {{% endfor %}}
                </ul>
            </div>

            <div class="schedule">
                <h2>⏰ Recommended Schedule</h2>
                {{{{ ai_analysis }}}}
            </div>
        </div>
        """

        system_prompt = """You are an AI personal assistant generating morning briefings. 
        Focus on:
        - Task priorities (High/Medium/Low) 
        - Remaining days for completion
        - ETA status tracking
        - Weather-impacted recommendations
        Output clean HTML without markdown."""

        # API call handling (same as before)
        if "gpt" in ai_version.lower():
            response = openai.ChatCompletion.create(
                model=ai_version,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": html_template}
                ],
                temperature=0.3
            )
        elif "glm" in ai_version.lower():
            client = ZhipuAI(AI_API_KEY)
            response = client.chat.completions.create(
                model=ai_version,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": html_template}
                ],
                temperature=0.3
            )

        return re.sub(r'<body>|</body>|```html?|```', '', response.choices[0].message.content.strip())

    except Exception as e:
        print(f"Generation error: {e}")
        return "Could not generate morning briefing"