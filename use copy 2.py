import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import base64
import threading
import time
import urllib3
from datetime import datetime, timedelta

# 禁用 SSL 警告
urllib3.disable_warnings()

# ==================== 🏸 14个场地完整字典 ====================
FIELD_MAP = {
    "主馆01号": "8a8586a89059b19401907cef13a07878",
    "主馆02号": "8a8586a89059b19401907cef13b8787b",
    "主馆03号": "8a8586a89059b19401907cef13be787e",
    "主馆04号": "8a8586a89059b19401907cef13c47881",
    "主馆05号": "8a8586a89059b19401907cef13ca7884",
    "主馆06号": "8a8586a89059b19401907cef13d07887",
    "主馆07号": "8a8586a89059b19401907cef13d5788a",
    "主馆08号": "8a8586a89059b19401907cef13db788d",
    "主馆09号": "8a8586a89059b19401907cef13e17890",
    "主馆10号": "8a8586a89059b19401907cef13e87893",
    "主馆11号": "8a8586a89059b19401907cef13ee7896",
    "主馆12号": "8a8586a89059b19401907cef13f47899",
    "主馆13号": "8a8586a892f9bb660193288b01204325",
    "主馆14号": "8a8586a892f9bb660193288b013f4328"
}

PREFIX = "ZrbjPmjb7QCMQ"
SUFFIX = "drswx3"
URL_OCCUPY = "https://resm.lzjtu.edu.cn/hzsun-resm/sub/occupy/doOccupy"
URL_HEARTBEAT = "https://resm.lzjtu.edu.cn/hzsun-resm/freeze/queryFreezeInfos"

MY_INFO = {
    "jobNum": "12251266", "userId": "12251266", "contact": "13800000000",
    "propertyId": "8a8586a89619a58b0196a3a5462079a5"
}

# ==================== 🧠 核心逻辑类 ====================

class BookingBot:
    def __init__(self, log_callback):
        self.log = log_callback
        self.is_running = False
        self.is_alive_running = False

    def generate_payload(self, date, start_h, end_h, info_id, location_name):
        t_start = f"{date} {int(start_h):02d}:00:00"
        t_end = f"{date} {int(end_h):02d}:00:00"
        data = {
            "users": [{"jobNum": MY_INFO["jobNum"], "userId": MY_INFO["userId"], "contact": MY_INFO["contact"], "checked": False}],
            "jobNum": MY_INFO["jobNum"], "userId": MY_INFO["userId"], "applyRemark": "",
            "infoId": info_id, "occupyId": "",
            "occupyTimeStart": t_start, "occupyTimeEnd": t_end,
            "occupyType": "1", "resUseType": "0", "timeChooseType": "2", "isInvite": "0",
            "location": location_name, 
            "msgLeadTime": [], "leaveUsers": [], "auditUserIds": [],
            "formManagePropertyValueList": [{"propertyId": MY_INFO["propertyId"], "propertyValue": MY_INFO["contact"], "propertyColumnCode": "LXDH"}]
        }
        json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        return PREFIX + b64_str + SUFFIX

    def decrypt_response(self, text):
        try: return json.loads(text)
        except: pass
        try:
            if len(text) > 20:
                core = text[13:-6]
                return json.loads(base64.b64decode(core).decode('utf-8'))
        except: pass
        return text

    def start_keep_alive(self, token):
        self.is_alive_running = True
        self.log("💓 保活模式已开启！(每3分钟心跳)")
        headers = {"User-Agent": "Mozilla/5.0", "X-Access-Token": token}
        
        while self.is_alive_running:
            try:
                resp = requests.get(URL_HEARTBEAT, headers=headers, verify=False, timeout=5)
                t = datetime.now().strftime("%H:%M:%S")
                if resp.status_code == 200:
                    self.log(f"💓 [{t}] Token存活确认 (200)")
                elif resp.status_code == 401:
                    self.log(f"💀 [{t}] 警告：Token可能已失效！")
                    self.is_alive_running = False
            except: pass
            
            for _ in range(180): # 3分钟
                if not self.is_alive_running: break
                time.sleep(1)
        self.log("🛑 保活已停止")

    def start_attack(self, token, date, start_h, end_h, selected_courts, schedule_time_str=None):
        self.is_running = True
        
        # === ⏰ 定时等待逻辑 (此处已修改) ===
        if schedule_time_str:
            try:
                now = datetime.now()
                target_t = datetime.strptime(schedule_time_str, "%H:%M:%S").time()
                # 先组合成今天的时间
                target_dt = datetime.combine(now.date(), target_t)
                
                # === 核心修改点：智能判断跨天 ===
                # 如果设置的目标时间小于或等于当前时间（说明今天的时间点已过）
                # 自动将目标日期加一天（变为明天）
                if target_dt <= now:
                    target_dt += timedelta(days=1)
                    self.log(f"📅 检测到时间已过，自动设定为【明天】的 {schedule_time_str}")
                # ===========================

                self.log(f"⏳ 定时启动模式：等待至 {target_dt} ...")
                self.log(f"☕ 你可以去休息了，脚本会自动干活。")
                
                while datetime.now() < target_dt:
                    if not self.is_running: return # 允许中途取消
                    
                    # 计算倒计时
                    delta = (target_dt - datetime.now()).total_seconds()
                    if delta > 60:
                        time.sleep(1) 
                    elif delta > 1:
                        time.sleep(0.1) 
                    else:
                        pass 
                    
                self.log(f"⏰ 时间到！{datetime.now().strftime('%H:%M:%S.%f')[:-3]} 准时开火！🔥")
                
            except Exception as e:
                self.log(f"❌ 时间格式错误，跳过定时: {e}")

        # === 🚀 开始 ===
        self.log(f"🚀 日期: {date} | 时间: {start_h}-{end_h}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "X-Access-Token": token,
            "Referer": "https://resm.lzjtu.edu.cn/"
        }

        round_count = 1
        while self.is_running:
            self.log(f"\n🔄 --- 第 {round_count} 轮极速扫描 ---")
            for court_name in selected_courts:
                if not self.is_running: break
                field_id = FIELD_MAP[court_name]
                try:
                    payload = self.generate_payload(date, start_h, end_h, field_id, court_name)
                    resp = requests.post(URL_OCCUPY, headers=headers, data=payload, verify=False, timeout=3)
                    res_data = self.decrypt_response(resp.text)
                    
                    raw_check = str(res_data) + resp.text
                    is_success = False
                    if "成功" in raw_check or "success" in raw_check.lower() or "5pON5L2c5oiQ5Yqf" in raw_check: is_success = True
                    if isinstance(res_data, dict) and (res_data.get("code") == 0 or res_data.get("responseResult", {}).get("occupyId")): is_success = True

                    if is_success:
                        self.log(f"🎉🎉🎉 抢到了！！！ [{court_name}]")
                        self.is_running = False; self.is_alive_running = False
                        messagebox.showinfo("大捷！", f"抢票成功！\n场地：{court_name}\n快去付款！")
                        return
                    elif "冲突" in raw_check or "占用" in raw_check:
                        self.log(f"❌ {court_name}: 被占用")
                    elif resp.status_code == 401 or "登录" in raw_check:
                        self.log("💀 Token 失效！请更新！")
                        self.is_running = False; self.is_alive_running = False
                        return
                    else:
                        if resp.status_code == 200: self.log(f"⚠️ {court_name}: 状态200但未确认")
                        else: self.log(f"❓ {court_name}: {resp.status_code}")
                except Exception as e: self.log(f"💥 网络错误: {e}")
                time.sleep(0.05)
            round_count += 1
            time.sleep(0.2)

# ==================== 🖥️ 图形界面 (GUI) ====================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("测试")
        self.root.geometry("650x850")
        self.bot = BookingBot(self.log_msg)

        # 1. 认证
        frame_auth = tk.LabelFrame(root, text="1. 身份认证 & 保活", padx=10, pady=5)
        frame_auth.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_auth, text="X-Access-Token:", fg="red").grid(row=0, column=0, sticky="w")
        self.entry_token = tk.Entry(frame_auth, width=50)
        self.entry_token.grid(row=0, column=1, padx=5)
        self.btn_alive = tk.Button(frame_auth, text="💓 开启保活", bg="pink", command=self.toggle_keep_alive)
        self.btn_alive.grid(row=0, column=2, padx=5)

        # 2. 预约信息
        frame_info = tk.LabelFrame(root, text="2. 预约信息", padx=10, pady=5)
        frame_info.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_info, text="日期(YYYY-MM-DD):").grid(row=0, column=0)
        self.entry_date = tk.Entry(frame_info, width=12); self.entry_date.grid(row=0, column=1, padx=5)
        # 默认日期改为明天，方便你直接用
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.entry_date.insert(0, tomorrow_str)
        
        tk.Label(frame_info, text="时间段:").grid(row=0, column=2)
        self.entry_start = tk.Entry(frame_info, width=4); self.entry_start.grid(row=0, column=3); self.entry_start.insert(0, "18")
        tk.Label(frame_info, text="至").grid(row=0, column=4)
        self.entry_end = tk.Entry(frame_info, width=4); self.entry_end.grid(row=0, column=5); self.entry_end.insert(0, "20")
        
        # 3. 定时启动
        frame_schedule = tk.LabelFrame(root, text="3. ⏰ 定时启动 (狙击模式)", padx=10, pady=5, fg="blue")
        frame_schedule.pack(fill="x", padx=10, pady=5)
        
        self.var_schedule = tk.BooleanVar()
        self.chk_schedule = tk.Checkbutton(frame_schedule, text="启用定时启动", variable=self.var_schedule, command=self.toggle_schedule_entry)
        self.chk_schedule.pack(side="left", padx=10)
        
        tk.Label(frame_schedule, text="启动时间 (HH:MM:SS):").pack(side="left")
        self.entry_schedule_time = tk.Entry(frame_schedule, width=10)
        self.entry_schedule_time.pack(side="left", padx=5)
        self.entry_schedule_time.insert(0, "06:59:59") # 帮你改成了早上7点前一秒
        self.entry_schedule_time["state"] = "disabled" # 默认灰显

        # 4. 场地
        frame_court = tk.LabelFrame(root, text="4. 目标场地 (14个场全覆盖)", padx=10, pady=10)
        frame_court.pack(fill="x", padx=10, pady=5)
        self.court_vars = {}
        sorted_courts = sorted(FIELD_MAP.keys(), key=lambda x: int(x[3:-1]))
        r = 0; c = 0
        for name in sorted_courts:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(frame_court, text=name, variable=var)
            chk.grid(row=r, column=c, sticky="w", padx=5, pady=2)
            self.court_vars[name] = var
            c += 1
            if c >= 4: c = 0; r += 1

        # 5. 按钮
        frame_btn = tk.Frame(root, pady=10)
        frame_btn.pack()
        self.btn_start = tk.Button(frame_btn, text="🚀 启动任务", bg="#008000", fg="white", font=("微软雅黑", 14, "bold"), width=15, command=self.start_thread)
        self.btn_start.pack(side="left", padx=20)
        self.btn_stop = tk.Button(frame_btn, text="🛑 停止", bg="#cc0000", fg="white", font=("微软雅黑", 14, "bold"), width=10, command=self.stop)
        self.btn_stop.pack(side="right", padx=20)
        self.btn_stop["state"] = "disabled"

        # 6. 日志
        self.text_log = scrolledtext.ScrolledText(root, height=12)
        self.text_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_msg("👋 ")
        self.log_msg("💡 提示：如果你现在是晚上，设置早上7点启动，系统会自动识别为【明天早上7点】。")

    def log_msg(self, msg):
        self.text_log.insert(tk.END, msg + "\n")
        self.text_log.see(tk.END)
        
    def toggle_schedule_entry(self):
        if self.var_schedule.get():
            self.entry_schedule_time["state"] = "normal"
        else:
            self.entry_schedule_time["state"] = "disabled"

    def toggle_keep_alive(self):
        token = self.entry_token.get().strip()
        if not token: messagebox.showerror("错误", "请先填入 Token！"); return
        if self.bot.is_alive_running:
            self.bot.is_alive_running = False
            self.btn_alive.config(text="💓 开启保活", bg="pink")
            self.log_msg("🛑 停止保活...")
        else:
            self.btn_alive.config(text="💓 保活运行中...", bg="#90EE90")
            t = threading.Thread(target=self.bot.start_keep_alive, args=(token,))
            t.daemon = True; t.start()

    def start_thread(self):
        token = self.entry_token.get().strip()
        if not token: messagebox.showerror("错误", "Token 不能为空！"); return
        selected = [name for name, var in self.court_vars.items() if var.get()]
        if not selected: messagebox.showwarning("提示", "请至少勾选一个场地！"); return

        schedule_time = None
        if self.var_schedule.get():
            schedule_time = self.entry_schedule_time.get().strip()

        self.btn_start["state"] = "disabled"; self.btn_stop["state"] = "normal"
        t = threading.Thread(target=self.bot.start_attack, 
                           args=(token, self.entry_date.get(), self.entry_start.get(), self.entry_end.get(), selected, schedule_time))
        t.daemon = True; t.start()

    def stop(self):
        self.bot.is_running = False
        self.log_msg("\n🛑 任务停止...")
        self.btn_start["state"] = "normal"; self.btn_stop["state"] = "disabled"

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()