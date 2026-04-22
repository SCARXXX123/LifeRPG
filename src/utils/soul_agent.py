# import os
# import json
# import time
# from datetime import datetime
# from openai import OpenAI
# from dotenv import load_dotenv
# import httpx
# load_dotenv()
#
#
# class SoulAuditAgent:
#     def __init__(self):
#         custom_http_client = httpx.Client(
#             verify=False,
#             timeout=httpx.Timeout(300, connect=10.0)
#         )
#         self.client = OpenAI(
#             api_key=os.getenv("DEEPSEEK_API_KEY"),
#             base_url="https://api.deepseek.com",
#             http_client=custom_http_client
#         )
#         # 状态颜色代码（保持风格统一）
#         self.BLUE = "\033[94m"
#         self.GREEN = "\033[92m"
#         self.YELLOW = "\033[93m"
#         self.RED = "\033[91m"
#         self.MAGENTA = "\033[95m"
#         self.RESET = "\033[0m"
#
#     def _log(self, status, message, color=""):
#         timestamp = time.strftime("%H:%M:%S")
#         print(f"{color}[{timestamp}] [SOUL_AUDIT] [{status}] {message}{self.RESET}")
#
#     def conduct_audit(self, current_profile, combined_data):
#         """
#         [审计阶段] 基于行为数据演化存档并生成深度报告
#         """
#         self._log("AGENT_WAKE", "正在调用灵魂审计专家 DeepSeek-v3...", self.MAGENTA)
#         start_time = time.time()
#
#         system_prompt = "你是一个冷酷、毒舌、具备RPG数值平衡经验的只输出 JSON 的游戏系统审计 AI。"
#
#         user_prompt = f"""
#         任务：基于最新行为数据演化 RPG 存档并生成深度报告。
#
#         --- 当前存档 ---
#         {json.dumps(current_profile, ensure_ascii=False)}
#         --- 原始行为记录 ---
#         {json.dumps(combined_data, ensure_ascii=False)}
#         数据说明：
#              1. pc_activity 和 android_activity 会提供timeline作为参考。把握用户的大体时间使用。
#              2. 如果数据缺失，随机应变，保证报告和更新质量。
#              3. 其他数据提供用户细节的行动。
#         进化规则：
#              1. 技能演化：与行为强相关的技能增加 exp_percent，满100则 lv+1。
#              2. 技能觉醒：若出现密集的新行为领域，必须在 skills 中新增 Lv.1 技能。
#              3. 技能衰退：完全无关的存量技能，lv > 1 时需扣除经验并标注 status 为 "衰退"。当lv=1且经验值为0时，不再写入该技能。
#              4. 新增技能上限：一天不超过5个，一周不超过30个。
#              5. 属性（radar_stats）也能增加,但是条件比较高，中高强度且持续的相关活动才会适当增加点数。如果数据量不够支撑，维持原状即可。
#         分析要求：
#             1. 行为分析：给出一个大致的评判，描述用户的事件时间线和使用习惯。
#             2. 技能培养：推断用户正在培养的技能。
#             3. 心理画像：给出精神状态报告。
#             4. 性癖分析：基于用户对于擦边类型视频的偏好分析。
#             5. 关注点：推断用户现在所关心的点及所处阶段。
#             6. 变化：需要和前面的对齐。不能前面智力从80变化到85，你的总结却写智力+3。
#         内容要求：
#             1. 不能重复！！！
#         输出纯 JSON (严禁 Markdown)：
#         {{
#             "updated_profile": {{
#                 "career": "根据最新偏好进化的职业名",
#                 "level": "评价等级（数字）",
#                 "brief_report": "基于本次审计生成的初始简报（80字左右，公正尖锐）",
#                 "system_comment": "犀利毒舌但不失公正的系统寄语（具有成长性、连贯性）",
#                 "radar_stats": {{ "智力": 0, "财力": 0, "力量": 0, "精力": 0, "魅力": 0, "韧性": 0 }},
#                 "skills": [ {{ "name": "...", "lv": 0, "exp_percent": 0, "status": "进化/维持/衰退/觉醒" }} ]
#                 "changes":"基于本次审计的结果，写一个变化总结。80字左右。如：职业变化为，等级增长，智力+2 (由于...), 精力-1 (由于...)"
#             }},
#             "audit_report": {{
#                 "insight": "一句话洞察",
#                 "tags": ["标签1", "标签2"],
#                 "full_report": "400字以上报告。每个要点空行，语气毒舌精准，最后一段小总结并空行。总结还需要包括角色的一些变化。",
#             }}
#         }}
#         """
#
#         try:
#             self._log("ANALYZING", "正在扫描数字足迹并计算灵魂权重...", self.YELLOW)
#
#             response = self.client.chat.completions.create(
#                 model="deepseek-chat",
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": user_prompt}
#                 ],
#                 response_format={'type': 'json_object'}
#             )
#
#             res_content = response.choices[0].message.content
#             data = json.loads(res_content)
#
#             elapsed_time = round(time.time() - start_time, 2)
#             self._log("SUCCESS", f"灵魂审计完成！耗时: {elapsed_time}s", self.GREEN)
#
#             # 简单校验
#             career = data.get('updated_profile', {}).get('career')
#             insight = data.get('audit_report', {}).get('insight')
#             self._log("EVOLUTION", f"进化职业: {career} | 洞察: {insight}", self.BLUE)
#
#             return data
#
#         except json.JSONDecodeError:
#             self._log("ERROR", "AI 返回了无效的 JSON 格式。", self.RED)
#             return None
#         except Exception as e:
#             self._log("CRITICAL", f"通讯中断: {str(e)}", self.RED)
#             return None


import os
import json
import time
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class SoulAuditAgent:
    def __init__(self, model_type="deepseek"):
        """
        :param model_type: "deepseek" 或 "qwen"
        """
        proxy_url = "http://127.0.0.1:7890"
        # 1. 配置映射
        configs = {
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": "https://api.deepseek.com",
                "model_name": "deepseek-chat"
            },
            "qwen": {
                "api_key": os.getenv("DASHSCOPE_API_KEY"),
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model_name": "qwen-max"
            },

        }

        current_cfg = configs.get(model_type.lower(), configs["deepseek"])

        custom_http_client = httpx.Client(
            verify=False,
            timeout=httpx.Timeout(600, connect=10.0)
        )



        self.client = OpenAI(
            api_key=current_cfg["api_key"],
            base_url=current_cfg["base_url"],
            http_client=custom_http_client
        )

        self.model_name = current_cfg["model_name"]
        self.model_label = model_type.upper()

        # 状态颜色
        self.BLUE = "\033[94m"
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.MAGENTA = "\033[95m"
        self.RESET = "\033[0m"

    def _log(self, status, message, color=""):
        timestamp = time.strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [SOUL_AUDIT] [{self.model_label}] [{status}] {message}{self.RESET}")

    def conduct_audit(self, current_profile, combined_data):
        """
        [审计阶段] 基于行为数据演化存档并生成深度报告
        """
        self._log("AGENT_WAKE", f"正在调用灵魂审计专家 {self.model_name}...", self.MAGENTA)
        start_time = time.time()

        # 针对 Qwen 优化了 System Prompt，确保必须返回 JSON
        system_prompt = "You are a cold, cynical RPG system auditor. You ONLY output pure JSON."

        user_prompt = f"""
        任务：基于最新行为数据演化 RPG 存档并生成深度报告。

        --- 当前存档 ---
        {json.dumps(current_profile, ensure_ascii=False)}
        --- 原始行为记录 ---
        {json.dumps(combined_data, ensure_ascii=False)}

        进化规则：
             1. 技能演化：与行为强相关的技能增加 exp_percent，满100则 lv+1。
             2. 技能觉醒：若出现密集新行为，新增 Lv.1 技能。
             3. 技能衰退：完全无关的技能需扣除经验，lv=1且经验为0时不再写入。
             4. 属性演化：高强度持续活动才适当增加 radar_stats 点数。

        输出要求：
            1. 行为分析、技能培养、心理画像、性癖分析（基于视频偏好）、当前关注点。
            2. 确保数值逻辑自洽（如：智力从80变85，总结必须写+5）。

        请严格输出如下格式的纯 JSON (禁止 Markdown 代码块)：
        {{
            "updated_profile": {{
                "career": "职业名",
                "level": 0,
                "brief_report": "80字简报",
                "system_comment": "毒舌寄语",
                "radar_stats": {{ "智力": 0, "财力": 0, "力量": 0, "精力": 0, "魅力": 0, "韧性": 0 }},
                "skills": [ {{ "name": "...", "lv": 0, "exp_percent": 0, "status": "进化/维持/衰退/觉醒" }} ],
                "changes": "变化总结(100字左右，描述职业，等级，属性，技能的变化)"
            }},
            "audit_report": {{
                "insight": "一句话洞察",
                "tags": ["标签1", "标签2"],
                "full_report": "400字以上报告。每个要点空行，语气毒舌精准，最后一段小总结并空行。。"
            }}
        }}
        """

        try:
            self._log("ANALYZING", "正在扫描数字足迹并计算灵魂权重...", self.YELLOW)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={'type': 'json_object'}
            )

            res_content = response.choices[0].message.content
            data = json.loads(res_content)

            elapsed_time = round(time.time() - start_time, 2)
            self._log("SUCCESS", f"灵魂审计完成！耗时: {elapsed_time}s", self.GREEN)
            return data

        except Exception as e:
            self._log("CRITICAL", f"通讯中断: {str(e)}", self.RED)
            return None