"""Core scheduling logic for the Smart Study Planner (no UI code here).

Keeping the logic separate from the Streamlit screen makes it easy to
test and to explain.
"""
from datetime import date, timedelta

DEFAULT_HOURS_NEEDED = 6.0


def generate_plan(subjects, hours_per_day, start, rest_weekday=None):
    """Build a day-by-day timetable.

    subjects      : list of {"name", "date" (ISO), "difficulty" (1-3), "hours_needed"}
    hours_per_day : study hours available on a normal day
    start         : first day of the plan (datetime.date)
    rest_weekday  : 0=Mon ... 6=Sun, or None for no weekly rest day

    Returns (plan, shortfall):
      plan      : list of {"date", "exams", "rest", "tasks":[{subject, hours, done}]}
      shortfall : {subject_name: hours that could not be fitted before the exam}
    """
    exam_day = {s["name"]: date.fromisoformat(s["date"]) for s in subjects}
    remaining = {s["name"]: float(s.get("hours_needed", DEFAULT_HOURS_NEEDED))
                 for s in subjects}
    diff = {s["name"]: s["difficulty"] for s in subjects}

    last_exam = max(exam_day.values())
    plan = []
    day = start

    while day <= last_exam:
        exams = [n for n, d in exam_day.items() if d == day]
        is_rest = rest_weekday is not None and day.weekday() == rest_weekday
        tasks = []

        if not is_rest:
            # still has an exam ahead AND still has hours left to study
            active = [n for n in exam_day if exam_day[n] > day and remaining[n] > 0]
            given = {n: 0.0 for n in active}

            # hours a subject MUST get today, or it can no longer finish before its exam
            must_today = {}
            for n in active:
                study_days = sum(
                    1 for k in range((exam_day[n] - day).days)
                    if rest_weekday is None or (day + timedelta(days=k)).weekday() != rest_weekday)
                must_today[n] = remaining[n] - (study_days - 1) * hours_per_day

            for _ in range(round(hours_per_day * 2)):          # 30-minute blocks
                best, best_score = None, 0.0
                for n in active:
                    if remaining[n] <= 0:
                        continue
                    days_left = (exam_day[n] - day).days
                    # hours still needed per remaining day, weighted by difficulty,
                    # reduced by what the subject already got today (fairness)
                    score = (diff[n] * remaining[n] / days_left) / (1 + given[n])
                    if given[n] < must_today[n]:
                        score += 1000                           # deadline-critical
                    if score > best_score:
                        best, best_score = n, score
                if best is None:
                    break                                       # nothing left to study
                given[best] += 0.5
                remaining[best] -= 0.5

            tasks = [{"subject": n, "hours": h, "done": False}
                     for n, h in given.items() if h > 0]

        plan.append({"date": day.isoformat(), "exams": exams,
                     "rest": is_rest, "tasks": tasks})
        day += timedelta(days=1)

    shortfall = {n: r for n, r in remaining.items() if r > 0}
    return plan, shortfall


def totals_by_subject(plan):
    """Return {subject: (done_hours, total_hours)}."""
    out = {}
    for day in plan:
        for t in day["tasks"]:
            done, total = out.get(t["subject"], (0.0, 0.0))
            out[t["subject"]] = (done + (t["hours"] if t["done"] else 0.0),
                                 total + t["hours"])
    return out


def plan_to_csv(plan):
    """Plain CSV text of the timetable (for download)."""
    lines = ["date,subject,hours,done"]
    for day in plan:
        for e in day["exams"]:
            lines.append(f'{day["date"]},EXAM: {e},0,')
        if day["rest"]:
            lines.append(f'{day["date"]},REST DAY,0,')
        for t in day["tasks"]:
            lines.append(f'{day["date"]},{t["subject"]},{t["hours"]},{"yes" if t["done"] else "no"}')
    return "\n".join(lines)