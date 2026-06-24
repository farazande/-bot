from balethon import Client
import random
import string
from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# ۱. تنظیمات عمومی
# ----------------------------------------------------------------------
TOKEN = "1963247885:gqtFoTs9MErbcmyon2m0CcBlXcohSu_ikjA"
ADMIN_PASSWORD = "ARF1392"
ADMIN_USERNAME = "@ARF_1392"
BOT_USERNAME = "tablighat_bale_plus_bot"

PRICE_WITH_IMAGE = 80000
PRICE_WITHOUT_IMAGE = 30000
INITIAL_CREDIT = 5000
INVITE_CREDIT = 5000

AD_CHANNELS = """
📢 کانال‌های تبلیغاتی:
➤ @tablighat_bale_plus
➤ @Lions1404
"""

# ----------------------------------------------------------------------
# ۲. ذخیره‌سازی داده‌ها
# ----------------------------------------------------------------------
user_states = {}
ads = []
invited_users = {}
gift_codes = {}  # {code: {"amount": int, "uses": int, "max_uses": int, "expires": datetime}}
partner_channels = []  # [{chat_id, username, name, status, owner_id}]
support_tickets = []  # [{id, user_id, text, status, messages}]

# ----------------------------------------------------------------------
# ۳. ساختار ربات
# ----------------------------------------------------------------------
bot = Client(TOKEN)

def make_keyboard(rows, resize=True, one_time=False):
    return {
        "keyboard": rows,
        "resize_keyboard": resize,
        "one_time_keyboard": one_time
    }

def generate_tracking_code():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"AD-{timestamp}-{random_part}"

def generate_gift_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_user_id(message):
    if hasattr(message, 'from_user') and message.from_user:
        return message.from_user.id
    return message.chat.id

# ----------------------------------------------------------------------
# ۴. هندلینگ پیام‌ها
# ----------------------------------------------------------------------
@bot.on_message()
async def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""
    
    if chat_id not in user_states:
        user_states[chat_id] = {
            "step": None,
            "wallet": INITIAL_CREDIT,
            "invited_by": None,
            "name": message.chat.first_name or "کاربر",
            "username": message.chat.username or "",
            "is_admin": False,
            "ad_history": []
        }
    
    state = user_states[chat_id]
    step = state.get("step")
    
    back_btn = [["بازگشت به منوی اصلی"]]
    main_menu = [
        ["📝 سفارش تبلیغات"],
        ["💰 موجودی کیف پول"],
        ["👤 پروفایل"],
        ["🎁 کد هدیه"],
        ["📢 کانال من را اضافه کن"],
        ["💬 پشتیبانی"],
        ["🔧 پنل ادمین"]
    ]
    
    admin_menu = [
        ["📋 سفارشات جدید"],
        ["📜 همه سفارشات"],
        ["🎁 ساخت کد هدیه"],
        ["📡 مدیریت کانال‌ها"],
        ["🎫 تیکت‌های پشتیبانی"],
        ["💵 انتقال اعتبار"],
        ["👥 لیست کاربران"],
        ["📢 پیام همگانی"],
        ["بازگشت به منوی اصلی"]
    ]

    # ------------------------------------------------------------------
    # /start
    # ------------------------------------------------------------------
    if text.startswith("/start"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            inviter_id = int(parts[1])
            if inviter_id != chat_id and chat_id not in invited_users:
                invited_users[chat_id] = inviter_id
                if inviter_id in user_states:
                    user_states[inviter_id]["wallet"] += INVITE_CREDIT
                    await bot.send_message(
                        inviter_id,
                        f"🎉 کاربر جدیدی با لینک شما وارد شد!\n"
                        f"💰 {INVITE_CREDIT} تومان به کیف پول شما اضافه شد."
                    )
        
        state["step"] = None
        await message.reply(
            f"سلام! 👋\n"
            f"به ربات ثبت تبلیغات خوش آمدید!\n\n"
            f"{AD_CHANNELS}\n"
            f"💳 شما {INITIAL_CREDIT} تومان اعتبار اولیه دارید.\n\n"
            f"لطفاً یکی از گزینه‌ها را انتخاب کنید:",
            reply_markup=make_keyboard(main_menu)
        )
        return

    # ------------------------------------------------------------------
    # بازگشت به منوی اصلی
    # ------------------------------------------------------------------
    if text == "بازگشت به منوی اصلی":
        state["step"] = None
        state["is_admin"] = False
        await message.reply("🔙 به منوی اصلی برگشتید.", reply_markup=make_keyboard(main_menu))
        return

    # ------------------------------------------------------------------
    # ورود به پنل ادمین
    # ------------------------------------------------------------------
    if text == "🔧 پنل ادمین" or text == "/admin":
        state["step"] = "admin_password"
        await message.reply("🔐 رمز عبور پنل ادمین را وارد کنید:", reply_markup=make_keyboard(back_btn))
        return
    
    if step == "admin_password":
        if text == ADMIN_PASSWORD:
            state["is_admin"] = True
            state["step"] = "admin_menu"
            await message.reply("✅ خوش آمدید ادمین!", reply_markup=make_keyboard(admin_menu))
        else:
            await message.reply("❌ رمز اشتباه است.", reply_markup=make_keyboard(back_btn))
        return

    # ------------------------------------------------------------------
    # منوی ادمین
    # ------------------------------------------------------------------
    if step == "admin_menu" and state.get("is_admin"):
        
        # 📋 سفارشات جدید
        if text == "📋 سفارشات جدید":
            pending_ads = [a for a in ads if a["status"] == "در انتظار تایید"]
            if not pending_ads:
                await message.reply("⚠️ هیچ سفارشی در انتظار تایید نیست.", reply_markup=make_keyboard(admin_menu))
            else:
                for ad in pending_ads:
                    msg = f"""
📋 سفارش #{ad['id']}
🆔 کد پیگیری: {ad['tracking_code']}
👤 مشتری: {ad['name']}
📝 نوع: {ad['type']}
💰 قیمت: {ad['price']} تومان
📅 تاریخ: {ad['date']}
📄 متن تبلیغات:
{ad['text']}
"""
                    await message.reply(msg, reply_markup=make_keyboard([
                        [f"✅ تایید #{ad['id']}", f"❌ رد #{ad['id']}"],
                        ["📋 سفارشات جدید"],
                        ["بازگشت به منوی اصلی"]
                    ]))
                    if ad.get("image_id"):
                        try:
                            await bot.send_photo(chat_id, ad["image_id"], caption="🖼️ عکس تبلیغات")
                        except:
                            pass
            return
        
        # 📜 همه سفارشات
        if text == "📜 همه سفارشات":
            if not ads:
                await message.reply("⚠️ هیچ سفارشی ثبت نشده.", reply_markup=make_keyboard(admin_menu))
            else:
                pending = len([a for a in ads if a["status"] == "در انتظار تایید"])
                approved = len([a for a in ads if a["status"] == "تایید شده"])
                rejected = len([a for a in ads if a["status"] == "رد شده"])
                total = sum([a["price"] for a in ads if a["status"] == "تایید شده"])
                msg = f"""
📊 گزارش کلی:
🆕 در انتظار: {pending}
✅ تایید شده: {approved}
❌ رد شده: {rejected}
📝 کل: {len(ads)}
💰 درآمد کل: {total} تومان
"""
                await message.reply(msg, reply_markup=make_keyboard(admin_menu))
            return
        
        # 🎁 ساخت کد هدیه
        if text == "🎁 ساخت کد هدیه":
            state["step"] = "create_gift_code"
            await message.reply(
                "🎁 ساخت کد هدیه\n\n"
                "فرمت: مبلغ:تعداد استفاده:روزهای اعتبار\n"
                "مثال: 50000:10:7\n"
                "(یعنی 50,000 تومان، 10 بار قابل استفاده، 7 روز اعتبار)",
                reply_markup=make_keyboard(back_btn)
            )
            return
        
        # 📡 مدیریت کانال‌ها
        if text == "📡 مدیریت کانال‌ها":
            pending_channels = [c for c in partner_channels if c["status"] == "در انتظار"]
            if not pending_channels:
                await message.reply("⚠️ هیچ کانالی در انتظار تایید نیست.", reply_markup=make_keyboard(admin_menu))
            else:
                for ch in pending_channels:
                    await message.reply(
                        f"📡 کانال جدید:\n\n"
                        f"نام: {ch['name']}\n"
                        f"یوزرنیم: @{ch['username']}\n"
                        f"مالک: {ch['owner_name']}\n\n"
                        f"برای تایید: /approve_channel {ch['chat_id']}\n"
                        f"برای رد: /reject_channel {ch['chat_id']}",
                        reply_markup=make_keyboard(admin_menu)
                    )
            return
        
        # 🎫 تیکت‌های پشتیبانی
        if text == "🎫 تیکت‌های پشتیبانی":
            open_tickets = [t for t in support_tickets if t["status"] == "باز"]
            if not open_tickets:
                await message.reply("⚠️ هیچ تیکت بازی وجود ندارد.", reply_markup=make_keyboard(admin_menu))
            else:
                for ticket in open_tickets:
                    await message.reply(
                        f"🎫 تیکت #{ticket['id']}\n"
                        f"کاربر: {ticket['user_name']}\n"
                        f"آیدی: {ticket['user_id']}\n"
                        f"موضوع: {ticket['text']}\n\n"
                        f"پاسخ: /reply_ticket {ticket['id']} متن پاسخ",
                        reply_markup=make_keyboard(admin_menu)
                    )
            return
        
        # 💵 انتقال اعتبار
        if text == "💵 انتقال اعتبار":
            state["step"] = "admin_transfer"
            await message.reply("فرمت: آیدی:مبلغ\nمثال: 123456789:50000", reply_markup=make_keyboard(back_btn))
            return
        
        # 👥 لیست کاربران
        if text == "👥 لیست کاربران":
            if not user_states:
                await message.reply("⚠️ هیچ کاربری وجود ندارد.", reply_markup=make_keyboard(admin_menu))
            else:
                msg = f"👥 تعداد کاربران: {len(user_states)}\n\n"
                for uid, ustate in list(user_states.items())[:10]:
                    msg += f"🆔 {uid} - {ustate['name']} - {ustate['wallet']} تومان\n"
                await message.reply(msg, reply_markup=make_keyboard(admin_menu))
            return
        
        # 📢 پیام همگانی
        if text == "📢 پیام همگانی":
            state["step"] = "admin_broadcast"
            await message.reply("📢 پیام همگانی را بنویسید:", reply_markup=make_keyboard(back_btn))
            return

    # ------------------------------------------------------------------
    # تایید سفارش
    # ------------------------------------------------------------------
    if text.startswith("✅ تایید #"):
        if not state.get("is_admin"):
            return
        try:
            ad_id = int(text.split("#")[1])
            ad = next((a for a in ads if a["id"] == ad_id), None)
            if ad and ad["status"] == "در انتظار تایید":
                ad["status"] = "تایید شده"
                user_id = ad["user_id"]
                await bot.send_message(
                    user_id,
                    f"✅ تبلیغات شما تایید و منتشر شد! 🎉\n\n"
                    f"🆔 کد پیگیری: {ad['tracking_code']}\n"
                    f"📝 نوع: {ad['type']}\n"
                    f"💰 قیمت: {ad['price']} تومان\n\n"
                    f"🚀 تبلیغات شما در کانال‌ها منتشر شد."
                )
                await message.reply(f"✅ سفارش #{ad_id} تایید و منتشر شد.", reply_markup=make_keyboard(admin_menu))
        except:
            pass
        return
    
    # ------------------------------------------------------------------
    # رد سفارش
    # ------------------------------------------------------------------
    if text.startswith("❌ رد #"):
        if not state.get("is_admin"):
            return
        try:
            ad_id = int(text.split("#")[1])
            ad = next((a for a in ads if a["id"] == ad_id), None)
            if ad and ad["status"] == "در انتظار تایید":
                ad["status"] = "رد شده"
                user_id = ad["user_id"]
                if user_id in user_states:
                    user_states[user_id]["wallet"] += ad["price"]
                await bot.send_message(
                    user_id,
                    f"❌ تبلیغات شما رد شد.\n\n"
                    f"🆔 کد پیگیری: {ad['tracking_code']}\n"
                    f"💰 مبلغ {ad['price']} تومان به کیف پول برگردانده شد."
                )
                await message.reply(f"❌ سفارش #{ad_id} رد شد.", reply_markup=make_keyboard(admin_menu))
        except:
            pass
        return

    # ------------------------------------------------------------------
    # ساخت کد هدیه
    # ------------------------------------------------------------------
    if step == "create_gift_code":
        try:
            parts = text.split(":")
            if len(parts) != 3:
                raise ValueError
            amount = int(parts[0])
            max_uses = int(parts[1])
            days = int(parts[2])
            
            code = generate_gift_code()
            expires = datetime.now() + timedelta(days=days)
            gift_codes[code] = {
                "amount": amount,
                "uses": 0,
                "max_uses": max_uses,
                "expires": expires
            }
            
            await message.reply(
                f"✅ کد هدیه ساخته شد!\n\n"
                f"🎁 کد: `{code}`\n"
                f"💰 مبلغ: {amount} تومان\n"
                f"🔢 تعداد استفاده: {max_uses}\n"
                f"📅 اعتبار: {days} روز\n\n"
                f"این کد را به کاربران بدهید.",
                reply_markup=make_keyboard(admin_menu)
            )
            state["step"] = "admin_menu"
        except:
            await message.reply("❌ فرمت نادرست!", reply_markup=make_keyboard(back_btn))
        return

    # ------------------------------------------------------------------
    # انتقال اعتبار
    # ------------------------------------------------------------------
    if step == "admin_transfer":
        try:
            parts = text.split(":")
            target_id = int(parts[0])
            amount = int(parts[1])
            
            if target_id not in user_states:
                user_states[target_id] = {
                    "step": None, "wallet": 0, "invited_by": None,
                    "name": "کاربر جدید", "username": "", "is_admin": False, "ad_history": []
                }
            
            user_states[target_id]["wallet"] += amount
            await bot.send_message(target_id, f"💰 ادمین {amount} تومان به کیف پول شما اضافه کرد!")
            await message.reply(f"✅ {amount} تومان به کاربر {target_id} انتقال یافت.", reply_markup=make_keyboard(admin_menu))
            state["step"] = "admin_menu"
        except:
            await message.reply("❌ فرمت نادرست!", reply_markup=make_keyboard(back_btn))
        return

    # ------------------------------------------------------------------
    # پیام همگانی
    # ------------------------------------------------------------------
    if step == "admin_broadcast":
        success = failed = 0
        for uid in user_states:
            try:
                await bot.send_message(uid, f"📢 پیام همگانی:\n\n{text}")
                success += 1
            except:
                failed += 1
        await message.reply(f"✅ ارسال شد!\nموفق: {success}\nناموفق: {failed}", reply_markup=make_keyboard(admin_menu))
        state["step"] = "admin_menu"
        return

    # ------------------------------------------------------------------
    # منوی اصلی
    # ------------------------------------------------------------------
    if step is None:
        
        # 📝 سفارش تبلیغات
        if text == "📝 سفارش تبلیغات":
            state["step"] = "ad_type"
            await message.reply(
                "📝 نوع تبلیغات را انتخاب کنید:",
                reply_markup=make_keyboard([
                    ["🖼️ تبلیغات با عکس"],
                    ["📄 تبلیغات متنی"],
                    back_btn[0]
                ])
            )
            return
        
        # 💰 موجودی کیف پول
        if text == "💰 موجودی کیف پول":
            wallet = state["wallet"]
            invite_balance = INVITE_CREDIT if state.get("invited_by") else 0
            await message.reply(
                f"💰 موجودی کیف پول:\n\n"
                f"• اعتبار اصلی: {wallet} تومان\n"
                f"• اعتبار دعوت: {invite_balance} تومان\n"
                f"• جمع کل: {wallet + invite_balance} تومان\n\n"
                f"⚠️ برای افزایش موجودی با ادمین تماس بگیرید:\n"
                f"📧 @{ADMIN_USERNAME}",
                reply_markup=make_keyboard([
                    ["💳 افزایش موجودی"],
                    back_btn[0]
                ])
            )
            return
        
        # 💳 افزایش موجودی
        if text == "💳 افزایش موجودی":
            await message.reply(
                f"⚠️ برای افزایش موجودی با ادمین تماس بگیرید:\n"
                f"📧 @{ADMIN_USERNAME}",
                reply_markup=make_keyboard(back_btn)
            )
            return
        
        # 👤 پروفایل
        if text == "👤 پروفایل":
            username_display = f"@{state['username']}" if state['username'] else "ندارد"
            user_ads = [a for a in ads if a['user_id'] == chat_id]
            total_wallet = state["wallet"] + (INVITE_CREDIT if state.get("invited_by") else 0)
            
            await message.reply(
                f"👤 پروفایل شما:\n\n"
                f"• نام: {state['name']}\n"
                f"• یوزرنیم: {username_display}\n"
                f"• آیدی: {chat_id}\n"
                f"• موجودی: {total_wallet} تومان\n"
                f"• سفارشات: {len(user_ads)}\n"
                f"• تایید شده: {len([a for a in user_ads if a['status'] == 'تایید شده'])}\n\n"
                f"📜 تاریخچه سفارشات:",
                reply_markup=make_keyboard([
                    ["📋 تاریخچه سفارشات"],
                    ["📨 دعوت دوستان"],
                    back_btn[0]
                ])
            )
            return
        
        # 📋 تاریخچه سفارشات
        if text == "📋 تاریخچه سفارشات":
            user_ads = [a for a in ads if a['user_id'] == chat_id]
            if not user_ads:
                await message.reply("⚠️ شما هنوز سفارشی ثبت نکرده‌اید.", reply_markup=make_keyboard(back_btn))
            else:
                msg = "📋 تاریخچه سفارشات شما:\n\n"
                for ad in user_ads[-5:]:
                    status_emoji = "✅" if ad["status"] == "تایید شده" else "⏳" if ad["status"] == "در انتظار تایید" else "❌"
                    msg += f"{status_emoji} #{ad['id']} - {ad['type']} - {ad['price']} تومان\n"
                    msg += f"   کد: {ad['tracking_code']}\n"
                    msg += f"   تاریخ: {ad['date']}\n\n"
                await message.reply(msg, reply_markup=make_keyboard(back_btn))
            return
        
        # 📨 دعوت دوستان
        if text == "📨 دعوت دوستان":
            invite_link = f"https://ble.ir/{BOT_USERNAME}?start={chat_id}"
            await message.reply(
                f"📨 لینک دعوت شما:\n\n{invite_link}\n\n"
                f"🎁 با هر دعوت موفق، {INVITE_CREDIT} تومان اعتبار!\n\n"
                f"⚠️ قوانین:\n"
                f"• خودتان را دعوت نکنید\n"
                f"• هر کاربر یک بار",
                reply_markup=make_keyboard(back_btn)
            )
            return
        
        # 🎁 کد هدیه
        if text == "🎁 کد هدیه":
            state["step"] = "redeem_gift"
            await message.reply(
                "🎁 وارد کردن کد هدیه:\n\n"
                "کد هدیه خود را وارد کنید:",
                reply_markup=make_keyboard(back_btn)
            )
            return
        
        # 📢 کانال من را اضافه کن
        if text == "📢 کانال من را اضافه کن":
            state["step"] = "add_channel"
            await message.reply(
                "📢 اضافه کردن کانال:\n\n"
                "یوزرنیم کانال را وارد کنید (مثلاً: @channelname):",
                reply_markup=make_keyboard(back_btn)
            )
            return
        
        # 💬 پشتیبانی
        if text == "💬 پشتیبانی":
            state["step"] = "support_ticket"
            await message.reply(
                "💬 ارسال تیکت پشتیبانی:\n\n"
                "پیام خود را بنویسید:",
                reply_markup=make_keyboard(back_btn)
            )
            return

    # ------------------------------------------------------------------
    # ثبت کد هدیه
    # ------------------------------------------------------------------
    if step == "redeem_gift":
        code = text.strip().upper()
        if code in gift_codes:
            gc = gift_codes[code]
            if datetime.now() > gc["expires"]:
                await message.reply("❌ این کد منقضی شده است.", reply_markup=make_keyboard(back_btn))
            elif gc["uses"] >= gc["max_uses"]:
                await message.reply("❌ این کد قبلاً استفاده شده است.", reply_markup=make_keyboard(back_btn))
            else:
                gc["uses"] += 1
                state["wallet"] += gc["amount"]
                await message.reply(
                    f"✅ کد هدیه فعال شد!\n\n"
                    f"🎁 {gc['amount']} تومان به کیف پول اضافه شد.\n"
                    f"💰 موجودی جدید: {state['wallet']} تومان",
                    reply_markup=make_keyboard(main_menu)
                )
        else:
            await message.reply("❌ کد نامعتبر است.", reply_markup=make_keyboard(back_btn))
        state["step"] = None
        return

    # ------------------------------------------------------------------
    # اضافه کردن کانال
    # ------------------------------------------------------------------
    if step == "add_channel":
        channel_username = text.strip()
        if not channel_username.startswith("@"):
            channel_username = "@" + channel_username
        
        # بررسی اینکه ربات ادمین کانال هست
        try:
            chat = await bot.get_chat(channel_username)
            member = await bot.get_chat_member(channel_username, (await bot.get_me()).id)
            
            if member.status in ["administrator", "member"]:
                partner_channels.append({
                    "chat_id": chat.id,
                    "username": chat.username,
                    "name": chat.title,
                    "owner_id": chat_id,
                    "owner_name": state["name"],
                    "status": "در انتظار"
                })
                await message.reply(
                    f"✅ کانال {chat.title} ثبت شد!\n"
                    f"منتظر تایید ادمین باشید.",
                    reply_markup=make_keyboard(main_menu)
                )
            else:
                await message.reply(
                    "❌ ربات باید ادمین کانال باشد!\n"
                    "لطفاً ربات را ادمین کانال کنید و دوباره تلاش کنید.",
                    reply_markup=make_keyboard(back_btn)
                )
        except Exception as e:
            await message.reply(
                f"❌ خطا! مطمئن شوید:\n"
                f"• ربات ادمین کانال است\n"
                f"• کانال عمومی است",
                reply_markup=make_keyboard(back_btn)
            )
        state["step"] = None
        return

    # ------------------------------------------------------------------
    # تیکت پشتیبانی
    # ------------------------------------------------------------------
    if step == "support_ticket":
        ticket_id = len(support_tickets) + 1
        ticket = {
            "id": ticket_id,
            "user_id": chat_id,
            "user_name": state["name"],
            "text": text,
            "status": "باز",
            "messages": []
        }
        support_tickets.append(ticket)
        
        await message.reply(
            f"✅ تیکت شما ثبت شد!\n\n"
            f"🎫 شماره تیکت: {ticket_id}\n"
            f"📝 موضوع: {text}\n\n"
            f"پاسخ ادمین به زودی ارسال می‌شود.",
            reply_markup=make_keyboard(main_menu)
        )
        
        # اطلاع به ادمین
        await bot.send_message(
            chat_id,  # اینجا باید آیدی ادمین باشد
            f"🎫 تیکت جدید!\n\n"
            f"کاربر: {state['name']}\n"
            f"آیدی: {chat_id}\n"
            f"موضوع: {text}\n\n"
            f"پاسخ: /reply_ticket {ticket_id} متن"
        )
        state["step"] = None
        return

    # ------------------------------------------------------------------
    # ثبت تبلیغات
    # ------------------------------------------------------------------
    if step == "ad_type":
        if text == "🖼️ تبلیغات با عکس":
            state["ad_type"] = "with_image"
            state["ad_price"] = PRICE_WITH_IMAGE
            state["step"] = "ad_text"
            await message.reply(
                f"🖼️ تبلیغات با عکس\n"
                f"💰 قیمت: {PRICE_WITH_IMAGE} تومان\n\n"
                f"✏️ متن تبلیغ را وارد کنید:",
                reply_markup=make_keyboard(back_btn)
            )
            return
        
        if text == "📄 تبلیغات متنی":
            state["ad_type"] = "without_image"
            state["ad_price"] = PRICE_WITHOUT_IMAGE
            state["step"] = "ad_text"
            await message.reply(
                f"📄 تبلیغات متنی\n"
                f"💰 قیمت: {PRICE_WITHOUT_IMAGE} تومان\n\n"
                f"✏️ متن تبلیغ را وارد کنید:",
                reply_markup=make_keyboard(back_btn)
            )
            return
    
    if step == "ad_text":
        state["ad_text"] = text
        
        if state["ad_type"] == "with_image":
            state["step"] = "ad_image"
            await message.reply(
                f"✅ متن ثبت شد:\n{text}\n\n"
                f"🖼️ عکس تبلیغ را ارسال کنید:",
                reply_markup=make_keyboard(back_btn)
            )
        else:
            # پیش‌نمایش تبلیغ متنی
            price = state["ad_price"]
            wallet = state["wallet"]
            
            if wallet < price:
                await message.reply(
                    f"❌ موجودی کافی نیست!\n"
                    f"💰 قیمت: {price} تومان\n"
                    f"💳 موجودی: {wallet} تومان",
                    reply_markup=make_keyboard(back_btn)
                )
                state["step"] = None
                return
            
            state["step"] = "ad_preview"
            await message.reply(
                f"🔍 پیش‌نمایش تبلیغ:\n\n"
                f"📝 نوع: متنی\n"
                f"💰 قیمت: {price} تومان\n"
                f"📄 متن:\n{text}\n\n"
                f"آیا این تبلیغ را ثبت می‌کنید؟",
                reply_markup=make_keyboard([
                    ["✅ تایید و پرداخت"],
                    ["❌ لغو"],
                    back_btn[0]
                ])
            )
        return
    
    if step == "ad_image":
        if message.photo:
            file_id = message.photo[-1].file_id
            price = state["ad_price"]
            wallet = state["wallet"]
            
            if wallet < price:
                await message.reply(
                    f"❌ موجودی کافی نیست!\n"
                    f"💰 قیمت: {price} تومان\n"
                    f"💳 موجودی: {wallet} تومان",
                    reply_markup=make_keyboard(back_btn)
                )
                state["step"] = None
                return
            
            state["image_id"] = file_id
            state["step"] = "ad_preview"
            
            # پیش‌نمایش با عکس
            await bot.send_photo(
                chat_id,
                file_id,
                caption=f"🔍 پیش‌نمایش تبلیغ:\n\n"
                        f"📝 نوع: با عکس\n"
                        f"💰 قیمت: {price} تومان\n"
                        f"📄 متن:\n{state.get('ad_text', '')}\n\n"
                        f"آیا این تبلیغ را ثبت می‌کنید؟"
            )
            await message.reply(
                "آیا این تبلیغ را ثبت می‌کنید؟",
                reply_markup=make_keyboard([
                    ["✅ تایید و پرداخت"],
                    ["❌ لغو"],
                    back_btn[0]
                ])
            )
        else:
            await message.reply("❌ لطفاً یک عکس ارسال کنید:", reply_markup=make_keyboard(back_btn))
        return
    
    if step == "ad_preview":
        if text == "✅ تایید و پرداخت":
            price = state["ad_price"]
            wallet = state["wallet"]
            
            tracking_code = generate_tracking_code()
            current_date = datetime.now().strftime("%Y/%m/%d - %H:%M")
            
            ad = {
                "id": len(ads) + 1,
                "tracking_code": tracking_code,
                "user_id": chat_id,
                "username": state["username"],
                "name": state["name"],
                "type": "با عکس" if state["ad_type"] == "with_image" else "متنی",
                "text": state.get("ad_text", ""),
                "image_id": state.get("image_id"),
                "price": price,
                "status": "در انتظار تایید",
                "date": current_date
            }
            ads.append(ad)
            state["wallet"] -= price
            state["ad_history"].append(ad["id"])
            
            await message.reply(
                f"✅ سفارش ثبت شد!\n\n"
                f"🆔 کد پیگیری: {tracking_code}\n"
                f"📝 نوع: {ad['type']}\n"
                f"💰 قیمت: {price} تومان\n"
                f"💳 موجودی جدید: {state['wallet']} تومان\n\n"
                f"⏰ منتظر تایید ادمین باشید.",
                reply_markup=make_keyboard(main_menu)
            )
            state["step"] = None
            state.pop("ad_text", None)
            state.pop("image_id", None)
            state.pop("ad_type", None)
            state.pop("ad_price", None)
        
        elif text == "❌ لغو":
            await message.reply("❌ سفارش لغو شد.", reply_markup=make_keyboard(main_menu))
            state["step"] = None
            state.pop("ad_text", None)
            state.pop("image_id", None)
            state.pop("ad_type", None)
            state.pop("ad_price", None)
        else:
            await message.reply("❌ لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=make_keyboard(back_btn))
        return

    # ------------------------------------------------------------------
    # پاسخ پیش‌فرض
    # ------------------------------------------------------------------
    if step is None:
        await message.reply(
            "❌ دستور نامعتبر.\n"
            "از منوی زیر استفاده کنید:",
            reply_markup=make_keyboard(main_menu)
        )
        return

# ----------------------------------------------------------------------
# ۵. دستورات ادمین
# ----------------------------------------------------------------------
@bot.on_command("/approve_channel")
async def approve_channel(message):
    try:
        parts = message.text.split()
        if len(parts) == 2:
            channel_id = int(parts[1])
            for ch in partner_channels:
                if ch["chat_id"] == channel_id and ch["status"] == "در انتظار":
                    ch["status"] = "تایید شده"
                    await message.reply(f"✅ کانال @{ch['username']} تایید شد.")
                    await bot.send_message(ch["owner_id"], f"✅ کانال @{ch['username']} تایید شد و تبلیغات در آن منتشر می‌شود.")
                    return
            await message.reply("❌ کانال یافت نشد.")
    except:
        await message.reply("❌ فرمت نادرست!")

@bot.on_command("/reject_channel")
async def reject_channel(message):
    try:
        parts = message.text.split()
        if len(parts) == 2:
            channel_id = int(parts[1])
            for ch in partner_channels:
                if ch["chat_id"] == channel_id and ch["status"] == "در انتظار":
                    ch["status"] = "رد شده"
                    await message.reply(f"❌ کانال @{ch['username']} رد شد.")
                    await bot.send_message(ch["owner_id"], f"❌ کانال @{ch['username']} رد شد.")
                    return
            await message.reply("❌ کانال یافت نشد.")
    except:
        await message.reply("❌ فرمت نادرست!")

@bot.on_command("/reply_ticket")
async def reply_ticket(message):
    try:
        parts = message.text.split(" ", 2)
        if len(parts) >= 3:
            ticket_id = int(parts[1])
            reply_text = parts[2]
            for ticket in support_tickets:
                if ticket["id"] == ticket_id:
                    ticket["status"] = "پاسخ داده شده"
                    await bot.send_message(ticket["user_id"], f"🎫 پاسخ تیکت #{ticket_id}:\n\n{reply_text}")
                    await message.reply("✅ پاسخ ارسال شد.")
                    return
            await message.reply("❌ تیکت یافت نشد.")
    except:
        await message.reply("❌ فرمت: /reply_ticket [id] [متن]")

# ----------------------------------------------------------------------
# ۶. اجرای ربات
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("🤖 ربات تبلیغات فعال شد!")
    bot.run()
