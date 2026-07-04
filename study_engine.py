import flet as ft
import json
import os
import sys
import time
import threading
import random
import traceback
from datetime import datetime, timedelta

# ================= 1. 核心数据管理 =================
def format_dur(seconds):
    s = max(0, int(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0: return f"{h}h {m}m"
    if m > 0: return f"{m}m {sec}s"
    return f"{sec}s"

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

# ================= 2. 主逻辑 =================
def main(page: ft.Page):
    # 配置
    db = DataManager(os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__), "study_data.json"))
    page.title = "冲刺备考引擎"
    page.theme_mode = ft.ThemeMode.SYSTEM
    
    # 容器：防止排版崩坏
    main_col = ft.Column(expand=True, scroll=ft.ScrollMode.ADAPTIVE)
    
    # 状态
    st = {"active": False, "elapsed": 0, "start_tick": 0}

    # 简单的组件构建 (使用最稳健的写法)
    timer_text = ft.Text("25:00", size=60, weight="bold")
    
    # 💡 核心修复：彻底不用 tab_content 和 tabs 参数
    t = ft.Tabs(selected_index=0)
    
    # 构建 Tab 内容
    focus_tab = ft.Column([ft.Text("专注时间", size=20), timer_text])
    forest_tab = ft.Column([ft.Text("图鉴面板")])
    
    # 用 append 添加 Tab，避开构造函数参数冲突
    t.tabs.append(ft.Tab(text="专注", content=focus_tab))
    t.tabs.append(ft.Tab(text="图鉴", content=forest_tab))
    
    main_col.controls.append(t)
    page.add(main_col)

# ================= 3. 入口 =================
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception:
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
