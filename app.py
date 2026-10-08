"""Smart Study Planner - Streamlit UI.

Run:
    pip3 install streamlit
    streamlit run app.py
"""
import json
import os
from datetime import date, timedelta

import streamlit as st

from planner_logic import (DEFAULT_HOURS_NEEDED, generate_plan, plan_to_csv,
                           totals_by_subject)

DATA_FILE = "planner_data.json"
DIFFICULTY = {"Easy": 1, "Medium": 2, "Hard": 3}
DIFF_NAME = {v: k for k, v in DIFFICULTY.items()}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ---------- storage ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"subjects": [], "plan": [], "shortfall": {}}


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"subjects": st.session_state.subjects,
                   "plan": st.session_state.plan,
                   "shortfall": st.session_state.shortfall}, f, indent=2)


st.set_page_config(page_title="Smart Study Planner", page_icon="📚", layout="centered")
st.title("📚 Smart Study Planner")
st.caption("Subjects + exam dates + hours per day → a day-by-day revision timetable with a progress checklist.")

if "subjects" not in st.session_state:
    data = load_data()
    st.session_state.subjects = data["subjects"]
    st.session_state.plan = data["plan"]
    st.session_state.shortfall = data.get("shortfall", {})

# ---------- 1. subjects ----------
st.header("1. Subjects")
with st.form("add_subject", clear_on_submit=True):
    c1, c2 = st.columns([3, 2])
    name = c1.text_input("Subject name")
    exam_date = c2.date_input("Exam date", value=date.today() + timedelta(days=7))
    c3, c4 = st.columns(2)
    diff = c3.selectbox("Difficulty", list(DIFFICULTY), index=1)
    need = c4.number_input("Total hours you want to study", min_value=0.5,
                           max_value=200.0, value=DEFAULT_HOURS_NEEDED, step=0.5)
    if st.form_submit_button("Add subject"):
        if not name.strip():
            st.warning("Enter a subject name.")
        elif exam_date <= date.today():
            st.warning("Exam date must be after today.")
        elif any(s["name"].lower() == name.strip().lower() for s in st.session_state.subjects):
            st.warning("That subject is already added.")
        else:
            st.session_state.subjects.append(
                {"name": name.strip(), "date": exam_date.isoformat(),
                 "difficulty": DIFFICULTY[diff], "hours_needed": need})
            save_data()
            st.rerun()

for i, s in enumerate(st.session_state.subjects):
    c1, c2 = st.columns([6, 1])
    c1.write(f"**{s['name']}** · {DIFF_NAME[s['difficulty']]} · "
             f"{s.get('hours_needed', DEFAULT_HOURS_NEEDED)} h needed · exam {s['date']}")
    if c2.button("✕", key=f"rm{i}", help="Remove subject"):
        st.session_state.subjects.pop(i)
        save_data()
        st.rerun()

# ---------- 2. availability ----------
st.header("2. Availability")
c1, c2, c3 = st.columns(3)
hours = c1.number_input("Hours per day", min_value=0.5, max_value=16.0, value=4.0, step=0.5)
start = c2.date_input("Start date", value=date.today())
rest_choice = c3.selectbox("Weekly rest day", ["None"] + WEEKDAYS)
rest_weekday = None if rest_choice == "None" else WEEKDAYS.index(rest_choice)

b1, b2 = st.columns(2)
if b1.button("Generate timetable", type="primary", use_container_width=True):
    subs = st.session_state.subjects
    if not subs:
        st.error("Add at least one subject first.")
    elif start >= max(date.fromisoformat(s["date"]) for s in subs):
        st.error("Start date must be before the last exam.")
    else:
        plan, shortfall = generate_plan(subs, hours, start, rest_weekday)
        st.session_state.plan, st.session_state.shortfall = plan, shortfall
        save_data()
        st.rerun()
if b2.button("Clear everything", use_container_width=True):
    st.session_state.subjects, st.session_state.plan, st.session_state.shortfall = [], [], {}
    save_data()
    st.rerun()

# ---------- 3. results ----------
if st.session_state.plan:
    # warning if the plan can't fit all requested hours
    for subj, missing in st.session_state.shortfall.items():
        st.warning(f"⚠️ **{subj}**: {missing:g} h could not be fitted before the exam. "
                   "Increase hours per day, start earlier, drop the rest day, "
                   "or lower this subject's target.")

    st.header("Progress")
    progress_slot = st.empty()
    breakdown_slot = st.container()

    st.header("Timetable")
    today = date.today().isoformat()
    for d_idx, day in enumerate(st.session_state.plan):
        label = date.fromisoformat(day["date"]).strftime("%a, %d %b %Y")
        if day["date"] == today:
            label += "  (today)"
        if day["rest"]:
            label += "  · rest"
        with st.expander(label, expanded=(day["date"] >= today and d_idx < 7)):
            for exam in day["exams"]:
                st.error(f"📝 Exam: {exam}")
            if day["rest"]:
                st.caption("😴 Rest day")
            elif not day["tasks"] and not day["exams"]:
                st.caption("Free day")
            for t_idx, task in enumerate(day["tasks"]):
                checked = st.checkbox(f"{task['subject']} — {task['hours']:g} h",
                                      value=task["done"], key=f"t{d_idx}_{t_idx}")
                if checked != task["done"]:
                    task["done"] = checked
                    save_data()

    # progress is computed after the checkboxes so it is always up to date
    per_subject = totals_by_subject(st.session_state.plan)
    total = sum(t for _, t in per_subject.values())
    done = sum(d for d, _ in per_subject.values())
    pct = done / total if total else 0
    progress_slot.progress(pct, text=f"{done:g} of {total:g} study hours completed ({pct:.0%})")
    with breakdown_slot:
        for subj, (d, t) in per_subject.items():
            st.progress(d / t if t else 0, text=f"{subj}: {d:g} / {t:g} h")

    st.download_button("⬇️ Download timetable (CSV)", plan_to_csv(st.session_state.plan),
                       file_name="study_timetable.csv", mime="text/csv")