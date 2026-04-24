import os
import json
import time
import httpx
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 中的 DEEPSEEK_API_KEY 和 DASHSCOPE_API_KEY
load_dotenv()


class InitAgent:
    def __init__(self, model_type="deepseek"):
        """
        :param model_type: 来自前端 select 标签的 value ('deepseek' 或 'qwen')
        """
        # 1. 配置映射表
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
            }
        }

        # 获取当前选择的配置，找不到则默认为 deepseek
        current_cfg = configs.get(model_type.lower(), configs["deepseek"])

        # 2. 共享的 HTTP 客户端配置（处理超时和 SSL）
        custom_http_client = httpx.Client(
            verify=False,
            timeout=httpx.Timeout(45.0, connect=10.0)
        )

        # 3. 统一使用 OpenAI SDK 进行实例化
        self.client = OpenAI(
            api_key=current_cfg["api_key"],
            base_url=current_cfg["base_url"],
            http_client=custom_http_client
        )

        self.model_name = current_cfg["model_name"]
        self.model_label = model_type.upper()

        # 状态颜色代码
        self.BLUE = "\033[94m"
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.RESET = "\033[0m"

    def _log(self, status, message, color=""):
        timestamp = time.strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [{status}] [{self.model_label}] {message}{self.RESET}")

    def generate_hero(self, background):
        """
        [初始化阶段] 将用户背景映射为 RPG 初始档案
        """
        self._log("AI_START", f"正在唤醒 {self.model_name} 建模专家...", self.BLUE)
        start_time = time.time()

        # 对于 Qwen 等模型，JSON 模式要求 System Prompt 必须包含 "JSON" 字样
        system_prompt = "You are a specialized behavioral modeling expert that outputs ONLY pure JSON."
        user_prompt = f"""
        请基于以下用户背景，初始化一个 RPG 风格的角色面板。
        背景内容：{background}
        内容要求：1.用户输入什么语言就返回什么语言的文本.
        2.用户的radar_stats适当给高点，不要过于严苛.
        3.必须返回如下格式的 JSON 字符串（严禁包含 Markdown 代码块或文字说明）：
        {{
            "career": "硬核风格职业名",
            "level": 1,
            "radar_stats": {{ "智力": 10, "财力": 10, "力量": 10, "精力": 10, "魅力": 10, "韧性": 10 }},
            "skills": [
                {{ "name": "核心技能", "lv": 1, "exp_percent": 10, "status": "NEW" }}
            ],
            "brief_report": "基于背景的初始审计简报（80字左右，客观公正）",
            "system_comment": "客观公正的系统寄语"
        }}
        """

        try:
            self._log("AI_THINK", "数据流解析中...", self.YELLOW)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # 开启 JSON 模式，确保返回格式正确
                response_format={'type': 'json_object'}
            )

            res_content = response.choices[0].message.content
            data = json.loads(res_content)

            elapsed_time = round(time.time() - start_time, 2)
            self._log("AI_SUCCESS", f"建模完成！耗时: {elapsed_time}s", self.GREEN)

            return data

        except Exception as e:
            self._log("AI_CRITICAL", f"通讯或解析中断: {str(e)}", self.RED)
            return None