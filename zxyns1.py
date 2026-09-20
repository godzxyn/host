import telebot
import time
import os
import subprocess
import psutil
import re
import json
import sys
import zipfile
import shutil
from telebot import types

# --- Configuration ---
API_TOKEN = '8419138760:AAHRuehYhskiERpWpQJQxBQtPxeHMfYfCmo'
ADMIN_ID = 8848159805
CHANNEL_ID = "@Hosterbyzxynbot" 
bot = telebot.TeleBot(API_TOKEN)

DB_FILE = "users_data.json"
SETTINGS_FILE = "bot_settings.json"
DEPLOY_DIR = "deployed_bots"

if not os.path.exists(DEPLOY_DIR):
    os.makedirs(DEPLOY_DIR)

# --- Persistence Functions ---
def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_db, f, ensure_ascii=False, indent=4)

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_settings():
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_settings():
    default = {
        "points_per_referral": 2, 
        "hosting_cost": 4,        
        "maintenance": False,
        "welcome_video": None,
        "pending_approvals": {}
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return default
    return default

users_db = load_db()
settings = load_settings()
running_processes = {} 

# --- Execution Logic & Error Catching ---
def run_user_file(f_path, user_id, f_name):
    ext = os.path.splitext(f_name)[1].lower()
    cmd = [sys.executable, f_path] if ext == '.py' else ['node', f_path]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        running_processes[f_path] = process
        
        time.sleep(3)
        if process.poll() is not None:
            _, stderr = process.communicate()
            error_msg = stderr if stderr else "Exited with unknown error."
            bot.send_message(user_id, f"⚠️Your Bot has a Runtime Error!\n\nFile: `{f_name}`\nError Log:\n`{error_msg[:3000]}`")
            if f_path in running_processes: del running_processes[f_path]
            return False
        return True
    except Exception as e:
        bot.send_message(user_id, f"❌ Server Error: {e}")
        return False

# --- UI Designs ---
def get_welcome_text(message):
    user = message.from_user
    points = users_db.get(str(user.id), {}).get('points', 0)
    status = 'ONLINE ✅' if not settings.get('maintenance') else 'MAINTENANCE ⚠️'
    return (
        "┏━━━━━━━━━━━━━━━━━┓\n"
        "┃ ⚡ ᴢxʏɴ ᴘʀᴇᴍɪᴜᴍ ʜᴏsᴛɪɴɢ ʙᴏᴛ  ⚡\n"
        "┃    ᴘʀᴇᴍɪᴜᴍ 24/7 ᴄʟᴏᴜᴅ ꜱᴇʀᴠɪᴄᴇ \n"
        "┗━━━━━━━━━━━━━━━━━┛\n"
        f"┃ 👋 ᴡᴇʟᴄᴏᴍᴇ: {user.first_name.upper()} 𓇻\n"
        "┃\n"
        "┃ 📤 ᴅᴇᴘʟᴏʏ ᴘʏᴛʜᴏɴ & ᴊꜱ & ᴢɪᴘ\n"
        "┃ 🚀 ᴀᴜᴛᴏ ᴅᴇᴘᴇɴᴅᴇɴᴄɪᴇs\n"
        "┃ 🔍 ʀᴇᴀʟ-ᴛɪᴍᴇ ʟᴏɢs\n"
        "┃ ⚡ 24/7 ᴜᴘᴛɪᴍᴇ ᴀᴄᴛɪᴠᴇ\n"
        "┣━━━━━━━━━━━━━━━━━┫\n"
        f"┃ 🆔 ɪᴅ   : {user.id}\n"
        f"┃ 💰 ᴘᴛs  : {points}\n"
        f"┃ ⚡ sᴛᴀᴛ : {status}\n"
        f"┃ 🏆 ᴘʟᴀɴ : ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ\n"
        "┗━━━━━━━━━━━━━━━━━┛\n\n"
        "👇 ᴜsᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ!"
    )

def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📢 Updates Channel"))
    markup.add(types.KeyboardButton("📤 Deploy File"), types.KeyboardButton("📂 My Files"))
    markup.add(types.KeyboardButton("💰 My Points"), types.KeyboardButton("🔗 Referral Link"))
    markup.add(types.KeyboardButton("📊 Statistics"), types.KeyboardButton("📞 Contact Owner"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("👑 Admin Panel"), types.KeyboardButton("🌍 All Files Control"))
    return markup

def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    m_text = "🔴 Maintenance: ON" if settings['maintenance'] else "🟢 Maintenance: OFF"
    markup.add(types.InlineKeyboardButton("➕ Add Points", callback_data="adm_add_pts"),
               types.InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast"))
    markup.add(types.InlineKeyboardButton("🎥 Set Welcome Video", callback_data="adm_set_video"))
    if settings.get('welcome_video'):
        markup.add(types.InlineKeyboardButton("❌ Remove Welcome Video", callback_data="adm_del_video"))
    markup.add(types.InlineKeyboardButton(m_text, callback_data="adm_toggle_maint"))
    markup.add(types.InlineKeyboardButton("🖥 Server Stats", callback_data="adm_stats"))
    return markup

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if settings['maintenance'] and message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "⚠️ System is under maintenance.")
    
    is_new = uid not in users_db
    if is_new:
        users_db[uid] = {'points': 10, 'files': []}
        params = message.text.split()
        if len(params) > 1:
            ref_id = params[1]
            if ref_id in users_db and ref_id != uid:
                users_db[ref_id]['points'] += settings.get('points_per_referral', 2)
                try: bot.send_message(int(ref_id), f"🎁 Referral Bonus! User {uid} joined. You got +{settings['points_per_referral']} pts!")
                except: pass
        save_db()

    caption = get_welcome_text(message)
    video = settings.get('welcome_video')
    if video:
        try: bot.send_video(message.chat.id, video, caption=caption, reply_markup=main_keyboard(message.from_user.id))
        except: bot.send_message(message.chat.id, caption, reply_markup=main_keyboard(message.from_user.id))
    else:
        bot.send_message(message.chat.id, caption, reply_markup=main_keyboard(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == "🔗 Referral Link")
def referral_link(message):
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f"🔗 Your Referral Link:\n\n`{ref_link}`\n\nShare this link to get {settings['points_per_referral']} points for every new user!")

@bot.message_handler(func=lambda m: m.text == "📂 My Files")
def show_my_files(message):
    uid = str(message.from_user.id)
    files = users_db.get(uid, {}).get('files', [])
    if not files: return bot.send_message(message.chat.id, "No deployed files.")
    for f_name in files:
        f_path = os.path.normpath(os.path.join(DEPLOY_DIR, f"{uid}_{f_name}"))
        status = "🟢 Running" if f_path in running_processes and running_processes[f_path].poll() is None else "🔴 Stopped"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ RUN", callback_data=f"run_{f_name}_{uid}"),
                   types.InlineKeyboardButton("⏸ STOP", callback_data=f"stop_{f_name}_{uid}"))
        markup.add(types.InlineKeyboardButton("📥 Download", callback_data=f"down_{f_name}_{uid}"),
                   types.InlineKeyboardButton("❌ DELETE", callback_data=f"del_{f_name}_{uid}"))
        bot.send_message(message.chat.id, f"📄 `{f_name}`\nStatus: {status}", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌍 All Files Control" and m.from_user.id == ADMIN_ID)
def admin_files_control(message):
    bot.send_message(message.chat.id, "🔍 Global File Control:")
    for target_uid, data in users_db.items():
        for f_name in data.get('files', []):
            f_path = os.path.normpath(os.path.join(DEPLOY_DIR, f"{target_uid}_{f_name}"))
            status = "🟢" if f_path in running_processes and running_processes[f_path].poll() is None else "🔴"
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("RUN", callback_data=f"run_{f_name}_{target_uid}"),
                types.InlineKeyboardButton("STOP", callback_data=f"stop_{f_name}_{target_uid}"),
                types.InlineKeyboardButton("📥 Download", callback_data=f"down_{f_name}_{target_uid}"),
                types.InlineKeyboardButton("DEL", callback_data=f"del_{f_name}_{target_uid}")
            )
            bot.send_message(message.chat.id, f"👤 User: `{target_uid}`\n📄 File: `{f_name}` {status}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = str(call.from_user.id)
    data = call.data

    # Approval actions are admin-only.
    if data.startswith("approve:") or data.startswith("reject:"):
        if call.from_user.id != ADMIN_ID:
            return bot.answer_callback_query(call.id, "Admin only.", show_alert=True)
        request_id = data.split(":", 1)[1]
        if data.startswith("approve:"):
            return approve_request(call, request_id)
        return reject_request(call, request_id)

    if "_" in data and not data.startswith("adm_"):
        parts = data.split("_")
        action, f_name, target_uid = parts[0], "_".join(parts[1:-1]), parts[-1]
        # Users may control only their own files; admin may control all files.
        if uid != target_uid and call.from_user.id != ADMIN_ID:
            return bot.answer_callback_query(call.id, "You can only control your own files.", show_alert=True)

        f_path = os.path.normpath(os.path.join(DEPLOY_DIR, f"{target_uid}_{f_name}"))

        if action == "stop" and f_path in running_processes:
            running_processes[f_path].terminate()
            del running_processes[f_path]
            bot.answer_callback_query(call.id, "Stopped")
        elif action == "run":
            if run_user_file(f_path, int(target_uid), f_name):
                bot.answer_callback_query(call.id, "Running")
        elif action == "down":
            if os.path.exists(f_path):
                with open(f_path, 'rb') as f:
                    bot.send_document(call.message.chat.id, f)
            else:
                bot.answer_callback_query(call.id, "File not found!")
        elif action == "del":
            if f_path in running_processes:
                running_processes[f_path].terminate()
                del running_processes[f_path]
            if os.path.exists(f_path):
                os.remove(f_path)
            if target_uid in users_db and f_name in users_db[target_uid].get('files', []):
                users_db[target_uid]['files'].remove(f_name)
            save_db()
            bot.delete_message(call.message.chat.id, call.message.message_id)

    if uid == str(ADMIN_ID):
        if data == "adm_toggle_maint":
            settings['maintenance'] = not settings['maintenance']
            save_settings()
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                          reply_markup=admin_keyboard())
        elif data == "adm_broadcast":
            msg = bot.send_message(call.message.chat.id, "📝 Send the message to broadcast:")
            bot.register_next_step_handler(msg, broadcast_logic)
        elif data == "adm_del_video":
            settings['welcome_video'] = None
            save_settings()
            bot.answer_callback_query(call.id, "Welcome Video Deleted.")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                          reply_markup=admin_keyboard())
        elif data == "adm_set_video":
            msg = bot.send_message(call.message.chat.id, "📹 Send me the video:")
            bot.register_next_step_handler(msg, save_video_logic)
        elif data == "adm_add_pts":
            msg = bot.send_message(call.message.chat.id, "👤 Send User ID to add points:")
            bot.register_next_step_handler(
                msg,
                lambda m: bot.register_next_step_handler(
                    bot.send_message(m.chat.id, "💰 How many points?"),
                    lambda p: admin_add_pts(m.text, p.text, m.chat.id)
                )
            )
        elif data == "adm_stats":
            bot.answer_callback_query(
                call.id,
                f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%",
                show_alert=True
            )
        elif data == "adm_pending":
            show_pending_requests(call.message)

def broadcast_logic(message):
    text = message.text
    count = 0
    for uid in users_db:
        try:
            bot.send_message(int(uid), f"📢 Announcement:\n\n{text}")
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Message sent to {count} users.")

def admin_add_pts(target, points, chat_id):
    try:
        if target in users_db:
            users_db[target]['points'] += int(points)
            save_db()
            bot.send_message(chat_id, f"✅ Done! Added {points} to {target}")
        else: bot.send_message(chat_id, "❌ User not found.")
    except: bot.send_message(chat_id, "❌ Invalid input.")

def save_video_logic(message):
    if message.video:
        settings['welcome_video'] = message.video.file_id
        save_settings()
        bot.send_message(message.chat.id, "✅ Welcome Video Set!")
    else: bot.send_message(message.chat.id, "❌ Not a video.")

@bot.message_handler(func=lambda m: m.text == "📤 Deploy File")
def start_deployment(message):
    uid = str(message.from_user.id)
    if settings.get('maintenance') and message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "⚠️ System is under maintenance.")

    if users_db.get(uid, {}).get('points', 0) < settings['hosting_cost']:
        return bot.send_message(message.chat.id, f"❌ Need {settings['hosting_cost']} points.")

    msg = bot.send_message(
        message.chat.id,
        "📤 Send your file (.py, .js or .zip).\n\n"
        "The file will NOT start until the admin approves it."
    )
    bot.register_next_step_handler(msg, process_upload)


def process_upload(message):
    if not message.document:
        return bot.send_message(message.chat.id, "❌ Please send a file/document.")

    f_name = os.path.basename(message.document.file_name)
    uid = str(message.from_user.id)

    if not f_name.lower().endswith(('.py', '.js', '.zip')):
        return bot.send_message(message.chat.id, "❌ Only .py, .js or .zip files are allowed.")

    pending_dir = os.path.join(DEPLOY_DIR, "pending")
    os.makedirs(pending_dir, exist_ok=True)
    safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', f_name)
    pending_path = os.path.normpath(os.path.join(pending_dir, f"{uid}_{safe_name}"))

    try:
        f_info = bot.get_file(message.document.file_id)
        file_content = bot.download_file(f_info.file_path)
        with open(pending_path, 'wb') as f:
            f.write(file_content)

        request_id = f"{uid}:{int(time.time())}:{safe_name}"
        settings.setdefault('pending_approvals', {})
        settings['pending_approvals'][request_id] = {
            'user_id': uid,
            'file_name': f_name,
            'path': pending_path,
            'telegram_file_id': message.document.file_id,
            'status': 'pending',
            'submitted_at': int(time.time())
        }
        save_settings()

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ APPROVE", callback_data=f"approve:{request_id}"),
            types.InlineKeyboardButton("❌ REJECT", callback_data=f"reject:{request_id}")
        )

        admin_text = (
            "🔔 NEW HOSTING REQUEST\n\n"
            f"👤 User ID: `{uid}`\n"
            f"📄 File: `{f_name}`\n"
            f"💰 Cost: {settings['hosting_cost']} points\n"
            "\nChoose an action:"
        )
        bot.send_document(ADMIN_ID, message.document.file_id, caption=admin_text,
                          reply_markup=markup, parse_mode="Markdown")
        bot.send_message(
            message.chat.id,
            f"⏳ `{f_name}` submitted for admin approval.\n\n"
            "You can host it only after the admin approves it.",
            parse_mode="Markdown"
        )
    except Exception as e:
        if os.path.exists(pending_path):
            try:
                os.remove(pending_path)
            except:
                pass
        bot.send_message(message.chat.id, f"❌ Upload Error: {e}")


def pending_approval_list():
    return settings.get('pending_approvals', {})


def approve_request(call, request_id):
    req = pending_approval_list().get(request_id)
    if not req or req.get('status') != 'pending':
        return bot.answer_callback_query(call.id, "Request is no longer pending.", show_alert=True)

    uid = req['user_id']
    f_name = req['file_name']
    pending_path = req['path']
    if not os.path.exists(pending_path):
        req['status'] = 'rejected'
        save_settings()
        return bot.answer_callback_query(call.id, "Pending file is missing.", show_alert=True)

    user_dir = DEPLOY_DIR
    final_name = f"{uid}_{f_name}"
    final_path = os.path.normpath(os.path.join(user_dir, final_name))

    try:
        # ZIP files are approved as uploaded archives and only extracted after approval.
        if f_name.lower().endswith('.zip'):
            extract_dir = os.path.normpath(os.path.join(user_dir, f"{uid}_{os.path.splitext(f_name)[0]}"))
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(pending_path, 'r') as z:
                z.extractall(extract_dir)
            os.remove(pending_path)
            run_path = extract_dir
        else:
            shutil.move(pending_path, final_path)
            run_path = final_path

        # Preserve the existing dependency installation behavior.
        if not os.path.isdir(run_path):
            with open(run_path, 'r', encoding='utf-8', errors='ignore') as f:
                libs = re.findall(r'^(?:import|from)\s+([\w\d_]+)', f.read(), re.MULTILINE)
            for lib in set(libs):
                if lib not in ['os', 'sys', 'time']:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', lib],
                                   stderr=subprocess.DEVNULL)

        if not run_user_file(run_path, int(uid), f_name):
            req['status'] = 'rejected'
            req['decision'] = 'runtime_error'
            save_settings()
            bot.send_message(int(uid),
                             f"❌ Admin approved `{f_name}`, but the file failed to start.\n"
                             "Check the runtime error sent above.",
                             parse_mode="Markdown")
            return bot.answer_callback_query(call.id, "Approved, but runtime failed.", show_alert=True)

        if uid not in users_db:
            users_db[uid] = {'points': 0, 'files': []}

        if users_db[uid].get('points', 0) < settings['hosting_cost']:
            # Do not keep an approved deployment if the user no longer has enough points.
            if run_path in running_processes:
                running_processes[run_path].terminate()
                del running_processes[run_path]
            if os.path.isfile(run_path):
                os.remove(run_path)
            elif os.path.isdir(run_path):
                shutil.rmtree(run_path, ignore_errors=True)
            req['status'] = 'rejected'
            req['decision'] = 'insufficient_points'
            save_settings()
            return bot.answer_callback_query(call.id, "User no longer has enough points.", show_alert=True)

        users_db[uid]['points'] -= settings['hosting_cost']
        if f_name not in users_db[uid].setdefault('files', []):
            users_db[uid]['files'].append(f_name)
        save_db()

        req['status'] = 'approved'
        req['decision'] = 'approved'
        req['approved_at'] = int(time.time())
        save_settings()

        bot.send_message(int(uid),
                         f"✅ APPROVED!\n\n📄 `{f_name}` is now LIVE.\n"
                         f"💰 {settings['hosting_cost']} points deducted.",
                         parse_mode="Markdown")
        bot.edit_message_caption(
            "✅ APPROVED\n\n" + call.message.caption.split("\n\n")[0] +
            f"\n\n📄 `{f_name}` is LIVE.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "File approved and hosted.")
    except Exception as e:
        req['status'] = 'error'
        req['decision'] = str(e)[:500]
        save_settings()
        bot.send_message(int(uid), f"❌ Approval failed: {e}")
        bot.answer_callback_query(call.id, "Approval failed.", show_alert=True)


def reject_request(call, request_id):
    req = pending_approval_list().get(request_id)
    if not req or req.get('status') != 'pending':
        return bot.answer_callback_query(call.id, "Request is no longer pending.", show_alert=True)

    path = req.get('path')
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass

    req['status'] = 'rejected'
    req['decision'] = 'rejected'
    req['rejected_at'] = int(time.time())
    save_settings()

    bot.send_message(
        int(req['user_id']),
        f"❌ REJECTED\n\n📄 `{req['file_name']}` was rejected by the admin.\n"
        "The file was not hosted and no hosting points were deducted.",
        parse_mode="Markdown"
    )
    try:
        bot.edit_message_caption(
            "❌ REJECTED\n\n" + call.message.caption.split("\n\n")[0] +
            f"\n\n📄 `{req['file_name']}` was rejected.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    except:
        pass
    bot.answer_callback_query(call.id, "File rejected.")


@bot.message_handler(func=lambda m: m.text == "💰 My Points")
def my_pts(message):
    pts = users_db.get(str(message.from_user.id), {}).get('points', 0)
    bot.send_message(message.chat.id, f"💰 Balance: {pts} Points", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def show_stats(message):
    uploaders = len([u for u in users_db if len(users_db[u].get('files', [])) > 0])
    bot.send_message(message.chat.id, f"📊 Total Users: {len(users_db)}\n📤 Users with Uploads: {uploaders}\n🤖 Bots Running: {len(running_processes)}")

@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel" and m.from_user.id == ADMIN_ID)
def show_admin_panel(message):
    bot.send_message(message.chat.id, "🎛 Admin Control Center", reply_markup=admin_keyboard())

@bot.message_handler(func=lambda m: m.text == "📞 Contact Owner")
def contact(message): bot.send_message(message.chat.id, "👤 Owner: @wannabimine")

@bot.message_handler(func=lambda m: m.text == "📢 Updates Channel")
def updates(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("JOIN CHANNEL", url=f"https://t.me/{CHANNEL_ID.replace('@codezxyna','')}"))
    bot.send_message(message.chat.id, "📢 Keep updated here:", reply_markup=markup)


def show_pending_requests(message):
    pending = [r for r in settings.get('pending_approvals', {}).values()
               if r.get('status') == 'pending']
    if not pending:
        return bot.send_message(message.chat.id, "✅ No pending hosting requests.")

    bot.send_message(message.chat.id, f"📥 Pending Requests: {len(pending)}")
    for req in pending:
        markup = types.InlineKeyboardMarkup(row_width=2)
        # Find request ID for callback actions.
        rid = next((k for k, v in settings.get('pending_approvals', {}).items() if v is req), None)
        if not rid:
            continue
        markup.add(
            types.InlineKeyboardButton("✅ APPROVE", callback_data=f"approve:{rid}"),
            types.InlineKeyboardButton("❌ REJECT", callback_data=f"reject:{rid}")
        )
        bot.send_document(
            message.chat.id,
            req['telegram_file_id'],
            caption=f"👤 User: `{req['user_id']}`\n📄 File: `{req['file_name']}`\n"
                    "⏳ Status: PENDING",
            reply_markup=markup,
            parse_mode="Markdown"
        )


@bot.message_handler(func=lambda m: m.text == "📝 Pending Requests" and m.from_user.id == ADMIN_ID)
def admin_pending_menu(message):
    show_pending_requests(message)


@bot.message_handler(func=lambda m: m.text == "👥 Users" and m.from_user.id == ADMIN_ID)
def admin_users(message):
    total = len(users_db)
    active = sum(1 for u in users_db.values() if u.get('files'))
    bot.send_message(
        message.chat.id,
        f"👥 USER MANAGEMENT\n\n"
        f"Total Users: {total}\n"
        f"Users With Files: {active}\n"
        f"Pending Requests: {sum(1 for r in settings.get('pending_approvals', {}).values() if r.get('status') == 'pending')}"
    )


@bot.message_handler(func=lambda m: m.text == "⚙️ Hosting Settings" and m.from_user.id == ADMIN_ID)
def hosting_settings(message):
    bot.send_message(
        message.chat.id,
        f"⚙️ HOSTING SETTINGS\n\n"
        f"💰 Hosting Cost: {settings.get('hosting_cost', 4)} points\n"
        f"🎁 Referral Reward: {settings.get('points_per_referral', 2)} points\n"
        f"🔧 Maintenance: {'ON' if settings.get('maintenance') else 'OFF'}"
    )


@bot.message_handler(func=lambda m: m.text == "📜 Approval History" and m.from_user.id == ADMIN_ID)
def approval_history(message):
    items = list(settings.get('pending_approvals', {}).values())[-15:]
    if not items:
        return bot.send_message(message.chat.id, "📜 No approval history.")
    lines = ["📜 LAST APPROVAL REQUESTS\n"]
    for r in reversed(items):
        lines.append(f"• {r.get('file_name')} | {r.get('status')} | User {r.get('user_id')}")
    bot.send_message(message.chat.id, "\n".join(lines))


# Expanded admin keyboard with approval management, user management and settings.
def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    m_text = "🔴 Maintenance: ON" if settings['maintenance'] else "🟢 Maintenance: OFF"
    pending_count = sum(1 for r in settings.get('pending_approvals', {}).values()
                        if r.get('status') == 'pending')
    markup.add(
        types.InlineKeyboardButton(f"📝 Pending ({pending_count})", callback_data="adm_pending"),
        types.InlineKeyboardButton("➕ Add Points", callback_data="adm_add_pts")
    )
    markup.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🎥 Welcome Video", callback_data="adm_set_video")
    )
    if settings.get('welcome_video'):
        markup.add(types.InlineKeyboardButton("❌ Remove Video", callback_data="adm_del_video"))
    markup.add(
        types.InlineKeyboardButton(m_text, callback_data="adm_toggle_maint"),
        types.InlineKeyboardButton("🖥 Server Stats", callback_data="adm_stats")
    )
    return markup


# Expanded user keyboard.
def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📢 Updates Channel"))
    markup.add(types.KeyboardButton("📤 Deploy File"), types.KeyboardButton("📂 My Files"))
    markup.add(types.KeyboardButton("💰 My Points"), types.KeyboardButton("🔗 Referral Link"))
    markup.add(types.KeyboardButton("📊 Statistics"), types.KeyboardButton("📞 Contact Owner"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("👑 Admin Panel"), types.KeyboardButton("🌍 All Files Control"))
        markup.add(types.KeyboardButton("📝 Pending Requests"), types.KeyboardButton("👥 Users"))
        markup.add(types.KeyboardButton("⚙️ Hosting Settings"), types.KeyboardButton("📜 Approval History"))
    return markup


if __name__ == "__main__":
    print("🤖 ⚡ ᴢxʏɴ ᴘʀᴇᴍɪᴜᴍ ʜᴏsᴛɪɴɢ ʙᴏᴛ  ⚡ Online...")
    bot.infinity_polling()
