import pandas as pd
from datetime import datetime, timedelta
import tzlocal

CSV_PATH = "charger_history.csv"

def fmt(td: timedelta) -> str:
    """Format a timedelta as Hh Mm (no seconds)."""
    total_minutes = int(td.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"


def load_data():
    df = pd.read_csv(CSV_PATH)

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", utc=True)

    local_tz = tzlocal.get_localzone()
    df["timestamp"] = df["timestamp"].dt.tz_convert(local_tz)

    df = df[~df["status"].str.startswith("Unknown")]

    df = df.sort_values(["charger_id", "timestamp"])
    return df


# ------------------------------------------------------------
# Extract complete Charging → Available sessions
# ------------------------------------------------------------
def extract_sessions(df):
    sessions = []

    for charger_id, group in df.groupby("charger_id"):
        group = group.sort_values("timestamp")
        start_time = None

        for _, row in group.iterrows():
            if row["status"] == "Charging":
                start_time = row["timestamp"]

            elif row["status"] == "Available" and start_time is not None:
                end_time = row["timestamp"]
                duration = end_time - start_time

                sessions.append({
                    "charger_id": charger_id,
                    "start": start_time,
                    "end": end_time,
                    "duration": duration
                })

                start_time = None

    return pd.DataFrame(sessions)

def compute_current_sessions(df):
    local_tz = tzlocal.get_localzone()
    now = datetime.now(local_tz)

    current = {}

    for charger_id, group in df.groupby("charger_id"):
        last = group.sort_values("timestamp").iloc[-1]

        if last["status"] == "Charging":
            current[charger_id] = now - last["timestamp"]
        else:
            current[charger_id] = None

    return current


def estimate_eta(avg_durations, current_sessions):
    local_tz = tzlocal.get_localzone()
    now = datetime.now(local_tz)

    eta = {}

    for charger_id in avg_durations.index:
        avg = avg_durations.loc[charger_id]
        current = current_sessions[charger_id]

        if current is None:
            eta[charger_id] = None
            continue

        remaining = avg - current
        eta[charger_id] = now + remaining if remaining > timedelta(0) else now

    return eta

def calculate_daily_usage(sessions):
    sessions["date"] = sessions["start"].dt.date
    sessions["weekday"] = sessions["start"].dt.day_name()
    sessions["hours"] = sessions["duration"].dt.total_seconds() / 3600

    daily = sessions.groupby(["charger_id", "date", "weekday"])["hours"].sum()

    print("\n=== Daily Charging Hours (hours only) ===")
    for (charger_id, date, weekday), hours in daily.items():
        print(f"{weekday} {date} — Charger {charger_id}: {hours:.2f} hours")

    return daily

def main():
    df = load_data()
    sessions = extract_sessions(df)

    if sessions.empty:
        print("No complete sessions found.")
        return

    # Average duration per charger
    avg_durations = sessions.groupby("charger_id")["duration"].mean()

    # Current session lengths
    current_sessions = compute_current_sessions(df)

    # ETA until available
    eta = estimate_eta(avg_durations, current_sessions)

    print("\n=== Average Charging Duration ===")
    for cid, avg in avg_durations.items():
        print(f"Charger {cid}: {fmt(avg)}")

    print("\n=== Current Session Length ===")
    for cid, cur in current_sessions.items():
        if cur is None:
            print(f"Charger {cid}: Not currently charging")
        else:
            print(f"Charger {cid}: {fmt(cur)}")

    print("\n=== ETA Until Available ===")
    for cid, t in eta.items():
        if t is None:
            print(f"Charger {cid}: Already available")
        else:
            print(f"Charger {cid}: {t.strftime('%Y-%m-%d %H:%M')}")

    calculate_daily_usage(sessions)


if __name__ == "__main__":
    main()
