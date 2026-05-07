import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config
import feeds, db, notifier
from keep_alive import keep_alive
import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — subscribe the user to news updates."""
    db.add_subscriber(update.effective_user.id)
    await update.message.reply_text(
        "👋 Welcome to <b>OdaPulse!</b>\n\n"
        "You are now subscribed to real-time updates from Nigerian and Foreign outlets.\n\n"
        "📰 I check sources every 60 seconds.\n"
        "Type /help to see all commands.",
        parse_mode='HTML'
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command — unsubscribe the user from news updates."""
    db.remove_subscriber(update.effective_user.id)
    await update.message.reply_text(
        "👋 You've been unsubscribed from OdaPulse.\n\n"
        "Send /start anytime to re-subscribe.",
        parse_mode='HTML'
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command — show available commands."""
    await update.message.reply_text(
        "📖 <b>OdaPulse — Commands</b>\n\n"
        "/start — Subscribe to news updates\n"
        "/stop — Unsubscribe from updates\n"
        "/help — Show this message\n\n"
        "🇳🇬 <b>Nigerian Sources:</b> Punch, Daily Trust, HumAngle, Sahara Reporters\n"
        "🌍 <b>International:</b> BBC World, ProPublica",
        parse_mode='HTML'
    )


async def check_feeds(context: ContextTypes.DEFAULT_TYPE):
    """Background job: fetch new articles and broadcast to all subscribers."""
    try:
        articles = feeds.fetch_latest_articles()
        subs = db.get_subscribers()

        if not articles or not subs:
            return

        # Batch dedup: 1 DB call instead of 30
        all_links = [art['link'] for art in articles if art.get('link')]
        new_links = db.filter_new_articles(all_links)

        for art in articles:
            if art['link'] in new_links:
                msg = notifier.format_message(art)
                for user_id in subs:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=msg,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send to {user_id}: {e}")
                        continue
                db.save_article(art['link'])

    except Exception as e:
        logger.error(f"Feed check cycle failed: {e}")


async def periodic_cleanup(context: ContextTypes.DEFAULT_TYPE):
    """Run daily cleanup of old seen_articles entries."""
    db.cleanup_old_articles(days=7)


def main():
    keep_alive()  # Start the background web server for Render
    app = Application.builder().token(Config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))

    # Background Tasks
    job_queue = app.job_queue
    job_queue.run_repeating(check_feeds, interval=Config.POLL_INTERVAL, first=10)
    midnight = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)
    job_queue.run_daily(periodic_cleanup, time=midnight)  # Runs once per day at midnight UTC

    print("OdaPulse Bot is Live...")
    app.run_polling()


if __name__ == "__main__":
    main()
