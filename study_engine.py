import flet as ft
import asyncio
import json
import os
import sys
import time
import random
import traceback
from datetime import datetime, timedelta

# ================= 数据文件 =================

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(application_path, "study_data.json")

ENCOURAGEMENTS = [
    "星光不问赶路人。",
    "乾坤未定，你我皆是黑马。",
    "坚持的意义会在未来显现。",
    "你正在变得更强。"
]

# ================= 数据管理 =================

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
            except:
                pass

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def add_record(self, subject, duration, mode, is_dead, note):
        logical_today = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")

        icon = "🌱"
        if mode == "pomodoro":
            icon = "🥀" if is_dead else "🌳"
        else:
            icon = "🏰" if duration > 3600 else "🏠"

        self.data["studyData"].append({
            "date": logical_today,
            "subject": subject,
            "duration": duration,
            "tree": icon,
            "note": note
        })
        self.save()

    def get_filtered(self, scope):
        now = datetime.now() - timedelta(hours=2)
        today = now.strftime("%Y-%m-%d")

        if scope == "day":
            return [x for x in self.data["studyData"] if x["date"] == today]

        if scope == "week":
            start = now - timedelta(days=now.weekday())
            days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            return [x for x in self.data["studyData"] if x["date"] in days]

        if scope == "month":
            prefix = now.strftime("%Y-%m-")
            return [x for x in self.data["studyData"] if x["date"].startswith(prefix)]

        return []


# ================= 工具 =================

def format_time(s):
    s = int(max(0, s))
    return f"{s//60:02d}:{s%60:02d}"


def format_dur(s):
    s = int(max(0, s))
    h = s // 3600
    m = (s % 3600) // 60
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def create_btn(text, on_click=None, color="white", bg="#34C759"):
    t = ft.Text(text, weight=ft.FontWeight.BOLD, color=color)
    c = ft.Container(
        content=ft.Row([t], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bg,
        padding=10,
        border_radius=20,
        on_click=on_click,
        expand=True
    )
    return c, t


# ================= 主程序 =================

async def main(page: ft.Page):

    db = DataManager(DATA_FILE)

    # ================= 状态机（核心） =================
    class State:
        state = "idle"   # idle / running / paused
        mode = "pomodoro"
        elapsed = 0
        start_tick = 0
        pomo_target = 60 * 60
        forest_scope = "day"
        stats_scope = "day"

    st = State()

    # ================= UI =================

    lbl_time = ft.Text("60:00", size=60, weight=ft.FontWeight.BOLD)
    lbl_icon = ft.Text("🌱", size=80)
    lbl_quote = ft.Text(random.choice(ENCOURAGEMENTS))

    sel_subject = ft.Dropdown(
        options=[ft.dropdown.Option(x) for x in db.data["subjects"]],
        value=db.data["currentSubject"],
        width=160
    )

    sel_pomo = ft.Dropdown(
        options=[ft.dropdown.Option(str(x)) for x in [15,25,35,45,60,90,120]],
        value="60",
        width=120
    )

    # ================= 核心逻辑 =================

    def can_switch_mode():
        return st.state == "idle"

    def switch_mode(m):
        if not can_switch_mode():
            return

        st.mode = m
        st.elapsed = 0
        update_ui()
        page.update()

    def toggle():
        if st.state == "idle" or st.state == "paused":
            st.state = "running"
            st.start_tick = time.time() - st.elapsed
            btn_start_text.value = "暂停"
        else:
            st.state = "paused"
            st.elapsed = time.time() - st.start_tick
            btn_start_text.value = "继续"

        page.update()

    def stop():
        if st.state == "idle":
            return

        st.state = "paused"
        elapsed = int(st.elapsed)

        db.add_record(
            sel_subject.value,
            elapsed,
            st.mode,
            False,
            ""
        )

        st.state = "idle"
        st.elapsed = 0
        btn_start_text.value = "开始"

        update_ui()
        page.update()

    # ================= UI刷新 =================

    def update_ui():
        t = int(st.elapsed)

        if st.mode == "pomodoro":
            remain = max(0, st.pomo_target - t)
            lbl_time.value = format_time(remain)
        else:
            lbl_time.value = format_time(t)

        page.update()

    # ================= 按钮 =================

    btn_start, btn_start_text = create_btn("开始", lambda e: toggle())
    btn_stop, _ = create_btn("结束", lambda e: stop(), bg="#FF3B30")

    # ================= heartbeat =================

    async def loop():
        while True:
            await asyncio.sleep(0.2)

            if st.state == "running":
                st.elapsed = time.time() - st.start_tick

                if st.mode == "pomodoro" and st.elapsed >= st.pomo_target:
                    stop()

            update_ui()

    # ================= 布局 =================

    page.add(
        ft.Column([
            lbl_icon,
            lbl_time,
            lbl_quote,
            sel_subject,
            sel_pomo,
            ft.Row([btn_start, btn_stop]),
        ])
    )

    page.run_task(loop)


if __name__ == "__main__":
    ft.app(target=main)
