import pandas as pd
from datetime import datetime

CSV_FILE = "charger_history.csv"

def load_data():
    df = pd.read_csv(
        "charger_history.csv",
        names=["timestamp", "charger_id", "status"],
        header=0,
        comment="#",
        skip_blank_lines=True,
        on_bad_lines="skip",
        encoding="utf-8-sig"
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    return df

def extract_sessions(df):
    sessions = []

    for charger_id, group in df.groupby("charger_id"):
        group = group.sort_values("timestamp")
        current_start = None

        for _, row in group.iterrows():
            if row["status"] == "Charging":
                current_start = row["timestamp"]

            elif row["status"] == "Available" and current_start is not None:
                duration = (row["timestamp"] - current_start).total_seconds() / 60
                sessions.append({
                    "charger_id": charger_id,
                    "start": current_start,
                    "end": row["timestamp"],
                    "duration_min": duration
                })
                current_start = None

    return pd.DataFrame(sessions)

def calculate_averages(sessions_df):
    return sessions_df.groupby("charger_id")["duration_min"].mean()

def predict(df, sessions_df, averages):
    predictions = {}

    latest = df.sort_values("timestamp").groupby("charger_id").tail(1)

    now = datetime.now()

    for _, row in latest.iterrows():
        charger_id = row["charger_id"]
        status = row["status"]

        if status == "Available":
            predictions[charger_id] = {
                "status": "Available",
                "message": "Charger is already free"
            }
            continue

        # Charger is Charging → find current session start
        last_session = sessions_df[sessions_df["charger_id"] == charger_id].iloc[-1]
        avg_duration = averages[charger_id]

        current_length = (now - last_session["start"]).total_seconds() / 60
        minutes_left = max(avg_duration - current_length, 0)

        predictions[charger_id] = {
            "status": "Charging",
            "avg_duration": avg_duration,
            "current_length": current_length,
            "minutes_left": minutes_left,
            "eta": now + pd.Timedelta(minutes=minutes_left)
        }

    return predictions

def main():
    df = load_data()
    sessions_df = extract_sessions(df)
    averages = calculate_averages(sessions_df)
    predictions = predict(df, sessions_df, averages)

    print("\n=== Charger Predictions ===\n")

    for charger_id, info in predictions.items():
        print(f"Charger {charger_id}:")

        if info["status"] == "Available":
            print("  → Already Available\n")
            continue

        print(f"  Average charge time: {info['avg_duration']:.1f} min")
        print(f"  Current session length: {info['current_length']:.1f} min")
        print(f"  Predicted minutes left: {info['minutes_left']:.1f} min")
        print(f"  ETA Available: {info['eta']}\n")

if __name__ == "__main__":
    main()