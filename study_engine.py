import flet as ft
import asyncio  
import json
import os
import sys
import time
import random
import traceback
from datetime import datetime, timedelta

# ================= 1. 初始化与数据管理 =================
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(application_path, "study_data.json")

ENCOURAGEMENTS = [
    "星光不问赶路人，时光不负有心人。",
    "你做三四月的事，在十二月自有答案。",
    "乾坤未定，你我皆是黑马。",
    "当前的每一次咬牙坚持，都是为了初试的毫不费力。",
    "那些看似不起波澜的日复一日，会突然在某天让人看到坚持的意义。",
    "顶峰相见吧，在十二月最冷的冬日里拼出最热血的成绩。"
]

class DataManager:
    def __init__(self, path):
        self.path = path
        self.data = {
            "dailyGoal": 6 * 3600,
            "currentSubject": "专业课",
            "subjects": ["专业课", "数学", "英语", "政治"],
            "studyData": [],
            "examDate": "2026-12-20"
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception:
                pass

    def save(self):
        tmp_path = self.path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            if os.path.exists(tmp_path):
                if os.path.exists(self.path):
                    os.remove(self.path)
                os.rename(tmp_path, self.path)
        except Exception:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
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
            else: icon = "🧱"

        self.data["studyData"].append({
            "date": logical_today,
            "subject": subject,
            "duration": duration,
            "tree": icon,
            "note": note
        })
        self.save()

    def get_filtered(self, range_str):
        logical_now = datetime.now() - timedelta(hours=2)
        today_str = logical_now.strftime("%Y-%m-%d")
        if range_str == "day":
            return [i for i in self.data["studyData"] if i.get("date") == today_str]
        elif range_str == "week":
            start = logical_now - timedelta(days=logical_now.weekday())
            week_dates = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            return [i for i in self.data["studyData"] if i.get("date") in week_dates]
        elif range_str == "month":
            prefix = logical_now.strftime("%Y-%m-")
            return [i for i in self.data["studyData"] if str(i.get("date")).startswith(prefix)]
        elif range_str.startswith("custom:"):
            target_date = range_str.split(":")[1]
            return [i for i in self.data["studyData"] if i.get("date") == target_date]
        return []

# ================= 2. 辅助函数与高能算法 =================
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
    return f"{s//60:02d}:{s%60:02d}"

def play_success_sound():
    if sys.platform == "win32":
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

def get_period_comparison(scope, data):
    logical_now = datetime.now() - timedelta(hours=2)
    today_str = logical_now.strftime("%Y-%m-%d")
    
    cur_dur = 0
    prev_dur = 0
    period_name = ""
    prev_name = ""

    if scope == "day":
        period_name = "今日"
        prev_name = "昨日"
        prev_date = (logical_now - timedelta(days=1)).strftime("%Y-%m-%d")
        cur_dur = sum(r["duration"] for r in data if r.get("date") == today_str)
        prev_dur = sum(r["duration"] for r in data if r.get("date") == prev_date)
    elif scope == "week":
        period_name = "本周"
        prev_name = "上周"
        start_this = logical_now - timedelta(days=logical_now.weekday())
        start_prev = start_this - timedelta(days=7)
        this_dates = [(start_this + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        prev_dates = [(start_prev + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        cur_dur = sum(r["duration"] for r in data if r.get("date") in this_dates)
        prev_dur = sum(r["duration"] for r in data if r.get("date") in prev_dates)
    elif scope == "month":
        period_name = "本月"
        prev_name = "上月"
        this_prefix = logical_now.strftime("%Y-%m-")
        first_day_this_month = logical_now.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        prev_prefix = last_day_prev_month.strftime("%Y-%m-")
        cur_dur = sum(r["duration"] for r in data if str(r.get("date")).startswith(this_prefix))
        prev_dur = sum(r["duration"] for r in data if str(r.get("date")).startswith(prev_prefix))
    elif scope.startswith("custom:"):
        target_date = scope.split(":")[1]
        if target_date == "none":
            return ""
        period_name = f"{target_date[-5:]}"
        prev_name = "前一天"
        td = datetime.strptime(target_date, "%Y-%m-%d")
        prev_date = (td - timedelta(days=1)).strftime("%Y-%m-%d")
        cur_dur = sum(r["duration"] for r in data if r.get("date") == target_date)
        prev_dur = sum(r["duration"] for r in data if r.get("date") == prev_date)
    else:
        return ""

    diff = cur_dur - prev_dur
    if diff > 0:
        return f"🔥 {period_name}比{prev_name}多学了 {format_dur(diff)}！继续保持！"
    elif diff < 0:
        return f"⚠️ {period_name}比{prev_name}少学了 {format_dur(abs(diff))}。注意调整状态哦！"
    else:
        if cur_dur == 0:
            return f"💤 {period_name}和{prev_name}都还没学习，快去筑城吧！"
        else:
            return f"⚖️ {period_name}与{prev_name}时长完全持平，节奏稳健！"

def create_btn(text, on_click=None, bgcolor="transparent", txt_color=None, radius=8, expand=False, width=None, height=None, padding=8):
    lbl = ft.Text(value=text, color=txt_color, weight="bold", max_lines=1)
    cnt = ft.Container(
        content=ft.Row([lbl], alignment="center", vertical_alignment="center"),
        bgcolor=bgcolor,
        border_radius=radius,
        padding=padding,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height
    )
    return cnt, lbl

# ================= 3. 核心 UI 引擎 =================
async def main(page: ft.Page):
    db = DataManager(DATA_FILE)
    page.title = "冲刺备考引擎"
    page.theme_mode = "light" 
    page.padding = 10
    page.scroll = None 
    
    try:
        page.window.resizable = False
        page.window.width = 380
        page.window.height = 600
    except AttributeError:
        try:
            page.window_resizable = False
            page.window_width = 380
            page.window_height = 600
        except: pass

    def open_dlg(d):
        if hasattr(page, "open"): page.open(d)
        else:
            page.dialog = d
            d.open = True
            page.update()

    def close_dlg(d):
        if hasattr(page, "close"): page.close(d)
        else:
            d.open = False
            page.update()

    def show_warning(msg):
        snack = ft.SnackBar(content=ft.Text(msg, color="white", weight="bold"), bgcolor="#FF3B30")
        if hasattr(page, "open"): page.open(snack)
        else:
            page.snack_bar = snack
            snack.open = True
            page.update()

    class State:
        session_active = False  
        timer_active = False 
        was_active = False 
        mode = "pomodoro"
        pomo_target = 60 * 60
        elapsed = 0
        start_tick = 0
        forest_scope = "day"
        stats_scope = "day"
        last_date = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        last_pomo_val = "60" 
        
        active_tab = 0
        forest_tab = 0
        stat_tab = 0
        chart_tab = 0 
        
        is_pinned = False
        is_mini_mode = False 
        goal_reached = False 
        goal_reached_this_session = False
        
        last_ui_second = -1

    st = State()

    # ========================================================
    # 🚀 主题色调度中心
    # ========================================================
    def apply_theme_colors():
        is_dark = page.theme_mode == "dark"
        
        bg = "#000000" if is_dark else "#F2F2F7"
        surface = "#1C1C1E" if is_dark else "#FFFFFF"
        surface_variant = "#2C2C2E" if is_dark else "#E5E5EA"
        text_main = "#FFFFFF" if is_dark else "#1C1C1E"
        text_sec = "#8E8E93"

        page.bgcolor = bg
        btn_theme_lbl.value = "☀️" if is_dark else "🌙"
        btn_theme_lbl.color = text_sec
        btn_pin_full_lbl.value = "📍" if st.is_pinned else "📌"
        btn_pin_full_lbl.color = "#FF9500" if st.is_pinned else text_sec
        btn_pin_mini_lbl.value = "📍" if st.is_pinned else "📌"
        btn_pin_mini_lbl.color = "#FF9500" if st.is_pinned else text_sec
        
        btn_mini_shrink_lbl.color = text_sec
        btn_mini_expand_lbl.color = text_sec
        
        card_countdown_full.bgcolor = surface
        nav_bar.bgcolor = surface_variant
        
        lbl_time.color = text_main
        lbl_time_mini.color = text_main
        lbl_quote.color = text_sec
        
        sel_subject.bgcolor = "transparent"
        sel_subject.border_color = "#38383A" if is_dark else "#C7C7CC"
        sel_subject.color = text_main
        
        bar_goal.bgcolor = surface_variant
        lbl_goal.color = text_sec
        
        mode_container.bgcolor = surface_variant
        mode_sw_view.bgcolor = surface if st.mode == "stopwatch" else "transparent"
        mode_sw_lbl.color = text_main if st.mode == "stopwatch" else text_sec
        mode_pm_view.bgcolor = surface if st.mode == "pomodoro" else "transparent"
        mode_pm_lbl.color = text_main if st.mode == "pomodoro" else text_main
        sel_pomo.color = text_main
        
        if st.session_active:
            btn_stop_view.bgcolor = "#FF3B30"
            btn_stop_lbl.color = "#FFFFFF"
            if st.timer_active:
                btn_start_view.bgcolor = "#FF9500"
            else:
                btn_start_view.bgcolor = "#34C759"
        else:
            btn_start_view.bgcolor = "#34C759"
            btn_stop_view.bgcolor = surface_variant
            btn_stop_lbl.color = text_sec
        
        lbl_title_confirm.color = text_main
        lbl_confirm_msg.color = text_sec
        btn_n.bgcolor = surface_variant
        btn_n_lbl.color = text_sec
        
        lbl_title_success.color = text_main
        lbl_success_quote.color = text_sec if not st.goal_reached_this_session else "#FF9500"
        txt_note.border_color = text_sec
        txt_note.color = text_main
        
        view_focus.bgcolor = surface
        lbl_forest_sum.color = text_sec
        lbl_forest_compare.color = "#FF9500" if is_dark else "#007AFF"
        row_forest_nav.bgcolor = surface_variant
        view_forest.bgcolor = surface
        container_forest_grid.bgcolor = "transparent"
        
        lbl_stat_total.color = text_main
        lbl_stat_compare.color = "#FF9500" if is_dark else "#007AFF"
        row_stat_nav.bgcolor = surface_variant
        view_stats.bgcolor = surface
        
        lbl_setting_1.color = text_main
        lbl_setting_2.color = text_main
        lbl_setting_3.color = text_main
        txt_goal.border_color = text_sec
        txt_goal.color = text_main
        txt_exam_date.border_color = text_sec
        txt_exam_date.color = text_main
        txt_new_sub.border_color = text_sec
        txt_new_sub.color = text_main
        btn_exp.bgcolor = surface_variant
        btn_exp_lbl.color = text_main
        btn_imp.bgcolor = surface_variant
        btn_imp_lbl.color = text_main
        view_settings.bgcolor = surface
        
        lbl_forest_history.color = text_sec
        forest_history_dropdown.bgcolor = "transparent"
        forest_history_dropdown.border_color = "#38383A" if is_dark else "#C7C7CC"
        forest_history_dropdown.color = text_main
        
        lbl_stat_history.color = text_sec
        history_dropdown.bgcolor = "transparent"
        history_dropdown.border_color = "#38383A" if is_dark else "#C7C7CC"
        history_dropdown.color = text_main
        
        for i, item in enumerate(nav_buttons):
            item["view"].bgcolor = surface if i == st.active_tab else "transparent"
            item["lbl"].color = text_main if i == st.active_tab else text_sec
            
        for i, item in enumerate(forest_nav_btns):
            item["view"].bgcolor = surface if i == st.forest_tab else "transparent"
            item["lbl"].color = text_main if i == st.forest_tab else text_sec
            
        for i, item in enumerate(stat_nav_btns):
            item["view"].bgcolor = surface if i == st.stat_tab else "transparent"
            item["lbl"].color = text_main if i == st.stat_tab else text_sec

        for i, item in enumerate(chart_nav_btns):
            item["view"].bgcolor = surface_variant if i == st.chart_tab else "transparent"
            item["lbl"].color = text_main if i == st.chart_tab else text_sec
            
        for c in col_subs.controls:
            c.bgcolor = bg
            c.content.controls[0].color = text_main

    # ----------------- 🎯 内嵌顶栏 -----------------
    def update_countdown():
        try:
            today = datetime.now().date()
            exam = datetime.strptime(db.data.get("examDate", "2026-12-20"), "%Y-%m-%d").date()
            diff = (exam - today).days
            countdown_text.value = f"距离初试仅剩 {diff} 天"
            countdown_text.color = "#FF3B30" if diff < 150 else "#007AFF"
        except:
            countdown_text.value = "距离初试仅剩 -- 天"

    def toggle_theme(e):
        page.theme_mode = "dark" if page.theme_mode == "light" else "light"
        apply_theme_colors()
        refresh_forest()
        refresh_stats()
        try: page.update()
        except: pass

    def toggle_pin(e):
        st.is_pinned = not st.is_pinned
        try: page.window.always_on_top = st.is_pinned
        except AttributeError:
            try: page.window_always_on_top = st.is_pinned
            except: pass
        apply_theme_colors()
        try: page.update()
        except: pass

    def toggle_mini_mode(e):
        st.is_mini_mode = not st.is_mini_mode
        apply_theme_and_layout()

    btn_pin_full, btn_pin_full_lbl = create_btn("📌", padding=6, width=35, on_click=toggle_pin)
    btn_mini_shrink, btn_mini_shrink_lbl = create_btn("🔽", padding=6, width=35, on_click=toggle_mini_mode)
    btn_theme, btn_theme_lbl = create_btn("🌙", padding=6, width=35, on_click=toggle_theme)

    row_left_controls_full = ft.Row([btn_pin_full, btn_mini_shrink], spacing=5, vertical_alignment="center")
    countdown_text = ft.Text(value="距离初试仅剩 -- 天", size=15, weight="bold", color="#007AFF", max_lines=1)

    card_countdown_full = ft.Container(
        content=ft.Row([row_left_controls_full, countdown_text, btn_theme], alignment="spaceBetween", vertical_alignment="center"),
        border_radius=12, padding=8, margin=5 
    )

    btn_mini_expand, btn_mini_expand_lbl = create_btn("🔼", padding=6, width=35, on_click=toggle_mini_mode)
    lbl_time_mini = ft.Text(value="60:00", size=24, weight="bold", max_lines=1)
    btn_pin_mini, btn_pin_mini_lbl = create_btn("📌", padding=6, width=35, on_click=toggle_pin)
    
    mini_top_bar = ft.Container(
        content=ft.Row([btn_mini_expand, lbl_time_mini, btn_pin_mini], alignment="spaceBetween", vertical_alignment="center"),
        padding=5, margin=0, visible=False
    )

    # ----------------- 导航栏 -----------------
    nav_buttons = []
    def switch_main_tab(index):
        if st.is_mini_mode and index != 0:
            show_warning("🚨 迷你模式下仅支持显示【专注】面板！")
            return
            
        st.active_tab = index
        is_dark = page.theme_mode == "dark"
        surface = "#1C1C1E" if is_dark else "#FFFFFF"
        text_main = "#FFFFFF" if is_dark else "#1C1C1E"
        text_sec = "#8E8E93"
        for i, item in enumerate(nav_buttons):
            item["view"].bgcolor = surface if i == index else "transparent"
            item["lbl"].color = text_main if i == index else text_sec
            
        view_focus.visible = (index == 0)
        view_forest.visible = (index == 1)
        view_stats.visible = (index == 2)
        view_settings.visible = (index == 3)
        
        if index == 1: refresh_forest()
        if index == 2: refresh_stats()

    def make_nav_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: (switch_main_tab(i), page.update()), radius=8, expand=True, padding=6)
        nav_buttons.append({"view": view, "lbl": lbl})
        return view

    nav_bar = ft.Container(
        content=ft.Row([make_nav_btn("专注", 0), make_nav_btn("图鉴", 1), make_nav_btn("统计", 2), make_nav_btn("设置", 3)], alignment="center", spacing=0, vertical_alignment="center"),
        border_radius=10, padding=4, margin=5
    )

    # ========================================================
    # 🚀 专注功能面板与组件美化
    # ========================================================
    lbl_icon = ft.Text(value="🌰", size=65, text_align="center", max_lines=1) 
    lbl_time = ft.Text(value="60:00", size=50, weight="bold", text_align="center", max_lines=1) 
    lbl_quote = ft.Text(value=random.choice(ENCOURAGEMENTS), size=11, text_align="center", max_lines=1)
    
    sel_subject = ft.Dropdown(
        options=[ft.dropdown.Option(key=s) for s in db.data["subjects"]],
        value=db.data["currentSubject"], 
        width=180, dense=True, border_radius=12, 
        text_align="center",  
        text_size=15, content_padding=8
    )
    def on_sub_change(e):
        db.data["currentSubject"] = sel_subject.value
        db.save()
    sel_subject.on_change = on_sub_change

    bar_goal = ft.ProgressBar(value=0, color="#34C759", height=6)
    lbl_goal = ft.Text(value="今日进度: 0m / 6h", size=11, weight="bold", max_lines=1)

    def switch_mode(m):
        if st.session_active:
            show_warning("🚨 当前专注尚未结算，无法切换模式！")
            return
        st.mode = m
        sel_pomo.disabled = (m == "stopwatch")
        if m == "pomodoro":
            try: st.pomo_target = int(sel_pomo.value) * 60
            except: st.pomo_target = 60 * 60
        st.elapsed = 0
        
        lbl_icon.value = "🌰" if m == "pomodoro" else "🚧"
        
        time_str = format_time(st.pomo_target) if m == "pomodoro" else "00:00"
        lbl_time.value = time_str
        lbl_time_mini.value = time_str
        
        apply_theme_colors() 
        try: page.update()
        except: pass

    mode_sw_view, mode_sw_lbl = create_btn("🧱 筑城 (正向)", radius=8, expand=True, padding=0, height=40, on_click=lambda e: switch_mode("stopwatch"))

    mode_pm_lbl = ft.Text("🌱 种树", weight="bold", max_lines=1)
    mode_pm_click_area = ft.Container(
        content=mode_pm_lbl, 
        on_click=lambda e: switch_mode("pomodoro"), 
        padding=5,
        bgcolor="transparent"
    )

    def on_pomo_change(e):
        if st.session_active:
            show_warning("🚨 专注期间禁止修改目标时间！")
            page.update()
            return
        st.last_pomo_val = str(sel_pomo.value)
        try: st.pomo_target = int(sel_pomo.value) * 60
        except: st.pomo_target = 60 * 60 
        st.mode = "pomodoro"
        sel_pomo.disabled = False
        st.elapsed = 0
        
        time_str = format_time(st.pomo_target)
        lbl_time.value = time_str
        lbl_time_mini.value = time_str
        
        apply_theme_colors()
        try: page.update()
        except: pass

    sel_pomo = ft.Dropdown(
        options=[ft.dropdown.Option(key=str(m), text=f"{m} 分钟") for m in [15, 25, 35, 45, 60, 90, 120]],
        value="60", width=110, dense=True, content_padding=0, text_size=13,
        text_align="center", border="none", filled=False, bgcolor="transparent"
    )
    sel_pomo.on_change = on_pomo_change  

    mode_pm_view = ft.Container(
        content=ft.Row(
            [mode_pm_click_area, sel_pomo], 
            spacing=2, alignment="center", vertical_alignment="center"
        ),
        border_radius=8, expand=True, height=40, padding=0
    )

    def stop_timer_handler(e):
        if not st.session_active: return
        st.was_active = st.timer_active
        st.timer_active = False 
        elapsed_int = int(st.elapsed)
        if st.mode == "pomodoro" and elapsed_int < st.pomo_target:
            show_confirm(f"番茄钟未完成 (仅专注 {elapsed_int}秒)\n放弃将留下枯树 🥀，确定吗？")
        elif st.mode == "stopwatch" and elapsed_int < 60:
            show_confirm(f"筑城不足1分钟 (仅专注 {elapsed_int}秒)\n只留下废料 🚧。确定保存吗？")
        else:
            show_success()

    def toggle_timer(e):
        if not st.session_active:
            st.session_active = True
            st.timer_active = True
            if st.mode == "pomodoro":
                try: st.pomo_target = int(sel_pomo.value) * 60
                except: pass
            st.start_tick = time.time() - st.elapsed
            btn_start_lbl.value = "⏸ 暂停"
            sel_subject.disabled = True
            sel_pomo.disabled = True  
            lbl_quote.value = random.choice(ENCOURAGEMENTS)
        elif not st.timer_active:
            st.timer_active = True
            st.start_tick = time.time() - st.elapsed
            btn_start_lbl.value = "⏸ 暂停"
        else:
            st.timer_active = False 
            btn_start_lbl.value = "▶ 继续专注"
        
        apply_theme_colors()
        st.last_ui_second = -1
        update_focus_ui()
        try: page.update()
        except: pass

    btn_start_view, btn_start_lbl = create_btn("▶ 开始专注", bgcolor="#34C759", txt_color="#FFFFFF", radius=25, height=42, expand=True, on_click=toggle_timer)
    btn_stop_view, btn_stop_lbl = create_btn("⏹ 结束", radius=25, height=42, expand=True, on_click=stop_timer_handler)

    subject_container = ft.Row([sel_subject], alignment="center")
    goal_container = ft.Column([lbl_goal, bar_goal], spacing=5, horizontal_alignment="center")
    
    mode_container = ft.Container(
        content=ft.Row(
            [mode_sw_view, mode_pm_view], 
            alignment="center", vertical_alignment="center", spacing=0
        ), 
        border_radius=10, padding=4
    )
    row_main_btns = ft.Row([btn_start_view, btn_stop_view], alignment="center", spacing=15)

    col_main = ft.Column([
        subject_container, lbl_icon, lbl_time, lbl_quote, goal_container, mode_container, row_main_btns
    ], alignment="center", horizontal_alignment="center", spacing=10, expand=True)

    # ========================================================
    # 🚀 确认与结算面板
    # ========================================================
    def reset_timer():
        st.session_active = False
        st.timer_active = False
        st.elapsed = 0
        st.last_ui_second = -1
        btn_start_lbl.value = "▶ 开始专注"
        sel_subject.disabled = False
        sel_pomo.disabled = (st.mode == "stopwatch") 
        apply_theme_colors() 

    def on_confirm_save(e):
        db.add_record(sel_subject.value, int(st.elapsed), st.mode, True, "中途放弃")
        reset_timer()
        refresh_forest()
        refresh_stats()
        show_main()

    def on_discard(e):
        reset_timer()
        show_main()

    def on_cancel_dialog(e):
        if st.was_active: 
            st.timer_active = True
            st.start_tick = time.time() - st.elapsed
        st.last_ui_second = -1
        show_main()

    lbl_icon_confirm = ft.Text("⚠️", size=35)
    lbl_title_confirm = ft.Text("确认结束", size=18, weight="bold")
    lbl_confirm_msg = ft.Text("", size=12, text_align="center")
    
    btn_y, btn_y_lbl = create_btn("保存战果", txt_color="#FFFFFF", bgcolor="#FF3B30", padding=5, height=36, expand=True, on_click=on_confirm_save)
    btn_n, btn_n_lbl = create_btn("直接销毁", padding=5, height=36, expand=True, on_click=on_discard)
    btn_c, btn_c_lbl = create_btn("手滑点错 (继续)", bgcolor="#34C759", txt_color="#FFFFFF", padding=5, height=36, expand=True, on_click=on_cancel_dialog)

    row_confirm_btns1 = ft.Row([btn_y, btn_n], alignment="center", spacing=10)
    row_confirm_btns2 = ft.Row([btn_c], alignment="center")

    col_confirm = ft.Column([
        lbl_icon_confirm, lbl_title_confirm, lbl_confirm_msg, row_confirm_btns1, row_confirm_btns2
    ], alignment="center", horizontal_alignment="center", spacing=6, expand=True)

    def on_success_save(e):
        db.add_record(sel_subject.value, int(st.elapsed), st.mode, False, txt_note.value)
        txt_note.value = ""
        reset_timer()
        refresh_forest()
        refresh_stats()
        show_main()

    lbl_icon_success = ft.Text("🎉", size=40)
    lbl_title_success = ft.Text("专注完成！", size=18, weight="bold")
    txt_note = ft.TextField(label="复盘便签 (选填)", expand=True, content_padding=5, text_size=12)
    row_note = ft.Row([txt_note], alignment="center")
    btn_success_save, btn_success_save_lbl = create_btn("保存战果并返回", bgcolor="#34C759", txt_color="#FFFFFF", padding=5, height=36, expand=True, on_click=on_success_save)
    row_success_btn = ft.Row([btn_success_save], alignment="center")
    lbl_success_quote = ft.Text("", size=11, text_align="center")

    col_success = ft.Column([
        lbl_icon_success, lbl_title_success, lbl_success_quote, row_note, row_success_btn
    ], alignment="center", horizontal_alignment="center", spacing=6, expand=True)

    def show_goal_reached_dialog():
        dlg_goal = ft.AlertDialog(
            title=ft.Text("🏆 目标达成！", weight="bold"),
            content=ft.Text("恭喜你完成了今天的专注总目标！\n考研路漫漫，今天的你又干掉了一天的硬仗，请继续保持！"),
            actions=[ft.TextButton("收下荣誉", on_click=lambda e: close_dlg(dlg_goal))]
        )
        open_dlg(dlg_goal)

    view_focus = ft.Container(content=col_main, border_radius=15, expand=True, margin=0, padding=15)

    def show_main():
        view_focus.content = col_main
        update_focus_ui()
        apply_theme_colors()
        try: page.update()
        except: pass

    def show_confirm(msg):
        lbl_confirm_msg.value = msg
        view_focus.content = col_confirm
        apply_theme_colors()
        try: page.update()
        except: pass

    def show_success():
        if st.goal_reached_this_session:
            lbl_success_quote.value = "🏆 太强了！不仅完成了本次专注，还达成了今日总目标！"
            st.goal_reached_this_session = False
        else:
            lbl_success_quote.value = random.choice(ENCOURAGEMENTS)
        view_focus.content = col_success
        apply_theme_colors()
        try: page.update()
        except: pass

    def update_focus_ui():
        elapsed_int = int(st.elapsed)

        if st.mode == "pomodoro":
            remain = max(0, st.pomo_target - elapsed_int)
            time_str = format_time(remain)
            lbl_time.value = time_str
            lbl_time_mini.value = time_str
            if remain <= 0: lbl_icon.value = "🌲"
            else:
                prog = elapsed_int / max(1, st.pomo_target)
                lbl_icon.value = "🌳" if prog >= 0.66 else "🌿" if prog >= 0.33 else "🌱" if elapsed_int >= 60 else "🌰"
        else:
            time_str = format_time(elapsed_int)
            lbl_time.value = time_str
            lbl_time_mini.value = time_str
            if elapsed_int >= 3600: lbl_icon.value = "🏰"
            elif elapsed_int >= 1800: lbl_icon.value = "🏠"
            elif elapsed_int >= 60: lbl_icon.value = "🧱"
            else: lbl_icon.value = "🚧"

        logical_today = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        
        if logical_today != st.last_date and not st.session_active:
            st.last_date = logical_today
            st.goal_reached = False 
            refresh_forest()
            refresh_stats()

        records = [item for item in db.data["studyData"] if item.get("date") == logical_today]
        total = sum(r["duration"] for r in records) + (elapsed_int if st.session_active or elapsed_int > 0 else 0)
        goal = max(db.data["dailyGoal"], 1) 
        
        lbl_goal.value = f"🎯 今日进度: {format_dur(total)} / {format_dur(goal)}"
        bar_goal.value = min(total / goal, 1.0)
        
        if total >= goal and not st.goal_reached and goal > 0:
            st.goal_reached = True
            st.goal_reached_this_session = True
            show_goal_reached_dialog()

    # ========================================================
    # 🚀 完美的程序控制切换：尺寸与缩放联动控制
    # ========================================================
    def apply_theme_and_layout():
        if st.is_mini_mode:
            switch_main_tab(0)
            card_countdown_full.visible = False
            mini_top_bar.visible = True
            nav_bar.visible = False
            subject_container.visible = False
            lbl_quote.visible = False
            goal_container.visible = False
            mode_container.visible = False
            lbl_time.visible = False
            lbl_icon.size = 50
            view_focus.padding = 10; view_focus.margin = 0
            btn_start_view.height = 36; btn_start_view.padding = 5; btn_start_lbl.size = 12
            btn_stop_view.height = 36; btn_stop_view.padding = 5; btn_stop_lbl.size = 12
            row_main_btns.spacing = 10; col_main.spacing = 5
            try:
                page.window.width = 300
                page.window.height = 320
            except:
                try: page.window_width = 300; page.window_height = 320
                except: pass
        else:
            mini_top_bar.visible = False
            lbl_time.visible = True
            card_countdown_full.visible = True
            nav_bar.visible = True
            subject_container.visible = True
            lbl_quote.visible = True
            goal_container.visible = True
            mode_container.visible = True
            lbl_icon.size = 65; lbl_time.size = 50
            view_focus.padding = 15; view_focus.margin = 0
            btn_start_view.height = 42; btn_start_view.padding = 8; btn_start_lbl.size = 14
            btn_stop_view.height = 42; btn_stop_view.padding = 8; btn_stop_lbl.size = 14
            row_main_btns.spacing = 15; col_main.spacing = 10
            try:
                page.window.width = 380
                page.window.height = 600 
            except:
                try: page.window_width = 380; page.window_height = 600
                except: pass
        
        apply_theme_colors()
        try: page.update()
        except: pass

    # ----------------- 图鉴视图 (1) -----------------
    lbl_forest_sum = ft.Text(value="共收获 0 个战果", weight="bold")
    lbl_forest_compare = ft.Text(value="", size=11, text_align="center")
    grid_forest = ft.Column(spacing=15, horizontal_alignment="center")
    
    lbl_forest_history = ft.Text("选择日期:", size=12, weight="bold")
    forest_history_dropdown = ft.Dropdown(
        options=[], width=140, dense=True, content_padding=5, text_size=13, text_align="center"
    )
    def on_forest_history_change(e):
        if forest_history_dropdown.value:
            st.forest_scope = f"custom:{forest_history_dropdown.value}"
        refresh_forest()
    forest_history_dropdown.on_change = on_forest_history_change
    
    row_forest_history = ft.Row([lbl_forest_history, forest_history_dropdown], alignment="center", visible=False)

    forest_nav_btns = []
    def sw_forest(idx):
        st.forest_tab = idx
        if idx == 0: st.forest_scope = "day"
        elif idx == 1: st.forest_scope = "week"
        elif idx == 2: st.forest_scope = "month"
        elif idx == 3:
            unique_dates = sorted(list(set(item["date"] for item in db.data["studyData"])), reverse=True)
            forest_history_dropdown.options = [ft.dropdown.Option(key=d) for d in unique_dates]
            if unique_dates and (forest_history_dropdown.value not in unique_dates):
                forest_history_dropdown.value = unique_dates[0]
            elif not unique_dates:
                forest_history_dropdown.value = None
            
            if forest_history_dropdown.value:
                st.forest_scope = f"custom:{forest_history_dropdown.value}"
            else:
                st.forest_scope = "custom:none"
                
        row_forest_history.visible = (idx == 3)
        apply_theme_colors()
        refresh_forest()

    def make_forest_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: (sw_forest(i), page.update()), radius=8, expand=True, padding=6)
        forest_nav_btns.append({"view": view, "lbl": lbl})
        return view

    row_forest_nav = ft.Container(
        content=ft.Row([make_forest_btn("今日", 0), make_forest_btn("本周", 1), make_forest_btn("本月", 2), make_forest_btn("历史", 3)], alignment="center", spacing=0, vertical_alignment="center"), 
        border_radius=10, padding=4
    )
    col_forest_scroll = ft.Column([grid_forest], scroll="adaptive", expand=True, horizontal_alignment="center")
    container_forest_grid = ft.Container(content=col_forest_scroll, expand=True, padding=5, border_radius=10, bgcolor="transparent")

    def refresh_forest():
        records = db.get_filtered(st.forest_scope)
        lbl_forest_sum.value = f"共收获 {len(records)} 个战果"
        lbl_forest_compare.value = get_period_comparison(st.forest_scope, db.data["studyData"])
        
        grid_forest.controls.clear()
        if not records:
            grid_forest.controls.append(
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🌱 这里的土地还在等待播种", size=14, weight="bold", color="#8E8E93"),
                            ft.Text("种一棵树最好的时间是十年前，其次是现在。\n请前往专注面板开启新一轮复习吧！", size=12, color="#8E8E93", text_align="center")
                        ], horizontal_alignment="center", spacing=8),
                        padding=20
                    )
                ], alignment="center")
            )
        else:
            current_row = []
            for r in records:
                tip = f"📅 {r['date']}\n📚 {r['subject']}\n⏱️ {format_dur(r['duration'])}\n📝 {r.get('note','') or '无便签'}"
                icon_view = ft.Container(
                    content=ft.Row([ft.Text(value=r.get("tree","🌲"), size=42, tooltip=tip)], alignment="center"),
                    width=55, height=55
                )
                current_row.append(icon_view)
                
                if len(current_row) == 4:
                    grid_forest.controls.append(ft.Row(current_row, alignment="center", spacing=15))
                    current_row = []
            if current_row:
                grid_forest.controls.append(ft.Row(current_row, alignment="center", spacing=15))
                
        try: page.update()
        except: pass

    view_forest = ft.Container(
        content=ft.Column([
            row_forest_nav, row_forest_history, ft.Container(height=2), 
            ft.Row([lbl_forest_sum], alignment="center"),
            ft.Row([lbl_forest_compare], alignment="center"),
            container_forest_grid
        ], spacing=5), border_radius=15, padding=15, expand=True, visible=False, margin=0
    )

    # ----------------- 🚀 统计视图 (2) -----------------
    lbl_stat_total = ft.Text(value="0s", size=42, weight="bold")
    lbl_stat_compare = ft.Text(value="", size=12, text_align="center", weight="bold")
    col_stats = ft.Column(scroll="adaptive", expand=True)
    
    lbl_stat_history = ft.Text("选择日期:", size=12, weight="bold")
    history_dropdown = ft.Dropdown(
        options=[], width=140, dense=True, content_padding=5, text_size=13, text_align="center"
    )
    def on_history_change(e):
        if history_dropdown.value:
            st.stats_scope = f"custom:{history_dropdown.value}"
        refresh_stats()
    history_dropdown.on_change = on_history_change
    row_history_select = ft.Row([lbl_stat_history, history_dropdown], alignment="center", visible=False)

    stat_nav_btns = []
    chart_nav_btns = []
    
    def sw_stat(idx):
        st.stat_tab = idx
        if idx == 0: st.stats_scope = "day"
        elif idx == 1: st.stats_scope = "week"
        elif idx == 2: st.stats_scope = "month"
        elif idx == 3:
            unique_dates = sorted(list(set(item["date"] for item in db.data["studyData"])), reverse=True)
            history_dropdown.options = [ft.dropdown.Option(key=d) for d in unique_dates]
            if unique_dates and (history_dropdown.value not in unique_dates):
                history_dropdown.value = unique_dates[0]
            elif not unique_dates:
                history_dropdown.value = None
            
            if history_dropdown.value:
                st.stats_scope = f"custom:{history_dropdown.value}"
            else:
                st.stats_scope = "custom:none"
                
        row_history_select.visible = (idx == 3)
        apply_theme_colors()
        refresh_stats()

    def drill_down_to_date(target_date):
        sw_stat(3) 
        history_dropdown.value = target_date
        forest_history_dropdown.value = target_date
        st.stats_scope = f"custom:{target_date}"
        st.forest_scope = f"custom:{target_date}"
        page.update()
        refresh_stats()
        refresh_forest()

    def sw_chart(idx):
        st.chart_tab = idx
        apply_theme_colors()
        refresh_stats()

    def make_stat_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: (sw_stat(i), page.update()), radius=8, expand=True, padding=6)
        stat_nav_btns.append({"view": view, "lbl": lbl})
        return view
        
    def make_chart_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: (sw_chart(i), page.update()), radius=6, expand=True, padding=4)
        chart_nav_btns.append({"view": view, "lbl": lbl})
        return view

    row_stat_nav = ft.Container(
        content=ft.Row([make_stat_btn("今日", 0), make_stat_btn("本周", 1), make_stat_btn("本月", 2), make_stat_btn("历史", 3)], alignment="center", spacing=0, vertical_alignment="center"), 
        border_radius=10, padding=4
    )
    row_chart_nav = ft.Container(
        content=ft.Row([make_chart_btn("条形图", 0), make_chart_btn("扇形图", 1), make_chart_btn("趋势图", 2)], alignment="center", spacing=5, vertical_alignment="center"),
        padding=0, margin=5
    )

    def refresh_stats():
        records = db.get_filtered(st.stats_scope)
        total = sum(r["duration"] for r in records)
        lbl_stat_total.value = format_dur(total)
        lbl_stat_compare.value = get_period_comparison(st.stats_scope, db.data["studyData"])
        col_stats.controls.clear()
        
        is_dark = page.theme_mode == "dark"
        text_main = "#FFFFFF" if is_dark else "#1C1C1E"
        text_sec = "#8E8E93"
        
        if not records:
            empty_msg = ft.Row([ft.Text(value="当前时段无专注数据", color="#8E8E93")], alignment="center")
            col_stats.controls.append(ft.Container(content=empty_msg, padding=20))
            try: page.update()
            except: pass
            return
            
        if st.chart_tab == 0:
            smap = {}
            for r in records: smap[r["subject"]] = smap.get(r["subject"], 0) + r["duration"]
            
            for sub, dur in sorted(smap.items(), key=lambda x: x[1], reverse=True):
                pct = dur / total if total > 0 else 0
                
                sub_records = [r for r in records if r["subject"] == sub]
                tooltip_lines = [f"【{sub}】详细记录:"]
                
                if st.stats_scope == "day" or st.stats_scope.startswith("custom:"):
                    for r in sub_records:
                        n_str = f" - {r.get('note','')}" if r.get('note','') else ""
                        tooltip_lines.append(f"• {format_dur(r['duration'])}{n_str}")
                elif st.stats_scope == "week":
                    day_map = {}
                    for r in sub_records: day_map[r["date"]] = day_map.get(r["date"], 0) + r["duration"]
                    for d in sorted(day_map.keys()): tooltip_lines.append(f"• {d[-5:]}: {format_dur(day_map[d])}")
                elif st.stats_scope == "month":
                    month_week_map = {"第1周":0, "第2周":0, "第3周":0, "第4周":0, "第5周":0}
                    for r in sub_records:
                        dt = datetime.strptime(r["date"], "%Y-%m-%d")
                        w_idx = (dt.day - 1) // 7 + 1
                        month_week_map[f"第{w_idx}周"] += r["duration"]
                    for w in ["第1周", "第2周", "第3周", "第4周", "第5周"]:
                        if month_week_map[w] > 0: tooltip_lines.append(f"• {w}: {format_dur(month_week_map[w])}")
                
                prog_bar = ft.Container(
                    content=ft.ProgressBar(value=pct, color="#00A2FF", bgcolor="#2C2C2E" if is_dark else "#E5E5EA", height=10, border_radius=5),
                    tooltip="\n".join(tooltip_lines)
                )
                
                col_stats.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(value=f"{sub} ({round(pct*100,1)}%)", weight="bold", color=text_main), 
                            ft.Text(value=f"{format_dur(dur)}", color=text_sec, size=11)
                        ], alignment="spaceBetween"),
                        prog_bar
                    ], spacing=6)
                )
                
        elif st.chart_tab == 1:
            smap = {}
            for r in records: smap[r["subject"]] = smap.get(r["subject"], 0) + r["duration"]
            colors = ["#FF3B30", "#FF9500", "#FFCC00", "#34C759", "#5AC8FA", "#007AFF", "#5856D6", "#FF2D55"]
            
            gradient_colors = []
            stops = []
            current_stop = 0.0
            legend_cols = []
            
            for i, (sub, dur) in enumerate(sorted(smap.items(), key=lambda x: x[1], reverse=True)):
                pct = dur / total if total > 0 else 0
                c = colors[i % len(colors)]
                gradient_colors.extend([c, c])
                stops.extend([current_stop, current_stop + pct])
                current_stop += pct
                
                sub_records = [r for r in records if r["subject"] == sub]
                tip_lines = [f"【{sub}】({pct*100:.1f}%)"]
                for r in sub_records: tip_lines.append(f"• {r['date'][-5:]}: {format_dur(r['duration'])}")
                
                legend_cols.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=12, height=12, bgcolor=c, border_radius=6),
                            ft.Text(f"{sub} {pct*100:.1f}%", size=12, color=text_main)
                        ], alignment="center"),
                        tooltip="\n".join(tip_lines)
                    )
                )
                
            pie = ft.Container(
                width=160, height=160, border_radius=80,
                gradient=ft.SweepGradient(
                    start_angle=0.0, end_angle=3.14159 * 2,
                    colors=gradient_colors, stops=stops,
                )
            )
            col_stats.controls.append(ft.Column([
                ft.Container(content=ft.Row([pie], alignment="center"), padding=10),
                ft.Column(legend_cols, spacing=5, horizontal_alignment="center")
            ], spacing=15))
            
        elif st.chart_tab == 2:
            date_map = {}
            for r in records:
                date_map[r["date"]] = date_map.get(r["date"], 0) + r["duration"]
            sorted_dates = sorted(list(date_map.keys()))
            max_dur_val = max(date_map.values()) if date_map else 0
            
            bars = []
            for d in sorted_dates:
                dur = date_map[d]
                h = (dur / max_dur_val) * 120 if max_dur_val > 0 else 0
                
                day_records = [r for r in records if r["date"] == d]
                day_smap = {}
                for r in day_records: day_smap[r["subject"]] = day_smap.get(r["subject"], 0) + r["duration"]
                breakdown = "\n".join([f"• {s}: {format_dur(s_dur)}" for s, s_dur in day_smap.items()])
                tip = f"📅 {d}\n总计: {format_dur(dur)}\n{breakdown}\n(点击钻取当日明细)"
                
                bars.append(
                    ft.Column([
                        ft.Text(format_dur(dur), size=9, color="#8E8E93"),
                        ft.Container(
                            width=25, height=max(h, 5), bgcolor="#00A2FF", border_radius=4, 
                            tooltip=tip,
                            on_click=lambda e, target_d=d: drill_down_to_date(target_d)
                        ),
                        ft.Text(d[-5:], size=10, color=text_main)
                    ], horizontal_alignment="center", spacing=4)
                )
            chart_row = ft.Row(bars, alignment="center", vertical_alignment="end", spacing=15)
            scroll_row = ft.Row([chart_row], scroll="adaptive", alignment="center")
            col_stats.controls.append(ft.Container(content=scroll_row, height=200, padding=10))

        try: page.update()
        except: pass

    view_stats = ft.Container(
        content=ft.Column([
            row_stat_nav, row_history_select, row_chart_nav, 
            ft.Row([lbl_stat_total], alignment="center"), 
            ft.Row([lbl_stat_compare], alignment="center"), 
            ft.Container(height=5), col_stats
        ], spacing=5),
        border_radius=15, padding=15, expand=True, visible=False, margin=0
    )

    # ----------------- 🚀 导入导出功能 (修复了 Type Hint 报错) -----------------
    def process_export(e):
        if e.path:
            try:
                with open(e.path, "w", encoding="utf-8") as f: 
                    json.dump(db.data, f, ensure_ascii=False, indent=4)
                show_warning(f"✅ 备份导出成功！")
            except Exception as ex: 
                show_warning(f"❌ 导出失败: {str(ex)}")

    def process_import(e):
        if e.files and len(e.files) > 0:
            path = e.files[0].path
            try:
                with open(path, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                db.data.clear()
                db.data.update(backup_data)
                db.save()
                
                txt_goal.value = str(int(db.data["dailyGoal"] // 3600))
                txt_exam_date.value = str(db.data.get("examDate", "2026-12-20"))
                sel_subject.options = [ft.dropdown.Option(key=x) for x in db.data["subjects"]]
                if db.data["subjects"]:
                    sel_subject.value = db.data.get("currentSubject", db.data["subjects"][0])
                
                update_countdown()
                update_focus_ui()
                render_subs()
                refresh_forest()
                refresh_stats()
                apply_theme_colors()
                page.update()
                show_warning("✅ 历史专注战果已成功导入！")
            except Exception as ex:
                show_warning(f"❌ 导入崩溃: {str(ex)}")

    export_picker = ft.FilePicker(on_result=process_export)
    import_picker = ft.FilePicker(on_result=process_import)
    page.overlay.append(export_picker)
    page.overlay.append(import_picker)

    # ----------------- 设置视图 (3) -----------------
    lbl_setting_1 = ft.Text(value="🎯 目标设置", weight="bold")
    lbl_setting_2 = ft.Text(value="🏷️ 科目管理", weight="bold")
    lbl_setting_3 = ft.Text(value="💾 数据安全", weight="bold")
    
    txt_goal = ft.TextField(value=str(int(db.data["dailyGoal"] // 3600)), label="每日专注目标 (小时)")
    def on_goal_blur(e):
        try: db.data["dailyGoal"] = float(txt_goal.value) * 3600; db.save(); update_focus_ui(); page.update()
        except: txt_goal.value = str(int(db.data["dailyGoal"] // 3600)); page.update()
    txt_goal.on_blur = on_goal_blur

    txt_exam_date = ft.TextField(value=str(db.data.get("examDate", "2026-12-20")), label="初试目标日期 (YYYY-MM-DD)")
    def on_exam_date_blur(e):
        val = txt_exam_date.value.strip()
        try:
            datetime.strptime(val, "%Y-%m-%d")
            db.data["examDate"] = val
            db.save()
            update_countdown()
            page.update()
        except:
            txt_exam_date.value = str(db.data.get("examDate", "2026-12-20"))
            page.update()
    txt_exam_date.on_blur = on_exam_date_blur

    col_subs = ft.Column(spacing=8)
    txt_new_sub = ft.TextField(hint_text="新科目", expand=True)

    def render_subs():
        is_dark = page.theme_mode == "dark"
        bg = "#000000" if is_dark else "#F2F2F7"
        text_main = "#FFFFFF" if is_dark else "#1C1C1E"
        
        col_subs.controls.clear()
        for sub in db.data["subjects"]:
            btn_del, _ = create_btn("删除", txt_color="#FF3B30", on_click=lambda e, s=sub: del_sub(s))
            col_subs.controls.append(ft.Container(content=ft.Row([ft.Text(value=sub, weight="bold", expand=True, color=text_main), btn_del]), bgcolor=bg, padding=8, border_radius=10))

    def add_sub(e):
        v = txt_new_sub.value.strip()
        if v and v not in db.data["subjects"]:
            db.data["subjects"].append(v); db.save()
            sel_subject.options = [ft.dropdown.Option(key=x) for x in db.data["subjects"]]
            txt_new_sub.value = ""; render_subs(); apply_theme_colors(); page.update()
            
    btn_add, _ = create_btn("添加", bgcolor="#34C759", txt_color="#FFFFFF", padding=12, on_click=add_sub)

    def del_sub(s):
        if len(db.data["subjects"]) > 1:
            db.data["subjects"].remove(s); db.save()
            sel_subject.options = [ft.dropdown.Option(key=x) for x in db.data["subjects"]]
            sel_subject.value = db.data["subjects"][0]
            db.data["currentSubject"] = sel_subject.value
            db.save(); render_subs(); apply_theme_colors(); page.update()

    btn_exp, btn_exp_lbl = create_btn("⬇ 导出备份", padding=12, expand=True, on_click=lambda _: export_picker.save_file(allowed_extensions=["json"], file_name="StudyEngine_Backup.json"))
    btn_imp, btn_imp_lbl = create_btn("⬆ 导入备份", padding=12, expand=True, on_click=lambda _: import_picker.pick_files(allowed_extensions=["json"]))
    row_backup_group = ft.Row([btn_exp, btn_imp], spacing=10, alignment="center")

    col_settings_scroll = ft.Column([
        lbl_setting_1, txt_goal, txt_exam_date, ft.Container(height=5),
        lbl_setting_2, col_subs, ft.Row([txt_new_sub, btn_add]), ft.Container(height=5), 
        lbl_setting_3, row_backup_group
    ], scroll="auto", expand=True)

    view_settings = ft.Container(
        content=col_settings_scroll,
        border_radius=15, padding=15, expand=True, visible=False, margin=0
    )

    # ========================================================
    # 🚀 组装与生命周期挂载
    # ========================================================
    page.add(
        ft.Column([
            mini_top_bar, card_countdown_full, nav_bar, view_focus, view_forest, view_stats, view_settings
        ], expand=True, spacing=0)
    )

    st.is_mini_mode = False
    apply_theme_and_layout()
    switch_main_tab(0)
    sw_forest(0)
    sw_stat(0)
    sw_chart(0) 
    render_subs()
    
    update_countdown()
    update_focus_ui()

    async def heart_beat():
        while True:
            await asyncio.sleep(0.1) 
            
            try:
                current_pomo_val = str(sel_pomo.value)
                if current_pomo_val != st.last_pomo_val:
                    if st.session_active:
                        sel_pomo.value = st.last_pomo_val
                        page.update()
                    else:
                        st.last_pomo_val = current_pomo_val
                        st.pomo_target = int(current_pomo_val) * 60
                        st.mode = "pomodoro"
                        sel_pomo.disabled = False
                        st.elapsed = 0
                        st.last_ui_second = -1 
                        
                        time_str = format_time(st.pomo_target)
                        lbl_time.value = time_str
                        lbl_time_mini.value = time_str
                        
                        apply_theme_colors()
                        page.update()
            except Exception: pass
            
            if not st.timer_active: continue
            
            try:
                st.elapsed = time.time() - st.start_tick
                if st.mode == "pomodoro" and int(st.elapsed) >= st.pomo_target:
                    st.timer_active = False 
                    st.elapsed = st.pomo_target
                    st.last_ui_second = -1 
                    update_focus_ui()
                    play_success_sound() 
                    show_success()
                    continue
                
                elapsed_int = int(st.elapsed)
                if elapsed_int != st.last_ui_second:
                    st.last_ui_second = elapsed_int
                    update_focus_ui()
                    try: page.update()
                    except: pass
            except Exception: pass

    page.run_task(heart_beat)

if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception:
        with open("crash_log.txt", "w", encoding="utf-8") as f: traceback.print_exc(file=f)
