import flet as ft
import asyncio
import json
import os
import time
import random
from datetime import datetime, timedelta


# =========================
# 数据层（稳定版）
# =========================

DATA_FILE = "study_data.json"

ENCOURAGEMENTS = [
    "你正在稳步变强。",
    "坚持会在未来兑现。",
    "今天的努力不会白费。",
    "保持专注，就是胜利。"
]


class DataManager:
    def __init__(self):
        self.data = {
            "subjects": ["专业课", "数学", "英语"],
            "currentSubject": "专业课",
            "dailyGoal": 6 * 3600,
            "studyData": []
        }

        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except:
                pass

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add(self, subject, duration, mode, note=""):
        day = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        self.data["studyData"].append({
            "date": day,
            "subject": subject,
            "duration": duration,
            "mode": mode,
            "note": note
        })
        self.save()

    def get_day(self):
        day = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        return [x for x in self.data["studyData"] if x["date"] == day]


# =========================
# 状态机（核心升级）
# =========================

class State:
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


class AppState:
    def __init__(self):
        self.state = State.IDLE
        self.mode = "pomodoro"

        self.elapsed = 0.0
        self.start_time = 0.0

        self.pomo_target = 3600


# =========================
# 工具函数
# =========================

def fmt(s):
    s = int(s)
    return f"{s//60:02d}:{s%60:02d}"


# =========================
# 主程序
# =========================

async def main(page: ft.Page):

    db = DataManager()
    st = AppState()

    # ========= UI =========
    lbl_time = ft.Text("60:00", size=60, weight=ft.FontWeight.BOLD)
    lbl_state = ft.Text("IDLE", color="gray")
    quote = ft.Text(random.choice(ENCOURAGEMENTS))

    sel_subject = ft.Dropdown(
        options=[ft.dropdown.Option(x) for x in db.data["subjects"]],
        value=db.data["currentSubject"]
    )

    sel_pomo = ft.Dropdown(
        options=[ft.dropdown.Option(str(x)) for x in [15,25,35,45,60,90,120]],
        value="60"
    )

    # =========================
    # 核心控制器（Enterprise级）
    # =========================

    def can_edit():
        return st.state == State.IDLE

    def sync_ui():
        if st.mode == "pomodoro":
            remain = max(0, st.pomo_target - st.elapsed)
            lbl_time.value = fmt(remain)
        else:
            lbl_time.value = fmt(st.elapsed)

        lbl_state.value = st.state.upper()
        page.update()

    # -------------------------
    # start
    # -------------------------
    def start(e):
        if st.state == State.IDLE:
            st.state = State.RUNNING
            st.start_time = time.time() - st.elapsed

        elif st.state == State.PAUSED:
            st.state = State.RUNNING
            st.start_time = time.time() - st.elapsed

        sync_ui()

    # -------------------------
    # pause/resume
    # -------------------------
    def toggle(e):
        if st.state == State.RUNNING:
            st.state = State.PAUSED
            st.elapsed = time.time() - st.start_time

        elif st.state == State.PAUSED:
            st.state = State.RUNNING
            st.start_time = time.time() - st.elapsed

        sync_ui()

    # -------------------------
    # stop（统一出口）
    # -------------------------
    def stop(e):
        if st.state == State.IDLE:
            return

        if st.state == State.RUNNING:
            st.elapsed = time.time() - st.start_time

        db.add(
            sel_subject.value,
            int(st.elapsed),
            st.mode
        )

        st.state = State.IDLE
        st.elapsed = 0

        sync_ui()

    # -------------------------
    # mode switch（锁死）
    # -------------------------
    def switch_mode(m):
        if not can_edit():
            return

        st.mode = m
        st.elapsed = 0
        sync_ui()

    # -------------------------
    # timer service（稳定心跳）
    # -------------------------
    async def loop():
        while True:
            await asyncio.sleep(0.3)

            if st.state == State.RUNNING:
                st.elapsed = time.time() - st.start_time

                if st.mode == "pomodoro" and st.elapsed >= st.pomo_target:
                    stop(None)

            sync_ui()

    # =========================
    # UI
    # =========================

    btn_start = ft.ElevatedButton("开始/暂停", on_click=toggle)
    btn_stop = ft.ElevatedButton("结束", on_click=stop, bgcolor="red", color="white")

    page.add(
        ft.Column([
            lbl_state,
            lbl_time,
            quote,
            sel_subject,
            sel_pomo,
            ft.Row([btn_start, btn_stop])
        ])
    )

    page.run_task(loop)


if __name__ == "__main__":
    ft.app(target=main)
