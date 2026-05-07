import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import Config
import feeds, db, notifier
from keep_alive import keep_alive

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ALL_SOURCES = ["PUNCH", "DAILY TRUST", "HUMANGLE", "SAHARA REPORTERS", "BBC WORLD", "PROPUBLICA"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — subscribe the user to news updates."""
    db.add_subscriber(update.effective_user.id)
    await update.message.reply_text(
        "👋 Welcome to <b>OdaPulse!</b>\n\n"
        "You are now subscribed to real-time updates from Nigerian and Foreign outlets.\n\n"
        "📰 I check sources every 60 seconds.\n"
        "Type /settings to choose exactly which news sources you want to receive.\n"
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
        "/settings — Choose your preferred news sources\n"
        "/help — Show this message",
        parse_mode='HTML'
    )


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the interactive settings menu for news sources."""
    user_id = update.effective_user.id
    user_sources = db.get_user_prefs(user_id)
    
    keyboard = []
    for source in ALL_SOURCES:
        status = "✅" if source in user_sources else "❌"
        text = f"{status} {source}"
        callback_data = f"toggle_{source}"
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ <b>News Source Settings</b>\nClick a source to turn it on or off:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings button clicks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("toggle_"):
        source_to_toggle = data.replace("toggle_", "")
        current_sources = db.get_user_prefs(user_id)
        
        if source_to_toggle in current_sources:
            current_sources.remove(source_to_toggle)
        else:
            current_sources.append(source_to_toggle)
            
        db.update_user_prefs(user_id, current_sources)
        
        # Re-build keyboard with updated statuses
        keyboard = []
        for source in ALL_SOURCES:
            status = "✅" if source in current_sources else "❌"
            text = f"{status} {source}"
            callback_data = f"toggle_{source}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="⚙️ <b>News Source Settings</b>\nClick a source to turn it on or off:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


async def silent_startup_poll(context: ContextTypes.DEFAULT_TYPE):
    """Fetch articles and save them without broadcasting to prevent old news bursts."""
    try:
        articles = feeds.fetch_latest_articles()
        all_links = [art['link'] for art in articles if art.get('link')]
        new_links = db.filter_new_articles(all_links)
        
        for art in articles:
            if art['link'] in new_links:
                db.save_article(art['link'])
                
        logger.info(f"Silent startup complete. Pre-warmed {len(new_links)} articles.")
    except Exception as e:
        logger.error(f"Silent startup failed: {e}")


async def check_feeds(context: ContextTypes.DEFAULT_TYPE):
    """Background job: fetch new articles and broadcast to subscribers based on preferences."""
    try:
        articles = feeds.fetch_latest_articles()
        subs_with_prefs = db.get_subscribers_with_prefs()

        if not articles or not subs_with_prefs:
            return

        all_links = [art['link'] for art in articles if art.get('link')]
        new_links = db.filter_new_articles(all_links)

        for art in articles:
            if art['link'] in new_links:
                msg = notifier.format_message(art)
                for user_id, user_sources in subs_with_prefs.items():
                    # Only send if user is subscribed to this specific source
                    if art['name'] in user_sources:
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
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Background Tasks
    job_queue = app.job_queue
    # Run a silent poll immediately at startup (when=0) to prevent old news bursts
    job_queue.run_once(silent_startup_poll, when=0)
    
    # Start regular broadcast polling 10 seconds later
    job_queue.run_repeating(check_feeds, interval=Config.POLL_INTERVAL, first=10)
    
    midnight = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)
    job_queue.run_daily(periodic_cleanup, time=midnight)  # Runs once per day at midnight UTC

    print("OdaPulse Bot is Live...")
    app.run_polling()


if __name__ == "__main__":
    main()
