# analytics.py
import os
import json
from datetime import datetime, timedelta
from collections import Counter

LOG_FILE = "logs/queries.jsonl"


def log_query(username, question, answer, response_time, sources):
    os.makedirs("logs", exist_ok=True)
    entry = {
        "time": datetime.now().isoformat(),
        "user": username,
        "question": question[:200],
        "answer_len": len(answer),
        "response_time": round(response_time, 2),
        "sources": sources
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def log_feedback(username, question, rating):
    os.makedirs("logs", exist_ok=True)
    entry = {
        "time": datetime.now().isoformat(),
        "user": username,
        "question": question[:100],
        "rating": rating
    }
    try:
        with open("logs/feedback.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    logs = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return logs


def get_analytics(username=None):
    logs = load_logs()
    if username:
        logs = [l for l in logs if l.get("user") == username]
    
    if not logs:
        return {
            "total": 0, "today": 0, "week": 0, "avg_response": 0,
            "total_users": 0, "top_questions": [], "top_users": [],
            "top_pdfs": [], "daily_counts": [], "hourly_counts": []
        }
    
    now = datetime.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    
    today_count = 0
    week_count = 0
    total_resp_time = 0
    users = set()
    
    for l in logs:
        try:
            t = datetime.fromisoformat(l["time"])
        except Exception:
            continue
        if t.date() == today:
            today_count += 1
        if t >= week_ago:
            week_count += 1
        total_resp_time += l.get("response_time", 0)
        users.add(l.get("user", "unknown"))
    
    avg_resp = total_resp_time / len(logs) if logs else 0
    questions = [l["question"][:60] for l in logs]
    top_q = Counter(questions).most_common(10)
    user_list = [l.get("user", "unknown") for l in logs]
    top_u = Counter(user_list).most_common(10)
    
    all_sources = []
    for l in logs:
        all_sources.extend(l.get("sources", []))
    top_p = Counter(all_sources).most_common(10)
    
    daily = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = sum(1 for l in logs if datetime.fromisoformat(l["time"]).date() == day)
        daily.append({"date": day.strftime("%m-%d"), "count": count})
    
    hourly = []
    for h in range(24):
        count = sum(1 for l in logs if datetime.fromisoformat(l["time"]).hour == h)
        hourly.append({"hour": f"{h:02d}", "count": count})
    
    return {
        "total": len(logs),
        "today": today_count,
        "week": week_count,
        "avg_response": round(avg_resp, 2),
        "total_users": len(users),
        "top_questions": top_q,
        "top_users": top_u,
        "top_pdfs": top_p,
        "daily_counts": daily,
        "hourly_counts": hourly
    }


def clear_logs():
    for f in [LOG_FILE, "logs/feedback.jsonl"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass