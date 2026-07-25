import os
import asyncio
import random
import datetime
import aiohttp
import aiosqlite
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, BotCommand
from aiohttp import web

# --- الإعدادات الأساسية تسحب من ريندر ---
TOKEN = os.environ.get("BOT_TOKEN")
API_ID = 28797361 # يفضل وضع API_ID الخاص بك من my.telegram.org (استخدمت رقم افتراضي يعمل للتيست)
API_HASH = "771041b32e83ab232e066b7adeee700b" # افتراضي 


ADMINS = [445421092, 729501226]
LOG_CHANNEL = "-1004418071359"
BOT_USERNAME = "SYU88BOT"

# --- الروابط المخفية والكليشات الثابتة ---
LINK_UPDATE = '<a href="https://t.me/BOTATE/137">✨ تحديث جديد لبوت صارحني .</a>'
LINK_NEW_CH = '<a href="https://t.me/+kyKBijTbDBxlY2Nk">- فضلاً تابع قناتنا {جديدنا على التيليجرام} 🤍🌿</a>'
LINK_ILLUSION = '<a href="http://t.me/Oneillusion">- فضلاً تابع قناتنا {وَهم - illusion} 💜🍃</a>'
LINK_DONATE = '<a href="http://t.me/Oneillusion">- تبرع لإستمرار عمل بوت صارحني 🎁</a>'
LINK_USER_HIDDEN = '<a href="http://t.me/Oneillusion">( المستخدم )</a>'

# ================== قاعدة البيانات السريعة (aiosqlite) ==================

async def init_db():
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute('PRAGMA journal_mode=WAL;')
        await db.execute('PRAGMA synchronous=NORMAL;')
        await db.execute('CREATE TABLE IF NOT EXISTS states (user_id INTEGER PRIMARY KEY, target_id INTEGER)')
        await db.execute('CREATE TABLE IF NOT EXISTS messages (receiver_id INTEGER, message_id INTEGER, sender_id INTEGER, PRIMARY KEY(receiver_id, message_id))')
        await db.execute('CREATE TABLE IF NOT EXISTS replies (user_id INTEGER, reply_msg_id INTEGER, sender_id INTEGER, sender_msg_id INTEGER, PRIMARY KEY(user_id, reply_msg_id))')
        await db.execute('CREATE TABLE IF NOT EXISTS bans (user_id INTEGER, banned_id INTEGER, PRIMARY KEY(user_id, banned_id))')
        await db.commit()

async def set_state(user_id, target_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("INSERT OR REPLACE INTO states (user_id, target_id) VALUES (?, ?)", (user_id, target_id))
        await db.commit()

async def get_state(user_id):
    async with aiosqlite.connect('sarahni.db') as db:
        async with db.execute("SELECT target_id FROM states WHERE user_id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def del_state(user_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("DELETE FROM states WHERE user_id=?", (user_id,))
        await db.commit()

async def save_msg(receiver_id, msg_id, sender_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("INSERT OR REPLACE INTO messages (receiver_id, message_id, sender_id) VALUES (?, ?, ?)", (receiver_id, msg_id, sender_id))
        await db.commit()

async def get_msg_sender(receiver_id, msg_id):
    async with aiosqlite.connect('sarahni.db') as db:
        async with db.execute("SELECT sender_id FROM messages WHERE receiver_id=? AND message_id=?", (receiver_id, msg_id)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_reply(user_id, reply_msg_id, sender_id, sender_msg_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("INSERT OR REPLACE INTO replies (user_id, reply_msg_id, sender_id, sender_msg_id) VALUES (?, ?, ?, ?)", (user_id, reply_msg_id, sender_id, sender_msg_id))
        await db.commit()

async def get_reply(user_id, reply_msg_id):
    async with aiosqlite.connect('sarahni.db') as db:
        async with db.execute("SELECT sender_id, sender_msg_id FROM replies WHERE user_id=? AND reply_msg_id=?", (user_id, reply_msg_id)) as cursor:
            return await cursor.fetchone()

async def del_reply(user_id, reply_msg_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("DELETE FROM replies WHERE user_id=? AND reply_msg_id=?", (user_id, reply_msg_id))
        await db.commit()

async def ban_user(user_id, banned_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("INSERT OR IGNORE INTO bans (user_id, banned_id) VALUES (?, ?)", (user_id, banned_id))
        await db.commit()

async def unban_user(user_id, banned_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("DELETE FROM bans WHERE user_id=? AND banned_id=?", (user_id, banned_id))
        await db.commit()

async def is_banned(user_id, target_id):
    async with aiosqlite.connect('sarahni.db') as db:
        async with db.execute("SELECT 1 FROM bans WHERE user_id=? AND banned_id=?", (user_id, target_id)) as cursor:
            return bool(await cursor.fetchone())

async def unban_all(user_id):
    async with aiosqlite.connect('sarahni.db') as db:
        await db.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
        await db.commit()

# ================== Raw API للرسائل الملونة (aiohttp) ==================

async def raw_send_message(chat_id, text, reply_markup=None, reply_to_message_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    if reply_to_message_id:
        data["reply_to_message_id"] = reply_to_message_id

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            return await resp.json()

async def raw_edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            return await resp.json()

# ================== النصوص والكليشات ==================

START_TEXT = f"اهلاً بك: \n\n▪️ بوت صارحني\n\n▫️ احصل على نقد بناء بسرية تامة من زملائك في العمل وأصدقائك.\n\n🌐 احصل على الرابط الخاص بك .\n💌 إقرأ ما كتبه الناس عنك .\n⚙️ أوامر البوت - /help\n{LINK_UPDATE}\n\n{LINK_NEW_CH}"

TERMS_TEXT = f"📝 شروط الاستخدام\n\n🔘 من خلال استخدامك لبوت صارحني، فإنك توافق على الالتزام بالشروط والأحكام المنصوص عليها لذا يجب عليك الاطلاع على هذه الأحكام وأخدها بعين الاعتبار:\n\n1️⃣. قبول الإتفاقية\nمن خلال استخدامك لهذا البوت، فهذا يشير الى موافقتك الكاملة على قبول جميع الشروط والأحكام الواردة هنا، يجب عدم استخدام هذا البوت في حال كنت غير موافق على أيّ من هذه الشروط والأحكام القياسية.\n\n2️⃣. حقوق الملكية الفردية\nنحن نقدم لك صلاحية استخدام البوت وإرسال الرسائل لأغراض شخصية فقط ولا يجوز بأي شكل من الأشكال استخدام البوت لأغراض تجارية.\n\n3️⃣. القيود\n▫️ يمنع نشر الكراهية أو العنصرية أو كلام بذيء أو محتوى اباحي.\n\n4️⃣. إخلاء المسؤولية\nإن وصولك إلى البوت واستخدامك للميزات الخاصة به يقع على مسؤوليك الخاصة.\n\n5️⃣. خصوصيتك\nالرجاء قراءة قسم سياسة الخصوصية في البوت.\n\n▫️ تم ٱخر تعديل لشروط الاستخدام في : 19/06/2022\n\n▪️ إذا كان لديك أيّ سؤال راسلنا : @RSaied_Bot\n\n{LINK_NEW_CH}"

PRIVACY_TEXT = f"🔐 سياسة الخصوصية\n\n🔘 في بوت صارحني، ندرك أن خصوصية معلوماتك الشخصية هامة لك ولنا.\n\n1️⃣. ملفات التخزين المؤقت:\nنقوم بجمع واستخدام id حسابك الشخصي للوصل بينك وبين المستخدمين.\n\n2️⃣. خصوصية ارسال الرسائل:\nيتم تشفير الرسائل لدى الطرفين دون الإفصاح عن أيّ هوية شخصية للمرسل.\n\n3️⃣. خصوصية الرد:\nيتم تضمين id المرسل مع الرسالة للرد عليه دون الكشف عن هويته.\n\n⁉️. أسئلة متكررة:\n𝟏. هل يمكن للمستخدم معرفة معلومات المرسل؟\n• لا.\n\n𝟐. هل يمكن للمطور معرفة معلومات المرسل؟\n• لا، يحق له الوصول فقط إلى الرسائل المبلغ عنها.\n\n▫️ تم ٱخر تعديل لسياسة الخصوصية في : 04/08/2022\n\n▪️ للتواصل : @RSaied_Bot\n\n{LINK_NEW_CH}"

HELP_TEXT = f"اهلاً بك: \n\n⁉️ إذا ظهرت لك رسالة :\n{{▪ رسالة غير مفهومة .}}\n🔘 يوجد لديك 4 أسباب لظهور هذه الرسالة\n\n1️⃣. لم تقم بالدخول إلى رابط أيّ شخص حتى ترسل رسائل المصارحة له\n2️⃣. قمت بارسال رسالتك دون عمل رد على شيء\n3️⃣. قمت بعمل رد على رسالة بوت وليس على رسالة الشخص\n4️⃣. قمت بعمل رد على رسالة مصارحة وصلتك قبل أكثر من يومين\n\n❗️ملاحظة : إن واجهتك مشاكل تواصل معنا : @RSaied_Bot\n\n{LINK_UPDATE}\n\n🌟 بعض الأوامر الخاصة بك:\n\n▪️ ️/ban -  مع الرد على الرسالة  - حظر\n▫ ️/unban  - مع الرد على الرسالة - رفع الحظر\n🔘 /unbanall - لرفع الحظر عن جميع المحظورين\n⚠️ /report - للابلاغ عن محتوى مخالف - ابلاغ\n🖇 /link - لإنشاء رابط صراحة خاص بك\n🚸 /exit - للخروج من رابط الصراحة\n🔏 /privacy - لقراءة سياسة الخصوصية\n📝 /termsofuse - لقراءة شروط الإستخدام\n\n{LINK_NEW_CH}"

ABOUT_TEXT = f"📩 بوت صارحني\n▫️صارحني لتلقي النقد البناء بسرية تامة لتنمية الذات مع الحفاظ على سرية هوية المرسل\n\n▪️ الفائدة .\n▫️عزز نقاط القوة لديك\n▫️عالج نقاط ضعفك\n▫️مكّن أصحابك من مصارحتك\n\n📱 يتيح لك بوت صارحني مشاركة الرابط والرد على الرسائل بسهولة\n\n🔘 هل أنت مستعد لمعرفة ملاحظات الناس عنك بدون أن تعرفهم ؟\n\n💡 إصدار البوت : V1.4\n🐘 إصدار ملف البوت : Php8.1.13\n👨🏻‍🔧 مبرمج البوت : @RSaied_Bot\n\n{LINK_NEW_CH}"

def get_main_markup():
    return {
        "inline_keyboard": [
            [{"text": "🎁 تبرع - Donate", "callback_data": "donate_btn", "style": "success"}],
            [
                {"text": "🔐 سياسة الخصوصية", "callback_data": "privacy"},
                {"text": "📝 شروط الاستخدام", "callback_data": "terms"}
            ],
            [
                {"text": "💡 عن بوت صارحني", "callback_data": "about"},
                {"text": "⚙️ أوامر البوت", "callback_data": "help"}
            ],
            [{"text": "🌐 إنشاء رابط خاص", "callback_data": "create_link", "style": "primary"}]
        ]
    }

def get_back_markup(to="main", extra=None):
    keys = []
    if extra == "privacy":
        keys.append([{"text": "🔐 سياسة الخصوصية", "callback_data": "privacy"}])
    elif extra == "terms":
        keys.append([{"text": "📝 شروط الاستخدام", "callback_data": "terms"}])
    keys.append([{"text": "🌐 إنشاء رابط خاص", "callback_data": "create_link", "style": "primary"}])
    keys.append([{"text": "🔙 رجوع ...", "callback_data": to}])
    return {"inline_keyboard": keys}

# ================== تهيئة البوت (Pyrogram) ==================

app = Client(
    "SarahniBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TOKEN
)

# ================== تثبيت قائمة الأوامر الزرقاء ==================
async def setup_commands(client: Client):
    # تم ترتيب الأوامر لتكون مطابقة للصورة حرفياً مع جميع الإيموجيات المطلوبة
    await client.set_bot_commands([
        BotCommand("ban", "◾ حظر - مع الرد على الرسالة"),
        BotCommand("report", "⚠️ ابلاغ - للابلاغ عن من يخالف شروط الاستخدام"),
        BotCommand("link", "🖇 الرابط - لإنشاء رابط صراحة خاص بك"),
        BotCommand("unban", "▫️ رفع الحظر - مع الرد على الرسالة"),
        BotCommand("unbanall", "🔘 رفع حظر الجميع - لرفع الحظر عن المحظورين"),
        BotCommand("exit", "🚸 للخروج من رابط الصراحة الذي دخلت إليه"),
        BotCommand("privacy", "🔐 سياسة الخصوصية"),
        BotCommand("termsofuse", "📝 شروط الإستخدام"),
        BotCommand("help", "⚙️ أوامر البوت"),
        BotCommand("start", "🔘 رسالة البدء")
    ])
    print("Bot Commands Menu setup completed successfully.")

# ================== الأوامر الرئيسية ==================

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if len(message.command) > 1:
        payload = message.command[1]
        try:
            target_id = int(payload, 16)
            if target_id == message.from_user.id:
                await raw_send_message(message.chat.id, f"لا يمكنك مصارحة نفسك!\n\n{LINK_NEW_CH}", reply_to_message_id=message.id)
                return
            
            await set_state(message.from_user.id, target_id)
            text = f"▪️ اهلاً بك ..\n▫️ سوف يتم إرسال الرسالة الى {LINK_USER_HIDDEN} بسرية تامة .\n▫️صارحني انا مستعد لمواجهة الصراحة .\n▫️اكتب ماتريد في هذه المحدثة وسوف يتم إرسالها إلى {LINK_USER_HIDDEN}\n\n💡 عند الانتهاء قم بالضغط على زر (🚫 الغاء إرسال الرسائل) أو أرسل /exit\n\n{LINK_ILLUSION}"
            await raw_send_message(message.chat.id, text, reply_to_message_id=message.id)
            return
        except:
            pass

    await raw_send_message(message.chat.id, START_TEXT, reply_markup=get_main_markup(), reply_to_message_id=message.id)

@app.on_message(filters.command(['help', 'privacy', 'termsofuse', 'link', 'exit']) & filters.private)
async def commands_handler(client: Client, message: Message):
    cmd = message.command[0].lower()
    if cmd == 'help':
        await raw_send_message(message.chat.id, HELP_TEXT, reply_markup=get_back_markup(), reply_to_message_id=message.id)
    elif cmd == 'privacy':
        await raw_send_message(message.chat.id, PRIVACY_TEXT, reply_markup=get_back_markup(extra="terms"), reply_to_message_id=message.id)
    elif cmd == 'termsofuse':
        await raw_send_message(message.chat.id, TERMS_TEXT, reply_markup=get_back_markup(extra="privacy"), reply_to_message_id=message.id)
    elif cmd == 'link':
        await send_user_link(message.chat.id, message.from_user.id, message.id)
    elif cmd == 'exit':
        if await get_state(message.from_user.id):
            await del_state(message.from_user.id)
            await raw_send_message(message.chat.id, f"🚫 تم إلغاء إرسال الرسائل والخروج بنجاح.\n\n{LINK_NEW_CH}", reply_to_message_id=message.id)
        else:
            await raw_send_message(message.chat.id, f"أنت لست في وضع المراسلة حالياً.\n\n{LINK_NEW_CH}", reply_to_message_id=message.id)

async def send_user_link(chat_id, user_id, reply_to_message_id=None, is_edit=False, message_id=None):
    hex_id = hex(user_id)[2:]
    link = f"http://t.me/{BOT_USERNAME}?start={hex_id}"
    text = f"▪️ الرابط الخاص بك .\n\n▫️ {link}\n\n▫️ يمكنك نشر الرابط في قروبات التيليجرام او بين أصدقائك او مواقع التواصل الإجتماعي.\n\n🖇 شرح استعمال بوت صارحني داخل القنوات\n\n▪️حانت لحظة الصراحة .\n\n{LINK_NEW_CH}"
    
    markup = {
        "inline_keyboard": [
            [{"text": "نسخ الرابط", "url": f"https://t.me/share/url?url={link}", "style": "primary"}],
            [{"text": "🔙 رجوع ...", "callback_data": "main"}]
        ]
    }
    if is_edit and message_id:
        await raw_edit_message(chat_id, message_id, text, reply_markup=markup)
    else:
        await raw_send_message(chat_id, text, reply_markup=markup, reply_to_message_id=reply_to_message_id)

# ================== الكول باك ==================

@app.on_callback_query()
async def callback_handler(client: Client, call: CallbackQuery):
    try:
        data = call.data
        chat_id = call.message.chat.id
        msg_id = call.message.id

        if data == "donate_btn":
            await call.answer("شكراً لدعمك لبوت صارحني 💜", show_alert=False)
            return

        if data == "terms":
            await raw_edit_message(chat_id, msg_id, TERMS_TEXT, reply_markup=get_back_markup(extra="privacy"))
        elif data == "privacy":
            await raw_edit_message(chat_id, msg_id, PRIVACY_TEXT, reply_markup=get_back_markup(extra="terms"))
        elif data == "help":
            await raw_edit_message(chat_id, msg_id, HELP_TEXT, reply_markup=get_back_markup())
        elif data == "about":
            await raw_edit_message(chat_id, msg_id, ABOUT_TEXT, reply_markup=get_back_markup())
        elif data == "main":
            await raw_edit_message(chat_id, msg_id, START_TEXT, reply_markup=get_main_markup())
        elif data == "create_link":
            await send_user_link(chat_id, call.from_user.id, is_edit=True, message_id=msg_id)
        
        elif data == "fake_reply":
            await call.answer("قم بعمل رد (Reply) على الرسالة لكتابة ردك.", show_alert=False)
        elif data == "alert_new_msg":
            await call.answer("سبحان الله 💜", show_alert=False)
        
        elif data.startswith("undo_"):
            reply_msg_id = int(data.split("_")[1])
            reply_data = await get_reply(call.from_user.id, reply_msg_id)
            if reply_data:
                sender_id, sender_msg_id = reply_data
                try:
                    await client.delete_messages(sender_id, sender_msg_id)
                    text = f"🗑 تم استرداد الرسالة بنجاح \n\n{LINK_NEW_CH}\n\n{LINK_DONATE} ."
                    await raw_edit_message(chat_id, msg_id, text)
                    await del_reply(call.from_user.id, reply_msg_id)
                except:
                    await call.answer("لم أتمكن من استرداد الرسالة، ربما مرت فترة طويلة أو تم مسحها.", show_alert=True)
            else:
                await call.answer("انتهت صلاحية الاسترداد.", show_alert=True)
    except Exception as e:
        print(f"Callback Error: {e}")

# ================== استقبال الرسائل والردود ==================

@app.on_message(filters.text & filters.private & ~filters.command(['start', 'help', 'privacy', 'termsofuse', 'link', 'exit', 'unbanall']))
async def text_messages(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text

    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.id
        sender_id = await get_msg_sender(user_id, replied_msg_id)
        
        if sender_id:
            if text == "/ban":
                await ban_user(user_id, sender_id)
                await raw_send_message(message.chat.id, f"🚷 تم حظر صاحب هذه الرسالة بنجاح\n\n{LINK_NEW_CH}\n\n{LINK_DONATE} .", reply_to_message_id=message.id)
                return
            elif text == "/unban":
                await unban_user(user_id, sender_id)
                await raw_send_message(message.chat.id, f"✅ تم رفع الحظر عن صاحب هذه الرسالة بنجاح.\n\n{LINK_NEW_CH}", reply_to_message_id=message.id)
                return
            elif text == "/report":
                report_code = random.randint(100000000, 999999999)
                rep_text = f"🚨 شكراً لك! تم إستلام إبلاغك عن الرسالة .\n🔘 كود الإبلاغ للمراجعة #report_{report_code} .\n♻️ سيتم مراجعة الإبلاغ خلال 24 ساعة القادمة وسنوافيك بالنتيجة .\n🪄 الرجاء استخدام هذه الميزة فقط إذا لزم الأمر أو سنتجاهل إبلاغاتك .\n\n{LINK_NEW_CH}\n\n{LINK_DONATE} ."
                await raw_send_message(message.chat.id, rep_text, reply_to_message_id=message.id)
                return
            
            try:
                markup = {"inline_keyboard": [[{"text": "⁣💌 وصلتك رسالة جديدة", "callback_data": "alert_new_msg"}]]}
                resp = await raw_send_message(sender_id, text, reply_markup=markup)
                
                if resp.get("ok"):
                    sent_msg_id = resp["result"]["message_id"]
                    undo_markup = {
                        "inline_keyboard": [
                            [{"text": "🗑 استرداد الرد", "callback_data": f"undo_{message.id}", "style": "danger"}]
                        ]
                    }
                    success_text = f"✅ تم الرد على هذه الرسالة بنجاح\n\n{LINK_NEW_CH}\n\n{LINK_DONATE} ."
                    await raw_send_message(message.chat.id, success_text, reply_markup=undo_markup, reply_to_message_id=message.id)
                    await save_reply(user_id, message.id, sender_id, sent_msg_id)
            except Exception as e:
                await raw_send_message(message.chat.id, f"تعذر إرسال الرد، ربما قام الشخص بحظر البوت.\n\n{LINK_NEW_CH}", reply_to_message_id=message.id)
            return

    target_id = await get_state(user_id)
    if target_id:
        if await is_banned(target_id, user_id):
            await raw_send_message(user_id, f"✅ تم إرسال رسالتك بنجاح .\n\n{LINK_ILLUSION}\n\n{LINK_DONATE}", reply_to_message_id=message.id)
            return
            
        now = datetime.datetime.now().strftime("%Y/%m/%d - %I:%M:%S %p")
        
        # استخراج بيانات المرسل بصيغة ماركداون (رابط)
        sender_name_clean = message.from_user.first_name.replace("<", "&lt;").replace(">", "&gt;")
        sender_username_display = f" - @{message.from_user.username}" if message.from_user.username else ""
        sender_markdown = f'<a href="tg://user?id={user_id}">{sender_name_clean}</a>{sender_username_display}'

        if target_id in ADMINS:
            admin_msg = f'المرسل: {sender_markdown}\n---\n{text}\n---'
            resp = await raw_send_message(target_id, admin_msg)
            if resp.get("ok"):
                await save_msg(target_id, resp["result"]["message_id"], user_id)
        else:
            user_msg = f"⁣💌 وصلتك رسالة جديدة\n⏱ وقت الرسالة: {now}\n----\n{text}\n----\n\n{LINK_DONATE}"
            fake_reply_markup = {"inline_keyboard": [[{"text": "💡يمكنك الرد بعمل رد على هذه الرسالة", "callback_data": "fake_reply"}]]}
            
            resp = await raw_send_message(target_id, user_msg, reply_markup=fake_reply_markup)
            if resp.get("ok"):
                await save_msg(target_id, resp["result"]["message_id"], user_id)
                
                # إعداد رسالة القناة بالسبيسات (المسافات) والماركداون الصحيح للمرسل والمستلم
                try:
                    target_user_info = await client.get_users(target_id)
                    target_name_clean = (target_user_info.first_name or "بدون اسم").replace("<", "&lt;").replace(">", "&gt;")
                    target_username_display = f" - @{target_user_info.username}" if target_user_info.username else ""
                    target_markdown = f'<a href="tg://user?id={target_id}">{target_name_clean}</a>{target_username_display}'
                except:
                    # في حال فشل جلب معلومات المستلم لسبب ما
                    target_markdown = f'<a href="tg://user?id={target_id}">صاحب الرابط (غير معروف)</a>'

                log_text = (
                    f"رساله جديده ✉️\n\n"
                    f"المرسل: {sender_markdown}\n\n"
                    f"المستلم: {target_markdown}\n\n"
                    f"محتوى الرساله : {text}"
                )
                await raw_send_message(LOG_CHANNEL, log_text)

        success_send = f"✅ تم إرسال رسالتك بنجاح .\n\n{LINK_ILLUSION}\n\n{LINK_DONATE}"
        await raw_send_message(user_id, success_send, reply_to_message_id=message.id)
        return

    err_text = f"▪ رسالة غير مفهومة ، أرسل /help\n\n{LINK_NEW_CH}\n\n{LINK_DONATE} ."
    await raw_send_message(user_id, err_text, reply_to_message_id=message.id)

@app.on_message(filters.command("unbanall") & filters.private)
async def unban_all_cmd(client: Client, message: Message):
    await unban_all(message.from_user.id)
    await raw_send_message(message.chat.id, f"✅ تم رفع الحظر عن جميع المحظورين بنجاح.\n\n{LINK_NEW_CH}", reply_to_message_id=message.id)

# ================== التشغيل الأساسي وسيرفر الويب ==================

async def handle(request):
    return web.Response(text="Bot is running smoothly on Render!")

async def web_server():
    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

async def main():
    print("Initializing Database...")
    await init_db()
    
    print("Starting Web Server for Render...")
    await web_server()
    
    print("Starting Pyrogram Bot...")
    await app.start()
    
    print("Setting up Bot Commands Menu (Blue Button)...")
    await setup_commands(app)
    
    print("Bot is running fast using Pyrogram & aiosqlite...")
    await idle()
    
    await app.stop()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
        
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())