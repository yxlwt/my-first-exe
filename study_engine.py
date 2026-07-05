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
    "当前的每一次咬牙坚持，都是为了初试的毫不费力。"
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
        self.data["studyData"].append({
            "date": logical_today,
            "subject": subject,
            "duration": duration,
            "tree": "🌲",
            "note": note
        })
        self.save()

    def get_filtered(self, range_str):
        logical_now = datetime.now() - timedelta(hours=2)
        today_str = logical_now.strftime("%Y-%m-%d")
        if range_str == "day":
            return [i for i in self.data["studyData"] if i.get("date") == today_str]
        return []

def format_dur(seconds):
    s = max(0, int(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    return f"{h}h {m}m" if h > 0 else f"{m}m {s%60}s"

def format_time(seconds):
    s = max(0, int(seconds))
    return f"{s//60:02d}:{s%60:02d}"

def create_btn(text, on_click=None, bgcolor="transparent", txt_color="#1C1C1E", radius=8, expand=False):
    lbl = ft.Text(value=text, color=txt_color, weight=ft.FontWeight.BOLD)
    cnt = ft.Container(
        content=ft.Row([lbl], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bgcolor, border_radius=radius, padding=10,
        on_click=on_click, expand=expand
    )
    return cnt, lbl

# ================= 3. 核心无极 UI 引擎 =================
async def main(page: ft.Page):
    db = DataManager(DATA_FILE)
    page.title = "冲刺备考引擎"
    page.bgcolor = "#F2F2F7"
    page.padding = 15
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.scroll = ft.ScrollMode.ADAPTIVE

    def show_warning(msg):
        snack = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor="#FF3B30")
        if hasattr(page, "open"):
            page.open(snack)
        else:
            page.snack_bar = snack
            snack.open = True
            page.update()

    # 🚀 极致兼容版弹窗挂载方法
    def open_dlg(d):
        try:
            if d not in page.overlay:
                page.overlay.append(d)
        except Exception: pass

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

    class State:
        session_active = False  
        timer_active = False    
        mode = "pomodoro"
        pomo_target = 60 * 60
        elapsed = 0
        start_tick = 0
        last_pomo_val = "60" 
    st = State()

    lbl_icon = ft.Text(value="🌰", size=100, text_align=ft.TextAlign.CENTER)
    lbl_time = ft.Text(value="60:00", size=70, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    lbl_quote = ft.Text(value=random.choice(ENCOURAGEMENTS), size=13, color="#8E8E93", text_align=ft.TextAlign.CENTER)
    
    sel_subject = ft.Dropdown(
        options=[ft.dropdown.Option(key=s) for s in db.data["subjects"]],
        value=db.data["currentSubject"], width=160
    )
    
    def on_sub_change(e):
        db.data["currentSubject"] = sel_subject.value
        db.save()
    sel_subject.on_change = on_sub_change

    def switch_mode(m):
        if st.session_active:
            show_warning("🚨 当前专注尚未结算，无法切换模式！")
            return
        st.mode = m
        sel_pomo.disabled = (m == "stopwatch")
        try: st.pomo_target = int(sel_pomo.value) * 60
        except: st.pomo_target = 60 * 60
        st.elapsed = 0
        update_focus_ui()
        page.update()

    mode_sw_view, mode_sw_lbl = create_btn("🧱 筑城 (正向)", expand=True, on_click=lambda e: switch_mode("stopwatch"))
    
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
        st.elapsed = 0
        update_focus_ui()
        page.update()

    sel_pomo = ft.Dropdown(
        options=[ft.dropdown.Option(key=str(m), text=f"{m} 分钟") for m in [15, 25, 35, 45, 60, 90, 120]],
        value="60", width=115, on_change=on_pomo_change
    )

    btn_start_view, btn_start_lbl = create_btn("▶ 开始专注", bgcolor="#34C759", txt_color="white", expand=True)
    
    # ========================================================
    # 🚀🚀 侦察兵代码区：捕获一切静默崩溃 🚀🚀
    # ========================================================
    def stop_timer_handler(e):
        try:
            if not st.session_active:
                return
                
            was_active = st.timer_active
            st.timer_active = False 
            page.update()
            
            elapsed_int = int(st.elapsed)
            msg = "确定要结束专注吗？"
            
            def on_confirm_save(e):
                close_dlg(dlg)
                db.add_record(sel_subject.value, elapsed_int, st.mode, True, "结束")
                reset_timer()

            def on_discard(e):
                close_dlg(dlg)
                reset_timer()

            def on_cancel_dialog(e):
                close_dlg(dlg)
                if was_active: 
                    st.timer_active = True
                    st.start_tick = time.time() - st.elapsed
                page.update()

            # 极其朴素的按钮，剥离全部可能报错的 style 和颜色
            btn_y = ft.TextButton(text="保存战果", on_click=on_confirm_save)
            btn_n = ft.TextButton(text="直接销毁", on_click=on_discard)
            btn_c = ft.TextButton(text="取消继续", on_click=on_cancel_dialog)

            # 极其朴素的弹窗，剥离 actions_alignment
            dlg = ft.AlertDialog(
                title=ft.Text("确认"),
                content=ft.Text(msg),
                actions=[btn_y, btn_n, btn_c]
            )
            
            open_dlg(dlg)

        except Exception as ex:
            # 🚨 核心探针：如果这里报错，一定会写进本地日志文件！
            err_str = traceback.format_exc()
            with open("debug_error.txt", "w", encoding="utf-8") as f:
                f.write(err_str)
            show_warning(f"弹窗崩溃了! 错误已写入 debug_error.txt, 请发给开发者: {str(ex)}")
    # ========================================================

    btn_stop_view, btn_stop_lbl = create_btn("⏹ 结束", bgcolor="#E5E5EA", expand=True, on_click=stop_timer_handler)

    def toggle_timer(e):
        if not st.session_active:
            st.session_active = True
            st.timer_active = True
            st.start_tick = time.time() - st.elapsed
            btn_start_lbl.value = "⏸ 暂停"
            sel_subject.disabled = True
            sel_pomo.disabled = True  
        elif not st.timer_active:
            st.timer_active = True
            st.start_tick = time.time() - st.elapsed
            btn_start_lbl.value = "⏸ 暂停"
        else:
            st.timer_active = False 
            btn_start_lbl.value = "▶ 继续专注"

        update_focus_ui()
        page.update()
    
    btn_start_view.on_click = toggle_timer

    def reset_timer():
        st.session_active = False
        st.timer_active = False
        st.elapsed = 0
        btn_start_lbl.value = "▶ 开始专注"
        sel_subject.disabled = False
        sel_pomo.disabled = (st.mode == "stopwatch") 
        update_focus_ui()
        page.update()

    view_focus = ft.Container(
        content=ft.Column([
            sel_subject, lbl_icon, lbl_time, lbl_quote,
            ft.Row([mode_sw_view, sel_pomo]),
            ft.Row([btn_start_view, btn_stop_view])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="white", padding=25, expand=True
    )

    def update_focus_ui():
        elapsed_int = int(st.elapsed)
        if st.mode == "pomodoro":
            lbl_time.value = format_time(max(0, st.pomo_target - elapsed_int))
        else:
            lbl_time.value = format_time(elapsed_int)
            
        try:
            lbl_time.update()
        except: pass

    page.add(view_focus)

    async def heart_beat():
        while True:
            await asyncio.sleep(0.2) 
            if not st.timer_active: continue
            try:
                st.elapsed = time.time() - st.start_tick
                if st.mode == "pomodoro" and int(st.elapsed) >= st.pomo_target:
                    st.timer_active = False 
                    st.elapsed = st.pomo_target
                    update_focus_ui()
                    continue
                update_focus_ui()
            except Exception: pass

    page.run_task(heart_beat)

if __name__ == "__main__":
    ft.app(target=main)
