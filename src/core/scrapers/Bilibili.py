import requests
import time
import datetime as dt_module
import pytz
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BiliScraper:
    def __init__(self, sessdata):
        self.sessdata = sessdata.strip()
        self.url = "https://api.bilibili.com/x/web-interface/history/cursor"
        self.headers = {
            "Cookie": f"SESSDATA={self.sessdata}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/"
        }
        self.device_map = {1: "Pad", 2: "PC", 3: "手机", 4: "TV", 5: "APP", 7: "H5"}

    def get_history(self, days=1):
        all_data = []
        now_ts = int(time.time())
        last_view_at = 0
        stop_scan = False

        print(f"\n📡 [BILI] 启动深度扫描: 目标范围 {days} 天 (已应用 Asia/Shanghai 时区对齐)")

        try:
            while not stop_scan:
                params = {"view_at": last_view_at} if last_view_at > 0 else {}
                resp = requests.get(self.url,
                                    headers=self.headers,
                                    params=params,
                                    timeout=10,
                                    verify=False)
                res_json = resp.json()

                if res_json.get("code") != 0:
                    print(f"⚠️ B站接口拒绝: {res_json.get('message')}")
                    break

                history_list = res_json.get("data", {}).get("list", [])
                if not history_list:
                    break

                for item in history_list:
                    view_at = item.get("view_at", 0)

                    # 1. 时间范围截断 (天数 * 86400秒)
                    if (now_ts - view_at) > (int(days) * 86400):
                        stop_scan = True
                        break

                    # 2. 时区修正逻辑 (确保喂给 AI 的是北京时间)
                    tz = pytz.timezone('Asia/Shanghai')
                    dt_object = dt_module.datetime.fromtimestamp(view_at, tz)
                    local_time_str = dt_object.strftime('%Y/%m/%d %H:%M:%S')

                    # 3. 提取 UP 主名称
                    owner = item.get("owner", {})
                    api_transmit_owner = item.get("api_transmit", {}).get("owner", {})
                    up_name = (
                        owner.get("name") or
                        item.get("author_name") or
                        api_transmit_owner.get("name") or
                        "未知UP主"
                    )

                    # 4. 进度转换逻辑
                    raw_progress = item.get("progress", 0)
                    duration = item.get("duration", 0)
                    actual_progress = duration if raw_progress == -1 else raw_progress

                    # 5. 完成率计算
                    completion_num = (actual_progress / duration * 100) if duration > 0 else 0
                    completion_rate = f"{completion_num:.2f}%"

                    # 6. 标题处理 (包含分P逻辑)
                    history_info = item.get("history", {})
                    part_name = history_info.get("part", "")
                    full_title = item.get("title", "")
                    display_title = full_title
                    if part_name and part_name != full_title:
                        display_title = f"{full_title} ({part_name})"

                    # 7. 统一结构封装
                    all_data.append({
                        "title": display_title or "无标题",
                        "up_name": up_name,
                        "view_time": view_at,
                        "view_time_local": local_time_str,
                        "progress": actual_progress,
                        "duration": duration,
                        "completion_rate": completion_rate,
                        "tag_name": item.get("tname") or item.get("tag_name") or "未分类",
                        "device": self.device_map.get(history_info.get("dt"), "其他")
                    })

                # 更新游标继续下一页
                if history_list:
                    last_view_at = history_list[-1].get("view_at")
                else:
                    break

                # 稍微停顿，防风控
                time.sleep(0.6)

        except Exception as e:
            print(f"❌ B站抓取异常: {str(e)}")

        print(f"✅ [BILI] 扫描结束，共计获取 {len(all_data)} 条记录。")
        return all_data