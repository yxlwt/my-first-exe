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
            except: pass

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

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
        return []

# ================= 2. 辅助函数 =================
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

def create_btn(text, on_click=None, bgcolor="transparent", txt_color=None, radius=8, expand=False, width=None, height=None, padding=10):
    lbl = ft.Text(value=text, color=txt_color, weight=ft.FontWeight.BOLD, max_lines=1)
    cnt = ft.Container(
        content=ft.Row([lbl], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bgcolor,
        border_radius=radius,
        padding=padding,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height
    )
    return cnt, lbl

# ================= 3. 核心无极 UI 引擎 =================
async def main(page: ft.Page):
    db = DataManager(DATA_FILE)
    page.title = "冲刺备考引擎"
    page.theme_mode = "light" 
    page.padding = 10
    
    # 🚀 彻底禁绝操作系统级别的鼠标拉伸！防止任何因为拖拽导致的留白断层
    try:
        page.window.resizable = False
        page.window.width = 400
        page.window.height = 760
    except AttributeError:
        try:
            page.window_resizable = False
            page.window_width = 400
            page.window_height = 760
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
        snack = ft.SnackBar(content=ft.Text(msg, color="white", weight=ft.FontWeight.BOLD), bgcolor="#FF3B30")
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
        
        is_pinned = False
        is_mini_mode = False 
        goal_reached = False 
        goal_reached_this_session = False

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
        btn_pin_lbl.value = "📍" if st.is_pinned else "📌"
        btn_pin_lbl.color = "#FF9500" if st.is_pinned else text_sec
        btn_mini_lbl.color = text_sec
        
        card_countdown.bgcolor = surface
        nav_bar.bgcolor = surface_variant
        
        lbl_time.color = text_main
        lbl_quote.color = text_sec
        
        sel_subject.bgcolor = surface_variant
        sel_subject.color = text_main
        
        bar_goal.bgcolor = surface_variant
        lbl_goal.color = text_sec
        
        mode_container.bgcolor = surface_variant
        mode_sw_view.bgcolor = surface if st.mode == "stopwatch" else "transparent"
        mode_sw_lbl.color = text_main if st.mode == "stopwatch" else text_sec
        mode_pm_view.bgcolor = surface if st.mode == "pomodoro" else "transparent"
        mode_pm_lbl.color = text_main if st.mode == "pomodoro" else text_sec
        sel_pomo.color = text_main
        
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
        row_forest_nav.bgcolor = surface_variant
        view_forest.bgcolor = surface
        container_forest_grid.bgcolor = bg
        lbl_stat_total.color = text_main
        row_stat_nav.bgcolor = surface_variant
        view_stats.bgcolor = surface
        
        lbl_setting_1.color = text_main
        lbl_setting_2.color = text_main
        lbl_setting_3.color = text_main
        txt_goal.border_color = text_sec
        txt_goal.color = text_main
        txt_new_sub.border_color = text_sec
        txt_new_sub.color = text_main
        btn_exp.bgcolor = surface_variant
        btn_exp_lbl.color = text_main
        view_settings.bgcolor = surface
        
        for i, item in enumerate(nav_buttons):
            item["view"].bgcolor = surface if i == st.active_tab else "transparent"
            item["lbl"].color = text_main if i == st.active_tab else text_sec
            
        for i, item in enumerate(forest_nav_btns):
            item["view"].bgcolor = surface if i == st.forest_tab else "transparent"
            item["lbl"].color = text_main if i == st.forest_tab else text_sec
            
        for i, item in enumerate(stat_nav_btns):
            item["view"].bgcolor = surface if i == st.stat_tab else "transparent"
            item["lbl"].color = text_main if i == st.stat_tab else text_sec
            
        for c in col_subs.controls:
            c.bgcolor = bg
            c.content.controls[0].color = text_main

    # ----------------- 🎯 内嵌顶栏 -----------------
    def toggle_theme(e):
        page.theme_mode = "dark" if page.theme_mode == "light" else "light"
        apply_theme_colors()
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

    btn_pin, btn_pin_lbl = create_btn("📌", padding=8, width=40, on_click=toggle_pin)
    btn_mini, btn_mini_lbl = create_btn("🔽", padding=8, width=40, on_click=toggle_mini_mode)
    btn_theme, btn_theme_lbl = create_btn("🌙", padding=8, width=40, on_click=toggle_theme)

    row_left_controls = ft.Row([btn_pin, btn_mini], spacing=5)

    countdown_text = ft.Text(value="距离初试仅剩 -- 天", size=17, weight=ft.FontWeight.BOLD, color="#007AFF", max_lines=1)
    try:
        today = datetime.now().date()
        exam = datetime.strptime(db.data["examDate"], "%Y-%m-%d").date()
        diff = (exam - today).days
        countdown_text.value = f"距离初试仅剩 {diff} 天"
        countdown_text.color = "#FF3B30" if diff < 150 else "#007AFF"
    except: pass

    card_countdown = ft.Container(
        content=ft.Row([row_left_controls, countdown_text, btn_theme], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        border_radius=12, padding=12, margin=5 
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
        try: page.update()
        except: pass

    def make_nav_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: switch_main_tab(i), radius=8, expand=True, padding=8)
        nav_buttons.append({"view": view, "lbl": lbl})
        return view

    nav_bar = ft.Container(
        content=ft.Row([make_nav_btn("专注", 0), make_nav_btn("图鉴", 1), make_nav_btn("统计", 2), make_nav_btn("设置", 3)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
        border_radius=10, padding=4, margin=5
    )

    # ========================================================
    # 🚀 专注功能面板与组件美化
    # ========================================================
    lbl_icon = ft.Text(value="🌰", size=90, text_align=ft.TextAlign.CENTER, max_lines=1) 
    lbl_time = ft.Text(value="60:00", size=65, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, max_lines=1)
    lbl_quote = ft.Text(value=random.choice(ENCOURAGEMENTS), size=13, text_align=ft.TextAlign.CENTER, max_lines=1)
    
    sel_subject = ft.Dropdown(
        options=[ft.dropdown.Option(key=s) for s in db.data["subjects"]],
        value=db.data["currentSubject"], 
        width=180, dense=True, border_radius=25, border_color="transparent", text_size=15, content_padding=15
    )
    def on_sub_change(e):
        db.data["currentSubject"] = sel_subject.value
        db.save()
    sel_subject.on_change = on_sub_change

    bar_goal = ft.ProgressBar(value=0, color="#34C759", height=8)
    lbl_goal = ft.Text(value="今日进度: 0m / 6h", size=12, weight=ft.FontWeight.BOLD, max_lines=1)

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
        lbl_time.value = format_time(st.pomo_target) if m == "pomodoro" else "00:00"
        
        apply_theme_colors() 
        try: page.update()
        except: pass

    mode_sw_view, mode_sw_lbl = create_btn("🧱 筑城 (正向)", radius=8, expand=True, padding=8, on_click=lambda e: switch_mode("stopwatch"))
    mode_sw_view.height = 42

    mode_pm_lbl = ft.Text("🌱 种树", weight=ft.FontWeight.BOLD, max_lines=1)
    mode_pm_click_area = ft.Container(
        content=mode_pm_lbl, 
        on_click=lambda e: switch_mode("pomodoro"), 
        padding=10, 
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
        
        lbl_time.value = format_time(st.pomo_target)
        apply_theme_colors()
        try: page.update()
        except: pass

    sel_pomo = ft.Dropdown(
        options=[ft.dropdown.Option(key=str(m), text=f"{m} 分钟") for m in [15, 25, 35, 45, 60, 90, 120]],
        value="60", width=115, dense=True, content_padding=10, text_size=13,
        border_color="transparent", bgcolor="transparent"
    )
    sel_pomo.on_change = on_pomo_change  

    mode_pm_view = ft.Container(
        content=ft.Row([mode_pm_click_area, sel_pomo], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
        height=42, border_radius=8, expand=True
    )

    def stop_timer_handler(e):
        if not st.session_active: return
        st.was_active = st.timer_active
        st.timer_active = False 
        elapsed_int = int(st.elapsed)
        if st.mode == "pomodoro" and elapsed_int < st.pomo_target:
            show_confirm(f"番茄钟未完成 (仅专注 {elapsed_int}秒)\n放弃将留枯树 🥀，确定吗？")
        elif st.mode == "stopwatch" and elapsed_int < 60:
            show_confirm(f"筑城不足1分钟 (仅专注 {elapsed_int}秒)\n只留废料 🚧。确定保存吗？")
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
            btn_start_view.bgcolor = "#FF9500"
            btn_stop_view.bgcolor = "#FF3B30"
            btn_stop_lbl.color = "white"
            sel_subject.disabled = True
            sel_pomo.disabled = True  
            lbl_quote.value = random.choice(ENCOURAGEMENTS)
        elif not st.timer_active:
            st.timer_active = True
            st.start_tick = time.time() - st.elapsed
            btn_start_lbl.value = "⏸ 暂停"
            btn_start_view.bgcolor = "#FF9500"
            btn_stop_view.bgcolor = "#FF3B30"
            btn_stop_lbl.color = "white"
        else:
            st.timer_active = False 
            btn_start_lbl.value = "▶ 继续专注"
            btn_start_view.bgcolor = "#34C759"
        update_focus_ui()
        try: page.update()
        except: pass

    btn_start_view,
