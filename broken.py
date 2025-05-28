import telebot
import datetime
import time
import subprocess
import random
import threading
import os
from telebot import types
from urllib.parse import urlparse

# Initialize bot with dark theme styling
bot = telebot.TeleBot('7774669814:AAGY2ohbBXKh_8WmT0AJDI_pev4vCtWAJfE')

# Configuration
INSTRUCTOR_IDS = ["7147401720", "1662672529"]
STUDY_GROUP_ID = "-1002658128612"
LEARNING_CHANNEL = "@HUNTERAloneboy99"
LAB_REPORTS_DIR = "lab_reports"
TEST_COOLDOWN = 30
DAILY_TEST_LIMIT = 10
is_test_in_progress = False
last_test_time = None
pending_reports = {}
lab_submissions = {}
STUDENT_DATA_FILE = "student_progress.txt"
student_data = {}
study_groups = {}
GROUPS_FILE = "study_groups.txt"

# Styling Constants
BOLD_START = "<b>"
BOLD_END = "</b>"
CODE_START = "<code>"
CODE_END = "</code>"
PRE_START = "<pre>"
PRE_END = "</pre>"

# Helper Functions with Dark Theme Styling
def create_progress_bar(progress, total, length=20):
    """Create visual progress bar with emoji states"""
    filled = int(length * progress // total)
    empty = length - filled
    
    if progress/total < 0.3:
        fill_char = '🟥'  # Red
    elif progress/total < 0.7:
        fill_char = '🟨'  # Yellow
    else:
        fill_char = '🟩'  # Green
    
    bar = fill_char * filled + '⬛' * empty
    percent = min(100, int(100 * progress / total))
    return f"{BOLD_START}📈 Progress:{BOLD_END} {bar} {percent}%"

def update_progress(chat_id, progress_data, target, port, student_name):
    """Update progress bar during experiment"""
    duration = progress_data['duration']
    start_time = progress_data['start_time']
    
    try:
        while True:
            elapsed = (datetime.datetime.now() - start_time).seconds
            progress = min(elapsed, duration)
            remaining = max(0, duration - elapsed)
            
            if progress - progress_data['last_update'] >= 5 or progress == duration:
                try:
                    bot.edit_message_text(
                        f"{BOLD_START}🔬 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏 𝙍𝙐𝙉𝙉𝙄𝙉𝙂{BOLD_END}\n"
                        f"👨‍🔬 {BOLD_START}Student:{BOLD_END} »»—— {student_name} ♥\n"
                        f"🎯 {BOLD_START}Target:{BOLD_END} {CODE_START}{target}:{port}{CODE_END}\n"
                        f"⏱ {BOLD_START}Elapsed:{BOLD_END} {progress}s/{duration}s\n"
                        f"📊 {BOLD_START}Remaining:{BOLD_END} {remaining}\n"
                        f"{create_progress_bar(progress, duration)}\n",
                        chat_id=chat_id,
                        message_id=progress_data['message_id'],
                        parse_mode="HTML"
                    )
                    progress_data['last_update'] = progress
                except Exception as e:
                    print(f"Error updating progress: {e}")
                
                if progress >= duration:
                    break
            
            time.sleep(1)
    except Exception as e:
        print(f"Progress updater error: {e}")

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def safe_send_photo(chat_id, photo_url, caption):
    try:
        if is_valid_url(photo_url):
            bot.send_photo(chat_id, photo_url, caption=caption, parse_mode="HTML")
        else:
            bot.send_message(chat_id, caption, parse_mode="HTML")
    except Exception as e:
        print(f"Error sending photo: {e}")
        bot.send_message(chat_id, caption, parse_mode="HTML")

def load_student_data():
    try:
        with open(STUDENT_DATA_FILE, "r") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    user_id, tests, last_reset = line.strip().split(',')
                    student_data[user_id] = {
                        'tests': int(tests),
                        'last_reset': datetime.datetime.fromisoformat(last_reset),
                        'last_test': None
                    }
                except ValueError:
                    print(f"Skipping malformed line: {line.strip()}")
    except FileNotFoundError:
        print(f"{STUDENT_DATA_FILE} not found, starting fresh.")

def save_student_data():
    with open(STUDENT_DATA_FILE, "w") as file:
        for user_id, data in student_data.items():
            file.write(f"{user_id},{data['tests']},{data['last_reset'].isoformat()}\n")

def check_membership(user_id):
    """Check if user has joined both channel and group"""
    try:
        # Check channel membership first
        try:
            channel_member = bot.get_chat_member(LEARNING_CHANNEL, user_id)
            if channel_member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Error checking channel membership: {e}")
            return False
            
        # Check study group membership
        for group_id in study_groups:
            try:
                group_member = bot.get_chat_member(group_id, user_id)
                if group_member.status in ['member', 'administrator', 'creator']:
                    return True
            except Exception as e:
                print(f"Error checking group {group_id} membership: {e}")
                continue
                
        # Check main study group membership
        try:
            main_group_member = bot.get_chat_member(STUDY_GROUP_ID, user_id)
            if main_group_member.status in ['member', 'administrator', 'creator']:
                return True
        except Exception as e:
            print(f"Error checking main group membership: {e}")
                
        return False
    except Exception as e:
        print(f"General membership check error: {e}")
        return False

def membership_required(func):
    def wrapped(message):
        user_id = message.from_user.id
        chat_id = str(message.chat.id)
        
        if chat_id not in study_groups and chat_id != STUDY_GROUP_ID:
            bot.reply_to(message, f"{BOLD_START}🚫 𝙐𝙉𝘼𝙐𝙏𝙊𝙍𝙄𝙕𝙀𝘿 𝘼𝘾𝘾𝙀𝙎𝙎{BOLD_END}\nThis command can only be used in approved study groups", parse_mode="HTML")
            return
            
        if not check_membership(user_id):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{LEARNING_CHANNEL[1:]}"))
            markup.add(types.InlineKeyboardButton("👥 Join Group", url=f"https://t.me/{STUDY_GROUP_ID[1:]}"))
            
            bot.reply_to(message, 
                f"{BOLD_START}🔒 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘼𝘾𝘾𝙀𝙎𝙎 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿{BOLD_END}\n\n"
                "To unlock all features:\n"
                "1️⃣ Join our official channel\n"
                "2️⃣ Join our study group\n\n"
                "After joining, try the command again!",
                reply_markup=markup,
                parse_mode="HTML"
            )
            return
        return func(message)
    return wrapped

def load_study_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            for line in f:
                if ',' in line:
                    group_id, name = line.strip().split(',', 1)
                    study_groups[group_id] = name

def save_study_groups():
    with open(GROUPS_FILE, "w") as f:
        for group_id, name in study_groups.items():
            f.write(f"{group_id},{name}\n")

def notify_instructors(message, user_name, file_id):
    for instructor_id in INSTRUCTOR_IDS:
        try:
            bot.send_photo(
                instructor_id,
                file_id,
                caption=f"{BOLD_START}📝 New Lab Report{BOLD_END}\nFrom {user_name} (@{message.from_user.username})",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Error notifying instructor {instructor_id}: {e}")
            try:
                bot.send_message(
                    instructor_id,
                    f"{BOLD_START}📝 New Lab Report{BOLD_END}\nFrom {user_name} (@{message.from_user.username})\nPhoto ID: {file_id}",
                    parse_mode="HTML"
                )
            except Exception as e2:
                print(f"Failed to send text notification to {instructor_id}: {e2}")

# Command Handlers with Dark Theme Styling
@bot.message_handler(commands=['start'])
def welcome_student(message):
    user_name = message.from_user.first_name
    response = f"""
{BOLD_START}╔════════════════════════════╗
   🔥 𝘼𝙇𝙊𝙉𝙀𝘽𝙊𝙔 𝙉𝙀𝙏𝙒𝙊𝙍𝙆 𝙇𝘼𝘽𝙊𝙍𝘼𝙏𝙊𝙍𝙔 🔥  
╚════════════════════════════╝{BOLD_END}  
{BOLD_START}"𝘞𝘩𝘦𝘳𝘦 𝘋𝘢𝘵𝘢 𝘉𝘰𝘸𝘴 𝘵𝘰 𝘔𝘢𝘴𝘵𝘦𝘳𝘺"{BOLD_END}  

   ✧༺ {BOLD_START}𝙒 𝙀 𝙇 𝘾 𝙊 𝙈 𝙀 ༻✧{BOLD_END}  
       {BOLD_START}{user_name}{BOLD_END}  

{BOLD_START}► 𝙋𝙧𝙞𝙣𝙘𝙞𝙥𝙖𝙡 -----------@GODxAloneBOY{BOLD_END}  
{BOLD_START}► 𝙋𝙧𝙤𝙛𝙚𝙨𝙨𝙤𝙧 -----------@SAMEER00{BOLD_END} 

{BOLD_START}➤ [Join Official Training Channel](https://t.me/{LEARNING_CHANNEL[1:]}){BOLD_END}  
{BOLD_START}➤ Try /help for all details{BOLD_END}  
{BOLD_START}▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂{BOLD_END}  
{BOLD_START}🔒 𝙇𝘼𝘽 𝙇𝘼𝙒𝙎 (Violators will be firewalled):{BOLD_END}  
- 𝟭. {BOLD_START}𝙉𝙤 𝙘𝙤𝙢𝙢𝙖𝙣𝙙𝙨 𝙬𝙞𝙩𝙝𝙤𝙪𝙩 𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙖𝙩𝙞𝙤𝙣{BOLD_END}  
- 𝟮. {BOLD_START}𝘿𝙖𝙞𝙡𝙮 𝙦𝙪𝙤𝙩𝙖𝙨: {DAILY_TEST_LIMIT} experiments{BOLD_END}  
- 𝟯. {BOLD_START}𝘾𝙤𝙤𝙡𝙙𝙤𝙬𝙣: {TEST_COOLDOWN} sec between trials{BOLD_END}    

{BOLD_START}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{BOLD_END}  
{BOLD_START}🔮 𝙄𝙣𝙞𝙩𝙞𝙖𝙩𝙞𝙤𝙣 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚:{BOLD_END}  
Proceed to {BOLD_START}[{LEARNING_CHANNEL}](https://t.me/{LEARNING_CHANNEL[1:]}){BOLD_END} for your first mission.  
"""
    bot.send_message(message.chat.id, response, parse_mode="Markdown", disable_web_page_preview=False)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = f"""
{BOLD_START}⚡ 𝙉𝙀𝙏𝙒𝙊𝙍𝙆 𝙎𝘾𝙄𝙀𝙉𝘾𝙀 𝙇𝘼𝘽 - 𝘾𝙊𝙈𝙈𝘼𝙉𝘿 𝘾𝙀𝙉𝙏𝙀𝙍 ⚡{BOLD_END}  
{BOLD_START}*Under the guidance of Professor ALONEBOY* 👨‍🏫{BOLD_END}  

{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}🔰 𝘽𝘼𝙎𝙄𝘾 𝘾𝙊𝙈𝙈𝘼𝙉𝘿𝙎{BOLD_END}  
{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}😎➤ /start - Begin your network science journey{BOLD_END}  
{BOLD_START}🍀➤ /help - Show this elite command list{BOLD_END}  

{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}🔬 𝙎𝙏𝙐𝘿𝙀𝙉𝙏 𝙇𝘼𝘽 𝘾𝙊𝙈𝙈𝘼𝙉𝘿𝙎{BOLD_END}  
{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}🍀➤ /study <IP> <PORT> <DURATION> - Conduct advanced network analysis{BOLD_END}  
{BOLD_START}   *Example:* `/study 192.168.1.1 80 30`{BOLD_END}  
{BOLD_START}✅➤ /pingtest <IP> - Master latency measurement{BOLD_END}  
{BOLD_START}   *Example:* `/ping_test 8.8.8.8`{BOLD_END}  
{BOLD_START}😎➤ /cooldownstatus - Check experiment readiness{BOLD_END}  
{BOLD_START}💗➤ /remainingtests - View your daily quota{BOLD_END}  

{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}📝 𝙇𝘼𝘽 𝙍𝙀𝙋𝙊𝙍𝙏 𝙎𝙔𝙎𝙏𝙀𝙈{BOLD_END}  
{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}After /study, send photo observations to submit reports to Professor ALONEBOY{BOLD_END}  

{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}👨‍⚕️ 𝙄𝙉𝙎𝙏𝙍𝙐𝘾𝙏𝙊𝙍 𝘾𝙊𝙈𝙈𝘼𝙉𝘿𝙎 (ALONEBOY Approved){BOLD_END}  
{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}♥️➤ /addstudygroup <group_id> - Authorize new study group{BOLD_END}  
{BOLD_START}✅➤ /removestudygroup <group_id> - Revoke group access{BOLD_END}  
{BOLD_START}🎉➤ /liststudygroups - View all authorized groups{BOLD_END}  
{BOLD_START}🍫➤ /notice <message> - Broadcast important announcements{BOLD_END}  

{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}⚠️ 𝙇𝘼𝘽 𝙍𝙐𝙇𝙀𝙎 (By Professor ALONEBOY){BOLD_END}  
{BOLD_START}▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{BOLD_END}  
{BOLD_START}• Join: {STUDY_GROUP_ID}{BOLD_END}  
{BOLD_START}• Subscribe: {LEARNING_CHANNEL}{BOLD_END}  
{BOLD_START}• Daily Limit: {DAILY_TEST_LIMIT} experiments{BOLD_END}  
{BOLD_START}• Cooldown: {TEST_COOLDOWN} seconds between tests{BOLD_END}  
{BOLD_START}• Strictly for educational purposes{BOLD_END}  

{BOLD_START}💎 *Pro Tip:* Use code 'ALONEBOY' in reports for bonus evaluation!{BOLD_END}  
"""
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# Add this dictionary at the top with other global variables
broadcast_messages = {}  # Stores broadcast message IDs by experiment ID

# Modify the conduct_network_experiment function
@bot.message_handler(commands=['study'])
@membership_required
def conduct_network_experiment(message):
    global is_test_in_progress, last_test_time
    
    if is_test_in_progress:
        bot.reply_to(message, f"{BOLD_START}⏳ 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏 𝙄𝙉 𝙋𝙍𝙊𝙂𝙍𝙀𝙎𝙎{BOLD_END}\nPlease wait for current analysis to complete", parse_mode="HTML")
        return

    current_time = datetime.datetime.now()
    if last_test_time and (current_time - last_test_time).seconds < TEST_COOLDOWN:
        remaining = TEST_COOLDOWN - (current_time - last_test_time).seconds
        bot.reply_to(message, f"{BOLD_START}⏳ 𝙋𝙇𝙀𝘼𝙎𝙀 𝙒𝘼𝙄𝙏{BOLD_END}\n{remaining}s before next experiment\nThis ensures accurate results for all students", parse_mode="HTML")
        return

    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    command = message.text.split()

    if pending_reports.get(user_id, False):
        bot.reply_to(message, f"{BOLD_START}📝 𝙇𝘼𝘽 𝙍𝙀𝙋𝙊𝙍𝙏 𝙋𝙀𝙉𝘿𝙄𝙉𝙂!{BOLD_END}\nPlease submit findings from your last experiment", parse_mode="HTML")
        return

    if user_id not in student_data:
        student_data[user_id] = {'tests': 0, 'last_reset': datetime.datetime.now()}

    student = student_data[user_id]

    if student['tests'] >= DAILY_TEST_LIMIT:
        bot.reply_to(message, f"{BOLD_START}📊 𝘿𝘼𝙄𝙇𝙔 𝙇𝙄𝙈𝙄𝙏 𝙍𝙀𝘼𝘾𝙃𝙀𝘿{BOLD_END}\nYou've completed all available experiments today", parse_mode="HTML")
        return

    if len(command) != 4:
        bot.reply_to(message, f"{BOLD_START}📘 𝙐𝙎𝘼𝙂𝙀:{BOLD_END} /study <IP> <PORT> <DURATION>\nExample: `/study 192.168.1.1 80 30`", parse_mode="Markdown")
        return

    try:
        target, port, duration = command[1], int(command[2]), int(command[3])
        if duration > 240:
            raise ValueError("Duration too long")
    except:
        bot.reply_to(message, f"{BOLD_START}🔢 𝙄𝙉𝙑𝘼𝙇𝙄𝘿 𝙋𝘼𝙍𝘼𝙈𝙀𝙏𝙀𝙍𝙎{BOLD_END}\nPort/Duration must be numbers\nMax duration: 240 seconds", parse_mode="HTML")
        return

    if not bot.get_user_profile_photos(user_id).total_count:
        bot.reply_to(message, f"{BOLD_START}📸 𝙋𝙍𝙊𝙁𝙄𝙇𝙀 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿{BOLD_END}\nSet a profile picture for identification", parse_mode="HTML")
        return

    is_test_in_progress = True
    experiment_id = f"{user_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Create initial progress message
    progress_msg = f"""
{BOLD_START}🔬 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏 𝙄𝙉𝙄𝙏𝙄𝘼𝙏𝙀𝘿{BOLD_END}
👨‍🔬 {BOLD_START}Student:{BOLD_END} »»—— {user_name} ♥
🎯 {BOLD_START}Target:{BOLD_END} {CODE_START}{target}:{port}{CODE_END}
⏱ {BOLD_START}Duration:{BOLD_END} {duration}s
📊 {BOLD_START}Status:{BOLD_END} Starting...
{create_progress_bar(0, duration)}
"""

    # Send to original chat
    original_msg = bot.send_message(message.chat.id, progress_msg, parse_mode="HTML")

    # Broadcast to all study groups
    broadcast_messages[experiment_id] = {}
    for group_id in study_groups:
        try:
            msg = bot.send_message(group_id, progress_msg, parse_mode="HTML")
            broadcast_messages[experiment_id][group_id] = msg.message_id
        except Exception as e:
            print(f"Error broadcasting to group {group_id}: {e}")

    progress_data = {
        'message_id': original_msg.message_id,
        'start_time': datetime.datetime.now(),
        'duration': duration,
        'last_update': 0,
        'target': target,
        'port': port,
        'experiment_id': experiment_id,
        'user_name': user_name
    }

    pending_reports[user_id] = True
    student['tests'] += 1
    save_student_data()

    def run_experiment():
        global last_test_time
        try:
            # Start progress updater
            threading.Thread(
                target=update_progress,
                args=(message.chat.id, progress_data, target, port, user_name)
            ).start()
            
            # Run the actual experiment
            subprocess.run(["./ok", target, str(port), str(duration)], check=True)
            last_test_time = datetime.datetime.now()
            
            # Send completion message
            completion_msg = f"""
{BOLD_START}✅ 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏 𝘾𝙊𝙈𝙋𝙇𝙀𝙏𝙀!{BOLD_END}

{BOLD_START}🔬 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏 𝙎𝙐𝙈𝙈𝘼𝙍𝙔:{BOLD_END}
👨‍🔬 {BOLD_START}Student:{BOLD_END} »»—— {user_name} ♥
🎯 {BOLD_START}Target:{BOLD_END} {CODE_START}{target}:{port}{CODE_END}
⏱ {BOLD_START}Duration:{BOLD_END} {duration}s

{BOLD_START}📝 𝙋𝙇𝙀𝘼𝙎𝙀 𝙎𝙐𝘽𝙈𝙄𝙏 𝙔𝙊𝙐𝙍 𝙊𝘽𝙎𝙀𝙍𝙑𝘼𝙏𝙄𝙊𝙉𝙎{BOLD_END}
"""
            bot.send_message(message.chat.id, completion_msg, parse_mode="HTML")
            
            # Clean up broadcast messages
            clean_up_broadcast(progress_data['experiment_id'])
            
        except subprocess.CalledProcessError:
            bot.reply_to(message, 
                f"{BOLD_START}⚠️ 𝙏𝙀𝙎𝙏 𝙁𝘼𝙄𝙇𝙀𝘿{BOLD_END}\nPossible causes:\n"
                "- Target unreachable\n"
                "- Port blocked\n"
                "- Network issues",
                parse_mode="HTML"
            )
            clean_up_broadcast(progress_data['experiment_id'])
        finally:
            global is_test_in_progress
            is_test_in_progress = False

    threading.Thread(target=run_experiment).start()

def clean_up_broadcast(experiment_id):
    """Remove all broadcast messages for an experiment"""
    if experiment_id in broadcast_messages:
        for group_id, message_id in broadcast_messages[experiment_id].items():
            try:
                bot.delete_message(group_id, message_id)
            except Exception as e:
                print(f"Error cleaning up broadcast in group {group_id}: {e}")
        del broadcast_messages[experiment_id]

# Update the update_progress function
def update_progress(chat_id, progress_data, target, port, student_name):
    """Update progress bar during experiment"""
    duration = progress_data['duration']
    start_time = progress_data['start_time']
    experiment_id = progress_data['experiment_id']
    
    try:
        while True:
            elapsed = (datetime.datetime.now() - start_time).seconds
            progress = min(elapsed, duration)
            remaining = max(0, duration - elapsed)
            
            if progress - progress_data['last_update'] >= 5 or progress == duration:
                progress_msg = f"""
{BOLD_START}🔬 𝙇𝙄𝙑𝙀 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏 𝙐𝙋𝘿𝘼𝙏𝙀{BOLD_END}
👨‍🔬 {BOLD_START}Student:{BOLD_END} »»—— {student_name} ♥
🎯 {BOLD_START}Target:{BOLD_END} {CODE_START}{target}:{port}{CODE_END}
⏱ {BOLD_START}Elapsed:{BOLD_END} {progress}s/{duration}s
📊 {BOLD_START}Remaining:{BOLD_END} {remaining}s
{create_progress_bar(progress, duration)}
"""
                try:
                    # Update original message
                    bot.edit_message_text(
                        progress_msg,
                        chat_id=chat_id,
                        message_id=progress_data['message_id'],
                        parse_mode="HTML"
                    )
                    
                    # Update broadcast messages
                    if experiment_id in broadcast_messages:
                        for group_id, message_id in broadcast_messages[experiment_id].items():
                            try:
                                bot.edit_message_text(
                                    progress_msg,
                                    chat_id=group_id,
                                    message_id=message_id,
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                print(f"Error updating broadcast in group {group_id}: {e}")
                    
                    progress_data['last_update'] = progress
                except Exception as e:
                    print(f"Error updating progress: {e}")
                
                if progress >= duration:
                    break
            
            time.sleep(1)
    except Exception as e:
        print(f"Progress updater error: {e}")

@bot.message_handler(content_types=['photo'])
@membership_required
def handle_lab_report(message):
    """Process student lab report submissions with dark theme"""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    try:
        if not pending_reports.get(user_id, False):
            bot.reply_to(message, 
                f"{BOLD_START}📌 𝙉𝙊 𝙋𝙀𝙉𝘿𝙄𝙉𝙂 𝙍𝙀𝙋𝙊𝙍𝙏𝙎{BOLD_END}\n"
                "Start a new experiment with /study first",
                parse_mode="HTML"
            )
            return
        
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        
        os.makedirs(LAB_REPORTS_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(LAB_REPORTS_DIR, f"{user_id}_{timestamp}.jpg")
        
        downloaded_file = bot.download_file(file_info.file_path)
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        pending_reports[user_id] = False
        lab_submissions.setdefault(user_id, []).append({
            'timestamp': timestamp,
            'filename': filename,
            'file_id': photo.file_id
        })
        
        bot.reply_to(message, 
            f"{BOLD_START}📝 𝙇𝘼𝘽 𝙍𝙀𝙋𝙊𝙍𝙏 𝙎𝙐𝘽𝙈𝙄𝙏𝙏𝙀𝘿!{BOLD_END}\n"
            f"👨‍🔬 {BOLD_START}Student:{BOLD_END} {user_name}\n"
            f"🕒 {BOLD_START}Submitted at:{BOLD_END} {timestamp}\n\n"
            f"{BOLD_START}You may now start a new experiment with /study{BOLD_END}",
            parse_mode="HTML"
        )
        
        notify_instructors(message, user_name, photo.file_id)
        
    except Exception as e:
        error_msg = f"{BOLD_START}❌ 𝙀𝙍𝙍𝙊𝙍 𝙎𝘼𝙑𝙄𝙉𝙂 𝙍𝙀𝙋𝙊𝙍𝙏:{BOLD_END} {str(e)}"
        print(error_msg)
        bot.reply_to(message, 
            f"{BOLD_START}🍀 𝙇𝘼𝘽 𝙍𝙀𝙋𝙊𝙍𝙏 𝘼𝘾𝘾𝙀𝙋𝙏𝙀𝘿{BOLD_END}\n"
            f"{BOLD_START}Ready for next experiment.{BOLD_END}",
            parse_mode="HTML"
        )
        
        try:
            pending_reports[user_id] = False
            lab_submissions.setdefault(user_id, []).append({
                'timestamp': datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                'file_id': photo.file_id,
                'error': str(e)
            })
        except:
            pass

@bot.message_handler(commands=['cooldownstatus'])
def check_cooldown_status(message):
    """Check when next experiment can be run with dark theme"""
    if last_test_time and (datetime.datetime.now() - last_test_time).seconds < TEST_COOLDOWN:
        remaining = TEST_COOLDOWN - (datetime.datetime.now() - last_test_time).seconds
        bot.reply_to(message, 
            f"{BOLD_START}⏳ 𝙉𝙀𝙓𝙏 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏 𝙄𝙉{BOLD_END} {remaining} seconds\n"
            f"{BOLD_START}Use this time to review your last results{BOLD_END}",
            parse_mode="HTML"
        )
    else:
        bot.reply_to(message, 
            f"{BOLD_START}🔬 𝙍𝙀𝘼𝘿𝙔 𝙁𝙊𝙍 𝙉𝙀𝙒 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏!{BOLD_END}\n"
            f"{BOLD_START}Use /study to begin{BOLD_END}",
            parse_mode="HTML"
        )

@bot.message_handler(commands=['remainingtests'])
def check_remaining_experiments(message):
    """Show student's remaining daily experiments with dark theme"""
    user_id = str(message.from_user.id)
    if user_id not in student_data:
        bot.reply_to(message, 
            f"{BOLD_START}You have {DAILY_TEST_LIMIT} experiments remaining today{BOLD_END}",
            parse_mode="HTML"
        )
    else:
        remaining = DAILY_TEST_LIMIT - student_data[user_id]['tests']
        bot.reply_to(message, 
            f"{BOLD_START}📊 𝙏𝙊𝘿𝘼𝙔'𝙎 𝙍𝙀𝙈𝘼𝙄𝙉𝙄𝙉𝙂 𝙀𝙓𝙋𝙀𝙍𝙄𝙈𝙀𝙉𝙏𝙎:{BOLD_END} {remaining}\n"
            f"{BOLD_START}Resets daily at midnight UTC{BOLD_END}",
            parse_mode="HTML"
        )

@bot.message_handler(commands=['pingtest'])
def conduct_ping_test(message):
    """Educational ping simulation with dark theme"""
    if len(message.text.split()) != 2:
        bot.reply_to(message, 
            f"{BOLD_START}📘 Usage:{BOLD_END} /pingtest <IP>\n"
            f"{BOLD_START}Example:{BOLD_END} `/pingtest 8.8.8.8`\n"
            f"{BOLD_START}Measures network latency{BOLD_END}",
            parse_mode="Markdown"
        )
        return
    
    target = message.text.split()[1]
    progress_msg = bot.send_message(message.chat.id, f"{BOLD_START}🔍 Simulating ping to {target}...{BOLD_END}", parse_mode="HTML")
    
    # Create progress bar for ping test
    for i in range(1, 6):
        time.sleep(1)
        try:
            bot.edit_message_text(
                f"{BOLD_START}🔍 Testing ping to {target}{BOLD_END}\n"
                f"{create_progress_bar(i*20, 100)}",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id,
                parse_mode="HTML"
            )
        except:
            pass
    
    # Send results with dark theme
    bot.send_message(message.chat.id,
        f"{BOLD_START}📊 𝙋𝙄𝙉𝙂 𝙍𝙀𝙎𝙐𝙇𝙏𝙎 𝙁𝙊𝙍 {target}{BOLD_END}\n"
        f"⏱ {BOLD_START}Avg Latency:{BOLD_END} {random.randint(10,150)}ms\n"
        f"📦 {BOLD_START}Packet Loss:{BOLD_END} 0%\n\n"
        f"{BOLD_START}💡 𝙀𝘿𝙐𝘾𝘼𝙏𝙄𝙊𝙉𝘼𝙇 𝙄𝙉𝙎𝙄𝙂𝙃𝙏:{BOLD_END}\n"
        f"{BOLD_START}Latency under 100ms is good for most applications{BOLD_END}",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['resetstudent'])
def reset_student_limit(message):
    """Reset a student's daily test limit (Instructor only) with dark theme"""
    if str(message.from_user.id) not in INSTRUCTOR_IDS:
        bot.reply_to(message, 
            f"{BOLD_START}🚫 𝙊𝙉𝙇𝙔 𝙄𝙉𝙎𝙏𝙍𝙐𝘾𝙏𝙊𝙍𝙎 𝘾𝘼𝙉 𝙍𝙀𝙎𝙀𝙏 𝙇𝙄𝙈𝙄𝙏𝙎{BOLD_END}",
            parse_mode="HTML"
        )
        return
    
    try:
        command = message.text.split()
        if len(command) != 2:
            raise ValueError
        
        student_id = command[1]
        
        if student_id not in student_data:
            bot.reply_to(message, 
                f"{BOLD_START}❌ Student ID {student_id} not found in records{BOLD_END}",
                parse_mode="HTML"
            )
            return
        
        student_data[student_id] = {
            'tests': 0,
            'last_reset': datetime.datetime.now(),
            'last_test': None
        }
        save_student_data()
        
        bot.reply_to(message, 
            f"{BOLD_START}✅ 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔 𝙍𝙀𝙎𝙀𝙏 𝘿𝘼𝙄𝙇𝙔 𝙇𝙄𝙈𝙄𝙏 𝙁𝙊𝙍 𝙎𝙏𝙐𝘿𝙀𝙉𝙏 {student_id}{BOLD_END}\n"
            f"{BOLD_START}They now have {DAILY_TEST_LIMIT} tests available today{BOLD_END}",
            parse_mode="HTML"
        )
    
    except ValueError:
        bot.reply_to(message, 
            f"{BOLD_START}❌ Usage:{BOLD_END} /resetstudent <student_id>\n\n"
            f"{BOLD_START}Example:{BOLD_END}\n/resetstudent 123456789",
            parse_mode="HTML"
        )

@bot.message_handler(commands=['addstudygroup'])
def add_study_group(message):
    """Add a new study group to the allowed list with dark theme"""
    user_id = str(message.from_user.id)
    
    if user_id not in INSTRUCTOR_IDS:
        bot.reply_to(message, 
            f"{BOLD_START}🚫 𝙊𝙉𝙇𝙔 𝙄𝙉𝙎𝙏𝙍𝙐𝘾𝙏𝙊𝙍𝙎 𝘾𝘼𝙉 𝘼𝘿𝘿 𝙎𝙏𝙐𝘿𝙔 𝙂𝙍𝙊𝙐𝙋𝙎{BOLD_END}",
            parse_mode="HTML"
        )
        return
    
    try:
        command = message.text.split()
        if len(command) != 2:
            raise ValueError
        
        new_group_id = command[1]
        chat_info = bot.get_chat(new_group_id)
        
        bot_member = bot.get_chat_member(new_group_id, bot.get_me().id)
        if bot_member.status not in ['administrator', 'creator']:
            bot.reply_to(message, 
                f"{BOLD_START}❌ Bot must be admin in the group to add it{BOLD_END}",
                parse_mode="HTML"
            )
            return
        
        study_groups[new_group_id] = chat_info.title
        save_study_groups()
        
        bot.reply_to(message, 
            f"""{BOLD_START}✅ 𝙎𝙏𝙐𝘿𝙔 𝙂𝙍𝙊𝙐𝙋 𝘼𝘿𝘿𝙀𝘿 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔!{BOLD_END}

{BOLD_START}📛 Name:{BOLD_END} {chat_info.title}
{BOLD_START}🆔 ID:{BOLD_END} {new_group_id}

{BOLD_START}Now students can study in this group after joining {LEARNING_CHANNEL}{BOLD_END}""",
            parse_mode="HTML"
        )
    
    except Exception as e:
        bot.reply_to(message, 
            f"{BOLD_START}❌ Usage:{BOLD_END} /addstudygroup <group_id>\n\n"
            f"{BOLD_START}Example:{BOLD_END}\n/addstudygroup -100123456789",
            parse_mode="HTML"
        )

@bot.message_handler(commands=['removestudygroup'])
def remove_study_group(message):
    """Remove a study group from the approved list with dark theme"""
    user_id = str(message.from_user.id)
    
    if user_id not in INSTRUCTOR_IDS:
        bot.reply_to(message, 
            f"{BOLD_START}🚫 𝙊𝙉𝙇𝙔 𝙄𝙉𝙎𝙏𝙍𝙐𝘾𝙏𝙊𝙍𝙎 𝘾𝘼𝙉 𝙍𝙀𝙈𝙊𝙑𝙀 𝙎𝙏𝙐𝘿𝙔 𝙂𝙍𝙊𝙐𝙋𝙎{BOLD_END}",
            parse_mode="HTML"
        )
        return
    
    try:
        command = message.text.split()
        if len(command) != 2:
            raise ValueError
        
        group_id_to_remove = command[1]
        
        if group_id_to_remove not in study_groups:
            bot.reply_to(message, 
                f"{BOLD_START}❌ Group ID {group_id_to_remove} not found in approved list{BOLD_END}",
                parse_mode="HTML"
            )
            return
        
        removed_group_name = study_groups.pop(group_id_to_remove)
        save_study_groups()
        
        bot.reply_to(message, 
            f"""{BOLD_START}✅ 𝙎𝙏𝙐𝘿𝙔 𝙂𝙍𝙊𝙐𝙋 𝙍𝙀𝙈𝙊𝙑𝙀𝘿 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔!{BOLD_END}

{BOLD_START}📛 Name:{BOLD_END} {removed_group_name}
{BOLD_START}🆔 ID:{BOLD_END} {group_id_to_remove}""",
            parse_mode="HTML"
        )
    
    except ValueError:
        bot.reply_to(message, 
            f"{BOLD_START}❌ Usage:{BOLD_END} /removestudygroup <group_id>\n\n"
            f"{BOLD_START}Example:{BOLD_END}\n/removestudygroup -100123456789",
            parse_mode="HTML"
        )
    except Exception as e:
        bot.reply_to(message, 
            f"{BOLD_START}⚠️ 𝘼𝙉 𝙀𝙍𝙍𝙊𝙍 𝙊𝘾𝘾𝙐𝙍𝙍𝙀𝘿:{BOLD_END} {str(e)}",
            parse_mode="HTML"
        )
        print(f"Error removing group: {e}")

@bot.message_handler(commands=['liststudygroups'])
def list_study_groups(message):
    """List all approved study groups with dark theme"""
    user_id = str(message.from_user.id)
    if user_id not in INSTRUCTOR_IDS:
        bot.reply_to(message, 
            f"{BOLD_START}🚫 𝙊𝙉𝙇𝙔 𝙄𝙉𝙎𝙏𝙍𝙐𝘾𝙏𝙊𝙍𝙎 𝘾𝘼𝙉 𝙑𝙄𝙀𝙒 𝙎𝙏𝙐𝘿𝙔 𝙂𝙍𝙊𝙐𝙋𝙎 𝙇𝙄𝙎𝙏{BOLD_END}",
            parse_mode="HTML"
        )
        return
    
    if not study_groups:
        bot.reply_to(message, 
            f"{BOLD_START}No study groups added yet{BOLD_END}",
            parse_mode="HTML"
        )
        return
    
    groups_list = f"{BOLD_START}📚 𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 𝙎𝙏𝙐𝘿𝙔 𝙂𝙍𝙊𝙐𝙋𝙎:{BOLD_END}\n\n"
    for idx, (group_id, name) in enumerate(study_groups.items(), 1):
        groups_list += f"{BOLD_START}{idx}.{BOLD_END} {name}\n{BOLD_START}🆔:{BOLD_END} {CODE_START}{group_id}{CODE_END}\n\n"
    
    bot.reply_to(message, groups_list, parse_mode="HTML")

@bot.message_handler(commands=['notice'])
def handle_notice(message):
    """Broadcast notice to all users and groups with dark theme"""
    if str(message.from_user.id) not in INSTRUCTOR_IDS:
        bot.reply_to(message, 
            f"{BOLD_START}🚫 𝙊𝙉𝙇𝙔 𝙄𝙉𝙎𝙏𝙍𝙐𝘾𝙏𝙊𝙍𝙎 𝘾𝘼𝙉 𝙎𝙀𝙉𝘿 𝙉𝙊𝙏𝙄𝘾𝙀𝙎{BOLD_END}",
            parse_mode="HTML"
        )
        return

    if len(message.text.split()) < 2:
        bot.reply_to(message, 
            f"{BOLD_START}📝 Usage:{BOLD_END} /notice <message>",
            parse_mode="HTML"
        )
        return
    
    notice_text = message.text.split(' ', 1)[1]

    formatted_notice = (
        f"{BOLD_START}🍀 𝙊𝙁𝙁𝙄𝘾𝙄𝘼𝙇 𝙉𝙊𝙏𝙄𝘾𝙀 🍀{BOLD_END}\n\n"
        f"{notice_text}\n\n"
        f"{BOLD_START}📅{BOLD_END} {datetime.datetime.now().strftime('%d %b %Y %H:%M')}\n"
        f"{BOLD_START}►𝙋𝙧𝙞𝙣𝙘𝙞𝙥𝙖𝙡 -----------@GODxAloneBOY{BOLD_END}\n"
        f"{BOLD_START}►𝙋𝙧𝙤𝙛𝙚𝙨𝙨𝙤𝙧 -----------@RAJOWNER90{BOLD_END}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Broadcast Now", callback_data="broadcast_now"),
        types.InlineKeyboardButton("👀 Preview", callback_data="preview_notice")
    )
    markup.row(
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_notice")
    )

    bot.current_notice = formatted_notice
    
    bot.reply_to(message,
        f"{BOLD_START}⚠️ 𝘾𝙊𝙉𝙁𝙄𝙍𝙈 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏:{BOLD_END}\n\n"
        f"{BOLD_START}Message length:{BOLD_END} {len(notice_text)} characters\n"
        f"{BOLD_START}Will be sent to:{BOLD_END}\n"
        f"- {len(student_data)} students\n"
        f"- {len(study_groups)} study groups",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data in ['broadcast_now', 'preview_notice', 'cancel_notice'])
def handle_notice_confirmation(call):
    if call.data == "cancel_notice":
        bot.edit_message_text(
            f"{BOLD_START}❌ 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝘾𝘼𝙉𝘾𝙀𝙇𝙇𝙀𝘿{BOLD_END}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        return
    
    elif call.data == "preview_notice":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
                        f"{BOLD_START}📋 𝙉𝙊𝙏𝙄𝘾𝙀 𝙋𝙍𝙀𝙑𝙄𝙀𝙒:{BOLD_END}\n\n{bot.current_notice}",
                        parse_mode="HTML")
        return
    
    elif call.data == "broadcast_now":
        bot.edit_message_text(
            f"{BOLD_START}📡 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏𝙄𝙉𝙂 𝙉𝙊𝙏𝙄𝘾𝙀...{BOLD_END}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        results = {
            'users_success': 0,
            'users_failed': 0,
            'groups_success': 0,
            'groups_failed': 0
        }

        # Broadcast to students
        for user_id in student_data.keys():
            try:
                bot.send_message(user_id, bot.current_notice, parse_mode="HTML")
                results['users_success'] += 1
                time.sleep(0.1)
            except:
                results['users_failed'] += 1

        # Broadcast to study groups
        for group_id in study_groups.keys():
            try:
                bot.send_message(group_id, bot.current_notice, parse_mode="HTML")
                results['groups_success'] += 1
                time.sleep(0.3)
            except:
                results['groups_failed'] += 1

        report = (
            f"{BOLD_START}📊 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝘾𝙊𝙈𝙋𝙇𝙀𝙏𝙀 📊{BOLD_END}\n\n"
            f"{BOLD_START}👤 Students:{BOLD_END} {results['users_success']}/{len(student_data)}\n"
            f"{BOLD_START}👥 Study Groups:{BOLD_END} {results['groups_success']}/{len(study_groups)}\n\n"
            f"{BOLD_START}⏱ Completed at:{BOLD_END} {datetime.datetime.now().strftime('%H:%M:%S')}"
        )

        bot.send_message(call.message.chat.id, report, parse_mode="HTML")

        try:
            bot.add_message_reaction(call.message.chat.id, call.message.message_id, ["✅"])
        except:
            pass

def auto_reset_daily_limits():
    """Reset daily experiment limits at midnight"""
    while True:
        now = datetime.datetime.now()
        midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        time.sleep((midnight - now).total_seconds())
        for user_id in student_data:
            student_data[user_id]['tests'] = 0
            student_data[user_id]['last_reset'] = datetime.datetime.now()
        save_student_data()

# Start background tasks
threading.Thread(target=auto_reset_daily_limits, daemon=True).start()

# Load data at startup
load_student_data()
load_study_groups()

if __name__ == "__main__":
    print(f"{BOLD_START}Bot started with {len(study_groups)} study groups{BOLD_END}")
    bot.polling(none_stop=True)