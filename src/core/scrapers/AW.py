# import requests
# import datetime as dt_module
# import pytz
#
#
# class AWScraper:
#     def __init__(self, host="127.0.0.1", port=5600):
#         self.base_url = f"http://{host}:{port}/api/0"
#         self.tz = pytz.timezone('Asia/Shanghai')
#         # 强制不使用系统代理，防止请求 127.0.0.1 时跑偏
#         self.session = requests.Session()
#         self.session.proxies = {'http': None, 'https': None}
#
#     def get_timeline(self, days=1):
#         print(f"📡 [AW] 启动本地链路扫描 | 追溯深度: {days}天")
#
#         try:
#             # 1. 获取所有 Buckets 并定位 Window 监控桶
#             resp = requests.get(f"{self.base_url}/buckets", timeout=5)
#             buckets = resp.json()
#
#             window_bucket = None
#             for b_id in buckets:
#                 if "aw-watcher-window" in b_id:
#                     window_bucket = b_id
#                     break
#
#             if not window_bucket:
#                 print("⚠️ [AW] 未找到 window-watcher bucket，请确保 ActivityWatch 已启动")
#                 return []
#
#             print(f"🔍 [AW] 识别到监控桶: {window_bucket}")
#
#             # 2. 计算时间区间 (ISO 8601 格式)
#             end_time = dt_module.datetime.now(pytz.utc)
#             start_time = end_time - dt_module.timedelta(days=int(days))
#
#             # 3. 构建请求参数
#             endpoint = f"{self.base_url}/buckets/{window_bucket}/events"
#             params = {
#                 "start": start_time.isoformat(),
#                 "end": end_time.isoformat()
#             }
#
#             # 4. 执行数据拉取
#             print(f"⏳ [AW] 正在从本地 API 拉取事件流...")
#             events_resp = requests.get(endpoint, params=params, timeout=10)
#             events = events_resp.json()
#
#             total_events = len(events)
#             print(f"📥 [AW] 成功下载 {total_events} 条原始事件")
#
#             # 5. 结构化解包 (带简单的同类合并逻辑)
#             raw_timeline = []
#             for ev in events:
#                 ts_str = ev['timestamp'].replace('Z', '+00:00')
#                 dt = dt_module.datetime.fromisoformat(ts_str).astimezone(self.tz)
#                 app_name = ev['data'].get('app', 'Unknown')
#                 title = ev['data'].get('title', 'Unknown')
#                 duration = round(ev['duration'], 2)
#
#                 # 过滤掉时长过短的杂讯 (比如小于 1 秒的切换)
#                 if duration < 1.0:
#                     continue
#
#                 raw_timeline.append({
#                     "time": dt.strftime('%H:%M:%S'),
#                     "app": app_name,
#                     "title": title,
#                     "duration": duration
#                 })
#
#             # --- 核心：同类行为合并 (极大节省 Token) ---
#             compressed_timeline = []
#             if raw_timeline:
#                 current_entry = raw_timeline[0].copy()
#
#                 for next_ev in raw_timeline[1:]:
#                     # 如果连续发生的事件 App 和 标题 都一样，就合并时长
#                     if next_ev['app'] == current_entry['app']:
#                         current_entry['duration'] += next_ev['duration']
#                     else:
#                         # 时长四舍五入
#                         current_entry['duration'] = round(current_entry['duration'], 1)
#                         compressed_timeline.append(current_entry)
#                         current_entry = next_ev.copy()
#
#                 compressed_timeline.append(current_entry)
#
#             print(f"✅ [AW] 原始数据 {total_events} 条 -> 压缩后 {len(compressed_timeline)} 条")
#             return compressed_timeline
#
#         except Exception as e:
#             print(f"❌ [AW] 链路中断: {str(e)}")
#             return []
#


import requests
import datetime as dt_module
import pytz
import os


class AWScraper:
    def __init__(self, host="127.0.0.1", port=5600):
        self.base_url = f"http://{host}:{port}/api/0"
        self.tz = pytz.timezone('Asia/Shanghai')
        # 强制不使用系统代理
        self.session = requests.Session()
        self.session.proxies = {'http': None, 'https': None}

    def get_timeline(self, days=1):
        """
        获取并清洗 PC 端的 ActivityWatch 时间轴数据
        """
        print(f"📡 [AW] 启动 PC 链路扫描 | 追溯深度: {days}天")

        try:
            # 1. 获取所有 Buckets
            resp = self.session.get(f"{self.base_url}/buckets", timeout=5)
            resp.raise_for_status()
            buckets = resp.json()

            window_bucket = next((b_id for b_id in buckets if "aw-watcher-window" in b_id), None)

            if not window_bucket:
                print("⚠️ [AW] 未找到 window-watcher 桶，请检查 ActivityWatch 是否正在运行。")
                return []

            # 2. 计算时间区间
            end_time = dt_module.datetime.now(pytz.utc)
            start_time = end_time - dt_module.timedelta(days=float(days))

            # 3. 拉取事件流
            endpoint = f"{self.base_url}/buckets/{window_bucket}/events"
            params = {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }

            events_resp = self.session.get(endpoint, params=params, timeout=10)
            events_resp.raise_for_status()
            events = events_resp.json()

            if not events:
                print("∅ [AW] 指定时间内没有捕获到任何事件。")
                return []

            # 4. 结构化解包并转为正序
            processed_events = []
            for ev in reversed(events):
                ts_str = ev['timestamp'].replace('Z', '+00:00')
                dt = dt_module.datetime.fromisoformat(ts_str).astimezone(self.tz)

                processed_events.append({
                    "time_obj": dt,
                    "time": dt.strftime('%H:%M:%S'),
                    "app": ev['data'].get('app', 'Unknown'),
                    "title": ev['data'].get('title', 'Unknown'),
                    "duration": ev['duration']
                })

            # 5. 智能同类合并
            compressed_timeline = []
            if processed_events:
                curr = processed_events[0]
                for nxt in processed_events[1:]:
                    if nxt['app'] == curr['app'] and nxt['title'] == curr['title']:
                        curr['duration'] += nxt['duration']
                    else:
                        if curr['duration'] >= 1.0:
                            curr['duration'] = round(curr['duration'], 1)
                            final_entry = {k: v for k, v in curr.items() if k != 'time_obj'}
                            compressed_timeline.append(final_entry)
                        curr = nxt

                # 处理最后一条记录
                curr['duration'] = round(curr['duration'], 1)
                compressed_timeline.append({k: v for k, v in curr.items() if k != 'time_obj'})

            print(f"✅ [AW] 原始记录: {len(events)} -> 压缩后: {len(compressed_timeline)}")
            return compressed_timeline

        except requests.exceptions.ConnectionError:
            print("❌ [AW] 无法连接到 ActivityWatch API。")
            return []
        except Exception as e:
            print(f"❌ [AW] 运行异常: {str(e)}")
            return []


# --- 独立运行测试 (这部分必须在 class 外部) ---
# if __name__ == "__main__":
#     scraper = AWScraper()
#     # 比如获取最近 12 小时的数据
#     timeline = scraper.get_timeline(days=1)
#
#     if timeline:
#         print("\n" + "=" * 50)
#         print(f"{'时间':<10} | {'时长(s)':<8} | {'应用':<20} | {'窗口标题'}")
#         print("-" * 80)
#         # 展示最后 10 条真实记录
#         for entry in timeline[-50:]:
#             print(f"{entry['time']:<10} | {entry['duration']:<8} | {entry['app'][:20]:<20} | {entry['title'][:40]}")
#         print("=" * 50)