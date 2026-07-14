import logging
import datetime
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import Config
import feeds, db, notifier, gdelt_search, ai_service, scheduler, emailer
from trafilatura import fetch_url, extract

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ALL_SOURCES = ["PUNCH", "DAILY TRUST", "HUMANGLE", "SAHARA REPORTERS", "BBC WORLD", "PROPUBLICA"]
ALL_TAGS = ["Politics", "Economy/Finance", "Security/Conflict", "Diaspora Policy", "Tech/Innovation", "Culture/Sports", "Health/Education"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.add_subscriber(update.effective_user.id)
    await update.message.reply_text(
        "👋 Welcome to <b>OdaPulse!</b>\n\n"
        "You are now subscribed to real-time updates from Nigerian and diaspora outlets.\n\n"
        "📰 Type /settings to choose your sources and interest topics.\n"
        "📧 Type /email your@email.com to get digests via email.\n"
        "Type /help to see all commands.",
        parse_mode='HTML'
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.remove_subscriber(update.effective_user.id)
    await update.message.reply_text(
        "👋 You've been unsubscribed from OdaPulse.\n\n"
        "Send /start anytime to re-subscribe.",
        parse_mode='HTML'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>OdaPulse — Commands</b>\n\n"
        "/start — Subscribe to news updates\n"
        "/stop — Unsubscribe from updates\n"
        "/settings — Configure sources, topics, delivery\n"
        "/email your@email.com — Set your email for digests\n"
        "/digest — Request an immediate digest\n"
        "/help — Show this message",
        parse_mode='HTML'
    )

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📰 News Sources", callback_data="menu_sources")],
        [InlineKeyboardButton("🏷️ Interest Topics", callback_data="menu_tags")],
        [InlineKeyboardButton("⏰ Delivery Time", callback_data="menu_time")],
        [InlineKeyboardButton("📬 Delivery Channel", callback_data="menu_channel")],
        [InlineKeyboardButton("📅 Frequency", callback_data="menu_frequency")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ <b>OdaPulse Settings</b>\nChoose what to configure:",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

async def email_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        prefs = db.get_user_subscriber_prefs(user_id)
        current = prefs.get("email", "") if prefs else ""
        msg = f"Current email: {current or 'Not set'}\nUsage: /email your@email.com" if current else "Usage: /email your@email.com"
        await update.message.reply_text(msg, parse_mode="HTML")
        return
    email = args[0]
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Invalid email format.", parse_mode="HTML")
        return
    db.update_user_subscriber_prefs(user_id, email=email)
    channel = db.get_user_subscriber_prefs(user_id)
    if channel and channel.get("delivery_channel") == "telegram":
        db.update_user_subscriber_prefs(user_id, delivery_channel="email")
    await update.message.reply_text(f"✅ Email set to {email}. You'll receive digests there.", parse_mode="HTML")

async def digest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Generating your digest, please wait...", parse_mode="HTML")
    user_id = update.effective_user.id
    prefs = db.get_user_subscriber_prefs(user_id) or {}
    tags = prefs.get("interest_tags", ALL_TAGS[:])
    since = datetime.now(timezone.utc) - timedelta(days=1)
    articles = db.get_articles_by_tags(tags, since=since)
    if not articles:
        await update.message.reply_text("📭 No new articles matching your interests.", parse_mode="HTML")
        return
    digest = ai_service.compose_digest(articles, daily=True)
    msg = notifier.format_digest(digest, articles, daily=True)
    await update.message.reply_text(msg, parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "menu_sources":
        await show_source_toggles(query, user_id)
    elif data == "menu_tags":
        await show_tag_toggles(query, user_id)
    elif data == "menu_time":
        context.user_data["awaiting_time"] = True
        await query.edit_message_text("⏰ Send me your preferred delivery time (24h format, e.g. 08:00 or 18:30):", parse_mode="HTML")
    elif data == "menu_channel":
        prefs = db.get_user_subscriber_prefs(user_id) or {}
        current = prefs.get("delivery_channel", "telegram")
        keyboard = [
            [InlineKeyboardButton(f"{'✅ ' if current=='telegram' else ''}💬 Telegram", callback_data="channel_telegram")],
            [InlineKeyboardButton(f"{'✅ ' if current=='email' else ''}📧 Email", callback_data="channel_email")],
            [InlineKeyboardButton(f"{'✅ ' if current=='both' else ''}Both", callback_data="channel_both")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📬 Choose delivery channel:", reply_markup=reply_markup, parse_mode="HTML")
    elif data == "menu_frequency":
        keyboard = [
            [InlineKeyboardButton("Daily", callback_data="freq_daily")],
            [InlineKeyboardButton("Weekly", callback_data="freq_weekly")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📅 Choose digest frequency:", reply_markup=reply_markup, parse_mode="HTML")
    elif data.startswith("channel_"):
        channel = data.replace("channel_", "")
        db.update_user_subscriber_prefs(user_id, delivery_channel=channel)
        await query.edit_message_text(f"✅ Delivery channel set to {channel}.", parse_mode="HTML")
    elif data.startswith("freq_"):
        freq = data.replace("freq_", "")
        db.update_user_subscriber_prefs(user_id, delivery_frequency=freq)
        await query.edit_message_text(f"✅ Frequency set to {freq}.", parse_mode="HTML")
    elif data.startswith("toggle_"):
        await handle_source_toggle(query, user_id, data)
    elif data.startswith("tagtoggle_"):
        await handle_tag_toggle(query, user_id, data)

async def show_source_toggles(query, user_id):
    user_sources = db.get_user_prefs(user_id)
    keyboard = []
    for source in ALL_SOURCES:
        status = "✅" if source in user_sources else "❌"
        keyboard.append([InlineKeyboardButton(f"{status} {source}", callback_data=f"toggle_{source}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "⚙️ <b>News Source Settings</b>\nClick a source to turn it on or off:",
        reply_markup=reply_markup, parse_mode='HTML'
    )

async def show_tag_toggles(query, user_id):
    prefs = db.get_user_subscriber_prefs(user_id) or {}
    active_tags = prefs.get("interest_tags", ALL_TAGS[:])
    keyboard = []
    for tag in ALL_TAGS:
        status = "✅" if tag in active_tags else "❌"
        keyboard.append([InlineKeyboardButton(f"{status} {tag}", callback_data=f"tagtoggle_{tag}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🏷️ <b>Your Interest Topics</b>\nTap to toggle:",
        reply_markup=reply_markup, parse_mode="HTML"
    )

async def handle_source_toggle(query, user_id, data):
    source_to_toggle = data.replace("toggle_", "")
    current_sources = db.get_user_prefs(user_id)
    if source_to_toggle in current_sources:
        current_sources.remove(source_to_toggle)
    else:
        current_sources.append(source_to_toggle)
    db.update_user_prefs(user_id, current_sources)
    await show_source_toggles(query, user_id)

async def handle_tag_toggle(query, user_id, data):
    tag = data.replace("tagtoggle_", "")
    prefs = db.get_user_subscriber_prefs(user_id) or {}
    active = prefs.get("interest_tags", ALL_TAGS[:])
    if tag in active:
        active.remove(tag)
    else:
        active.append(tag)
    db.update_user_subscriber_prefs(user_id, interest_tags=active)
    await show_tag_toggles(query, user_id)

async def handle_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_time"):
        text = update.message.text.strip()
        try:
            parts = text.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time_str = f"{hour:02d}:{minute:02d}"
                db.update_user_subscriber_prefs(update.effective_user.id, delivery_time=time_str)
                context.user_data["awaiting_time"] = False
                await update.message.reply_text(f"✅ Delivery time set to {time_str}.", parse_mode="HTML")
                return
        except (ValueError, IndexError):
            pass
        await update.message.reply_text("❌ Invalid format. Use 24h format like 08:00 or 18:30.", parse_mode="HTML")

async def fetch_article_text(url):
    try:
        downloaded = fetch_url(url)
        text = extract(downloaded)
        return text[:4000] if text else None
    except Exception as e:
        logger.warning(f"Failed to fetch article text: {url} - {e}")
        return None

async def discover_and_process():
    all_articles = []
    rss_articles = await feeds.fetch_latest_articles_async()
    gdelt_articles = await gdelt_search.search_diaspora_news()

    for art in rss_articles:
        all_articles.append(art)
    for art in gdelt_articles:
        all_articles.append({
            "name": art.get("domain", "GDELT"),
            "flag": "🌐",
            "color": "🔍",
            "title": art.get("title", ""),
            "link": art.get("url", ""),
            "category": "Diaspora Media",
            "published": art.get("seendate", ""),
            "source_type": "gdelt",
        })

    all_links = [art["link"] for art in all_articles if art.get("link")]
    new_links = db.filter_new_articles(all_links)

    processed = 0
    for art in all_articles:
        if art["link"] in new_links:
            full_text = await fetch_article_text(art["link"])
            if full_text:
                ai_result = ai_service.tag_article(full_text)
                db.save_article_meta(
                    url=art["link"],
                    title=art["title"],
                    source=art.get("name", art.get("domain", "Unknown")),
                    source_type=art.get("source_type", "rss"),
                    tags=ai_result["tags"],
                    gist=ai_result["gist"],
                )
            db.save_article(art["link"])
            processed += 1

    logger.info(f"Discovery cycle: {len(new_links)} new, {processed} processed.")
    return processed

async def silent_startup_poll(context):
    try:
        await discover_and_process()
        logger.info("Silent startup pre-warm complete.")
    except Exception as e:
        logger.error(f"Silent startup failed: {e}")

async def check_feeds(context):
    try:
        await discover_and_process()
    except Exception as e:
        logger.error(f"Feed check cycle failed: {e}")

async def dispatch_digest(context):
    current_hour = datetime.now(timezone.utc).hour
    due_users = scheduler.get_due_users(current_hour)

    for user in due_users:
        try:
            tags = user["interest_tags"] if user["interest_tags"] else ALL_TAGS
            since = datetime.now(timezone.utc) - timedelta(days=1 if user["delivery_frequency"] == "daily" else 7)
            articles = db.get_articles_by_tags(tags, since=since)

            if not articles:
                msg = "📭 No new articles matching your interests since your last digest."
                digest_body = msg
                html_body = msg
            else:
                daily = user["delivery_frequency"] == "daily"
                digest = ai_service.compose_digest(articles, daily=daily)
                msg = notifier.format_digest(digest, articles, daily=daily)
                html_body = notifier.format_email_digest(digest, articles, daily=daily)

            channel = user.get("delivery_channel", "telegram")
            if channel in ("telegram", "both"):
                await context.bot.send_message(chat_id=user["user_id"], text=msg, parse_mode="HTML")
            if channel in ("email", "both") and user.get("email"):
                emailer.send_digest(user["email"], html_body, daily=user["delivery_frequency"] == "daily")

            scheduler.mark_digest_sent(user["user_id"])
            logger.info(f"Digest sent to user {user['user_id']} via {channel}")
        except Exception as e:
            logger.error(f"Failed to send digest to user {user['user_id']}: {e}")

async def periodic_cleanup(context):
    db.cleanup_old_articles(days=7)

def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("email", email_cmd))
    app.add_handler(CommandHandler("digest", digest_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_input))

    job_queue = app.job_queue
    job_queue.run_once(silent_startup_poll, when=0)
    job_queue.run_repeating(check_feeds, interval=Config.POLL_INTERVAL, first=10)
    job_queue.run_repeating(dispatch_digest, interval=3600, first=120)
    midnight = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)
    job_queue.run_daily(periodic_cleanup, time=midnight)

    print("OdaPulse Bot is Live...")
    app.run_polling()

if __name__ == "__main__":
    main()
