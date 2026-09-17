import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS interactions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 event_date TEXT NOT NULL,
 task_type TEXT NOT NULL,
 duration_min REAL NOT NULL,
 task_switches INTEGER NOT NULL,
 completed INTEGER NOT NULL,
 difficulty INTEGER NOT NULL,
 help_requests INTEGER NOT NULL,
 hour INTEGER NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS goals (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 title TEXT NOT NULL,
 target_date TEXT NOT NULL,
 progress REAL NOT NULL,
 status TEXT NOT NULL DEFAULT 'Active',
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS memories (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 memory_type TEXT NOT NULL,
 content TEXT NOT NULL,
 confidence REAL NOT NULL DEFAULT .7,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS predictions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 predicted TEXT NOT NULL,
 confidence REAL NOT NULL,
 actual TEXT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS feedback (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 prediction_id INTEGER,
 feedback TEXT NOT NULL,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
"""

def connect(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def init_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = connect(path)
    con.executescript(SCHEMA)
    con.commit()
    con.close()

def seed_demo(path):
    import random
    from datetime import date, timedelta
    con = connect(path)
    if con.execute("SELECT id FROM users WHERE username='demo'").fetchone():
        con.close()
        return

    uid = con.execute(
        "INSERT INTO users(username,password_hash) VALUES(?,?)",
        ("demo", generate_password_hash("demo123"))
    ).lastrowid

    goals = [
        ("Become job-ready for ML engineering","2026-12-31",.74),
        ("Complete Deep Learning specialization","2026-10-15",.60),
        ("Build and deploy an AI product","2026-11-30",.40),
    ]
    con.executemany(
        "INSERT INTO goals(user_id,title,target_date,progress) VALUES(?,?,?,?)",
        [(uid,*g) for g in goals]
    )

    memories = [
        ("learning","Prefers practical examples when learning difficult concepts.",.88),
        ("routine","Highest completion rate for analytical work between 08:00 and 11:00.",.91),
        ("productivity","Large tasks are more likely to be postponed when more than four tasks are scheduled.",.84),
        ("knowledge","Strong Python foundation; probability is a weaker prerequisite for machine learning.",.80),
        ("preference","Recent sessions show increased preference for structured, goal-oriented work.",.79),
    ]
    con.executemany(
        "INSERT INTO memories(user_id,memory_type,content,confidence) VALUES(?,?,?,?)",
        [(uid,*m) for m in memories]
    )

    rng = random.Random(42)
    tasks = ["Deep Work","Learning","Project","Admin","Revision"]
    start = date.today() - timedelta(days=89)
    rows = []
    for i in range(90):
        d = start + timedelta(days=i)
        phase = 0 if i < 55 else 1
        hour = rng.choice([8,9,10,10,11,18,19,20])
        task = rng.choices(tasks,weights=[34,30,20,10,6])[0]
        duration = max(15,rng.gauss(58 if phase == 0 else 72,16))
        switches = max(0,int(rng.gauss(3.8 if phase == 0 else 2.1,1.6)))
        difficulty = min(5,max(1,int(rng.gauss(3.1,.9))))
        help_req = max(0,int(rng.gauss(1.1 if difficulty >= 4 else .5,.8)))
        completed = int(rng.random() < max(.35,.78-switches*.035-(difficulty-3)*.03))
        rows.append((uid,d.isoformat(),task,duration,switches,completed,difficulty,help_req,hour))

    con.executemany(
        """INSERT INTO interactions
        (user_id,event_date,task_type,duration_min,task_switches,completed,difficulty,help_requests,hour)
        VALUES(?,?,?,?,?,?,?,?,?)""", rows
    )
    con.commit()
    con.close()
