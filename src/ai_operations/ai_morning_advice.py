import openai
from zhipuai import ZhipuAI
from config import AI_API_KEY
from src.ai_operations.ai_iterator import iterator
import re

def email_advice_with_ai(data, ai_version, present_location, user_career, local_time, schedule_prompt=""):
    print("\nGenerating morning advice with GPT...")
    try:
        prompt_info = f"""
        1. 基础信息：
        - 天气信息：{data['weather']}
        - 雇主职业：{user_career}
        - 雇主所在地：{present_location}
        - 现在的时间：{local_time}
        - 雇主的时间安排需求：{schedule_prompt}

        2. 今日任务：
        - 紧急任务（今日到期）：{data['today_tasks']}
        - 进行中任务：{data['in_progress_tasks']}
        - 剩余天数：从任务属性中提取剩余天数
        - ETA状态：从任务属性中提取# ETA标记

        3. 其他信息：
        - 优先级分类：高（High）、中（Medium）、低（Low）
        """

        prompt_for_iter = f"""
        请根据以下任务属性生成优先级排序：
        1. 紧急任务（剩余天数 ≤1 或 Priority=High）
        2. 高优先级任务（Priority=High）
        3. 中优先级任务（Priority=Medium）
        4. 低优先级任务（Priority=Low）
        对每个任务标注剩余天数和ETA状态。
        """
        
        ai_schedule = iterator(prompt_for_iter, ai_version)

        prompt = f"""
        <!-- 修改后的HTML模板 -->
        <div class="section">
            <div class="section-header">
                <h2>📅 今日任务概览</h2>
            </div>
            <div class="section-content">
                <ul class="task-list">
                    {{% for task in tasks %}}
                    <li class="task-item">
                        <span class="priority-{task['Priority'].lower()}">{{task['Priority']}}</span>
                        <div class="task-details">
                            <h3>{{task['Name']}}</h3>
                            <p class="deadline">剩余天数: {{task['RemainingDays']}}</p>
                            <p class="eta">{{ '✅ ETA达成' if task['ETA'] else '⏳ 进行中' }}</p>
                        </div>
                    </li>
                    {{% endfor %}}
                </ul>
            </div>
        </div>
        """

        system_content = f"""
        作为私人秘书，请根据以下规则生成晨报：
        1. 按优先级（High > Medium > Low）排序任务
        2. 显示剩余天数和ETA状态
        3. 移除所有事件相关的内容
        直接输出HTML，不要Markdown。
        """

        # [保留原有的API调用逻辑]
        # ...
        
        return formatted_html

    except Exception as e:
        print(f"Error: {e}")
        return "生成晨报时出错"