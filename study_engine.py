import customtkinter as ctk
import json
import os
import time
import random
from datetime import datetime, timedelta
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

# ================= 1. 环境与配置初始化 =================
ctk.set_appearance_mode("System")  # 自动跟随系统深色/浅色护眼模式
ctk.set_default_color_theme("green") 

DATA_FILE = "study_data.json"

# ================= 2. 工具函数 =================
def format_dur(seconds):
    s = max(0, int(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0: return f"{h}h {m}m"
    if m > 0: return f"{m}m {sec}s"
    return f"{sec}s"

def format_time(seconds):
    s = max(0, int(seconds))
    if s >= 3600:
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"
    return f"{(s%3600)//60:02d}:{s%60:02d}"

# ================= 3. 核心数据管理引擎 =================
class DataManager:
    def __init__(self):
        self.data = {
            "dailyGoal": 6 * 3600,
            "currentSubject": "专业课",
            "subjects": ["专业课", "数学", "英语", "政治"],
            "studyData": [],
            "examDate": "2026-12-20"
        }
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for key in self.data:
                        if key in loaded:
                            self.data[key] = loaded[key]
            except Exception:
                pass

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def add_record(self, subject, duration, mode, is_dead, note):
        # 严格执行考研党熬夜修正逻辑：凌晨2点前算作前一天
        logical_today = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        
        # 智能战果判定染色系统
        icon = "🌱"
        if mode == "pomodoro":
            if is_dead: icon = "🥀"
            elif duration >= 25 * 60: icon = "🌲"
            elif duration >= 15 * 60: icon = "🌳"
            else: icon = "🌿"
        else:
            if duration >= 60 * 60: icon = "🏰"
            elif duration >= 45 * 60: icon = "🏛️"
            elif duration >= 30 * 60: icon = "🏠"
            elif duration >= 15 * 60: icon = "⛺"
            elif duration >= 60: icon = "🧱"
            else: icon = "🚧"

        self.data["studyData"].append({
            "date": logical_today,
            "subject": subject,
            "duration": duration,
            "tree": icon,
            "note": note
        })
        self.save_data()

    def get_filtered_data(self, range_str):
        logical_now = datetime.now() - timedelta(hours=2)
        today_str = logical_now.strftime("%Y-%m-%d")
        
        if range_str == "day":
            return [item for item in self.data["studyData"] if item.get("date") == today_str]
        elif range_str == "week":
            start_of_week = logical_now - timedelta(days=logical_now.weekday())
            week_dates = [(start_of_week + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            return [item for item in self.data["studyData"] if item.get("date") in week_dates]
        elif range_str == "month":
            current_month_prefix = logical_now.strftime("%Y-%m-")
            return [item for item in self.data["studyData"] if str(item.get("date")).startswith(current_month_prefix)]
        return []

# ================= 4. 响应式桌面 UI 交互系统 =================
class StudyEngineApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = DataManager()
        self.encouragements = [
            "星光不问赶路人，时光不负有心人。",
            "你做三四月的事，在十二月自有答案。",
            "那些看似不起波澜的日复一日，会突然在某天让人看到坚持的意义。",
            "当前的每一次咬牙坚持，都是为了初试的毫不费力。",
            "顶峰相见吧，在十二月最冷的冬日里拼出最热血的成绩。"
        ]

        # 宿主窗口物理规格定义
        self.title("冲刺备考引擎")
        self.geometry("450x720")
        self.set_window_center()

        # 核心线程变量控制
        self.timer_active = False
        self.mode = ctk.StringVar(value="pomodoro")
        self.pomo_target = 25 * 60
        self.elapsed_time = 0
        self.start_tick = 0
        self.current_forest_range = "day"
        self.current_stats_range = "day"
        self.last_logical_date = self.get_logical_date_string()

        self.build_ui()
        self.loop_worker()

    def set_window_center(self):
        self.update_idletasks()
        width = 450
        height = 720
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def get_logical_date_string(self):
        return (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")

    def get_random_quote(self):
        return random.choice(self.encouragements)

    def build_ui(self):
        # 顶置全局卡片：考研倒计时看板
        self.countdown_frame = ctk.CTkFrame(self, height=45, fg_color=("#E5F1FF", "#1C2D42"))
        self.countdown_frame.pack(fill="x", padx=15, pady=(15, 5))
        self.countdown_label = ctk.CTkLabel(self.countdown_frame, text="距离考研初试仅剩 -- 天", font=("Helvetica", 14, "bold"), text_color=("#007AFF", "#66B2FF"))
        self.countdown_label.pack(expand=True)
        self.refresh_exam_countdown()

        # 灵动多签页面板
        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color="#34C759")
        self.tabview.pack(padx=15, pady=(5, 15), fill="both", expand=True)
        
        self.tab_focus = self.tabview.add("专注")
        self.tab_forest = self.tabview.add("图鉴")
        self.tab_stats = self.tabview.add("统计")
        self.tab_settings = self.tabview.add("设置")

        # 装配底层子面板
        self.assemble_focus_tab()
        self.assemble_forest_tab()
        self.assemble_stats_tab()
        self.assemble_settings_tab()

    def assemble_focus_tab(self):
        # 科目快捷浮动下拉盒
        self.subject_var = ctk.StringVar(value=self.db.data["currentSubject"])
        self.subject_menu = ctk.CTkOptionMenu(self.tab_focus, values=self.db.data["subjects"], variable=self.subject_var, command=self.sync_subject_preference)
        self.subject_menu.pack(pady=(15, 10))

        # 场景拟物拟态图标区
        self.icon_label = ctk.CTkLabel(self.tab_focus, text="🌰", font=("Segoe UI Emoji", 72))
        self.icon_label.pack(pady=10)

        # 数字化高刷时钟
        self.time_label = ctk.CTkLabel(self.tab_focus, text="25:00", font=("Consolas", 52, "bold"))
        self.time_label.pack(pady=5)

        # 随动动态格言便签
        self.quote_label = ctk.CTkLabel(self.tab_focus, text=self.encouragements[0], font=("Helvetica", 12), text_color="#8E8E93")
        self.quote_label.pack(pady=(0, 15))

        # 智能秒级实时填充进度槽
        self.goal_frame = ctk.CTkFrame(self.tab_focus, fg_color="transparent")
        self.goal_frame.pack(fill="x", padx=25, pady=10)
        self.goal_header_label = ctk.CTkLabel(self.goal_frame, text="🎯 今日目标进度: 0m / 6h", font=("Helvetica", 12, "bold"))
        self.goal_header_label.pack(anchor="w", pady=2)
        self.goal_progress_bar = ctk.CTkProgressBar(self.goal_frame, progress_color="#30D158", height=8)
        self.goal_progress_bar.pack(fill="x")
        self.goal_progress_bar.set(0)

        # 双轨模式锁
        self.mode_frame = ctk.CTkFrame(self.tab_focus, fg_color=("#F2F2F7", "#2C2C2E"))
        self.mode_frame.pack(pady=15, padx=25, fill="x")
        ctk.CTkRadioButton(self.mode_frame, text="🧱 筑城 (正向)", variable=self.mode, value="stopwatch", command=self.handle_mode_switch).pack(side="left", padx=20, pady=10)
        ctk.CTkRadioButton(self.mode_frame, text="🌱 种树 (番茄)", variable=self.mode, value="pomodoro", command=self.handle_mode_switch).pack(side="right", padx=20, pady=10)

        # 番茄钟时间选择器
        self.pomo_options = ["15分钟", "25分钟", "35分钟", "45分钟", "60分钟", "90分钟"]
        self.pomo_var = ctk.StringVar(value="25分钟")
        self.pomo_menu = ctk.CTkOptionMenu(self.tab_focus, values=self.pomo_options, variable=self.pomo_var, command=self.change_pomo_time)
        self.pomo_menu.pack(pady=(0, 10))

        # 控制中枢网格
        self.ctrl_frame = ctk.CTkFrame(self.tab_focus, fg_color="transparent")
        self.ctrl_frame.pack(pady=10)
        self.start_btn = ctk.CTkButton(self.ctrl_frame, text="▶ 开始专注", font=("Helvetica", 13, "bold"), width=130, height=38, command=self.trigger_timer_switch)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = ctk.CTkButton(self.ctrl_frame, text="⏹ 结束", fg_color="#FF3B30", hover_color="#C92A20", font=("Helvetica", 13, "bold"), width=130, height=38, command=lambda: self.terminate_session(False), state="disabled")
        self.stop_btn.pack(side="left", padx=8)

    def assemble_forest_tab(self):
        self.forest_selector = ctk.CTkSegmentedButton(self.tab_forest, values=["今日战果", "本周图鉴", "本月图鉴"], command=self.switch_forest_scope)
        self.forest_selector.set("今日战果")
        self.forest_selector.pack(pady=10, padx=15, fill="x")

        self.forest_summary = ctk.CTkLabel(self.tab_forest, text="累计收获 0 个战果", font=("Helvetica", 12, "bold"), text_color="#8E8E93")
        self.forest_summary.pack(pady=2)

        self.forest_scroll = ctk.CTkScrollableFrame(self.tab_forest, label_text="生态图鉴面板")
        self.forest_scroll.pack(fill="both", expand=True, padx=15, pady=10)

    def assemble_stats_tab(self):
        self.stats_selector = ctk.CTkSegmentedButton(self.tab_stats, values=["今日", "本周", "本月"], command=self.switch_stats_scope)
        self.stats_selector.set("今日")
        self.stats_selector.pack(pady=10, padx=15, fill="x")

        self.stats_summary_card = ctk.CTkFrame(self.tab_stats, height=70)
        self.stats_summary_card.pack(fill="x", padx=15, pady=5)
        
        self.stats_total_label = ctk.CTkLabel(self.stats_summary_card, text="0s", font=("Helvetica", 24, "bold"))
        self.stats_total_label.pack(side="left", padx=20)
        
        self.stats_delta_label = ctk.CTkLabel(self.stats_summary_card, text="当前无历史比对数据", font=("Helvetica", 11, "bold"), text_color="#8E8E93")
        self.stats_delta_label.pack(side="right", padx=20)

        self.chart_scroll = ctk.CTkScrollableFrame(self.tab_stats, label_text="多科目复盘仪表盘")
        self.chart_scroll.pack(fill="both", expand=True, padx=15, pady=10)

    def assemble_settings_tab(self):
        self.settings_scroll = ctk.CTkScrollableFrame(self.tab_settings, label_text="引擎高级配置")
        self.settings_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(self.settings_scroll, text="🎯 调整每日专注目标 (小时):", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.goal_input_var = ctk.StringVar(value=str(self.db.data["dailyGoal"] / 3600))
        self.goal_input = ctk.CTkEntry(self.settings_scroll, textvariable=self.goal_input_var, width=120)
        self.goal_input.pack(anchor="w", padx=10, pady=5)
        self.goal_input.bind("<FocusOut>", self.update_goal_threshold)
        self.goal_input.bind("<Return>", self.update_goal_threshold)

        ctk.CTkLabel(self.settings_scroll, text="🏷️ 管理备考科目分类:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10, pady=(15, 2))
        self.subject_listbox_frame = ctk.CTkFrame(self.settings_scroll)
        self.subject_listbox_frame.pack(fill="x", padx=10, pady=5)
        
        self.refresh_settings_subject_view()

        ctk.CTkLabel(self.settings_scroll, text="💾 数据底层备份与容灾恢复:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10, pady=(20, 2))
        ctk.CTkButton(self.settings_scroll, text="⬇ 导出本地记录备份 (JSON)", command=self.export_records_safe).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.settings_scroll, text="⬆ 导入历史数据恢复", fg_color="transparent", border_width=1, command=self.import_records_safe).pack(fill="x", padx=10, pady=5)

    # ================= 5. 底层逻辑核运行方法 =================
    def sync_subject_preference(self, choice):
        if self.timer_active:
            messagebox.showwarning("限制", "当前正在高能专注中，不可更换科目！")
            self.subject_var.set(self.db.data["currentSubject"])
            return
        self.db.data["currentSubject"] = choice
        self.db.save_data()

    def change_pomo_time(self, choice):
        if self.timer_active:
            messagebox.showwarning("拦截", "🍅 计时正在进行中，无法修改目标时间！")
            self.pomo_var.set(f"{int(self.pomo_target/60)}分钟")
            return
        mins = int(choice.replace("分钟", ""))
        self.pomo_target = mins * 60
        self.elapsed_time = 0
        self.time_label.configure(text=format_time(self.pomo_target))

    def handle_mode_switch(self):
        if self.timer_active:
            messagebox.showwarning("拦截", "请先安全截断或完成当前的专注线程！")
            self.mode.set("pomodoro" if self.mode.get() == "stopwatch" else "stopwatch")
            return
        self.elapsed_time = 0
        if self.mode.get() == "pomodoro":
            self.time_label.configure(text=format_time(self.pomo_target))
            self.icon_label.configure(text="🌰")
            self.pomo_menu.configure(state="normal")
        else:
            self.time_label.configure(text="00:00:00")
            self.icon_label.configure(text="🚧")
            self.pomo_menu.configure(state="disabled")

    def trigger_timer_switch(self):
        if not self.timer_active:
            self.timer_active = True
            self.start_tick = time.time() - self.elapsed_time
            self.start_btn.configure(text="⏸ 暂停专注", fg_color="#FF9500", hover_color="#E08300")
            self.stop_btn.configure(state="normal")
            self.subject_menu.configure(state="disabled")
            self.pomo_menu.configure(state="disabled")
        else:
            self.timer_active = False
            self.start_btn.configure(text="▶ 继续专注", fg_color="#34C759", hover_color="#248A3D")

    def terminate_session(self, auto_save=False):
        is_dead = False
        force_save_short = False
        if not auto_save:
            if self.mode.get() == "pomodoro" and self.elapsed_time < self.pomo_target:
                if self.elapsed_time < 60:
                    if not messagebox.askyesno("微短时间校验", "当前专注不足 1 分钟，胚胎尚未破土。\n\n点击【是】强行记入惩罚枯树 🥀，点击【否】无痛销毁。"):
                        self.abort_current_run()
                        return
                    is_dead = True
                else:
                    if messagebox.askyesno("放弃警告", "警告：当前番茄未孵化完成！\n\n如果强行退场，幼苗将会直接枯死(🥀)。确定终止吗？"):
                        is_dead = True
                    else:
                        return
            elif self.mode.get() == "stopwatch" and self.elapsed_time < 60:
                if not messagebox.askyesno("微短时间校验", "正向筑城不足 1 分钟，未完成一块完整基砖。\n\n是否仍要保存这几秒的路障(🚧)痕迹？"):
                    self.abort_current_run()
                    return
                force_save_short = True

        self.timer_active = False
        note_content = ""
        if not is_dead and self.elapsed_time >= 60:
            dialog = ctk.CTkInputDialog(text=f"📝 本轮学习结束！\n\n送你一句：{self.get_random_quote()}\n\n留下你的复盘便签（选填）：", title="知识存根")
            note_content = dialog.get() or ""
            note_content = note_content.strip()[:50]

        self.db.add_record(self.db.data["currentSubject"], self.elapsed_time, self.mode.get(), is_dead, note_content)
        self.abort_current_run()

    def abort_current_run(self):
        self.timer_active = False
        self.elapsed_time = 0
        self.start_btn.configure(text="▶ 开始专注", fg_color="#34C759", hover_color="#248A3D")
        self.stop_btn.configure(state="disabled")
        self.subject_menu.configure(state="normal")
        self.pomo_menu.configure(state="normal")
        self.handle_mode_switch()
        self.render_forest_view()
        self.render_stats_dashboard()
        self.title("冲刺备考引擎")

    def check_cross_day(self):
        if not self.timer_active:
            self.elapsed_time = 0
        else:
            self.terminate_session(auto_save=True)
            self.start_tick = time.time()
            self.timer_active = True

    def loop_worker(self):
        # 跨天校验
        current_logical_date = self.get_logical_date_string()
        if current_logical_date != self.last_logical_date:
            self.last_logical_date = current_logical_date
            self.check_cross_day()

        if self.timer_active:
            self.elapsed_time = time.time() - self.start_tick
            
            if self.mode.get() == "pomodoro":
                remain = self.pomo_target - self.elapsed_time
                if remain <= 0:
                    self.elapsed_time = self.pomo_target
                    self.terminate_session(auto_save=True)
                    messagebox.showinfo("达成", "🌲 终点到！一棵考研必胜树已牢牢锁进你的图鉴里！")
                    return
                else:
                    self.time_label.configure(text=format_time(remain))
                    # Python 原生的 f-string 语法，彻底消除 JS 报错
                    self.title(f"(🌱 {int(remain//60)}m) 考研必胜室")
            else:
                self.time_label.configure(text=format_time(self.elapsed_time))
                self.title(f"(🧱 {format_dur(self.elapsed_time)}) 正在搬砖...")

            self.refresh_live_tree_icon()
            self.refresh_live_goal_bar()

        self.after(200, self.loop_worker)

    def refresh_live_tree_icon(self):
        icon = "🌱"
        if self.mode.get() == "pomodoro":
            progress = self.elapsed_time / self.pomo_target
            if progress >= 1.0: icon = "🌲"
            elif progress >= 0.66: icon = "🌳"
            elif progress >= 0.33: icon = "🌿"
            elif self.elapsed_time >= 60: icon = "🌱"
            else: icon = "🌰"
        else:
            if self.elapsed_time >= 3600: icon = "🏰"
            elif self.elapsed_time >= 2700: icon = "🏛️"
            elif self.elapsed_time >= 1800: icon = "🏠"
            elif self.elapsed_time >= 900: icon = "⛺"
            elif self.elapsed_time >= 60: icon = "🧱"
            else: icon = "🚧"
        self.icon_label.configure(text=icon)

    def refresh_live_goal_bar(self):
        logical_today = self.get_logical_date_string()
        records = [item for item in self.db.data["studyData"] if item.get("date") == logical_today]
        total = sum(r["duration"] for r in records)
        if self.timer_active:
            total += self.elapsed_time
        
        goal = self.db.data["dailyGoal"]
        percent = min(total / goal, 1.0)
        self.goal_header_label.configure(text=f"🎯 今日目标进度: {format_dur(total)} / {format_dur(goal)}")
        self.goal_progress_bar.set(percent)

    def refresh_exam_countdown(self):
        try:
            today = datetime.now().date()
            exam = datetime.strptime(self.db.data["examDate"], "%Y-%m-%d").date()
            diff = (exam - today).days
            color = "#FF3B30" if diff < 150 else "#007AFF"
            self.countdown_label.configure(text=f"距离考研初试仅剩 {diff} 天", text_color=color)
        except:
            pass

    # ================= 6. 图鉴与统计高级排版引擎 =================
    def switch_forest_scope(self, selection):
        mapping = {"今日战果": "day", "本周图鉴": "week", "本月图鉴": "month"}
        self.current_forest_range = mapping.get(selection, "day")
        self.render_forest_view()

    def render_forest_view(self):
        for widget in self.forest_scroll.winfo_children():
            widget.destroy()

        records = self.db.get_filtered_data(self.current_forest_range)
        self.forest_summary.configure(text=f"当前时段累计收获 {len(records)} 个战果")

        if not records:
            ctk.CTkLabel(self.forest_scroll, text="此片净土暂无数据\n\n快去控制台开启你的第一轮专注吧 ✨", font=("Helvetica", 12), text_color="#8E8E93").pack(pady=40)
            return

        grid_frame = ctk.CTkFrame(self.forest_scroll, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        
        row, col = 0, 0
        for r in records:
            lbl = ctk.CTkLabel(grid_frame, text=r.get("tree", "🌲"), font=("Segoe UI Emoji", 28), cursor="hand2")
            lbl.grid(row=row, column=col, padx=8, pady=8)
            
            note_text = f" [{r['note']}]" if r.get("note") else ""
            info_string = f"{r['subject']} | {format_dur(r['duration'])}{note_text}"
            self.bind_hover_tip(lbl, info_string)
            
            col += 1
            if col > 6: 
                col = 0
                row += 1

    def bind_hover_tip(self, widget, text):
        def on_enter(e):
            self.forest_summary.configure(text=text, text_color=("#007AFF", "#66B2FF"))
        def on_leave(e):
            count = len(self.db.get_filtered_data(self.current_forest_range))
            self.forest_summary.configure(text=f"当前时段累计收获 {count} 个战果", text_color="#8E8E93")
            
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def switch_stats_scope(self, selection):
        mapping = {"今日": "day", "本周": "week", "本月": "month"}
        self.current_stats_range = mapping.get(selection, "day")
        self.render_stats_dashboard()

    def render_stats_dashboard(self):
        for widget in self.chart_scroll.winfo_children():
            widget.destroy()

        curr_records = self.db.get_filtered_data(self.current_stats_range)
        curr_total = sum(r["duration"] for r in curr_records)
        self.stats_total_label.configure(text=format_dur(curr_total))

        logical_now = datetime.now() - timedelta(hours=2)
        if self.current_stats_range == "day":
            p_start = logical_now - timedelta(days=1)
            p_end = p_start
        elif self.current_stats_range == "week":
            p_start = logical_now - timedelta(days=logical_now.weekday() + 7)
            p_end = p_start + timedelta(days=6)
        else:
            p_start = (logical_now.replace(day=1) - timedelta(days=1)).replace(day=1)
            p_end = logical_now.replace(day=1) - timedelta(days=1)

        prev_total = sum(r["duration"] for r in self.db.data["studyData"] if p_start.strftime("%Y-%m-%d") <= str(r.get("date")) <= p_end.strftime("%Y-%m-%d"))
        
        delta = curr_total - prev_total
        if curr_total == 0 and prev_total == 0:
            self.stats_delta_label.configure(text="暂无对比样本", text_color="#8E8E93")
        elif delta >= 0:
            self.stats_delta_label.configure(text=f"↑ 比上期多 {format_dur(delta)}", text_color="#34C759")
        else:
            self.stats_delta_label.configure(text=f"↓ 比上期少 {format_dur(abs(delta))}", text_color="#FF3B30")

        if not curr_records:
            ctk.CTkLabel(self.chart_scroll, text="当前无分析样本", font=("Helvetica", 12), text_color="#8E8E93").pack(pady=30)
            return

        subject_map = {}
        for r in curr_records:
            subject_map[r["subject"]] = subject_map.get(r["subject"], 0) + r["duration"]

        for sub, dur in sorted(subject_map.items(), key=lambda x: x[1], reverse=True):
            pct = dur / curr_total if curr_total > 0 else 0
            
            bar_frame = ctk.CTkFrame(self.chart_scroll, fg_color="transparent")
            bar_frame.pack(fill="x", pady=6, padx=5)

            lbl_title = ctk.CTkLabel(bar_frame, text=f"{sub} ({round(pct*100, 1)}%)", font=("Helvetica", 12, "bold"))
            lbl_title.pack(side="left")
            
            lbl_time = ctk.CTkLabel(bar_frame, text=format_dur(dur), font=("Helvetica", 11), text_color="#8E8E93")
            lbl_time.pack(side="right")

            p_bar = ctk.CTkProgressBar(self.chart_scroll, height=6, progress_color="#007AFF")
            p_bar.pack(fill="x", pady=(0, 10), padx=5)
            p_bar.set(pct)

    # ================= 7. 高级设置与全能生命周期控制 =================
    def update_goal_threshold(self, event=None):
        try:
            val = float(self.goal_input_var.get())
            if val > 0:
                self.db.data["dailyGoal"] = val * 3600
                self.db.save_data()
                self.refresh_live_goal_bar()
        except:
            self.goal_input_var.set(str(self.db.data["dailyGoal"] / 3600))

    def refresh_settings_subject_view(self):
        for widget in self.subject_listbox_frame.winfo_children():
            widget.destroy()

        for sub in self.db.data["subjects"]:
            sub_row = ctk.CTkFrame(self.subject_listbox_frame, fg_color="transparent")
            sub_row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(sub_row, text=f"• {sub}", font=("Helvetica", 12)).pack(side="left", padx=5)
            
            btn_del = ctk.CTkButton(sub_row, text="删除", width=45, height=20, fg_color="#FF3B30", hover_color="#C92A20", font=("Helvetica", 10), command=lambda s=sub: self.remove_custom_subject(s))
            btn_del.pack(side="right", padx=5)

        add_row = ctk.CTkFrame(self.subject_listbox_frame, fg_color="transparent")
        add_row.pack(fill="x", pady=8)
        self.new_sub_entry = ctk.CTkEntry(add_row, placeholder_text="输入新科目...", height=25, width=150)
        self.new_sub_entry.pack(side="left", padx=5)
        ctk.CTkButton(add_row, text="＋ 新增", width=60, height=25, font=("Helvetica", 11, "bold"), command=self.append_custom_subject).pack(side="left", padx=5)

    def append_custom_subject(self):
        name = self.new_sub_entry.get().strip()
        if not name: return
        name = name[:10]
        if name in self.db.data["subjects"]:
            messagebox.showwarning("冲突", "该科目分类已存在！")
            return
        self.db.data["subjects"].append(name)
        self.db.save_data()
        self.refresh_settings_subject_view()
        self.subject_menu.configure(values=self.db.data["subjects"])
        self.new_sub_entry.delete(0, 'end')

    def remove_custom_subject(self, name):
        if self.timer_active:
            messagebox.showwarning("锁定", "高能状态中禁止重构科目群！")
            return
        if len(self.db.data["subjects"]) <= 1:
            messagebox.showwarning("限制", "至少需要保留一个激活的科目分类！")
            return
        if messagebox.askyesno("确认", f"确定要剥离【{name}】分类吗？\n\n历史统计记录将被保全，不会受影响。"):
            self.db.data["subjects"].remove(name)
            if self.db.data["currentSubject"] == name:
                self.db.data["currentSubject"] = self.db.data["subjects"][0]
                self.subject_var.set(self.db.data["currentSubject"])
            self.db.save_data()
            self.refresh_settings_subject_view()
            self.subject_menu.configure(values=self.db.data["subjects"])

    def export_records_safe(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.db.data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", "考研数据备份全量导出成功！")

    def import_records_safe(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if "studyData" in loaded:
                    self.db.data.update(loaded)
                    self.db.save_data()
                    self.abort_current_run() 
                    messagebox.showinfo("复原", "历史归档数据灾后重建复原成功！")
            except Exception:
                messagebox.showerror("失败", "文件损坏或结构遭污染，导入失败！")

if __name__ == "__main__":
    app = StudyEngineApp()
    app.render_forest_view()
    app.render_stats_dashboard()
    app.mainloop()
