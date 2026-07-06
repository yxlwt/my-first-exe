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
    page.padding = 15
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # 🚀 极其硬核的尺寸限制：绝不允许随意拉伸变形！
    try:
        page.window.width = 420
        page.window.height = 780
        page.window.min_width = 300   # 极限小组件宽度，防止文字换行
        page.window.min_height = 360  # 极限小组件高度
        page.window.max_width = 460   # 最大也就是个大号手机，防止变宽变丑
        page.window.max_height = 850
    except AttributeError:
        try:
            page.window_width = 420
            page.window_height = 780
            page.window_min_width = 300
            page.window_min_height = 360
            page.window_max_width = 460
            page.window_max_height = 850
        except: pass

    def open_dlg(d):
        if hasattr(page, "open"):
            page.open(d)
        else:
            page.dialog = d
            d.open = True
            page.update()

    def close_dlg(d):
        if hasattr(page, "close"):
            page.close(d)
        else:
            d.open = False
            page.update()

    def show_warning(msg):
        snack = ft.SnackBar(content=ft.Text(msg, color="white", weight=ft.FontWeight.BOLD), bgcolor="#FF3B30")
        if hasattr(page, "open"):
            page.open(snack)
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
        
        switch_main_tab(st.active_tab)
        sw_forest(st.forest_tab)
        sw_stat(st.stat_tab)
        render_subs()

    def toggle_theme(e):
        page.theme_mode = "dark" if page.theme_mode == "light" else "light"
        apply_theme_colors()
        page.update()

    def toggle_pin(e):
        st.is_pinned = not st.is_pinned
        try: page.window.always_on_top = st.is_pinned
        except AttributeError:
            try: page.window_always_on_top = st.is_pinned
            except: pass
        apply_theme_colors()
        page.update()

    btn_pin, btn_pin_lbl = create_btn("📌", padding=8, width=40, on_click=toggle_pin)
    btn_theme, btn_theme_lbl = create_btn("🌙", padding=8, width=40, on_click=toggle_theme)

    countdown_text = ft.Text(value="距离初试仅剩 -- 天", size=17, weight=ft.FontWeight.BOLD, color="#007AFF", max_lines=1)
    try:
        today = datetime.now().date()
        exam = datetime.strptime(db.data["examDate"], "%Y-%m-%d").date()
        diff = (exam - today).days
        countdown_text.value = f"距离初试仅剩 {diff} 天"
        countdown_text.color = "#FF3B30" if diff < 150 else "#007AFF"
    except: pass

    card_countdown = ft.Container(
        content=ft.Row([btn_pin, countdown_text, btn_theme], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        border_radius=12, padding=12, margin=5 
    )

    nav_buttons = []
    
    def switch_main_tab(index):
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
        view, lbl = create_btn(text, on_click=lambda e, i=idx: (switch_main_tab(i), page.update()), radius=8, expand=True, padding=8)
        nav_buttons.append({"view": view, "lbl": lbl})
        return view

    nav_bar = ft.Container(
        content=ft.Row([make_nav_btn("专注", 0), make_nav_btn("图鉴", 1), make_nav_btn("统计", 2), make_nav_btn("设置", 3)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
        border_radius=10, padding=4, margin=5
    )

    # ========================================================
    # 🚀 专注功能面板
    # ========================================================
    lbl_icon = ft.Text(value="🌰", size=90, text_align=ft.TextAlign.CENTER, max_lines=1) 
    # 🚨 强制 max_lines=1 杜绝时间被挤换行！
    lbl_time = ft.Text(value="60:00", size=65, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, max_lines=1)
    lbl_quote = ft.Text(value=random.choice(ENCOURAGEMENTS), size=13, text_align=ft.TextAlign.CENTER, max_lines=1)
    
    sel_subject = ft.Dropdown(
        options=[ft.dropdown.Option(key=s) for s in db.data["subjects"]],
        value=db.data["currentSubject"], 
        width=180, 
        dense=True, 
        border_radius=25, 
        border_color="transparent",
        text_size=15,
        content_padding=15
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
        page.update()

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
            sel_pomo.value = st.last_pomo_val
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
        page.update()

    sel_pomo = ft.Dropdown(
        options=[ft.dropdown.Option(key=str(m), text=f"{m} 分钟") for m in [15, 25, 35, 45, 60, 90, 120]],
        value="60", width=115, dense=True, content_padding=10, text_size=13,
        border_color="transparent", bgcolor="transparent"
    )
    sel_pomo.on_change = on_pomo_change  

    mode_pm_view = ft.Container(
        content=ft.Row([mode_pm_click_area, sel_pomo], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
        height=42, 
        border_radius=8, expand=True
    )

    def stop_timer_handler(e):
        if not st.session_active:
            return
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
        page.update()

    btn_start_view, btn_start_lbl = create_btn("▶ 开始专注", bgcolor="#34C759", txt_color="white", radius=25, height=45, expand=True, on_click=toggle_timer)
    btn_stop_view, btn_stop_lbl = create_btn("⏹ 结束", radius=25, height=45, expand=True, on_click=stop_timer_handler)

    subject_container = ft.Row([sel_subject], alignment=ft.MainAxisAlignment.CENTER)
    goal_container = ft.Column([lbl_goal, bar_goal], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    mode_container = ft.Container(content=ft.Row([mode_sw_view, mode_pm_view], alignment=ft.MainAxisAlignment.CENTER, spacing=0), border_radius=10, padding=4)
    row_main_btns = ft.Row([btn_start_view, btn_stop_view], alignment=ft.MainAxisAlignment.CENTER, spacing=15)

    col_main = ft.Column([
        subject_container, lbl_icon, lbl_time, lbl_quote, goal_container, mode_container, row_main_btns
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)

    # ========================================================
    # 🚀 确认与结算面板
    # ========================================================
    def reset_timer():
        st.session_active = False
        st.timer_active = False
        st.elapsed = 0
        btn_start_lbl.value = "▶ 开始专注"
        btn_start_view.bgcolor = "#34C759"
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
        show_main()

    lbl_icon_confirm = ft.Text("⚠️", size=50)
    lbl_title_confirm = ft.Text("确认结束", size=22, weight=ft.FontWeight.BOLD)
    lbl_confirm_msg = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)
    
    btn_y, btn_y_lbl = create_btn("保存战果", txt_color="white", bgcolor="#FF3B30", padding=12, expand=True, on_click=on_confirm_save)
    btn_n, btn_n_lbl = create_btn("直接销毁", padding=12, expand=True, on_click=on_discard)
    btn_c, btn_c_lbl = create_btn("手滑点错 (继续)", bgcolor="#34C759", txt_color="white", padding=12, expand=True, on_click=on_cancel_dialog)

    row_confirm_btns1 = ft.Row([btn_y, btn_n], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
    row_confirm_btns2 = ft.Row([btn_c], alignment=ft.MainAxisAlignment.CENTER)

    col_confirm = ft.Column([
        lbl_icon_confirm, lbl_title_confirm, lbl_confirm_msg, row_confirm_btns1, row_confirm_btns2
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

    def on_success_save(e):
        db.add_record(sel_subject.value, int(st.elapsed), st.mode, False, txt_note.value)
        txt_note.value = ""
        reset_timer()
        refresh_forest()
        refresh_stats()
        show_main()

    lbl_icon_success = ft.Text("🎉", size=60)
    lbl_title_success = ft.Text("专注完成！", size=22, weight=ft.FontWeight.BOLD)
    txt_note = ft.TextField(label="复盘便签 (选填)", expand=True)
    row_note = ft.Row([txt_note], alignment=ft.MainAxisAlignment.CENTER)
    btn_success_save, btn_success_save_lbl = create_btn("保存战果并返回", bgcolor="#34C759", txt_color="white", padding=12, expand=True, on_click=on_success_save)
    row_success_btn = ft.Row([btn_success_save], alignment=ft.MainAxisAlignment.CENTER)
    lbl_success_quote = ft.Text("", size=13, text_align=ft.TextAlign.CENTER)

    col_success = ft.Column([
        lbl_icon_success, lbl_title_success, lbl_success_quote, row_note, row_success_btn
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

    def show_goal_reached_dialog():
        dlg_goal = ft.AlertDialog(
            title=ft.Text("🏆 目标达成！", weight=ft.FontWeight.BOLD),
            content=ft.Text("恭喜你完成了今天的专注总目标！\n考研路漫漫，今天的你又干掉了一天的硬仗，请继续保持！"),
            actions=[ft.TextButton("收下荣誉", on_click=lambda e: close_dlg(dlg_goal))]
        )
        open_dlg(dlg_goal)

    view_focus = ft.Container(content=col_main, border_radius=15, expand=True)

    def show_main():
        view_focus.content = col_main
        update_focus_ui()
        apply_theme_colors()
        page.update()

    def show_confirm(msg):
        lbl_confirm_msg.value = msg
        view_focus.content = col_confirm
        apply_theme_colors()
        page.update()

    def show_success():
        if st.goal_reached_this_session:
            lbl_success_quote.value = "🏆 太强了！不仅完成了本次专注，还达成了今日总目标！"
            st.goal_reached_this_session = False
        else:
            lbl_success_quote.value = random.choice(ENCOURAGEMENTS)
        view_focus.content = col_success
        apply_theme_colors()
        page.update()

    def update_focus_ui():
        elapsed_int = int(st.elapsed)
        if st.mode == "pomodoro":
            remain = max(0, st.pomo_target - elapsed_int)
            lbl_time.value = format_time(remain)
            if remain <= 0: lbl_icon.value = "🌲"
            else:
                prog = elapsed_int / max(1, st.pomo_target)
                lbl_icon.value = "🌳" if prog >= 0.66 else "🌿" if prog >= 0.33 else "🌱" if elapsed_int >= 60 else "🌰"
        else:
            lbl_time.value = format_time(elapsed_int)
            if elapsed_int >= 3600: lbl_icon.value = "🏰"
            elif elapsed_int >= 1800: lbl_icon.value = "🏠"
            elif elapsed_int >= 60: lbl_icon.value = "🧱"
            else: lbl_icon.value = "🚧"

        logical_today = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        if logical_today != st.last_date:
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
    # 🚀 尺寸侦测 (智能压缩字体，防止文字折行)
    # ========================================================
    def apply_responsive_layout():
        w = page.window.width if page.window.width else 420
        h = page.window.height if page.window.height else 750
        
        is_compact = h < 600 or w < 380
        
        # 如果是悬浮窗模式，但在非专注界面，强制切回专注界面！
        if is_compact and st.active_tab != 0:
            st.active_tab = 0
        
        card_countdown.visible = not is_compact
        nav_bar.visible = not is_compact
        subject_container.visible = not is_compact
        lbl_quote.visible = not is_compact
        goal_container.visible = not is_compact
        mode_container.visible = not is_compact
        
        if is_compact:
            lbl_icon.size = 70; lbl_time.size = 50
            view_focus.padding = 15; view_focus.margin = 0
            btn_start_view.height = 40; btn_start_view.padding = 5; btn_start_lbl.size = 12
            btn_stop_view.height = 40; btn_stop_view.padding = 5; btn_stop_lbl.size = 12
            row_main_btns.spacing = 8; col_main.spacing = 8
            
            lbl_icon_confirm.size = 40; lbl_title_confirm.size = 18; lbl_confirm_msg.size = 12
            col_confirm.spacing = 8
            btn_y.padding = 8; btn_y_lbl.size = 12
            btn_n.padding = 8; btn_n_lbl.size = 12
            btn_c.padding = 8; btn_c_lbl.size = 12
            row_confirm_btns1.spacing = 8
            
            lbl_icon_success.size = 50; lbl_title_success.size = 18; lbl_success_quote.size = 12
            col_success.spacing = 8
            txt_note.content_padding = 5; txt_note.text_size = 12
            btn_success_save.padding = 8; btn_success_save_lbl.size = 12
        else:
            lbl_icon.size = 90; lbl_time.size = 65
            view_focus.padding = 25; view_focus.margin = 5
            btn_start_view.height = 45; btn_start_view.padding = 10; btn_start_lbl.size = 14
            btn_stop_view.height = 45; btn_stop_view.padding = 10; btn_stop_lbl.size = 14
            row_main_btns.spacing = 15; col_main.spacing = 12
            
            lbl_icon_confirm.size = 50; lbl_title_confirm.size = 22; lbl_confirm_msg.size = 14
            col_confirm.spacing = 15
            btn_y.padding = 12; btn_y_lbl.size = 14
            btn_n.padding = 12; btn_n_lbl.size = 14
            btn_c.padding = 12; btn_c_lbl.size = 14
            row_confirm_btns1.spacing = 15
            
            lbl_icon_success.size = 60; lbl_title_success.size = 22; lbl_success_quote.size = 13
            col_success.spacing = 15
            txt_note.content_padding = 10; txt_note.text_size = 14
            btn_success_save.padding = 12; btn_success_save_lbl.size = 14
        
        apply_theme_colors()

    page.on_resize = lambda e: apply_responsive_layout()

    # ----------------- 图鉴视图 (1) -----------------
    lbl_forest_sum = ft.Text(value="共收获 0 个战果", weight=ft.FontWeight.BOLD)
    grid_forest = ft.Row(wrap=True, spacing=15, run_spacing=15)
    
    forest_nav_btns = []
    def sw_forest(idx):
        st.forest_tab = idx
        st.forest_scope = ["day", "week", "month"][idx]
        apply_theme_colors()

    def make_forest_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: (sw_forest(i), page.update()), radius=8, expand=True, padding=8)
        forest_nav_btns.append({"view": view, "lbl": lbl})
        return view

    row_forest_nav = ft.Container(content=ft.Row([make_forest_btn("今日", 0), make_forest_btn("本周", 1), make_forest_btn("本月", 2)], alignment=ft.MainAxisAlignment.CENTER, spacing=0), border_radius=10, padding=4)
    container_forest_grid = ft.Container(content=grid_forest, expand=True, padding=15, border_radius=10)

    def refresh_forest():
        records = db.get_filtered(st.forest_scope)
        lbl_forest_sum.value = f"共收获 {len(records)} 个战果"
        grid_forest.controls.clear()
        if not records:
            grid_forest.controls.append(ft.Text(value="空空如也，快去专注吧 ✨", color="#8E8E93"))
        for r in records:
            tip = f"{r['subject']} | {format_dur(r['duration'])} {r.get('note','')}"
            grid_forest.controls.append(ft.Text(value=r.get("tree","🌲"), size=45, tooltip=tip))

    view_forest = ft.Container(
        content=ft.Column([
            row_forest_nav, ft.Container(height=5), ft.Row([lbl_forest_sum], alignment=ft.MainAxisAlignment.CENTER), container_forest_grid
        ]), border_radius=15, padding=25, expand=True, visible=False, margin=5
    )

    # ----------------- 统计视图 (2) -----------------
    lbl_stat_total = ft.Text(value="0s", size=42, weight=ft.FontWeight.BOLD)
    col_stats = ft.Column(scroll=ft.ScrollMode.ADAPTIVE)

    stat_nav_btns = []
    def sw_stat(idx):
        st.stat_tab = idx
        st.stats_scope = ["day", "week", "month"][idx]
        apply_theme_colors()

    def make_stat_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: (sw_stat(i), page.update()), radius=8, expand=True, padding=8)
        stat_nav_btns.append({"view": view, "lbl": lbl})
        return view

    row_stat_nav = ft.Container(content=ft.Row([make_stat_btn("今日", 0), make_stat_btn("本周", 1), make_stat_btn("本月", 2)], alignment=ft.MainAxisAlignment.CENTER, spacing=0), border_radius=10, padding=4)

    def refresh_stats():
        records = db.get_filtered(st.stats_scope)
        total = sum(r["duration"] for r in records)
        lbl_stat_total.value = format_dur(total)
        col_stats.controls.clear()
        if not records:
            col_stats.controls.append(ft.Text(value="当前时段无专注数据", color="#8E8E93"))
        smap = {}
        for r in records: smap[r["subject"]] = smap.get(r["subject"], 0) + r["duration"]
        for sub, dur in sorted(smap.items(), key=lambda x: x[1], reverse=True):
            pct = dur / total if total > 0 else 0
            is_dark = page.theme_mode == "dark"
            col_stats.controls.append(
                ft.Column([
                    ft.Row([ft.Text(value=f"{sub} ({round(pct*100,1)}%)", weight=ft.FontWeight.BOLD, color="#FFFFFF" if is_dark else "#1C1C1E"), ft.Text(value=format_dur(dur), color="#8E8E93")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ProgressBar(value=pct, color="#00A2FF", bgcolor="#2C2C2E" if is_dark else "#E5E5EA", height=10, border_radius=5)
                ], spacing=8)
            )

    view_stats = ft.Container(
        content=ft.Column([row_stat_nav, ft.Container(height=15), ft.Row([lbl_stat_total], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=15), col_stats]),
        border_radius=15, padding=25, expand=True, visible=False, margin=5
    )

    # ----------------- 设置视图 (3) -----------------
    lbl_setting_1 = ft.Text(value="🎯 目标设置", weight=ft.FontWeight.BOLD)
    lbl_setting_2 = ft.Text(value="🏷️ 科目管理", weight=ft.FontWeight.BOLD)
    lbl_setting_3 = ft.Text(value="💾 数据安全", weight=ft.FontWeight.BOLD)
    
    txt_goal = ft.TextField(value=str(db.data["dailyGoal"] // 3600), label="每日专注目标 (小时)")
    def on_goal_blur(e):
        try: db.data["dailyGoal"] = float(txt_goal.value) * 3600; db.save(); update_focus_ui(); page.update()
        except: txt_goal.value = str(db.data["dailyGoal"] // 3600); page.update()
    txt_goal.on_blur = on_goal_blur

    col_subs = ft.Column(spacing=8)
    txt_new_sub = ft.TextField(hint_text="新科目", expand=True)

    def render_subs():
        is_dark = page.theme_mode == "dark"
        bg = "#000000" if is_dark else "#F2F2F7"
        text_main = "#FFFFFF" if is_dark else "#1C1C1E"
        
        col_subs.controls.clear()
        for sub in db.data["subjects"]:
            btn_del, _ = create_btn("删除", txt_color="#FF3B30", on_click=lambda e, s=sub: del_sub(s))
            col_subs.controls.append(ft.Container(content=ft.Row([ft.Text(value=sub, weight=ft.FontWeight.BOLD, expand=True, color=text_main), btn_del]), bgcolor=bg, padding=8, border_radius=10))

    def add_sub(e):
        v = txt_new_sub.value.strip()
        if v and v not in db.data["subjects"]:
            db.data["subjects"].append(v); db.save()
            sel_subject.options = [ft.dropdown.Option(key=x) for x in db.data["subjects"]]
            txt_new_sub.value = ""; render_subs(); apply_theme_colors(); page.update()
            
    btn_add, _ = create_btn("添加", bgcolor="#34C759", txt_color="white", padding=12, on_click=add_sub)

    def del_sub(s):
        if len(db.data["subjects"]) > 1:
            db.data["subjects"].remove(s); db.save()
            sel_subject.options = [ft.dropdown.Option(key=x) for x in db.data["subjects"]]
            sel_subject.value = db.data["subjects"][0]
            db.data["currentSubject"] = sel_subject.value
            db.save(); render_subs(); apply_theme_colors(); page.update()

    def on_export(e):
        try:
            with open("StudyEngine_Backup.json", "w", encoding="utf-8") as f: json.dump(db.data, f, ensure_ascii=False, indent=4)
        except: pass

    btn_exp, btn_exp_lbl = create_btn("⬇ 导出本地备份 (同目录)", padding=15, on_click=on_export)

    view_settings = ft.Container(
        content=ft.Column([
            lbl_setting_1, txt_goal, lbl_setting_2, col_subs, ft.Row([txt_new_sub, btn_add]), ft.Container(height=10), lbl_setting_3, btn_exp
        ], scroll=ft.ScrollMode.ADAPTIVE),
        border_radius=15, padding=25, expand=True, visible=False, margin=5
    )

    # ----------------- 组装与循环 -----------------
    page.add(
        ft.Column([
            card_countdown, nav_bar, view_focus, view_forest, view_stats, view_settings
        ], expand=True)
    )

    apply_responsive_layout()

    async def heart_beat():
        while True:
            await asyncio.sleep(0.2) 
            
            current_pomo_val = str(sel_pomo.value)
            if current_pomo_val != st.last_pomo_val:
                if st.session_active:
                    sel_pomo.value = st.last_pomo_val
                    page.update()
                else:
                    st.last_pomo_val = current_pomo_val
                    try: st.pomo_target = int(current_pomo_val) * 60
                    except: st.pomo_target = 60 * 60
                    st.mode = "pomodoro"
                    sel_pomo.disabled = False
                    st.elapsed = 0
                    
                    lbl_time.value = format_time(st.pomo_target)
                    apply_theme_colors()
                    page.update()
            
            if not st.timer_active: continue
            
            try:
                st.elapsed = time.time() - st.start_tick
                if st.mode == "pomodoro" and int(st.elapsed) >= st.pomo_target:
                    st.timer_active = False 
                    st.elapsed = st.pomo_target
                    update_focus_ui()
                    show_success()
                    continue
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
