import customtkinter as ctk
import json
import os
import sys
import time
import random
from datetime import datetime, timedelta
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

# ================= 1. 环境与配置初始化 =================
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    
DATA_FILE = os.path.join(application_path, "study_data.json")

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
        logical_today = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        
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

# ================= 4. 极致自适应 UI 系统 =================
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

        # 💡 解除限制：允许自适应调整，但设定最小安全尺寸
        self.title("冲刺备考引擎")
        self.geometry("500x820")
        self.minsize(400, 650) 
        self.configure(fg_color=("#F2F2F7", "#000000")) 
        self.set_window_center()

        # 定义全局柔和字体
        self.font_main = ("Microsoft YaHei UI", 14)
        self.font_title = ("Microsoft YaHei UI", 16, "bold")
        self.font_number = ("Consolas", 72, "bold")

        self.timer_active = False
        self.mode = "pomodoro" 
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
        width = 500
        height = 820
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def get_logical_date_string(self):
        return (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")

    def get_random_quote(self):
        return random.choice(self.encouragements)

    def create_card(self, parent, **kwargs):
        bg_color = kwargs.pop("fg_color", ("#FFFFFF", "#1C1C1E"))
        radius = kwargs.pop("corner_radius", 18) # 更圆润的苹果卡片风格
        return ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=radius, **kwargs)

    def build_ui(self):
        # 顶部考研倒计时 (自动拉伸 fill="x")
        self.countdown_card = self.create_card(self)
        self.countdown_card.pack(fill="x", padx=20, pady=(20, 10))
        self.countdown_label = ctk.CTkLabel(self.countdown_card, text="距离初试仅剩 -- 天", font=self.font_title, text_color=("#007AFF", "#0A84FF"))
        self.countdown_label.pack(pady=16)
        self.refresh_exam_countdown()

        # 核心多标签页面板 (自动拉伸 fill="both", expand=True)
        self.tabview = ctk.CTkTabview(self, fg_color="transparent", bg_color="transparent", 
                                      segmented_button_selected_color=("#34C759", "#30D158"), 
                                      segmented_button_selected_hover_color=("#248A3D", "#248A3D"),
                                      text_color=("#1C1C1E", "#FFFFFF"), font=("Microsoft YaHei UI", 14, "bold"))
        self.tabview.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        
        self.tab_focus = self.tabview.add("专注")
        self.tab_forest = self.tabview.add("图鉴")
        self.tab_stats = self.tabview.add("统计")
        self.tab_settings = self.tabview.add("设置")

        self.assemble_focus_tab()
        self.assemble_forest_tab()
        self.assemble_stats_tab()
        self.assemble_settings_tab()

    def assemble_focus_tab(self):
        self.focus_card = self.create_card(self.tab_focus)
        self.focus_card.pack(fill="both", expand=True, pady=5)

        # 💡 弹性排版：将倒计时区域放在中间自适应扩展
        self.focus_top = ctk.CTkFrame(self.focus_card, fg_color="transparent")
        self.focus_top.pack(fill="x", pady=20)
        
        self.subject_var = ctk.StringVar(value=self.db.data["currentSubject"])
        self.subject_menu = ctk.CTkOptionMenu(self.focus_top, values=self.db.data["subjects"], variable=self.subject_var, command=self.sync_subject_preference, 
                                              fg_color=("#F2F2F7", "#2C2C2E"), text_color=("#1C1C1E", "#FFFFFF"), button_color=("#E5E5EA", "#3A3A3C"), 
                                              font=("Microsoft YaHei UI", 14, "bold"), corner_radius=10, height=36)
        self.subject_menu.pack()

        # 中部弹性扩展区
        self.focus_center = ctk.CTkFrame(self.focus_card, fg_color="transparent")
        self.focus_center.pack(expand=True, fill="both")

        self.icon_label = ctk.CTkLabel(self.focus_center, text="🌰", font=("Segoe UI Emoji", 90))
        self.icon_label.pack(expand=True, side="bottom", pady=(0, 0))

        self.time_label = ctk.CTkLabel(self.focus_center, text="25:00", font=self.font_number, text_color=("#1C1C1E", "#FFFFFF"))
        self.time_label.pack(expand=True, side="bottom", pady=(0, 0))

        self.quote_label = ctk.CTkLabel(self.focus_center, text=self.encouragements[0], font=("Microsoft YaHei UI", 13), text_color="#8E8E93")
        self.quote_label.pack(expand=True, side="bottom", pady=(0, 20))

        # 底部控制区锚定
        self.focus_bottom = ctk.CTkFrame(self.focus_card, fg_color="transparent")
        self.focus_bottom.pack(fill="x", side="bottom", pady=20, padx=20)

        self.goal_frame = ctk.CTkFrame(self.focus_bottom, fg_color="transparent")
        self.goal_frame.pack(fill="x", pady=(0, 20))
        self.goal_header_label = ctk.CTkLabel(self.goal_frame, text="🎯 今日进度: 0m / 6h", font=("Microsoft YaHei UI", 12, "bold"), text_color="#8E8E93")
        self.goal_header_label.pack(anchor="w", pady=2)
        self.goal_progress_bar = ctk.CTkProgressBar(self.goal_frame, progress_color=("#34C759", "#30D158"), height=8, corner_radius=4)
        self.goal_progress_bar.pack(fill="x")
        self.goal_progress_bar.set(0)

        self.mode_selector = ctk.CTkSegmentedButton(self.focus_bottom, values=["🧱 正向筑城", "🌱 番茄种树"], command=self.handle_mode_switch, 
                                                    selected_color=("#007AFF", "#0A84FF"), selected_hover_color=("#0056B3", "#0056B3"), font=("Microsoft YaHei UI", 13, "bold"), height=36)
        self.mode_selector.set("🌱 番茄种树")
        self.mode_selector.pack(fill="x", pady=(0, 15))

        self.pomo_options = ["15分钟", "25分钟", "35分钟", "45分钟", "60分钟", "90分钟"]
        self.pomo_var = ctk.StringVar(value="25分钟")
        self.pomo_menu = ctk.CTkOptionMenu(self.focus_bottom, values=self.pomo_options, variable=self.pomo_var, command=self.change_pomo_time, 
                                           fg_color=("#F2F2F7", "#2C2C2E"), text_color=("#007AFF", "#0A84FF"), button_color=("#E5E5EA", "#3A3A3C"), 
                                           font=("Microsoft YaHei UI", 13, "bold"), corner_radius=10, height=36)
        self.pomo_menu.pack(pady=(0, 20))

        self.ctrl_frame = ctk.CTkFrame(self.focus_bottom, fg_color="transparent")
        self.ctrl_frame.pack(fill="x")
        self.start_btn = ctk.CTkButton(self.ctrl_frame, text="▶ 开始专注", font=("Microsoft YaHei UI", 16, "bold"), height=50, corner_radius=25, 
                                       fg_color=("#34C759", "#30D158"), hover_color=("#248A3D", "#248A3D"), command=self.trigger_timer_switch)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(self.ctrl_frame, text="⏹ 结束", font=("Microsoft YaHei UI", 16, "bold"), height=50, corner_radius=25, 
                                      fg_color=("#FF3B30", "#FF453A"), hover_color=("#C92A20", "#C92A20"), command=lambda: self.terminate_session(False), state="disabled")
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def assemble_forest_tab(self):
        self.forest_selector = ctk.CTkSegmentedButton(self.tab_forest, values=["今日战果", "本周图鉴", "本月图鉴"], command=self.switch_forest_scope, font=("Microsoft YaHei UI", 13, "bold"), height=36)
        self.forest_selector.set("今日战果")
        self.forest_selector.pack(pady=(10, 15), fill="x", padx=10)

        self.forest_summary = ctk.CTkLabel(self.tab_forest, text="累计收获 0 个战果", font=("Microsoft YaHei UI", 14, "bold"), text_color="#8E8E93")
        self.forest_summary.pack(pady=(0, 10))

        self.forest_card = self.create_card(self.tab_forest)
        self.forest_card.pack(fill="both", expand=True)
        
        self.forest_scroll = ctk.CTkScrollableFrame(self.forest_card, fg_color="transparent", corner_radius=0)
        self.forest_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.forest_grid_frame = ctk.CTkFrame(self.forest_scroll, fg_color="transparent")
        self.forest_grid_frame.pack(fill="both", expand=True)
        
        # 💡 动态网格监听：随窗口宽度自动折行排版
        self.forest_scroll.bind("<Configure>", self.on_forest_resize)
        self.forest_widgets = []

    def on_forest_resize(self, event=None):
        if not hasattr(self, 'forest_widgets') or not self.forest_widgets: return
        self.forest_scroll.update_idletasks()
        width = self.forest_scroll.winfo_width()
        cols = max(1, width // 80) # 每棵树预留80像素宽度
        if cols == getattr(self, 'current_forest_cols', 0): return
        self.current_forest_cols = cols
        
        for i, w in enumerate(self.forest_widgets):
            w.grid(row=i//cols, column=i%cols, padx=15, pady=15)

    def assemble_stats_tab(self):
        self.stats_selector = ctk.CTkSegmentedButton(self.tab_stats, values=["今日", "本周", "本月"], command=self.switch_stats_scope, font=("Microsoft YaHei UI", 13, "bold"), height=36)
        self.stats_selector.set("今日")
        self.stats_selector.pack(pady=(10, 15), fill="x", padx=10)

        self.stats_summary_card = self.create_card(self.tab_stats, height=90)
        self.stats_summary_card.pack(fill="x", pady=(0, 15))
        self.stats_summary_card.pack_propagate(False) 
        
        self.stats_total_label = ctk.CTkLabel(self.stats_summary_card, text="0s", font=("Consolas", 36, "bold"), text_color=("#1C1C1E", "#FFFFFF"))
        self.stats_total_label.pack(side="left", padx=25, pady=20)
        
        self.stats_delta_label = ctk.CTkLabel(self.stats_summary_card, text="无对比数据", font=("Microsoft YaHei UI", 13, "bold"), text_color="#8E8E93")
        self.stats_delta_label.pack(side="right", padx=25, pady=20)

        self.chart_card = self.create_card(self.tab_stats)
        self.chart_card.pack(fill="both", expand=True)
        self.chart_scroll = ctk.CTkScrollableFrame(self.chart_card, fg_color="transparent", corner_radius=0)
        self.chart_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def assemble_settings_tab(self):
        self.settings_scroll = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent", corner_radius=0)
        self.settings_scroll.pack(fill="both", expand=True)

        goal_card = self.create_card(self.settings_scroll)
        goal_card.pack(fill="x", pady=(10, 15), ipady=15)
        ctk.CTkLabel(goal_card, text="🎯 每日专注目标 (小时)", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=25, pady=(15, 10))
        self.goal_input_var = ctk.StringVar(value=str(self.db.data["dailyGoal"] / 3600))
        self.goal_input = ctk.CTkEntry(goal_card, textvariable=self.goal_input_var, font=("Microsoft YaHei UI", 15), corner_radius=10, height=40)
        self.goal_input.pack(fill="x", padx=25, pady=(0, 10))
        self.goal_input.bind("<FocusOut>", self.update_goal_threshold)
        self.goal_input.bind("<Return>", self.update_goal_threshold)

        sub_card = self.create_card(self.settings_scroll)
        sub_card.pack(fill="x", pady=(0, 15), ipady=15)
        ctk.CTkLabel(sub_card, text="🏷️ 备考科目管理", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=25, pady=(15, 10))
        self.subject_listbox_frame = ctk.CTkFrame(sub_card, fg_color="transparent")
        self.subject_listbox_frame.pack(fill="x", padx=25)
        self.refresh_settings_subject_view()

        data_card = self.create_card(self.settings_scroll)
        data_card.pack(fill="x", pady=(0, 10), ipady=15)
        ctk.CTkLabel(data_card, text="💾 数据安全与容灾", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=25, pady=(15, 10))
        ctk.CTkButton(data_card, text="⬇ 导出记录备份 (JSON)", font=("Microsoft YaHei UI", 14, "bold"), height=42, corner_radius=10, fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1C1C1E", "#FFFFFF"), hover_color=("#D1D1D6", "#48484A"), command=self.export_records_safe).pack(fill="x", padx=25, pady=(5, 10))
        ctk.CTkButton(data_card, text="⬆ 导入历史数据恢复", font=("Microsoft YaHei UI", 14, "bold"), height=42, corner_radius=10, fg_color="transparent", border_width=2, border_color=("#D1D1D6", "#48484A"), text_color=("#1C1C1E", "#FFFFFF"), hover_color=("#E5E5EA", "#3A3A3C"), command=self.import_records_safe).pack(fill="x", padx=25, pady=(5, 10))

    # ================= 5. 底层逻辑 =================
    def sync_subject_preference(self, choice):
        if self.timer_active:
            messagebox.showwarning("限制", "当前正在专注中，不可更换科目！")
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

    def handle_mode_switch(self, choice):
        if self.timer_active:
            messagebox.showwarning("拦截", "请先结束当前的专注线程！")
            self.mode_selector.set("🌱 番茄种树" if self.mode == "pomodoro" else "🧱 正向筑城")
            return
        
        self.mode = "pomodoro" if "番茄" in choice else "stopwatch"
        self.elapsed_time = 0
        
        if self.mode == "pomodoro":
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
            self.start_btn.configure(text="⏸ 暂停专注", fg_color=("#FF9500", "#FF9F0A"), hover_color="#E08300")
            self.stop_btn.configure(state="normal")
            self.subject_menu.configure(state="disabled")
            self.pomo_menu.configure(state="disabled")
            self.mode_selector.configure(state="disabled")
        else:
            self.timer_active = False
            self.start_btn.configure(text="▶ 继续专注", fg_color=("#34C759", "#30D158"), hover_color="#248A3D")

    def terminate_session(self, auto_save=False):
        is_dead = False
        if not auto_save:
            if self.mode == "pomodoro" and self.elapsed_time < self.pomo_target:
                if self.elapsed_time < 60:
                    if not messagebox.askyesno("提示", "专注不足 1 分钟，直接放弃不会枯死。\n\n点【是】强行记入惩罚枯树 🥀，点【否】销毁记录。"):
                        self.abort_current_run()
                        return
                    is_dead = True
                else:
                    if messagebox.askyesno("放弃警告", "警告：番茄钟未完成，放弃将导致树苗枯死(🥀)！\n确定终止吗？"):
                        is_dead = True
                    else:
                        return
            elif self.mode == "stopwatch" and self.elapsed_time < 60:
                if not messagebox.askyesno("提示", "筑城不足 1 分钟，只留下了废料(🚧)。\n\n是否仍要强行保存？"):
                    self.abort_current_run()
                    return

        self.timer_active = False
        note_content = ""
        if not is_dead and self.elapsed_time >= 60:
            dialog = ctk.CTkInputDialog(text=f"📝 送你一句：{self.get_random_quote()}\n\n留下复盘便签（选填）：", title="完成专注")
            note_content = dialog.get() or ""
            note_content = note_content.strip()[:50]

        self.db.add_record(self.db.data["currentSubject"], self.elapsed_time, self.mode, is_dead, note_content)
        self.abort_current_run()

    def abort_current_run(self):
        self.timer_active = False
        self.elapsed_time = 0
        self.start_btn.configure(text="▶ 开始专注", fg_color=("#34C759", "#30D158"), hover_color="#248A3D")
        self.stop_btn.configure(state="disabled")
        self.subject_menu.configure(state="normal")
        self.pomo_menu.configure(state="normal")
        self.mode_selector.configure(state="normal")
        
        self.handle_mode_switch(self.mode_selector.get())
        self.render_forest_view()
        self.render_stats_dashboard()
        self.title("冲刺备考引擎")

    def check_cross_day(self):
        if not self.timer_active:
            self.elapsed_time = 0
        else:
            self.terminate_session(auto_save=True)
            self.timer_active = True
            self.start_tick = time.time()
            self.start_btn.configure(text="⏸ 暂停专注", fg_color=("#FF9500", "#FF9F0A"), hover_color="#E08300")
            self.stop_btn.configure(state="normal")
            self.subject_menu.configure(state="disabled")
            self.pomo_menu.configure(state="disabled")
            self.mode_selector.configure(state="disabled")

    def loop_worker(self):
        current_logical_date = self.get_logical_date_string()
        if current_logical_date != self.last_logical_date:
            self.last_logical_date = current_logical_date
            self.check_cross_day()

        if self.timer_active:
            self.elapsed_time = time.time() - self.start_tick
            
            if self.mode == "pomodoro":
                remain = self.pomo_target - self.elapsed_time
                if remain <= 0:
                    self.elapsed_time = self.pomo_target
                    self.terminate_session(auto_save=True)
                    messagebox.showinfo("达成", "🌲 专注完成，一棵大树已记录！")
                    return
                else:
                    self.time_label.configure(text=format_time(remain))
                    self.title(f"(🌱 {int(remain//60)}m) 考研引擎")
            else:
                self.time_label.configure(text=format_time(self.elapsed_time))
                self.title(f"(🧱 {format_dur(self.elapsed_time)}) 考研引擎")

            self.refresh_live_tree_icon()
            self.refresh_live_goal_bar()

        self.after(200, self.loop_worker)

    def refresh_live_tree_icon(self):
        icon = "🌱"
        if self.mode == "pomodoro":
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
        self.goal_header_label.configure(text=f"🎯 今日进度: {format_dur(total)} / {format_dur(goal)}")
        self.goal_progress_bar.set(percent)

    def refresh_exam_countdown(self):
        try:
            today = datetime.now().date()
            exam = datetime.strptime(self.db.data["examDate"], "%Y-%m-%d").date()
            diff = (exam - today).days
            color = "#FF3B30" if diff < 150 else ("#007AFF", "#0A84FF")
            self.countdown_label.configure(text=f"距离初试仅剩 {diff} 天", text_color=color)
        except:
            pass

    # ================= 6. 图鉴与统计渲染 =================
    def switch_forest_scope(self, selection):
        mapping = {"今日战果": "day", "本周图鉴": "week", "本月图鉴": "month"}
        self.current_forest_range = mapping.get(selection, "day")
        self.render_forest_view()

    def render_forest_view(self):
        for widget in self.forest_grid_frame.winfo_children():
            widget.destroy()

        records = self.db.get_filtered_data(self.current_forest_range)
        self.forest_summary.configure(text=f"当前时段累计收获 {len(records)} 个战果")
        self.forest_widgets = []
        self.current_forest_cols = 0 # 触发强制重新排版

        if not records:
            lbl = ctk.CTkLabel(self.forest_grid_frame, text="空空如也，快去专注吧 ✨", font=("Microsoft YaHei UI", 14), text_color="#8E8E93")
            lbl.grid(row=0, column=0, pady=50)
            self.forest_widgets.append(lbl)
            return

        for r in records:
            lbl = ctk.CTkLabel(self.forest_grid_frame, text=r.get("tree", "🌲"), font=("Segoe UI Emoji", 42), cursor="hand2")
            note_text = f" [{r['note']}]" if r.get("note") else ""
            info_string = f"{r['subject']} | {format_dur(r['duration'])}{note_text}"
            self.bind_hover_tip(lbl, info_string)
            self.forest_widgets.append(lbl)
            
        self.on_forest_resize() # 初始化布局

    def bind_hover_tip(self, widget, text):
        def on_enter(e):
            self.forest_summary.configure(text=text, text_color=("#007AFF", "#0A84FF"))
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
            self.stats_delta_label.configure(text="无历史数据", text_color="#8E8E93")
        elif delta >= 0:
            self.stats_delta_label.configure(text=f"↑ 多 {format_dur(delta)}", text_color=("#34C759", "#30D158"))
        else:
            self.stats_delta_label.configure(text=f"↓ 少 {format_dur(abs(delta))}", text_color=("#FF3B30", "#FF453A"))

        if not curr_records:
            ctk.CTkLabel(self.chart_scroll, text="当前时段无专注数据", font=("Microsoft YaHei UI", 14), text_color="#8E8E93").pack(pady=50)
            return

        subject_map = {}
        for r in curr_records:
            subject_map[r["subject"]] = subject_map.get(r["subject"], 0) + r["duration"]

        for sub, dur in sorted(subject_map.items(), key=lambda x: x[1], reverse=True):
            pct = dur / curr_total if curr_total > 0 else 0
            
            bar_frame = ctk.CTkFrame(self.chart_scroll, fg_color="transparent")
            bar_frame.pack(fill="x", pady=8, padx=10)

            lbl_title = ctk.CTkLabel(bar_frame, text=f"{sub} ({round(pct*100, 1)}%)", font=("Microsoft YaHei UI", 14, "bold"))
            lbl_title.pack(side="left")
            
            lbl_time = ctk.CTkLabel(bar_frame, text=format_dur(dur), font=("Microsoft YaHei UI", 13), text_color="#8E8E93")
            lbl_time.pack(side="right")

            p_bar = ctk.CTkProgressBar(self.chart_scroll, height=10, corner_radius=5, progress_color=("#007AFF", "#0A84FF"))
            p_bar.pack(fill="x", pady=(0, 15), padx=10)
            p_bar.set(pct)

    # ================= 7. 高级设置 =================
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
            sub_row = self.create_card(self.subject_listbox_frame, fg_color=("#F2F2F7", "#2C2C2E"), corner_radius=10)
            sub_row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(sub_row, text=sub, font=("Microsoft YaHei UI", 14, "bold")).pack(side="left", padx=15, pady=10)
            btn_del = ctk.CTkButton(sub_row, text="删除", width=55, height=28, corner_radius=8, fg_color=("#FF3B30", "#FF453A"), hover_color="#C92A20", font=("Microsoft YaHei UI", 12, "bold"), command=lambda s=sub: self.remove_custom_subject(s))
            btn_del.pack(side="right", padx=15)

        add_row = ctk.CTkFrame(self.subject_listbox_frame, fg_color="transparent")
        add_row.pack(fill="x", pady=(15, 0))
        self.new_sub_entry = ctk.CTkEntry(add_row, placeholder_text="输入新科目...", font=("Microsoft YaHei UI", 14), height=38, corner_radius=10)
        self.new_sub_entry.pack(side="left", expand=True, fill="x", padx=(0, 15))
        ctk.CTkButton(add_row, text="＋", width=45, height=38, corner_radius=10, font=("Microsoft YaHei UI", 18, "bold"), command=self.append_custom_subject).pack(side="right")

    def append_custom_subject(self):
        name = self.new_sub_entry.get().strip()
        if not name: return
        name = name[:10]
        if name in self.db.data["subjects"]:
            messagebox.showwarning("冲突", "该科目已存在！")
            return
        self.db.data["subjects"].append(name)
        self.db.save_data()
        self.refresh_settings_subject_view()
        self.subject_menu.configure(values=self.db.data["subjects"])
        self.new_sub_entry.delete(0, 'end')

    def remove_custom_subject(self, name):
        if self.timer_active:
            messagebox.showwarning("锁定", "专注中禁止删改科目！")
            return
        if len(self.db.data["subjects"]) <= 1:
            messagebox.showwarning("限制", "至少需保留一个科目！")
            return
        if messagebox.askyesno("确认", f"确定删除【{name}】吗？"):
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
            messagebox.showinfo("成功", "数据导出成功！")

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
                    messagebox.showinfo("复原", "历史数据导入成功！")
            except Exception:
                messagebox.showerror("失败", "文件解析失败！")

if __name__ == "__main__":
    app = StudyEngineApp()
    app.render_forest_view()
    app.render_stats_dashboard()
    app.mainloop()
