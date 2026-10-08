# Smart Study Planner

A Streamlit app that turns **subjects, exam dates and daily study hours** into a
**day-by-day revision timetable** with a progress checklist.

## Features
- Add subjects with exam date, difficulty (Easy / Medium / Hard) and total hours you want to study
- Set hours available per day, a start date and an optional weekly rest day
- Automatic timetable: harder subjects and closer exams get more time
- Exam days are marked; no studying is scheduled for a subject after its exam
- Warning when the requested hours cannot fit before an exam
- Progress checklist: overall progress bar plus a per-subject breakdown
- Data saved to `planner_data.json`, so progress survives a restart
- Download the timetable as CSV

## How the scheduling works
Each day is split into 30-minute blocks. For every block, each subject (exam still ahead,
hours still left) gets a score:

```
score = (difficulty × hours_remaining ÷ days_left) ÷ (1 + hours_given_today)
```

- `hours_remaining ÷ days_left` is the pace needed to finish in time (urgency)
- `difficulty` weights harder subjects higher
- `1 + hours_given_today` stops one subject taking the whole day

The block goes to the highest score. Repeat for every block of every day until the last exam.

## Project structure
| File | Purpose |
|---|---|
| `planner_logic.py` | Scheduling logic (loops and date handling), no UI |
| `app.py` | Streamlit interface |
| `test_planner.py` | Tests for the logic |

## Run
```
pip3 install streamlit
streamlit run app.py
```
Run the tests with `python3 test_planner.py`.

## Possible extensions
- Browser or email reminders for today's tasks
- Split each subject into chapters or topics
- Spaced-repetition revision sessions before the exam