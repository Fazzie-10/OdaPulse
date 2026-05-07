import os
import logging
from dotenv import load_dotenv

# load_dotenv() will load variables from the .env file if it exists (Local Development).
# If the file does not exist (Cloud Deployment), it safely ignores it and 
# relies on the cloud provider's native environment variables instead.
load_dotenv()

class Config:
    # Fetch from environment (works for both local .env and cloud variables)
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

# Validation: Fail fast and explicitly if variables are missing
missing_vars = []
if not Config.BOT_TOKEN:
    missing_vars.append("BOT_TOKEN")
if not Config.SUPABASE_URL:
    missing_vars.append("SUPABASE_URL")
if not Config.SUPABASE_KEY:
    missing_vars.append("SUPABASE_KEY")

if missing_vars:
    error_msg = (
        f"CRITICAL ERROR: Missing required environment variables: {', '.join(missing_vars)}.\n"
        f"-> Local Dev: Check that your .env file exists and contains these keys.\n"
        f"-> Cloud Deploy: Ensure these are added to your project's Variables tab."
    )
    logging.error(error_msg)
    raise ValueError(error_msg)
