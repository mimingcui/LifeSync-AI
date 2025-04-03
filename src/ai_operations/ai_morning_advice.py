import openai
from zhipuai import ZhipuAI
from config import AI_API_KEY
from src.ai_operations.ai_iterator import iterator
import re

def email_advice_with_ai(data, ai_version, present_location, user_career, local_time, schedule_prompt=""):
    print("\nGenerating morning advice...")
    try:
        # ========== Weather Data Handling ==========
        # Safely extract weather information with defaults
        weather_info = data.get('weather', {})
        weather_str = (
            f"Temperature: {weather_info.get('temp', 'N/A')}°C\n"
            f"Conditions: {weather_info.get('description', 'No data')}\n"
            f"Humidity: {weather_info.get('humidity', 'N/A')}%\n"
            f"Wind Speed: {weather_info.get('wind_speed', 'N/A')} m/s"
        )

        # ========== Task Data Handling ==========
        def get_task_details(task_list):
            return "\n".join([f"- {task.get('Name', 'Unnamed Task')} "
                            f"(Priority: {task.get('Priority', 'N/A')}, "
                            f"Days Left: {task.get('RemainingDays', 'N/A')}, "
                            f"ETA: {'✅' if task.get('ETA') else '⚠️'})" 
                            for task in task_list])

        # ========== Construct Prompts ==========
        prompt_info = f"""
        1. Core Information:
        - Location: {present_location}
        - Local Time: {local_time.strftime('%Y-%m-%d %H:%M')}
        - User Profession: {user_career}
        - Schedule Preferences: {schedule_prompt}

        2. Weather Conditions:
        {weather_str}

        3. Tasks:
        * Urgent (Today's Deadline):
        {get_task_details(data.get('today_tasks', []))}

        * In Progress:
        {get_task_details(data.get('in_progress_tasks', []))}

        * Future Tasks:
        {get_task_details(data.get('future_tasks', []))}
        """

        analysis_prompt = f"""
        Analyze this schedule considering:
        1. Task priority levels (High/Medium/Low)
        2. Remaining days until deadlines
        3. ETA status indicators
        4. Current weather conditions
        5. User's professional context: {user_career}
        
        Provide:
        - Time-sensitive priority ranking
        - Weather-impacted activity recommendations
        - ETA risk assessment for urgent tasks
        """

        ai_analysis = iterator(analysis_prompt, ai_version)

        # ========== HTML Template ==========
        html_template = f"""
        <div class="morning-brief">
            <h1>Morning Briefing - {local_time.strftime('%A, %B %d')}</h1>
            
            <div class="weather-section">
                <h2>🌤️ Current Weather</h2>
                <p>Temperature: {weather_info.get('temp', 'N/A')}°C</p>
                <p>Conditions: {weather_info.get('description', 'No data')}</p>
                <p>Humidity: {weather_info.get('humidity', 'N/A')}%</p>
                <p>Wind: {weather_info.get('wind_speed', 'N/A')} m/s</p>
            </div>

            <div class="task-priorities">
                <h2>🔝 Priority Tasks</h2>
                <ul>
                    {"".join([f'''
                    <li class="priority-{task.get('Priority', 'medium').lower()}">
                        <h3>{task.get('Name', 'Unnamed Task')}</h3>
                        <div class="task-meta">
                            <span class="eta">{'✅ On Track' if task.get('ETA') else '⚠️ Needs Attention'}</span>
                            <span class="days-remaining">{task.get('RemainingDays', 'N/A')} days remaining</span>
                        </div>
                        {f'<p class="task-desc">{task.get("Description", "")}</p>' if task.get("Description") else ''}
                    </li>
                    ''' for task in data.get('today_tasks', [])])}
                </ul>
            </div>

            <div class="schedule-recommendations">
                <h2>⏳ Recommended Schedule</h2>
                <div class="ai-analysis">
                    {ai_analysis}
                </div>
            </div>
        </div>
        """

        # ========== AI Configuration ==========
        system_prompt = """You are a professional scheduling assistant. Generate morning briefings that:
        - Prioritize tasks based on urgency and importance
        - Consider weather impacts on outdoor activities
        - Align with the user's professional context
        - Highlight time-sensitive commitments
        Output clean HTML without markdown formatting."""

        # ========== API Handling ==========
        if "gpt" in ai_version.lower():
            response = openai.ChatCompletion.create(
                model=ai_version,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": html_template}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content
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
            content = response.choices[0].message.content
        else:
            raise ValueError(f"Unsupported AI version: {ai_version}")

        # ========== Clean Output ==========
        return re.sub(r'<body>|</body>|```html?|```', '', content.strip())

    except Exception as e:
        print(f"Generation error: {str(e)}")
        return "Could not generate morning briefing due to system error"