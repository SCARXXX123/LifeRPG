import webview
import os
import json
import threading
import time
# 确保导入了 Skill 模型
from src.database.models import db, Hero, Skill, init_db,DailyRecord
from src.utils.init_agent import InitAgent
from src.utils.soul_agent import SoulAuditAgent
from src.core.scrapers.Bilibili import BiliScraper
from src.core.scrapers.AW import AWScraper
from src.core.scrapers.AW_Phone import AndroidScraper
import datetime as dt_module
import sys
from dotenv import load_dotenv

def get_resource_path(relative_path):
    """ 获取资源绝对路径，兼容开发环境和 PyInstaller 打包环境 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# 1. 之前定义的获取路径函数
def get_internal_env():
    import sys
    # 注意！这里必须用 sys._MEIPASS，因为文件被封在了 EXE 内部
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ".env")
    return os.path.join(os.path.abspath("."), ".env")

# 加载内部的 .env
load_dotenv(get_internal_env())

class LifeRPGApi:
    def __init__(self):
        print("\n>>> [节点检查] 正在初始化 API 系统...")
        self.current_hero_name = "None"  # 默认设为 Scar，或者设为 None
        try:
            self.init_agent = InitAgent()
            print(">>> [节点检查] InitAgent 加载成功")
        except Exception as e:
            print(f">>> [错误] InitAgent 加载失败: {e}")
        try:
            # 实例化你定义的 SoulAuditAgent
            self.soul_agent = SoulAuditAgent()
            print(">>> [节点检查] SoulAuditAgent 唤醒成功")
        except Exception as e:
            print(f">>> [严重错误] SoulAuditAgent 加载失败: {e}")
        try:
            self.bili_scraper_class = BiliScraper
            print(">>> [节点检查] Bilibili 爬虫模块挂载成功")
        except ImportError as e:
            print(f">>> [警告] 无法加载 Bilibili 爬虫: {e}")
        try:
            self.aw_scraper_class = AWScraper()
            print(">>> [节点检查] AW 爬虫模块挂载成功")
        except ImportError as e:
            print(f">>> [警告] 无法加载 AW爬虫: {e}")
        try:
            self.android_scraper_class = AndroidScraper
            print(">>> [节点检查] AW_Phone_Android 爬虫模块挂载成功")
        except ImportError as e:
            print(f">>> [警告] 无法加载 AW_Phone_Android 爬虫: {e}")


    def navigate(self, page_name):
        def _async_nav():
            time.sleep(0.1)
            # base_path = os.path.dirname(os.path.abspath(__file__))
            # target_path = os.path.join(base_path, f"src/web/{page_name}.html")
            # target_path = get_resource_path(f"src/web/{page_name}.html")
            # file_url = f"file:///{target_path.replace('\\', '/')}"

            # 1. 先在外部处理路径，避开 f-string 内部的反斜杠
            target_path = get_resource_path(f"src/web/{page_name}.html")
            safe_path = target_path.replace('\\', '/')

            # 2. 这里的 f-string 只负责引用变量
            file_url = f"file:///{safe_path}"
            print(f">>> [节点检查] 正在切换物理页面至: {page_name}.html")
            window.load_url(file_url)

        print(f">>> [节点检查] 接收到跳转指令: {page_name}")
        threading.Thread(target=_async_nav, daemon=True).start()
        return None

    # ---  登录验证 ---
    def login_confirm(self, username, password):
        """对应 login.html 调用的 attemptLogin()"""
        print(f">>> [身份校验] 接入请求: {username}")
        try:
            db.connect(reuse_if_open=True)
            user = Hero.get_or_none(Hero.name == username)

            if user and user.password == password:
                # 正式锚定当前用户
                self.current_hero_name = username
                print(f">>> [授权成功] 执行者 {username} 已上线")

                # 登录成功直接进入中枢
                self.navigate('dashboard')
                return {"success": True}

            return {"success": False, "message": "密钥不匹配或代号不存在"}
        except Exception as e:
            return {"success": False, "message": f"底层异常: {str(e)}"}

    # ---  核心业务：初始化/覆盖数字人 ---
    def init_hero(self, name, password, bio, model):
        """
        对应 subject_registry.html 调用的 triggerInit(name, password, desc, model)
        """
        # 这里的 model 参数是从前端 select 标签传过来的 'deepseek' 或 'qwen'
        print(f"\n>>> [觉醒仪式] 正在使用驱动引擎 [{model.upper()}] 为 {name} 注入灵魂...")

        try:
            # 1. 动态初始化 Agent（这里不再使用 self.init_agent，而是根据用户选择即时创建）
            # 这样可以确保用户每次签署契约时都能切换不同的 AI 引擎
            current_agent = InitAgent(model_type=model)

            # 2. 调用 AI 建模逻辑
            ai_data = current_agent.generate_hero(bio)

            if not ai_data:
                raise Exception(f"AI ({model}) 响应超时或格式错误")

            # 3. 提取雷达图数据
            stats = ai_data.get("radar_stats", {})

            # 4. 数据库持久化
            with db.atomic():
                # 如果存在同名用户，先删除旧档案（覆盖逻辑）
                Hero.delete().where(Hero.name == name).execute()

                hero = Hero.create(
                    name=name,
                    password=password,
                    career=ai_data.get("career", "UNIDENTIFIED_SUBJECT"),
                    level=1,
                    status_summary=ai_data.get("brief_report", ""),
                    system_comment=ai_data.get("system_comment", ""),
                    # 注意：如果 AI 返回的字段名是中文，这里要对应好
                    intellect=stats.get("智力", 10),
                    wealth=stats.get("财力", 10),
                    strength=stats.get("力量", 10),
                    energy=stats.get("精力", 10),
                    charm=stats.get("魅力", 10),
                    resilience=stats.get("韧性", 10),
                    last_update=dt_module.datetime.now()
                )

                # 5. 初始技能挂载
                for sk in ai_data.get("skills", []):
                    Skill.create(
                        hero=hero,
                        name=sk.get("name"),
                        level=sk.get("lv", 1),
                        exp_percent=sk.get("exp_percent", 0),
                        status="觉醒"
                    )

            # 6. 状态锚定与页面跳转
            self.current_hero_name = name
            print(f">>> [状态锚定] 使用 {model.upper()} 建模成功，当前角色: {self.current_hero_name}")

            # 通知前端跳转至角色展示页
            self.navigate('character')
            return True

        except Exception as e:
            print(f">>> [觉醒失败] 引擎报错: {e}")
            return False

    # def init_hero(self, name, password, bio):
    #     """对应 initialize.html 调用的 triggerInit()"""
    #     print(f"\n>>> [觉醒仪式] 正在为 {name} 注入灵魂描述...")
    #     try:
    #         ai_data = self.init_agent.generate_hero(bio)
    #         if not ai_data: raise Exception("AI 响应超时")
    #
    #         stats = ai_data.get("radar_stats", {})
    #
    #         with db.atomic():
    #             # 如果存在同名用户，先删除（覆盖逻辑）
    #             Hero.delete().where(Hero.name == name).execute()
    #
    #             hero = Hero.create(
    #                 name=name,
    #                 password=password,
    #                 career=ai_data.get("career", "UNIDENTIFIED_SUBJECT"),
    #                 level=1,
    #                 status_summary=ai_data.get("brief_report", ""),
    #                 system_comment=ai_data.get("system_comment", ""),
    #                 intellect=stats.get("智力", 10),
    #                 wealth=stats.get("财力", 10),
    #                 strength=stats.get("力量", 10),
    #                 energy=stats.get("精力", 10),
    #                 charm=stats.get("魅力", 10),
    #                 resilience=stats.get("韧性", 10),
    #                 last_update=dt_module.datetime.now()
    #             )
    #
    #             # 技能初始化
    #             for sk in ai_data.get("skills", []):
    #                 Skill.create(
    #                     hero=hero,
    #                     name=sk.get("name"),
    #                     level=sk.get("lv", 1),
    #                     exp_percent=sk.get("exp_percent", 0),
    #                     status="觉醒"
    #                 )
    #
    #         # 觉醒成功后，锚定用户并跳转至“角色展示页”
    #         self.current_hero_name = name
    #         print(f">>> [状态锚定] 当前活动角色已切换至: {self.current_hero_name}")
    #         self.navigate('character')
    #         return True  # 返回给前端 success 处理
    #
    #     except Exception as e:
    #         print(f">>> [觉醒失败] {e}")
    #         return False

    def get_hero_data(self):
        print(">>> [节点检查] 前端正在调取全维度档案...")
        try:
            # hero = Hero.get_or_none()
            # if not hero: return None
            if not self.current_hero_name:
                latest = Hero.select().order_by(Hero.last_update.desc()).first()
                if latest: self.current_hero_name = latest.name

            hero = Hero.get_or_none(Hero.name == self.current_hero_name)
            if not hero: return None

            # 抓取关联技能列表
            skill_list = []
            for s in hero.skills:
                skill_list.append({
                    "name": s.name,
                    "level": s.level,
                    "exp": s.exp_percent,
                    "status": s.status
                })

            return {
                "name": hero.name,
                "career": hero.career,
                "level": hero.level,
                "stats": [
                    hero.intellect, hero.charm, hero.energy,
                    hero.strength, hero.resilience, hero.wealth
                ],
                "skills": skill_list,
                "summary": hero.status_summary,
                "comment": hero.system_comment,
                "last_update": hero.last_update.strftime("%H:%M:%S")
            }
        except Exception as e:
            print(f">>> [错误] 数据读取异常: {e}")
            return None

    # ---  character ---
    def get_character_init_data(self):
        """获取当前已登录英雄的完整档案"""
        try:
            # hero = Hero.get_or_none(Hero.name == self.current_hero_name)
            # if not hero: return None
            if not self.current_hero_name:
                latest = Hero.select().order_by(Hero.last_update.desc()).first()
                if latest: self.current_hero_name = latest.name

            hero = Hero.get_or_none(Hero.name == self.current_hero_name)
            if not hero: return None
            print('正在获取英雄档案')
            return {
                "name": hero.name,
                "title": hero.career,
                "level": hero.level,
                "status_summary": hero.status_summary,
                "system_comment": hero.system_comment,
                "stats": {
                    "intellect": hero.intellect,
                    "charm": hero.charm,
                    "energy": hero.energy,
                    "strength": hero.strength,
                    "resilience": hero.resilience,
                    "wealth": hero.wealth
                },
                "skills": [{"name": s.name, "lv": s.level, "exp_percent": s.exp_percent, "status": s.status} for s in
                           hero.skills]
            }
        except:
            return None

    def go_to_dashboard(self):
        print(">>> [节点检查] 正在建立中枢连接...")
        self.navigate('dashboard') # 确保你有 dashboard.html
        return True

    def _save_test_json(self, filename, data):
        """测试专用：将抓取到的原始数据持久化"""
        try:
            # 获取当前脚本所在目录，确保文件存在你找得到的地方
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f">>> [存档成功] 原始数据已写入: {os.path.abspath(filename)}")
        except Exception as e:
            print(f">>> [存档失败] 无法写入 {filename}: {e}")
    # --- 核心审计：行为分析与灵魂演化 ---
    def run_behavioral_audit(self, config):
        days = config.get('days', 1)
        # 获取前端选择的模型引擎，默认为 deepseek
        selected_model = config.get('model', 'deepseek')

        print(f"\n>>> [系统指令] 启动全维度审计 | 周期: {days}天 | 引擎: {selected_model.upper()}")

        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{dt_module.datetime.now()}] --- 启动审计 ---\n")
            f.write(f"收到前端 Config: {str(config)}\n")

        try:
            # 1. 身份锁定
            hero = Hero.get_or_none(Hero.name == self.current_hero_name)
            if not hero:
                print(f">>> [严重错误] 内存身份为 {self.current_hero_name}，但数据库查无此人")
                return {"success": False, "msg": "身份丢失"}

            safe_hero_id = hero.id
            print(f">>> [身份确认] 正在为 {hero.name} (ID: {safe_hero_id}) 执行审计...")

            # 初始化统一数据结构
            combined_data = {
                "bilibili_history": [],
                "pc_activity": [],
                "android_activity": [],
                "meta": {"analysis_days": days, "engine": selected_model}
            }

            # --- 【爬虫插槽 01: BiliBili】 ---
            if config.get('use_bili') and config.get('sessdata'):
                sd = config['sessdata']
                print(f">>> [同步中] 接入 BiliBili 节点 | 凭据预览: {sd[:6]}***{sd[-4:]}")
                try:
                    # 实例化 BiliScraper
                    scraper = self.bili_scraper_class(config['sessdata'])
                    bili_data = scraper.get_history(days)
                    if bili_data:
                        combined_data["bilibili_history"] = bili_data
                        print(f">>> [同步完成] 成功抓取到 {len(bili_data)} 条播放记录")
                except Exception as e:
                    print(f">>> [同步中断] Bilibili 执行异常: {str(e)}")

            # --- 【爬虫插槽 02: ActivityWatch_PC】 ---
            if config.get('use_aw'):
                print(">>> [同步中] 正在接入 ActivityWatch 本地监控...")
                try:
                    # 假设 self.aw_scraper 是已经实例化好的类或工具
                    aw_events = self.aw_scraper_class.get_timeline(days)
                    if aw_events:
                        combined_data["pc_activity"] = aw_events
                        print(f">>> [同步完成] 捕获 {len(aw_events)} 条 PC 行为脉冲")
                except Exception as e:
                    print(f">>> [AW 同步中断]: {e}")

            # --- 【爬虫插槽 03: ActivityWatch_Phone (Android)】 ---
            if config.get('use_android'):
                raw_path = config.get('android_adb_path', '').strip()
                # 路径自动补全 adb.exe
                if raw_path and not raw_path.lower().endswith('adb.exe'):
                    separator = "" if raw_path.endswith(("\\", "/")) else "\\"
                    adb_p = f"{raw_path}{separator}adb.exe"
                else:
                    adb_p = raw_path

                dev_id = config.get('android_device_id', '').strip()

                if not adb_p or not dev_id:
                    print(">>> [同步失败] Android 配置不全：需提供 ADB 路径和设备 ID")
                else:
                    print(f">>> [同步中] 接入 Android 节点 | 目标设备: {dev_id}")
                    try:
                        # 实例化 AndroidScraper
                        scraper = self.android_scraper_class(adb_path=adb_p, device_id=dev_id)
                        android_data = scraper.get_timeline(days)
                        if android_data:
                            combined_data["android_activity"] = android_data
                            print(f">>> [同步完成] 成功捕获 {len(android_data)} 条手机记录")
                    except Exception as e:
                        print(f">>> [同步中断] Android 模块异常: {str(e)}")

            # 调试存档：保存最终喂给 AI 的 Payload
            self._save_test_json("test_combined_payload.json", combined_data)

            # 2. 获取当前英雄最新档案
            current_profile = self.get_character_init_data()

            # 3. AI 深度审计（动态选择引擎）
            print(f">>> [AI 审计] 正在通过 {selected_model.upper()} 演化灵魂状态...")
            dynamic_audit_agent = SoulAuditAgent(model_type=selected_model)
            audit_result = dynamic_audit_agent.conduct_audit(current_profile, combined_data)

            if not audit_result:
                raise Exception(f"AI 审计模块 ({selected_model}) 未返回有效数据")

            # 4. 身份防漂移校验
            if hero.id != safe_hero_id:
                print(f">>> [异常纠偏] 检测到身份漂移，强制还原为 ID: {safe_hero_id}")
                hero = Hero.get_by_id(safe_hero_id)

            # 执行进化：写入数据库
            self._apply_evolution(hero, audit_result['updated_profile'], audit_result['audit_report'])

            # 5. 组装前端回执
            payload = {
                "insight": audit_result['audit_report'].get('insight', '未感悟'),
                "tags": audit_result['audit_report'].get('tags', []),
                "full_report": audit_result['audit_report'].get('full_report', ''),
                "stats": combined_data.get("bilibili_history", []),
                "aw_stats": combined_data.get("pc_activity", []),
                "android_stats": combined_data.get("android_activity", [])
            }

            print(f">>> [审计完成] 使用 {selected_model.upper()} 演化完毕，等待前端展示...")
            return {"success": True, "payload": payload}

        except Exception as e:
            print(f">>> [审计中断] 错误详情: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "msg": str(e)}

    # def run_behavioral_audit(self, config):
    #     days = config.get('days', 1)
    #     print(f"\n>>> [系统指令] 启动全维度审计 | 周期: {days}天")
    #
    #     with open("debug_log.txt", "a", encoding="utf-8") as f:
    #         f.write(f"\n[{dt_module.datetime.now()}] --- 启动审计 ---\n")
    #         f.write(f"收到前端 Config: {str(config)}\n")
    #
    #         days = config.get('days', 1)
    #         sess = config.get('sessdata', '')
    #         f.write(f"解析天数: {days}, SESSDATA 长度: {len(sess)}\n")
    #
    #     try:
    #         # 【关键锁定】根据当前登录名锁定 Hero，并存入局部变量，不再中途重新获取
    #         hero = Hero.get_or_none(Hero.name == self.current_hero_name)
    #         if not hero:
    #             print(f">>> [严重错误] 内存身份为 {self.current_hero_name}，但数据库查无此人")
    #             return {"success": False, "msg": "身份丢失"}
    #
    #         # 记录下 ID，作为最终双保险
    #         safe_hero_id = hero.id
    #         print(f">>> [身份确认] 正在为 {hero.name} (ID: {safe_hero_id}) 执行审计...")
    #         # 1. 统一初始化结构
    #         combined_data = {
    #             "bilibili_history": [],
    #             "pc_activity": [],  # 统一使用 pc_activity
    #             "android_activity": [],
    #             "meta": {"analysis_days": days}
    #         }
    #
    #         # 【爬虫插槽 01: BiliBili】
    #         if config.get('use_bili') and config.get('sessdata'):
    #             # 凭证脱敏预览 (显示前6位和后4位)
    #             sd = config['sessdata']
    #             print(f">>> [同步中] 接入 BiliBili 节点 | 凭据预览: {sd[:6]}***{sd[-4:]}")
    #
    #             try:
    #                 # 关键补全：利用挂载的类进行实例化
    #                 scraper = self.bili_scraper_class(config['sessdata'])
    #                 bili_data = scraper.get_history(days)
    #
    #                 if bili_data:
    #                     combined_data["bilibili_history"] = bili_data
    #                     print(f">>> [同步完成] 成功抓取到 {len(bili_data)} 条播放记录")
    #                     # 测试存档
    #                     self._save_test_json("test_bili_data.json", bili_data)
    #                 else:
    #                     print(">>> [同步警告] B站节点返回数据为空，请检查 Cookie 状态")
    #             except Exception as e:
    #                 print(f">>> [同步中断] Bilibili 执行异常: {str(e)}")
    #
    #         # 【爬虫插槽 02: ActivityWatch_PC】
    #         if config.get('use_aw'):
    #             print(">>> [同步中] 正在接入 ActivityWatch 本地监控...")
    #             try:
    #                 # 注意这里调用的变量名，确保 self.aw_scraper_class 已经实例化
    #                 aw_events = self.aw_scraper_class.get_timeline(days)
    #                 if aw_events:
    #                     combined_data["pc_activity"] = aw_events  # 存入对应的 Key
    #                     print(f">>> [同步完成] 捕获 {len(aw_events)} 条行为脉冲")
    #                     # 测试存档
    #                     self._save_test_json("test_aw_data.json", aw_events)
    #             except Exception as e:
    #                 print(f">>> [AW 同步中断]: {e}")
    #
    #         # 【爬虫插槽 03: ActivityWatch_Phone】
    #         if config.get('use_android'):
    #             # 获取并清洗参数
    #             raw_path = config.get('android_adb_path', '').strip()
    #             # 自动补全逻辑：如果路径指向文件夹，自动加上 \adb.exe
    #             if raw_path and not raw_path.lower().endswith('adb.exe'):
    #                 # 处理路径结尾是否有斜杠的情况
    #                 separator = "" if raw_path.endswith(("\\", "/")) else "\\"
    #                 adb_p = f"{raw_path}{separator}adb.exe"
    #             else:
    #                 adb_p = raw_path
    #
    #             dev_id = config.get('android_device_id', '').strip()
    #
    #             print(f">>> [状态检测] Android 审计节点已激活")
    #
    #             # 检查核心参数是否缺失
    #             if not adb_p or not dev_id:
    #                 print(">>> [同步失败] Android 审计已开启但配置不全：需提供 ADB 路径和设备 ID")
    #             else:
    #                 # 参数存在，开始执行同步
    #                 dev_preview = f"{dev_id[:4]}***{dev_id[-4:]}" if len(dev_id) > 8 else dev_id
    #                 print(f">>> [同步中] 接入 Android 节点 | 目标设备: {dev_preview}")
    #
    #                 try:
    #                     # 实例化
    #                     scraper = self.android_scraper_class(adb_path=adb_p, device_id=dev_id)
    #                     android_data = scraper.get_timeline(days)
    #
    #                     if android_data:
    #                         combined_data["android_activity"] = android_data
    #                         print(f">>> [同步完成] 成功捕获 {len(android_data)} 条行为记录")
    #                         # 存档以便检查
    #                         self._save_test_json("test_android_data.json", android_data)
    #                     else:
    #                         print(">>> [同步警告] Android 节点数据为空，请确认手机已连接且开启 USB 调试")
    #
    #                 except Exception as e:
    #                     print(f">>> [同步中断] Android 模块执行异常: {str(e)}")
    #
    #         # 这个文件就是喂给 DeepSeek 的最终输入，400KB 变几 KB 后就在这里验证
    #         self._save_test_json("test_combined_payload.json", combined_data)
    #         # 2. 获取英雄档案
    #         # hero = Hero.get_or_none()
    #         current_profile = self.get_character_init_data()
    #
    #         # 3. AI 审计
    #         print(">>> [AI 审计] 正在上传数字足迹...")
    #         audit_result = self.soul_agent.conduct_audit(current_profile, combined_data)
    #
    #         if not audit_result:
    #             raise Exception("AI 审计模块未返回有效数据")
    #
    #         if hero.id != safe_hero_id:
    #             print(f">>> [异常纠偏] 检测到身份漂移，强制还原为 ID: {safe_hero_id}")
    #             hero = Hero.get_by_id(safe_hero_id)
    #         # 4. 自动演化
    #         self._apply_evolution(hero, audit_result['updated_profile'], audit_result['audit_report'])
    #
    #         # 5. 【核心修复点】安全组装返回给前端的数据包
    #         # 使用 .get(key, []) 哪怕爬虫失败了也不会报错崩溃
    #         payload = {
    #             "insight": audit_result['audit_report'].get('insight', '未感悟'),
    #             "tags": audit_result['audit_report'].get('tags', []),
    #             "full_report": audit_result['audit_report'].get('full_report', ''),
    #             "stats": combined_data.get("bilibili_history", []),
    #             "aw_stats": combined_data.get("pc_activity", []),
    #             "android_stats": combined_data.get("android_activity", [])  # <--- 返回给前端
    #         }
    #
    #         print(">>> [审计完成] 命格已演化，等待前端跳转...")
    #         return {"success": True, "payload": payload}
    #
    #     except Exception as e:
    #         print(f">>> [审计中断] 错误详情: {str(e)}")
    #         import traceback
    #         traceback.print_exc()  # 打印完整堆栈，方便你抓出到底是哪一行
    #         return {"success": False, "msg": str(e)}

    def _apply_evolution(self, hero, up, audit_report):
        """
        up: AI 返回的更新后的 profile (updated_profile)
        audit_report: AI 生成的审计报告文本 (audit_report)
        """
        # 记录当前执行者的 ID 和 名字，防止后续混淆
        target_hero_id = hero.id
        target_hero_name = hero.name

        try:
            with db.atomic():
                # --- 1. 更新 Hero 基础属性 ---
                hero.career = up.get('career', hero.career)
                hero.level = int(up.get('level', hero.level))
                hero.status_summary = up.get('brief_report', hero.status_summary)
                hero.system_comment = up.get('system_comment', hero.system_comment)


                # 映射六维属性
                rs = up.get('radar_stats', {})
                hero.intellect = rs.get('智力', hero.intellect)
                hero.wealth = rs.get('财力', hero.wealth)
                hero.strength = rs.get('力量', hero.strength)
                hero.energy = rs.get('精力', hero.energy)
                hero.charm = rs.get('魅力', hero.charm)
                hero.resilience = rs.get('韧性', hero.resilience)
                hero.last_update = dt_module.datetime.now()
                hero.save()

                # --- 2. 写入 DailyRecord (显式 ID 绑定) ---

                DailyRecord.create(
                    hero_id=target_hero_id,  # 强制绑定 Ting 的 ID (2)
                    date=dt_module.date.today(),
                    insight=audit_report.get('insight', '未感悟'),
                    tags=",".join(audit_report.get('tags', [])),
                    summary=audit_report.get('full_report', ''),
                    attribute_changes=json.dumps(up.get('changes', '无变化')),
                    activity_snapshot=json.dumps(audit_report.get('raw_stats', {}))
                )

                # --- 3. 更新技能演化 ---
                for sk in up.get('skills', []):
                    skill, created = Skill.get_or_create(
                        hero_id=target_hero_id,  # 同样显式绑定 ID
                        name=sk['name'],
                        defaults={'level': sk.get('lv', 1), 'status': '觉醒'}
                    )
                    if not created:
                        skill.level = sk.get('lv', skill.level)
                        skill.exp_percent = sk.get('exp_percent', skill.exp_percent)
                        skill.status = sk.get('status', skill.status)
                        skill.save()

            # 事务完成后，更新 API 内存状态
            self.current_hero_name = target_hero_name
            print(f">>> [同步成功] 物理落盘完成。执行者: {self.current_hero_name} (ID: {target_hero_id})")
            return {"success": True}

        except Exception as e:
            print(f">>> [同步崩溃] 错误详情: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "msg": str(e)}

    def get_latest_audit_report(self):
            print(f">>> [节点检查] 正在检索执行者 {self.current_hero_name} 的审计档案...")
            try:
                # 先根据名字找到人
                hero = Hero.get_or_none(Hero.name == self.current_hero_name)
                if not hero:
                    # 最后的保底：如果名字对不上，抓数据库里最后一个活跃的人
                    hero = Hero.select().order_by(Hero.last_update.desc()).first()
                    if hero: self.current_hero_name = hero.name

                if not hero: return None

                # 放弃对象匹配，直接用 ID 匹配数据库字段
                record = DailyRecord.select().where(
                    DailyRecord.hero_id == hero.id
                ).order_by(DailyRecord.id.desc()).first()

                if not record:
                    print(f">>> [诊断] 检索失败。ID:{hero.id} 名下无记录。请检查数据库 DailyRecord 表的 hero_id 列。")
                    return None

                return {
                    "insight": record.insight,
                    "tags": record.tags.split(',') if record.tags else [],
                    "summary": record.summary,
                    "attribute_changes": json.loads(record.attribute_changes),
                    "date": str(record.date)
                }
            except Exception as e:
                print(f">>> [错误] {e}")
                return None


    def update_password(self, new_password):
        """修改当前锁定英雄的密码"""
        try:
            hero = Hero.get(Hero.name == self.current_hero_name)
            hero.password = new_password
            hero.save()
            print(f">>> [安全] 执行者 {self.current_hero_name} 密钥已重置。")
            return {"success": True}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    def delete_account(self):
        """格式化全量数据（销号）"""
        try:
            # 这里的删除会触发数据库的 Cascade 连带删除技能和记录
            Hero.delete().where(Hero.name == self.current_hero_name).execute()
            print(f">>> [警告] 执行者 {self.current_hero_name} 档案已从系统中永久抹除。")

            # 抹除后，重定向回登录页
            self.navigate('login')
            return {"success": True}
        except Exception as e:
            return {"success": False, "msg": str(e)}

# --- 启动层 ---
api = LifeRPGApi()
base_dir = os.path.dirname(os.path.abspath(__file__))
# start_html = os.path.join(base_dir, "src/web/index.html")
start_html = get_resource_path("src/web/index.html")

window = webview.create_window(
    title='LifeRPG OS',
    url=start_html,
    js_api=api,
    width=1200, height=900,
    background_color='#020205'
)

def on_closed():
    """当窗口关闭时，强制杀掉所有进程"""
    print(">>> [系统指令] 物理窗口已销毁，正在强制离线所有后端进程...")
    # os._exit(0) 比 sys.exit() 更彻底，能直接清理僵尸线程
    os._exit(0)

if __name__ == '__main__':
    # 初始化数据库（如果表不存在则创建）
    init_db()
    #绑定关闭事件
    window.events.closed += on_closed
    # 启动应用
    webview.start(debug=False)