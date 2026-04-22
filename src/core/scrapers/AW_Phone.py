import subprocess
import re
import os
from datetime import datetime, timedelta


class AndroidScraper:
    def __init__(self, adb_path, device_id):
        # 像 B站 SESSDATA 一样处理输入，增加去空格处理
        self.adb_path = str(adb_path).strip() if adb_path else ""
        self.device_id = str(device_id).strip() if device_id else ""
        self.output_text = "phone_stats_raw.txt"

    def _is_config_valid(self):
        """检查用户填写的配置是否基本完整"""
        return bool(self.adb_path and self.device_id)

    def _fetch_raw_data(self):
        """执行 ADB 命令，失败时静默返回 False"""
        if not self._is_config_valid():
            print(">>> [Android] 授权配置缺失，跳过抓取")
            return False

        # 增加 --full-history 参数还原真实 Timeline
        cmd = f'"{self.adb_path}" -s {self.device_id} shell dumpsys usagestats --full-history'
        try:
            with open(self.output_text, "w", encoding="utf-8") as f:
                # 设定 timeout，防止 ADB 挂起导致整个审计卡死
                subprocess.run(cmd, shell=True, check=True, stdout=f, timeout=15)
            return True
        except Exception as e:
            print(f">>> [Android] ADB 通信失败（请检查连接或路径）: {str(e)}")
            return False

    def get_timeline(self, days=1):
        print(f"📡 [AW_Phone_Android] 启动 Android 链路扫描 | 追溯深度: {days}天")
        """主入口：参照 BiliScraper，支持天数过滤且保证不崩溃"""
        all_data = []

        # 第一层防护：配置无效或抓取失败，直接返回空列表，不抛出异常
        if not self._fetch_raw_data():
            return []

        try:
            if not os.path.exists(self.output_text):
                return []

            # 计算审计时间阈值
            threshold = datetime.now() - timedelta(days=float(days))

            with open(self.output_text, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            temp_list = []
            current_session = None
            pattern = r'time="([\d\-\s:]+)" type=(\w+) package=([\w\.]+)'

            for line in lines:
                match = re.search(pattern, line)
                if not match: continue

                t_str, e_type, pkg = match.groups()
                t_dt = datetime.strptime(t_str, '%Y-%m-%d %H:%M:%S')

                # 时间过滤（只保留用户决定审计的天数内的数据）
                if t_dt < threshold:
                    continue

                if e_type == "ACTIVITY_RESUMED":
                    if current_session:
                        self._push_event(temp_list, current_session, t_dt)
                    current_session = {'app': pkg, 'start': t_dt}
                elif e_type in ["ACTIVITY_PAUSED", "SCREEN_NON_INTERACTIVE", "ACTIVITY_STOPPED"]:
                    if current_session and current_session['app'] == pkg:
                        self._push_event(temp_list, current_session, t_dt)
                        current_session = None

            # 压缩合并同类行为
            all_data = self._compress(temp_list)

        except Exception as e:
            print(f">>> [Android] 解析过程异常: {str(e)}")
            # 即使解析出错，也返回已拿到的部分或空列表，确保审计主流程继续

        return all_data

    def _push_event(self, target_list, session, end_time):
        dur = (end_time - session['start']).total_seconds()
        if 1.0 < dur < 14400:  # 过滤掉 1 秒以下的杂讯
            target_list.append({
                "time": session['start'].strftime('%Y/%m/%d %H:%M:%S'),
                "app": session['app'],
                "duration": round(dur, 1),
                "type": "Mobile_Activity"
            })

    def _compress(self, data):
        if not data: return []
        data.sort(key=lambda x: x['time'])
        res = []
        curr = data[0]
        for nxt in data[1:]:
            if nxt['app'] == curr['app']:
                curr['duration'] += nxt['duration']
            else:
                res.append(curr)
                curr = nxt
        res.append(curr)
        return res