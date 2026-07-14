import logging
from datetime import datetime, timezone, timedelta
from db import supabase

logger = logging.getLogger(__name__)

def get_due_users(current_hour):
    res = supabase.table("subscribers").select("*").execute()
    due = []
    for row in res.data:
        delivery_time = row.get("delivery_time", "08:00")
        try:
            hour = int(delivery_time.split(":")[0])
        except (ValueError, IndexError):
            hour = 8

        if hour != current_hour:
            continue

        last_sent = row.get("last_digest_sent")
        if last_sent:
            last = datetime.fromisoformat(last_sent.replace("Z", "+00:00"))
            freq = row.get("delivery_frequency", "daily")
            window = timedelta(hours=23) if freq == "daily" else timedelta(days=6)
            if datetime.now(timezone.utc) - last < window:
                continue

        due.append({
            "user_id": row["user_id"],
            "delivery_frequency": row.get("delivery_frequency", "daily"),
            "delivery_channel": row.get("delivery_channel", "telegram"),
            "email": row.get("email", ""),
            "interest_tags": row.get("interest_tags", []),
        })
    return due

def mark_digest_sent(user_id):
    supabase.table("subscribers").update(
        {"last_digest_sent": datetime.now(timezone.utc).isoformat()}
    ).eq("user_id", user_id).execute()
