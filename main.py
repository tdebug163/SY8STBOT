import telebot
import requests
import sqlite3
import random
import datetime

# --- الإعدادات الأساسية ---
import os

TOKEN = os.environ.get("BOT_TOKEN")

bot = TeleBot(TOKEN, parse_mode='HTML')


ADMINS = [445421092, 729501226]
LOG_CHANNEL = "-1004418071359"
BOT_USERNAME = "SYU88BOT"

# --- الروابط المخفية والكليشات الثابتة ---
LINK_UPDATE = '<a href="https://t.me/BOTATE/137">✨ تحديث جديد لبوت صارحني .</a>'
LINK_NEW_CH = '<a href="https://t.me/+kyKBijTbDBxlY2Nk">- فضلاً تابع قناتنا {جديدنا على التيليجرام} 🤍🌿</a>'
LINK_ILLUSION = '<a href="http://t.me/Oneillusion">- فضلاً تابع قناتنا {وَهم - illusion} 💜🍃</a>'
LINK_DONATE = '<a href="http://t.me/Oneillusion">- تبرع لإستمرار عمل بوت صارحني 🎁</a>'
LINK_USER_HIDDEN = '<a href="http://t.me/Oneillusion">( المستخدم )</a>'

# ================== قاعدة البيانات (SQLite3) ==================

conn = sqlite3.connect('sarahni.db', check_same_thread=False)
c = conn.cursor()

# إنشاء الجداول
c.execute('''CREATE TABLE IF NOT EXISTS states (user_id INTEGER PRIMARY KEY, target_id INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (receiver_id INTEGER, message_id INTEGER, sender_id INTEGER, PRIMARY KEY(receiver_id, message_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS replies (user_id INTEGER, reply_msg_id INTEGER, sender_id INTEGER, sender_msg_id INTEGER, PRIMARY KEY(user_id, reply_msg_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS bans (user_id INTEGER, banned_id INTEGER, PRIMARY KEY(user_id, banned_id))''')
conn.commit()

# دوال مساعدة لقاعدة البيانات
def set_state(user_id, target_id):
    c.execute("INSERT OR REPLACE INTO states (user_id, target_id) VALUES (?, ?)", (user_id, target_id))
    conn.commit()

def get_state(user_id):
    c.execute("SELECT target_id FROM states WHERE user_id=?", (user_id,))
    res = c.fetchone()
    return res[0] if res else None

def del_state(user_id):
    c.execute("DELETE FROM states WHERE user_id=?", (user_id,))
    conn.commit()

def save_msg(receiver_id, msg_id, sender_id):
    c.execute("INSERT OR REPLACE INTO messages (receiver_id, message_id, sender_id) VALUES (?, ?, ?)", (receiver_id, msg_id, sender_id))
    conn.commit()

def get_msg_sender(receiver_id, msg_id):
    c.execute("SELECT sender_id FROM messages WHERE receiver_id=? AND message_id=?", (receiver_id, msg_id))
    res = c.fetchone()
    return res[0] if res else None

def save_reply(user_id, reply_msg_id, sender_id, sender_msg_id):
    c.execute("INSERT OR REPLACE INTO replies (user_id, reply_msg_id, sender_id, sender_msg_id) VALUES (?, ?, ?, ?)", (user_id, reply_msg_id, sender_id, sender_msg_id))
    conn.commit()

def get_reply(user_id, reply_msg_id):
    c.execute("SELECT sender_id, sender_msg_id FROM replies WHERE user_id=? AND reply_msg_id=?", (user_id, reply_msg_id))
    return c.fetchone()

def del_reply(user_id, reply_msg_id):
    c.execute("DELETE FROM replies WHERE user_id=? AND reply_msg_id=?", (user_id, reply_msg_id))
    conn.commit()

def ban_user(user_id, banned_id):
    c.execute("INSERT OR IGNORE INTO bans (user_id, banned_id) VALUES (?, ?)", (user_id, banned_id))
    conn.commit()

def unban_user(user_id, banned_id):
    c.execute("DELETE FROM bans WHERE user_id=? AND banned_id=?", (user_id, banned_id))
    conn.commit()

def is_banned(user_id, target_id):
    c.execute("SELECT 1 FROM bans WHERE user_id=? AND banned_id=?", (user_id, target_id))
    return bool(c.fetchone())

def unban_all(user_id):
    c.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
    conn.commit()

# ================== Raw API Requests للملصقات الملونة ==================

def raw_send_message(chat_id, text, reply_markup=None, disable_preview=True, reply_to_message_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    if reply_to_message_id:
        data["reply_to_message_id"] = reply_to_message_id
        
    response = requests.post(url, json=data)
    try:
        return response.json()
    except:
        return {}

def raw_edit_message(chat_id, message_id, text, reply_markup=None, disable_preview=True):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(url, json=data)

# ================== الكليشات والأزرار الملونة (Raw Keyboards) ==================

START_TEXT = f"""اهلاً بك: 

▪️ بوت صارحني

▫️ احصل على نقد بناء بسرية تامة من زملائك في العمل وأصدقائك.

🌐 احصل على الرابط الخاص بك .
💌 إقرأ ما كتبه الناس عنك .
⚙️ أوامر البوت - /help
{LINK_UPDATE}

{LINK_NEW_CH}"""

TERMS_TEXT = f"""📝 شروط الاستخدام

🔘 من خلال استخدامك لبوت صارحني، فإنك توافق على الالتزام بالشروط والأحكام المنصوص عليها لذا يجب عليك الاطلاع على هذه الأحكام وأخدها بعين الاعتبار:

1️⃣. قبول الإتفاقية
من خلال استخدامك لهذا البوت، فهذا يشير الى موافقتك الكاملة على قبول جميع الشروط والأحكام الواردة هنا، يجب عدم استخدام هذا البوت في حال كنت غير موافق على أيّ من هذه الشروط والأحكام القياسية.

2️⃣. حقوق الملكية الفردية
كافة المحتوى المعروض على هذا البوت من صور وموسيقى ورسوم وغيرها هي ملك خاص للمرسل لا تمثل بوت صارحني بشيء.
نحن نقدم لك صلاحية استخدام البوت وإرسال الرسائل لأغراض شخصية فقط ولا يجوز بأي شكل من الأشكال استخدامه لأغراض تجارية.

3️⃣. القيود
▫️ في حال استخدامك لهذا البوت يمنع عليك نشر الكراهية أو العنصرية أو كلام بذيء أو محتوى اباحي.

4️⃣. إخلاء المسؤولية
إن وصولك إلى البوت واستخدامك للميزات الخاصة به يقع على مسؤوليك الخاصة.

5️⃣. خصوصيتك
الرجاء قراءة قسم سياسة الخصوصية في البوت.

▫️ تم ٱخر تعديل لشروط الاستخدام في : 19/06/2022

▪️ إذا كان لديك أيّ سؤال راسلنا : @RSaied_Bot

{LINK_NEW_CH}"""

PRIVACY_TEXT = f"""🔐 سياسة الخصوصية

🔘 في بوت صارحني، ندرك أن خصوصية معلوماتك الشخصية هامة لك ولنا.

1️⃣. ملفات التخزين المؤقت:
كما هو الحال مع معظم بوتات تيليجرام يشمل ذلك id حسابك الشخصي الذي نحتاجه للوصل بينك وبين المستخدمين.

2️⃣. خصوصية ارسال الرسائل:
يتم تشفير الرسائل لدى الطرفين دون الإفصاح عن أيّ هوية شخصية للمرسل أو للمستلم لضمان خصوصية الإرسال.

3️⃣. خصوصية الرد:
يتم تضمين id حساب المرسل مع الرسالة وتشفيره لغرض الرد عليه دون الكشف عن هويته.

⁉️. أسئلة متكررة:
𝟏. هل يمكن للمستخدم معرفة معلومات المرسل؟
• لا لايمكن لأي شخص الوصول إلى أيّ معلومة عن المرسل.

𝟐. هل يمكن لمطور بوت صارحني معرفة معلومات المرسل؟
• لا لايمكن لمطور البوت معرفة ذلك وإنما يحق له الوصول فقط للرسائل المبلغ عنها بواسطة /report.

▫️ تم ٱخر تعديل لسياسة الخصوصية في : 04/08/2022

▪️ للتواصل : @RSaied_Bot

{LINK_NEW_CH}"""

HELP_TEXT = f"""اهلاً بك: 

⁉️ إذا ظهرت لك رسالة :
{{▪ رسالة غير مفهومة .}}
🔘 يوجد لديك 4 أسباب لظهور هذه الرسالة

1️⃣. لم تقم بالدخول إلى رابط أيّ شخص حتى ترسل رسائل المصارحة له
2️⃣. قمت بارسال رسالتك دون عمل رد على شيء
3️⃣. قمت بعمل رد على رسالة بوت وليس على رسالة الشخص الذي قام بارسال رسالة صراحة لك
4️⃣. قمت بعمل رد على رسالة مصارحة وصلتك قبل أكثر من يومين (هذا التقييد من تيليجرام وليس منا)

❗️ملاحظة : إن واجهتك مشاكل أخرى لاتتردد في إخبارنا بها على بوت التواصل : @RSaied_Bot

{LINK_UPDATE}

🌟 بعض الأوامر الخاصة بك:

▪️ ️/ban -  مع الرد على الرسالة  - حظر
▫ ️/unban  - مع الرد على الرسالة - رفع الحظر
🔘 /unbanall - لرفع الحظر عن جميع المحظورين - رفع حظر الجميع
⚠️ /report - للابلاغ عن محتوى مخالف شروط الاستخدام - ابلاغ
🖇 /link - لإنشاء رابط صراحة خاص بك - الرابط
🚸 /exit - للخروج من رابط الصراحة الذي دخلت إليه - خروج
🔏 /privacy - لقراءة سياسة الخصوصية بوت صارحني
📝 /termsofuse - لقراءة شروط إستخدام بوت صارحني

{LINK_NEW_CH}"""

ABOUT_TEXT = f"""📩 بوت صارحني
▫️صارحني لتلقي النقد البناء بسرية تامة لتنمية الذات مع الحفاظ على سرية هوية المرسل وخصوصية الرسائل

▫️ احصل على نقد بناء بسرية تامة من زملائك في العمل وأصدقائك.

▪️ الفائدة .
▫️عزز نقاط القوة لديك
▫️عالج نقاط ضعفك
▫️عزز صداقاتك بمعرفة مزاياك وعيوبك
▫️مكّن أصحابك من مصارحتك

📱 يتيح لك بوت صارحني مشاركة الرابط والرد على الرسائل بسهولة وحظر المستخدمين المزعجين

🔘 هل أنت مستعد لمعرفة ملاحظات الناس عنك بدون أن تعرفهم ؟

💡 إصدار البوت : V1.4
🐘 إصدار ملف البوت : Php8.1.13
👨🏻‍🔧 مبرمج البوت : @RSaied_Bot

{LINK_NEW_CH}"""

def get_main_markup():
    # هنا تم تلوين الزر الخاص بالرابط للون الأزرق style: primary
    return {
        "inline_keyboard": [
            [
                {"text": "🔐 سياسة الخصوصية", "callback_data": "privacy"},
                {"text": "📝 شروط الاستخدام", "callback_data": "terms"}
            ],
            [
                {"text": "💡 عن بوت صارحني", "callback_data": "about"},
                {"text": "⚙️ أوامر البوت", "callback_data": "help"}
            ],
            [
                {"text": "🌐 إنشاء رابط خاص", "callback_data": "create_link", "style": "primary"}
            ]
        ]
    }

def get_back_markup(to="main", extra=None):
    keys = []
    if extra == "privacy":
        keys.append([{"text": "🔐 سياسة الخصوصية", "callback_data": "privacy"}])
    elif extra == "terms":
        keys.append([{"text": "📝 شروط الاستخدام", "callback_data": "terms"}])
    keys.append([{"text": "🔙 رجوع ...", "callback_data": to}])
    return {"inline_keyboard": keys}

# ================== الأوامر الرئيسية ==================

@bot.message_handler(commands=['start'])
def start_handler(message):
    payload = message.text.replace("/start", "").strip()
    
    if payload:
        try:
            target_id = int(payload, 16) # فك تشفير الرابط
            if target_id == message.from_user.id:
                raw_send_message(message.chat.id, f"لا يمكنك مصارحة نفسك!\n\n{LINK_NEW_CH}")
                return
            
            set_state(message.from_user.id, target_id)
            
            text = f"""▪️ اهلاً بك ..
▫️ سوف يتم إرسال الرسالة الى {LINK_USER_HIDDEN} بسرية تامة .
▫️صارحني انا مستعد لمواجهة الصراحة .
▫️اكتب ماتريد في هذه المحدثة وسوف يتم إرسالها إلى {LINK_USER_HIDDEN}

💡 عند الانتهاء قم بالضغط على زر (🚫 الغاء إرسال الرسائل) أو أرسل /exit

{LINK_ILLUSION}"""
            raw_send_message(message.chat.id, text)
            return
        except:
            pass

    # الواجهة الرئيسية
    raw_send_message(message.chat.id, START_TEXT, reply_markup=get_main_markup())

@bot.message_handler(commands=['help', 'privacy', 'termsofuse', 'link', 'exit'])
def commands_handler(message):
    cmd = message.text.split()[0].lower()
    if cmd == '/help':
        raw_send_message(message.chat.id, HELP_TEXT, reply_markup=get_back_markup())
    elif cmd == '/privacy':
        raw_send_message(message.chat.id, PRIVACY_TEXT, reply_markup=get_back_markup(extra="terms"))
    elif cmd == '/termsofuse':
        raw_send_message(message.chat.id, TERMS_TEXT, reply_markup=get_back_markup(extra="privacy"))
    elif cmd == '/link':
        send_user_link(message.chat.id, message.from_user.id)
    elif cmd == '/exit':
        if get_state(message.from_user.id):
            del_state(message.from_user.id)
            raw_send_message(message.chat.id, f"🚫 تم إلغاء إرسال الرسائل والخروج بنجاح.\n\n{LINK_NEW_CH}")
        else:
            raw_send_message(message.chat.id, f"أنت لست في وضع المراسلة حالياً.\n\n{LINK_NEW_CH}")

def send_user_link(chat_id, user_id):
    hex_id = hex(user_id)[2:]
    link = f"http://t.me/{BOT_USERNAME}?start={hex_id}"
    text = f"""▪️ الرابط الخاص بك .

▫️ {link}

▫️ يمكنك نشر الرابط في قروبات التيليجرام او بين أصدقائك او مواقع التواصل الإجتماعي.

🖇 شرح استعمال بوت صارحني داخل القنوات

▪️حانت لحظة الصراحة .

{LINK_NEW_CH}"""
    
    # الزر الأزرق لنسخ الرابط
    markup = {
        "inline_keyboard": [
            [{"text": "نسخ الرابط", "url": f"https://t.me/share/url?url={link}", "style": "primary"}]
        ]
    }
    raw_send_message(chat_id, text, reply_markup=markup)

# ================== الكول باك (الإنلاين) ==================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == "terms":
            raw_edit_message(call.message.chat.id, call.message.message_id, TERMS_TEXT, reply_markup=get_back_markup(extra="privacy"))
        elif call.data == "privacy":
            raw_edit_message(call.message.chat.id, call.message.message_id, PRIVACY_TEXT, reply_markup=get_back_markup(extra="terms"))
        elif call.data == "help":
            raw_edit_message(call.message.chat.id, call.message.message_id, HELP_TEXT, reply_markup=get_back_markup())
        elif call.data == "about":
            raw_edit_message(call.message.chat.id, call.message.message_id, ABOUT_TEXT, reply_markup=get_back_markup())
        elif call.data == "main":
            raw_edit_message(call.message.chat.id, call.message.message_id, START_TEXT, reply_markup=get_main_markup())
        elif call.data == "create_link":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_user_link(call.message.chat.id, call.from_user.id)
        elif call.data == "fake_reply":
            bot.answer_callback_query(call.id, "قم بعمل رد (Reply) على الرسالة لكتابة ردك.")
        elif call.data == "alert_new_msg":
            bot.answer_callback_query(call.id, "سبحان الله 💜", show_alert=False)
        elif call.data.startswith("undo_"):
            reply_msg_id = int(call.data.split("_")[1])
            reply_data = get_reply(call.from_user.id, reply_msg_id)
            if reply_data:
                sender_id, sender_msg_id = reply_data
                try:
                    bot.delete_message(sender_id, sender_msg_id)
                    text = f"🗑 تم استرداد الرسالة بنجاح \n\n{LINK_NEW_CH}\n\n{LINK_DONATE} ."
                    raw_edit_message(call.message.chat.id, call.message.message_id, text)
                    del_reply(call.from_user.id, reply_msg_id)
                except:
                    bot.answer_callback_query(call.id, "لم أتمكن من استرداد الرسالة، ربما مرت فترة طويلة أو تم مسحها.")
            else:
                bot.answer_callback_query(call.id, "انتهت صلاحية الاسترداد.")
    except Exception as e:
        pass

# ================== استقبال الرسائل والردود ==================

@bot.message_handler(func=lambda message: True)
def text_messages(message):
    user_id = message.from_user.id
    text = message.text

    # حالة 1: المستخدم يرد على رسالة صراحة وصلته
    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id
        sender_id = get_msg_sender(user_id, replied_msg_id)
        
        if sender_id:
            # أوامر الرد (حظر، فك حظر، ابلاغ)
            if text == "/ban":
                ban_user(user_id, sender_id)
                raw_send_message(message.chat.id, f"🚷 تم حظر صاحب هذه الرسالة بنجاح\n\n{LINK_NEW_CH}\n\n{LINK_DONATE} .", reply_to_message_id=message.message_id)
                return
            elif text == "/unban":
                unban_user(user_id, sender_id)
                raw_send_message(message.chat.id, f"✅ تم رفع الحظر عن صاحب هذه الرسالة بنجاح.\n\n{LINK_NEW_CH}", reply_to_message_id=message.message_id)
                return
            elif text == "/report":
                report_code = random.randint(100000000, 999999999)
                rep_text = f"""🚨 شكراً لك! تم إستلام إبلاغك عن الرسالة .
🔘 كود الإبلاغ للمراجعة #report_{report_code} .
♻️ سيتم مراجعة الإبلاغ خلال 24 ساعة القادمة وسنوافيك بالنتيجة .
🪄 الرجاء استخدام هذه الميزة فقط إذا لزم الأمر أو سنتجاهل إبلاغاتك .

{LINK_NEW_CH}

{LINK_DONATE} ."""
                raw_send_message(message.chat.id, rep_text, reply_to_message_id=message.message_id)
                return
            
            # الرد العادي على المرسل
            try:
                markup = {"inline_keyboard": [[{"text": "⁣💌 وصلتك رسالة جديدة", "callback_data": "alert_new_msg"}]]}
                resp = raw_send_message(sender_id, text, reply_markup=markup)
                
                if resp.get("ok"):
                    sent_msg_id = resp["result"]["message_id"]
                    
                    # زر الاسترداد باللون الأحمر style: danger
                    undo_markup = {
                        "inline_keyboard": [
                            [{"text": "🗑 استرداد الرد", "callback_data": f"undo_{message.message_id}", "style": "danger"}]
                        ]
                    }
                    success_text = f"✅ تم الرد على هذه الرسالة بنجاح\n\n{LINK_NEW_CH}\n\n{LINK_DONATE} ."
                    raw_send_message(message.chat.id, success_text, reply_markup=undo_markup, reply_to_message_id=message.message_id)
                    
                    # حفظ العلاقة للاسترداد اللاحق
                    save_reply(user_id, message.message_id, sender_id, sent_msg_id)
            except Exception as e:
                raw_send_message(message.chat.id, f"تعذر إرسال الرد، ربما قام الشخص بحظر البوت.\n\n{LINK_NEW_CH}", reply_to_message_id=message.message_id)
            return

    # معالجة أمر فك الحظر للكل
    if text == "/unbanall":
        unban_all(user_id)
        raw_send_message(user_id, f"✅ تم رفع الحظر عن جميع المحظورين بنجاح.\n\n{LINK_NEW_CH}")
        return

    # حالة 2: المستخدم داخل وضع إرسال صراحة لشخص (الحصول من DB)
    target_id = get_state(user_id)
    if target_id:
        if is_banned(target_id, user_id):
            # تمويه بالنجاح في حال كان محظوراً
            raw_send_message(user_id, f"✅ تم إرسال رسالتك بنجاح .\n\n{LINK_ILLUSION}\n\n{LINK_DONATE}")
            return
            
        now = datetime.datetime.now().strftime("%Y/%m/%d - %I:%M:%S %p")
        
        # إذا كان المستلم أدمن
        if target_id in ADMINS:
            username_display = message.from_user.username or 'بدون_يوزر'
            admin_msg = f"""المرسل: <a href="tg://user?id={user_id}">{message.from_user.first_name}</a> --- @{username_display}
---
{text}
---"""
            resp = raw_send_message(target_id, admin_msg)
            if resp.get("ok"):
                save_msg(target_id, resp["result"]["message_id"], user_id)
        else:
            # مستخدم عادي (توصل مجهولة وتتخزن في القناة)
            user_msg = f"""⁣💌 وصلتك رسالة جديدة
⏱ وقت الرسالة: {now}
----
{text}
----

{LINK_DONATE}"""
            fake_reply_markup = {"inline_keyboard": [[{"text": "💡يمكنك الرد بعمل رد على هذه الرسالة", "callback_data": "fake_reply"}]]}
            
            resp = raw_send_message(target_id, user_msg, reply_markup=fake_reply_markup)
            if resp.get("ok"):
                save_msg(target_id, resp["result"]["message_id"], user_id)
                
                # إرسال نسخة لقناة السجل
                username_display = message.from_user.username or 'بدون_يوزر'
                log_text = f"""رساله جديده ✉️
المرسل: <a href="tg://user?id={user_id}">{message.from_user.first_name}</a> --- @{username_display}
المستلم: <a href="tg://user?id={target_id}">صاحب الرابط</a> 
محتوى الرساله : {text}"""
                raw_send_message(LOG_CHANNEL, log_text)

        # تأكيد الإرسال للمرسل السري
        success_send = f"✅ تم إرسال رسالتك بنجاح .\n\n{LINK_ILLUSION}\n\n{LINK_DONATE}"
        raw_send_message(user_id, success_send)
        return

    # حالة 3: رسالة غير مفهومة
    err_text = f"▪ رسالة غير مفهومة ، أرسل /help\n\n{LINK_NEW_CH}\n\n{LINK_DONATE} ."
    raw_send_message(user_id, err_text)

# ================== التشغيل ==================
if __name__ == "__main__":
    print("Bot is running securely with DB & Raw Colored Buttons...")
    bot.infinity_polling(skip_pending=True)
