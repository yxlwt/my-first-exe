import flet as ft
import json
import os
import sys
import time
import threading
import random
import traceback
from datetime import datetime, timedelta

# ================= 1. 初始化与数据管理 =================
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(application_path, "study_data.json")

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
    if s >= 3600:
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"
    return f"{(s%3600)//60:02d}:{s%60:02d}"

# 💡 核心防御黑科技：我们自己手搓一个“绝对安全”的按钮，不用官方的 Button！
def create_btn(text, on_click=None, bgcolor="transparent", txt_color="#1C1C1E", radius=8, expand=False, height=None, padding=10):
    lbl = ft.Text(value=text, color=txt_color, weight="bold")
    cnt = ft.Container(
        content=ft.Row([lbl], alignment="center"),
        bgcolor=bgcolor,
        border_radius=radius,
        padding=padding,
        on_click=on_click,
        expand=expand,
        height=height
    )
    return cnt, lbl

# ================= 3. 核心无极 UI 引擎 =================
def main(page: ft.Page):
    db = DataManager(DATA_FILE)
    page.title = "冲刺备考引擎"
    page.bgcolor = "#F4F5F7" 
    page.padding = 15
    page.theme_mode = "system"
    page.scroll = "adaptive"
    
    try:
        page.window.width = 460
        page.window.height = 800
        page.window.min_width = 350
    except AttributeError: pass

    class State:
        timer_active = False
        mode = "pomodoro"
        pomo_target = 25 * 60
        elapsed = 0
        start_tick = 0
        forest_scope = "day"
        stats_scope = "day"

    st = State()

    # ----------------- 顶部倒计时看板 -----------------
    countdown_text = ft.Text(value="距离初试仅剩 -- 天", size=18, weight="bold", color="#007AFF")
    try:
        today = datetime.now().date()
        exam = datetime.strptime(db.data["examDate"], "%Y-%m-%d").date()
        diff = (exam - today).days
        countdown_text.value = f"距离初试仅剩 {diff} 天"
        countdown_text.color = "#FF3B30" if diff < 150 else "#007AFF"
    except: pass

    card_countdown = ft.Container(
        content=ft.Row([countdown_text], alignment="center"),
        bgcolor="white", border_radius=15, padding=15, margin=10
    )

    # ----------------- 自定义防崩溃导航栏 -----------------
    nav_buttons = []
    
    def switch_main_tab(index):
        for i, item in enumerate(nav_buttons):
            item["view"].bgcolor = "#1C1C1E" if i == index else "transparent"
            item["lbl"].color = "white" if i == index else "#8E8E93"
        
        view_focus.visible = (index == 0)
        view_forest.visible = (index == 1)
        view_stats.visible = (index == 2)
        view_settings.visible = (index == 3)
        
        if index == 1: refresh_forest()
        if index == 2: refresh_stats()
        page.update()

    def make_nav_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: switch_main_tab(i), txt_color="#8E8E93", radius=10, expand=True, padding=8)
        nav_buttons.append({"view": view, "lbl": lbl})
        return view

    nav_bar = ft.Container(
        content=ft.Row([
            make_nav_btn("专注", 0),
            make_nav_btn("图鉴", 1),
            make_nav_btn("统计", 2),
            make_nav_btn("设置", 3)
        ], alignment="center", spacing=5),
        bgcolor="white", border_radius=15, padding=5, margin=10
    )

    # ----------------- 专注视图 (0) -----------------
    lbl_icon = ft.Text(value="🌰", size=90)
    lbl_time = ft.Text(value="25:00", size=70, weight="bold")
    lbl_quote = ft.Text(value="乾坤未定，你我皆是黑马。", size=13, color="#8E8E93")
    
    # Dropdown 也是安全的
    sel_subject = ft.Dropdown(
        options=[ft.dropdown.Option(key=s) for s in db.data["subjects"]],
        value=db.data["currentSubject"],
        width=150, border_radius=10, border_color="#D1D1D6"
    )
    def on_sub_change(e):
        db.data["currentSubject"] = sel_subject.value
        db.save()
    sel_subject.on_change = on_sub_change

    bar_goal = ft.ProgressBar(value=0, color="#34C759", bgcolor="#E5E5EA", height=8)
    lbl_goal = ft.Text(value="今日进度: 0 / 6h", size=12, color="#8E8E93", weight="bold")

    mode_sw_view, mode_sw_lbl = create_btn("🧱 正向筑城", radius=10, expand=True, txt_color="#8E8E93", on_click=lambda e: switch_mode("stopwatch"))
    mode_pm_view, mode_pm_lbl = create_btn("🌱 番茄种树", radius=10, expand=True, bgcolor="#E5E5EA", on_click=lambda e: switch_mode("pomodoro"))

    def switch_mode(m):
        if st.timer_active: return
        st.mode = m
        mode_sw_view.bgcolor = "#E5E5EA" if m == "stopwatch" else "transparent"
        mode_sw_lbl.color = "#1C1C1E" if m == "stopwatch" else "#8E8E93"
        mode_pm_view.bgcolor = "#E5E5EA" if m == "pomodoro" else "transparent"
        mode_pm_lbl.color = "#1C1C1E" if m == "pomodoro" else "#8E8E93"
        sel_pomo.disabled = (m == "stopwatch")
        st.elapsed = 0
        update_focus_ui()
    
    sel_pomo = ft.Dropdown(
        options=[ft.dropdown.Option(key=f"{m}分钟") for m in [15, 25, 35, 45, 60, 90]],
        value="25分钟", width=120, border_radius=10, border_color="#D1D1D6"
    )
    def on_pomo_change(e):
        if st.timer_active: return
        st.pomo_target = int(sel_pomo.value.replace("分钟", "")) * 60
        st.elapsed = 0
        update_focus_ui()
    sel_pomo.on_change = on_pomo_change

    # 用手搓容器替代按钮
    btn_start_view, btn_start_lbl = create_btn("▶ 开始专注", bgcolor="#34C759", txt_color="white", radius=22, height=45, expand=True)
    btn_stop_view, btn_stop_lbl = create_btn("⏹ 结束", bgcolor="#F4F5F7", txt_color="#8E8E93", radius=22, height=45, expand=True)

    def toggle_timer(e):
        if not st.timer_active:
            st.timer_active = True
            st.start_tick = time.time() - st.elapsed
            btn_start_lbl.value = "⏸ 暂停"
            btn_start_view.bgcolor = "#FF9500"
            btn_stop_view.on_click = stop_timer # 激活结束按钮
            btn_stop_view.bgcolor = "#FF3B30"
            btn_stop_lbl.color = "white"
            sel_subject.disabled = True
        else:
            st.timer_active = False
            btn_start_lbl.value = "▶ 继续专注"
            btn_start_view.bgcolor = "#34C759"
        page.update()
    
    btn_start_view.on_click = toggle_timer

    def stop_timer(e):
        if st.mode == "pomodoro" and st.elapsed < st.pomo_target:
            msg = "番茄钟未完成，放弃将留下枯树 🥀，确定吗？" if st.elapsed >= 60 else "不足 1 分钟，放弃不留记录。"
        elif st.mode == "stopwatch" and st.elapsed < 60:
            msg = "筑城不足 1 分钟，只留下废料 🚧。确定保存吗？"
        else:
            finish_and_save()
            return

        def on_confirm(save_dead):
            dlg.open = False
            page.update()
            if save_dead: finish_and_save(is_dead=True)
            else: reset_timer()

        btn_y, _ = create_btn("是 (保存)", txt_color="white", bgcolor="#FF3B30", on_click=lambda e: on_confirm(True))
        btn_n, _ = create_btn("否 (销毁)", bgcolor="#F4F5F7", on_click=lambda e: on_confirm(False))

        dlg = ft.AlertDialog(
            title=ft.Text(value="确认结束", weight="bold"),
            content=ft.Text(value=msg),
            actions=[btn_y, btn_n]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def finish_and_save(is_dead=False):
        if st.elapsed < 60:
            db.add_record(sel_subject.value, st.elapsed, st.mode, is_dead, "")
            reset_timer()
            return
            
        txt_note = ft.TextField(label="复盘便签 (选填)", border_color="#D1D1D6")
        def on_save(e):
            dlg.open = False
            db.add_record(sel_subject.value, st.elapsed, st.mode, is_dead, txt_note.value)
            reset_timer()
            page.update()

        btn_save, _ = create_btn("保存战果", bgcolor="#34C759", txt_color="white", on_click=on_save)

        dlg = ft.AlertDialog(
            title=ft.Text(value="专注完成！", weight="bold"),
            content=txt_note,
            actions=[btn_save]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def reset_timer():
        st.timer_active = False
        st.elapsed = 0
        btn_start_lbl.value = "▶ 开始专注"
        btn_start_view.bgcolor = "#34C759"
        btn_stop_view.on_click = None
        btn_stop_view.bgcolor = "#F4F5F7"
        btn_stop_lbl.color = "#8E8E93"
        sel_subject.disabled = False
        update_focus_ui()

    view_focus = ft.Container(
        content=ft.Column([
            ft.Row([sel_subject], alignment="center"),
            ft.Container(height=5),
            ft.Row([lbl_icon], alignment="center"),
            ft.Row([lbl_time], alignment="center"),
            ft.Row([lbl_quote], alignment="center"),
            ft.Container(height=10),
            ft.Column([lbl_goal, bar_goal], spacing=5),
            ft.Container(height=10),
            ft.Row([mode_sw_view, mode_pm_view], alignment="center"),
            ft.Row([sel_pomo], alignment="center"),
            ft.Container(height=10),
            ft.Row([btn_start_view, btn_stop_view], alignment="center", spacing=15)
        ]),
        bgcolor="white", border_radius=15, padding=20, expand=True
    )

    def update_focus_ui():
        if st.mode == "pomodoro":
            remain = st.pomo_target - st.elapsed
            if remain <= 0:
                lbl_time.value = "00:00"
                lbl_icon.value = "🌲"
            else:
                lbl_time.value = format_time(remain)
                prog = st.elapsed / st.pomo_target
                lbl_icon.value = "🌳" if prog >= 0.66 else "🌿" if prog >= 0.33 else "🌱" if st.elapsed >= 60 else "🌰"
        else:
            lbl_time.value = format_time(st.elapsed)
            if st.elapsed >= 3600: lbl_icon.value = "🏰"
            elif st.elapsed >= 1800: lbl_icon.value = "🏠"
            elif st.elapsed >= 60: lbl_icon.value = "🧱"
            else: lbl_icon.value = "🚧"

        logical_today = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d")
        records = [item for item in db.data["studyData"] if item.get("date") == logical_today]
        total = sum(r["duration"] for r in records) + (st.elapsed if st.timer_active else 0)
        goal = db.data["dailyGoal"]
        
        lbl_goal.value = f"🎯 今日进度: {format_dur(total)} / {format_dur(goal)}"
        bar_goal.value = min(total / goal, 1.0)
        page.update()

    # ----------------- 图鉴视图 (1) -----------------
    lbl_forest_sum = ft.Text(value="共收获 0 个战果", weight="bold", color="#8E8E93")
    grid_forest = ft.Row(wrap=True, spacing=15, run_spacing=15)
    
    forest_nav_btns = []
    def sw_forest(idx):
        for i, item in enumerate(forest_nav_btns):
            item["view"].bgcolor = "#1C1C1E" if i == idx else "transparent"
            item["lbl"].color = "white" if i == idx else "#8E8E93"
        st.forest_scope = ["day", "week", "month"][idx]
        refresh_forest()

    def make_forest_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: sw_forest(i), txt_color="#8E8E93")
        forest_nav_btns.append({"view": view, "lbl": lbl})
        return view

    row_forest_nav = ft.Row([make_forest_btn("今日", 0), make_forest_btn("本周", 1), make_forest_btn("本月", 2)], alignment="center")

    def refresh_forest():
        records = db.get_filtered(st.forest_scope)
        lbl_forest_sum.value = f"共收获 {len(records)} 个战果"
        grid_forest.controls.clear()
        if not records:
            grid_forest.controls.append(ft.Text(value="空空如也，快去专注吧 ✨", color="#8E8E93"))
        for r in records:
            tip = f"{r['subject']} | {format_dur(r['duration'])} {r.get('note','')}"
            grid_forest.controls.append(ft.Text(value=r.get("tree","🌲"), size=42, tooltip=tip))
        page.update()

    view_forest = ft.Container(
        content=ft.Column([
            row_forest_nav,
            ft.Row([lbl_forest_sum], alignment="center"),
            ft.Container(content=grid_forest, expand=True, bgcolor="#F4F5F7", padding=15, border_radius=10)
        ]),
        bgcolor="white", border_radius=15, padding=20, expand=True, visible=False
    )

    # ----------------- 统计视图 (2) -----------------
    lbl_stat_total = ft.Text(value="0s", size=42, weight="bold")
    col_stats = ft.Column(scroll="adaptive")

    stat_nav_btns = []
    def sw_stat(idx):
        for i, item in enumerate(stat_nav_btns):
            item["view"].bgcolor = "#1C1C1E" if i == idx else "transparent"
            item["lbl"].color = "white" if i == idx else "#8E8E93"
        st.stats_scope = ["day", "week", "month"][idx]
        refresh_stats()

    def make_stat_btn(text, idx):
        view, lbl = create_btn(text, on_click=lambda e, i=idx: sw_stat(i), txt_color="#8E8E93")
        stat_nav_btns.append({"view": view, "lbl": lbl})
        return view

    row_stat_nav = ft.Row([make_stat_btn("今日", 0), make_stat_btn("本周", 1), make_stat_btn("本月", 2)], alignment="center")

    def refresh_stats():
        records = db.get_filtered(st.stats_scope)
        total = sum(r["duration"] for r in records)
        lbl_stat_total.value = format_dur(total)
        
        col_stats.controls.clear()
        if not records:
            col_stats.controls.append(ft.Text(value="当前时段无专注数据", color="#8E8E93"))
        
        smap = {}
        for r in records:
            smap[r["subject"]] = smap.get(r["subject"], 0) + r["duration"]
            
        for sub, dur in sorted(smap.items(), key=lambda x: x[1], reverse=True):
            pct = dur / total if total > 0 else 0
            col_stats.controls.append(
                ft.Column([
                    ft.Row([ft.Text(value=f"{sub} ({round(pct*100,1)}%)", weight="bold"), ft.Text(value=format_dur(dur), color="#8E8E93")], alignment="spaceBetween"),
                    ft.ProgressBar(value=pct, color="#00A2FF", bgcolor="#E5E5EA", height=8, border_radius=4)
                ], spacing=5)
            )
        page.update()

    view_stats = ft.Container(
        content=ft.Column([
            row_stat_nav,
            ft.Container(content=lbl_stat_total, padding=ft.margin.only(top=10, bottom=10)),
            col_stats
        ]),
        bgcolor="white", border_radius=15, padding=20, expand=True, visible=False
    )

    # ----------------- 设置视图 (3) -----------------
    txt_goal = ft.TextField(value=str(db.data["dailyGoal"] // 3600), label="每日专注目标 (小时)", border_color="#D1D1D6")
    def on_goal_blur(e):
        try: db.data["dailyGoal"] = float(txt_goal.value) * 3600; db.save(); update_focus_ui()
        except: txt_goal.value = str(db.data["dailyGoal"] // 3600); page.update()
    txt_goal.on_blur = on_goal_blur

    col_subs = ft.Column(spacing=5)
    txt_new_sub = ft.TextField(hint_text="新科目", expand=True, border_color="#D1D1D6")

    def render_subs():
        col_subs.controls.clear()
        for sub in db.data["subjects"]:
            btn_del, _ = create_btn("删除", txt_color="red", on_click=lambda e, s=sub: del_sub(s))
            col_subs.controls.append(
                ft.Container(
                    content=ft.Row([ft.Text(value=sub, weight="bold", expand=True), btn_del]),
                    bgcolor="#F4F5F7", padding=5, border_radius=8
                )
            )
        page.update()

    def add_sub(e):
        v = txt_new_sub.value.strip()
        if v and v not in db.data["subjects"]:
            db.data["subjects"].append(v); db.save()
            sel_subject.options = [ft.dropdown.Option(key=x) for x in db.data["subjects"]]
            txt_new_sub.value = ""; render_subs()
            
    btn_add, _ = create_btn("添加", bgcolor="#34C759", txt_color="white", on_click=add_sub)

    def del_sub(s):
        if len(db.data["subjects"]) > 1:
            db.data["subjects"].remove(s); db.save()
            sel_subject.options = [ft.dropdown.Option(key=x) for x in db.data["subjects"]]
            sel_subject.value = db.data["subjects"][0]
            render_subs()

    def on_export(e):
        try:
            with open("StudyEngine_Backup.json", "w", encoding="utf-8") as f:
                json.dump(db.data, f, ensure_ascii=False, indent=4)
        except: pass

    btn_exp, _ = create_btn("⬇ 导出本地备份 (当前目录)", bgcolor="#E5E5EA", on_click=on_export)

    view_settings = ft.Container(
        content=ft.Column([
            ft.Text(value="🎯 目标设置", weight="bold"),
            txt_goal,
            ft.Divider(),
            ft.Text(value="🏷️ 科目管理", weight="bold"),
            col_subs,
            ft.Row([txt_new_sub, btn_add]),
            ft.Divider(),
            ft.Text(value="💾 数据安全", weight="bold"),
            btn_exp
        ], scroll="adaptive"),
        bgcolor="white", border_radius=15, padding=20, expand=True, visible=False
    )

    # ----------------- 组装与循环 -----------------
    page.add(
        ft.Column([
            card_countdown,
            nav_bar,
            view_focus,
            view_forest,
            view_stats,
            view_settings
        ], expand=True)
    )

    switch_main_tab(0)
    switch_mode("pomodoro")
    sw_forest(0)
    sw_stat(0)
    render_subs()

    def loop():
        while True:
            if st.timer_active:
                st.elapsed = time.time() - st.start_tick
                if st.mode == "pomodoro" and st.elapsed >= st.pomo_target:
                    st.elapsed = st.pomo_target
                    finish_and_save(is_dead=False)
                    try: import winsound; winsound.Beep(800, 500)
                    except: pass
            update_focus_ui()
            time.sleep(0.5)

    threading.Thread(target=loop, daemon=True).start()

# ================= 5. 防崩沙盒入口 =================
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception:
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
