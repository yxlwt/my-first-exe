import flet as ft
import json
import os
import sys
import time
import threading
import random
from datetime import datetime, timedelta

# ================= 1. 环境与配置初始化 =================
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

# ================= 4. Flet 引擎主逻辑 =================
def main(page: ft.Page):
    # --- 窗口与主题设置 ---
    page.title = "冲刺备考引擎"
    page.window.width = 460
    page.window.height = 800
    page.window.min_width = 350
    page.window.min_height = 500
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.ADAPTIVE 

    db = DataManager()
    encouragements = [
        "星光不问赶路人，时光不负有心人。",
        "你做三四月的事，在十二月自有答案。",
        "当前的每一次咬牙坚持，都是为了初试的毫不费力。",
        "顶峰相见吧，在十二月最冷的冬日里拼出最热血的成绩。"
    ]

    # 状态管理
    class State:
        timer_active = False
        mode = "pomodoro"
        pomo_target = 25 * 60
        elapsed_time = 0
        start_tick = 0
        last_logical_date = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        forest_range = "day"
        stats_range = "day"

    st = State()

    # ================= UI 组件 =================
    def get_exam_text():
        try:
            today = datetime.now().date()
            exam = datetime.strptime(db.data["examDate"], "%Y-%m-%d").date()
            diff = (exam - today).days
            color = ft.Colors.RED if diff < 150 else ft.Colors.BLUE
            return f"距离初试仅剩 {diff} 天", color
        except:
            return "距离初试仅剩 -- 天", ft.Colors.BLUE

    exam_text, exam_color = get_exam_text()
    countdown_text = ft.Text(exam_text, size=18, weight=ft.FontWeight.BOLD, color=exam_color)
    
    # 💡 核心修复：彻底抛弃 ft.alignment，采用最安全的 ft.Row 居中排版，免疫所有版本报错
    countdown_container = ft.Container(
        content=ft.Row([countdown_text], alignment=ft.MainAxisAlignment.CENTER),
        padding=20,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        border_radius=15,
        margin=15
    )

    # --- 专注 Tab ---
    subject_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(s) for s in db.data["subjects"]],
        value=db.data["currentSubject"],
        width=150,
        border_radius=10,
        dense=True
    )
    
    icon_text = ft.Text("🌰", size=90)
    time_text = ft.Text("25:00", size=75, weight=ft.FontWeight.BOLD, font_family="Consolas")
    quote_text = ft.Text(random.choice(encouragements), size=13, color=ft.Colors.ON_SURFACE_VARIANT)
    
    goal_label = ft.Text("🎯 今日进度: 0m / 6h", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT)
    goal_bar = ft.ProgressBar(value=0, color=ft.Colors.GREEN, bgcolor=ft.Colors.ON_INVERSE_SURFACE, height=8, border_radius=4)
    
    mode_tabs = ft.Tabs(
        selected_index=1,
        animation_duration=300,
        tabs=[ft.Tab(text="🧱 正向筑城"), ft.Tab(text="🌱 番茄种树")]
    )
    
    pomo_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(f"{m}分钟") for m in [15, 25, 35, 45, 60, 90]],
        value="25分钟", width=120, border_radius=10, dense=True
    )

    btn_start = ft.ElevatedButton("▶ 开始专注", width=160, height=45, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=22), bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE))
    btn_stop = ft.ElevatedButton("⏹ 结束", width=160, height=45, disabled=True, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=22)))

    focus_col = ft.Column(
        controls=[
            ft.Row([subject_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            icon_text, time_text, quote_text,
            ft.Container(height=10),
            ft.Column([goal_label, goal_bar], spacing=5),
            ft.Container(height=10),
            mode_tabs,
            ft.Row([pomo_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.Row([btn_start, btn_stop], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        scroll=ft.ScrollMode.ADAPTIVE
    )

    # --- 图鉴 Tab ---
    forest_tabs = ft.Tabs(selected_index=0, tabs=[ft.Tab(text="今日战果"), ft.Tab(text="本周图鉴"), ft.Tab(text="本月图鉴")])
    forest_summary = ft.Text("累计收获 0 个战果", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT)
    
    forest_grid = ft.Row(wrap=True, spacing=15, run_spacing=15, alignment=ft.MainAxisAlignment.START)
    
    # 💡 核心修复：再次使用 ft.Row 替代 ft.alignment，切断报错源头
    forest_col = ft.Column([
        forest_tabs, 
        ft.Container(content=ft.Row([forest_summary], alignment=ft.MainAxisAlignment.CENTER), padding=5),
        ft.Container(content=forest_grid, padding=15, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=15, expand=True)
    ], expand=True)

    # --- 统计 Tab ---
    stats_tabs = ft.Tabs(selected_index=0, tabs=[ft.Tab(text="今日"), ft.Tab(text="本周"), ft.Tab(text="本月")])
    stats_total = ft.Text("0s", size=36, weight=ft.FontWeight.BOLD)
    stats_delta = ft.Text("无对比数据", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT)
    
    stats_chart_col = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE)
    
    stats_col = ft.Column([
        stats_tabs,
        ft.Container(
            content=ft.Row([stats_total, stats_delta], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=15
        ),
        ft.Container(content=stats_chart_col, padding=15, expand=True)
    ], expand=True)

    # --- 设置 Tab ---
    goal_input = ft.TextField(value=str(db.data["dailyGoal"] // 3600), label="每日专注目标 (小时)", width=150)
    sub_list_col = ft.Column(spacing=5)
    new_sub_input = ft.TextField(hint_text="新科目名称", expand=True)
    
    def on_export(e):
        try:
            with open("StudyEngine_Backup.json", "w", encoding="utf-8") as f:
                json.dump(db.data, f, ensure_ascii=False, indent=4)
            page.snack_bar = ft.SnackBar(ft.Text("数据已导出为 StudyEngine_Backup.json！"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            pass

    settings_col = ft.Column([
        ft.Text("🎯 核心配置", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([goal_input]),
        ft.Divider(),
        ft.Text("🏷️ 科目管理", size=16, weight=ft.FontWeight.BOLD),
        sub_list_col,
        ft.Row([new_sub_input, ft.ElevatedButton("＋ 新增", on_click=lambda e: add_subject())]),
        ft.Divider(),
        ft.Text("💾 数据容灾", size=16, weight=ft.FontWeight.BOLD),
        # 💡 核心修复：用安全字符串替代图标对象枚举，绝不报错
        ft.ElevatedButton("⬇ 导出本地记录备份 (当前目录)", icon="download", on_click=on_export)
    ], scroll=ft.ScrollMode.ADAPTIVE)

    # --- 主导航框架 ---
    main_tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="专注", content=ft.Container(content=focus_col, padding=15)),
            ft.Tab(text="图鉴", content=ft.Container(content=forest_col, padding=15)),
            ft.Tab(text="统计", content=ft.Container(content=stats_col, padding=15)),
            ft.Tab(text="设置", content=ft.Container(content=settings_col, padding=15))
        ]
    )

    page.add(countdown_container, main_tabs)

    # ================= 交互逻辑 =================
    def update_visuals():
        if st.mode == "pomodoro":
            remain = st.pomo_target - st.elapsed_time
            if remain <= 0:
                time_text.value = "00:00"
                icon_text.value = "🌲"
            else:
                time_text.value = format_time(remain)
                prog = st.elapsed_time / st.pomo_target
                icon_text.value = "🌳" if prog >= 0.66 else "🌿" if prog >= 0.33 else "🌱" if st.elapsed_time >= 60 else "🌰"
                
                page.title = f"(🌱 {int(remain//60)}m) 冲刺备考引擎"
        else:
            time_text.value = format_time(st.elapsed_time)
            if st.elapsed_time >= 3600: icon_text.value = "🏰"
            elif st.elapsed_time >= 2700: icon_text.value = "🏛️"
            elif st.elapsed_time >= 1800: icon_text.value = "🏠"
            elif st.elapsed_time >= 900: icon_text.value = "⛺"
            elif st.elapsed_time >= 60: icon_text.value = "🧱"
            else: icon_text.value = "🚧"
            page.title = f"(🧱 {format_dur(st.elapsed_time)}) 冲刺备考引擎"
            
        if not st.timer_active:
            page.title = "冲刺备考引擎"

        logical_today = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        records = [item for item in db.data["studyData"] if item.get("date") == logical_today]
        total = sum(r["duration"] for r in records) + (st.elapsed_time if st.timer_active else 0)
        goal = db.data["dailyGoal"]
        
        goal_label.value = f"🎯 今日进度: {format_dur(total)} / {format_dur(goal)}"
        goal_bar.value = min(total / goal, 1.0)
        page.update()

    def handle_start_stop(e):
        if not st.timer_active:
            st.timer_active = True
            st.start_tick = time.time() - st.elapsed_time
            btn_start.text = "⏸ 暂停专注"
            btn_start.style.bgcolor = ft.Colors.ORANGE
            btn_stop.disabled = False
            btn_stop.style.bgcolor = ft.Colors.RED
            btn_stop.style.color = ft.Colors.WHITE
            subject_dropdown.disabled = True
            pomo_dropdown.disabled = True
        else:
            st.timer_active = False
            btn_start.text = "▶ 继续专注"
            btn_start.style.bgcolor = ft.Colors.GREEN
        page.update()

    def process_termination(auto_save=False):
        is_dead = False
        if not auto_save:
            if st.mode == "pomodoro" and st.elapsed_time < st.pomo_target:
                def confirm_pomo(e, yes):
                    dlg.open = False
                    page.update()
                    if yes: 
                        ask_for_note(is_dead=True)
                    else:
                        abort_run()

                dlg = ft.AlertDialog(
                    title=ft.Text("放弃警告"),
                    content=ft.Text("番茄钟未完成，放弃将留下枯树 🥀，确定吗？" if st.elapsed_time >= 60 else "不足 1 分钟，直接放弃不会枯死。\n强行保存将记入枯树 🥀。"),
                    actions=[
                        ft.TextButton("是 (保存枯树)", on_click=lambda e: confirm_pomo(e, True)),
                        ft.TextButton("否 (销毁记录)", on_click=lambda e: confirm_pomo(e, False)),
                    ]
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()
                return

            elif st.mode == "stopwatch" and st.elapsed_time < 60:
                def confirm_sw(e, yes):
                    dlg.open = False
                    page.update()
                    if yes: ask_for_note(is_dead=False)
                    else: abort_run()

                dlg = ft.AlertDialog(
                    title=ft.Text("时间极短"),
                    content=ft.Text("筑城不足 1 分钟，只留下了废料 🚧。\n是否仍要保存？"),
                    actions=[
                        ft.TextButton("是", on_click=lambda e: confirm_sw(e, True)),
                        ft.TextButton("否", on_click=lambda e: confirm_sw(e, False)),
                    ]
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()
                return

        ask_for_note(is_dead=False)

    def ask_for_note(is_dead):
        if is_dead or st.elapsed_time < 60:
            save_and_reset(is_dead, "")
            return
            
        note_field = ft.TextField(label="复盘便签 (选填)", width=300)
        
        def finish_save(e):
            dlg.open = False
            page.update()
            save_and_reset(is_dead, note_field.value)

        dlg = ft.AlertDialog(
            title=ft.Text("专注完成！"),
            content=ft.Column([ft.Text(f"💡 {random.choice(encouragements)}"), note_field], tight=True),
            actions=[ft.ElevatedButton("保存战果", on_click=finish_save)]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def save_and_reset(is_dead, note):
        db.add_record(subject_dropdown.value, st.elapsed_time, st.mode, is_dead, note[:50])
        abort_run()
        refresh_forest()
        refresh_stats()

    def abort_run():
        st.timer_active = False
        st.elapsed_time = 0
        btn_start.text = "▶ 开始专注"
        btn_start.style.bgcolor = ft.Colors.GREEN
        btn_stop.disabled = True
        btn_stop.style.bgcolor = None
        btn_stop.style.color = None
        subject_dropdown.disabled = False
        pomo_dropdown.disabled = False
        
        update_visuals()

    btn_start.on_click = handle_start_stop
    btn_stop.on_click = lambda e: process_termination(False)

    def on_mode_change(e):
        if st.timer_active:
            mode_tabs.selected_index = 1 if st.mode == "pomodoro" else 0
            page.update()
            return
        st.mode = "pomodoro" if mode_tabs.selected_index == 1 else "stopwatch"
        pomo_dropdown.disabled = (st.mode == "stopwatch")
        st.elapsed_time = 0
        update_visuals()
        
    mode_tabs.on_change = on_mode_change

    def on_pomo_change(e):
        if st.timer_active:
            pomo_dropdown.value = f"{st.pomo_target//60}分钟"
            page.update()
            return
        st.pomo_target = int(pomo_dropdown.value.replace("分钟", "")) * 60
        st.elapsed_time = 0
        update_visuals()

    pomo_dropdown.on_change = on_pomo_change

    # --- 渲染逻辑 ---
    def refresh_forest(e=None):
        idx = forest_tabs.selected_index
        st.forest_range = "day" if idx == 0 else "week" if idx == 1 else "month"
        records = db.get_filtered_data(st.forest_range)
        forest_summary.value = f"当前时段累计收获 {len(records)} 个战果"
        
        forest_grid.controls.clear()
        if not records:
            forest_grid.controls.append(ft.Text("空空如也，快去专注吧 ✨", color=ft.Colors.ON_SURFACE_VARIANT))
        else:
            for r in records:
                note_str = f" [{r['note']}]" if r.get('note') else ""
                tip = f"{r['subject']} | {format_dur(r['duration'])}{note_str}"
                forest_grid.controls.append(ft.Text(r.get("tree", "🌲"), size=42, tooltip=tip))
        page.update()

    forest_tabs.on_change = refresh_forest

    def refresh_stats(e=None):
        idx = stats_tabs.selected_index
        st.stats_range = "day" if idx == 0 else "week" if idx == 1 else "month"
        records = db.get_filtered_data(st.stats_range)
        curr_total = sum(r["duration"] for r in records)
        stats_total.value = format_dur(curr_total)
        
        stats_chart_col.controls.clear()
        if not records:
            stats_chart_col.controls.append(ft.Text("当前时段无专注数据", color=ft.Colors.ON_SURFACE_VARIANT))
        else:
            subject_map = {}
            for r in records:
                subject_map[r["subject"]] = subject_map.get(r["subject"], 0) + r["duration"]
                
            for sub, dur in sorted(subject_map.items(), key=lambda x: x[1], reverse=True):
                pct = dur / curr_total if curr_total > 0 else 0
                stats_chart_col.controls.append(
                    ft.Column([
                        ft.Row([ft.Text(f"{sub} ({round(pct*100,1)}%)", weight="bold"), ft.Text(format_dur(dur), color=ft.Colors.ON_SURFACE_VARIANT)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.ProgressBar(value=pct, height=8, border_radius=4)
                    ], spacing=5)
                )
        page.update()

    stats_tabs.on_change = refresh_stats

    def update_goal(e):
        try:
            db.data["dailyGoal"] = float(goal_input.value) * 3600
            db.save_data()
            update_visuals()
        except:
            goal_input.value = str(db.data["dailyGoal"] // 3600)
            page.update()
    goal_input.on_blur = update_goal

    def render_settings_subjects():
        sub_list_col.controls.clear()
        for sub in db.data["subjects"]:
            def make_del_func(s):
                return lambda e: del_sub(s)
                
            row = ft.Row([
                ft.Text(f"• {sub}", size=14, weight="bold", expand=True),
                # 💡 核心修复：用安全字符串替代图标对象枚举，绝不报错
                ft.TextButton("删除", icon="delete", icon_color=ft.Colors.RED, on_click=make_del_func(sub))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            sub_list_col.controls.append(row)
        page.update()

    def add_subject():
        name = new_sub_input.value.strip()[:10]
        if name and name not in db.data["subjects"]:
            db.data["subjects"].append(name)
            db.save_data()
            subject_dropdown.options = [ft.dropdown.Option(s) for s in db.data["subjects"]]
            new_sub_input.value = ""
            render_settings_subjects()

    def del_sub(name):
        if len(db.data["subjects"]) <= 1: return
        db.data["subjects"].remove(name)
        if db.data["currentSubject"] == name:
            db.data["currentSubject"] = db.data["subjects"][0]
            subject_dropdown.value = db.data["currentSubject"]
        db.save_data()
        subject_dropdown.options = [ft.dropdown.Option(s) for s in db.data["subjects"]]
        render_settings_subjects()

    render_settings_subjects()

    def timer_loop():
        while True:
            logical_now = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
            if logical_now != st.last_logical_date:
                st.last_logical_date = logical_now
                if st.timer_active:
                    process
