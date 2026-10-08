"""Simple tests. Run with:  python3 test_planner.py"""
from datetime import date
from planner_logic import generate_plan, totals_by_subject

START = date(2026, 10, 7)  # Wednesday


def hours(plan, subject):
    return sum(t["hours"] for d in plan for t in d["tasks"] if t["subject"] == subject)


def test_no_study_on_or_after_exam_day():
    subs = [{"name": "DS", "date": "2026-10-09", "difficulty": 3, "hours_needed": 6}]
    plan, _ = generate_plan(subs, 4, START)
    for d in plan:
        if d["date"] >= "2026-10-09":
            assert d["tasks"] == [], d


def test_never_exceeds_hours_needed():
    subs = [{"name": "Maths", "date": "2026-10-20", "difficulty": 2, "hours_needed": 5}]
    plan, short = generate_plan(subs, 4, START)
    assert hours(plan, "Maths") == 5 and short == {}


def test_daily_hours_not_exceeded():
    subs = [{"name": "A", "date": "2026-10-15", "difficulty": 3, "hours_needed": 30},
            {"name": "B", "date": "2026-10-16", "difficulty": 2, "hours_needed": 30}]
    plan, _ = generate_plan(subs, 4, START)
    for d in plan:
        assert sum(t["hours"] for t in d["tasks"]) <= 4


def test_shortfall_reported_when_time_is_too_short():
    subs = [{"name": "OS", "date": "2026-10-09", "difficulty": 3, "hours_needed": 20}]
    plan, short = generate_plan(subs, 4, START)       # only 7 Oct + 8 Oct = 8 h
    assert short == {"OS": 12.0}


def test_rest_day_has_no_tasks():
    subs = [{"name": "A", "date": "2026-10-14", "difficulty": 2, "hours_needed": 10}]
    plan, _ = generate_plan(subs, 4, START, rest_weekday=6)   # Sunday = 11 Oct
    sunday = next(d for d in plan if d["date"] == "2026-10-11")
    assert sunday["rest"] and sunday["tasks"] == []


def test_harder_and_closer_exam_gets_more_time_on_day_one():
    subs = [{"name": "DS", "date": "2026-10-09", "difficulty": 3, "hours_needed": 8},
            {"name": "Maths", "date": "2026-10-12", "difficulty": 2, "hours_needed": 8}]
    plan, _ = generate_plan(subs, 4, START)
    day1 = {t["subject"]: t["hours"] for t in plan[0]["tasks"]}
    assert day1["DS"] > day1.get("Maths", 0)


def test_feasible_plan_has_no_shortfall():
    # DS needs 6 h and has exactly 8 h before its exam; Maths must not steal that time
    subs = [{"name": "DS", "date": "2026-10-09", "difficulty": 3, "hours_needed": 6},
            {"name": "Maths", "date": "2026-10-14", "difficulty": 2, "hours_needed": 10},
            {"name": "DBMS", "date": "2026-10-16", "difficulty": 1, "hours_needed": 8}]
    plan, short = generate_plan(subs, 4, START, rest_weekday=6)
    assert short == {}, short
    assert hours(plan, "DS") == 6


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"\nAll {len(tests)} tests passed.")