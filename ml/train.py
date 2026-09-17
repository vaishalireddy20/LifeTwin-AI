import sqlite3
from pathlib import Path
import pandas as pd
from ml.model import train_behavior_model,train_progress_model,train_drift_model

DB = Path(__file__).resolve().parent.parent/"instance"/"lifetwin.db"

if __name__ == "__main__":
    con = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM interactions WHERE user_id=1",con)
    con.close()
    train_behavior_model(df)
    train_progress_model(df)
    train_drift_model(df)
    print("LifeTwin AI models trained.")
