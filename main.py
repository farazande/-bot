from balethon import Client
import asyncio
import uuid
from datetime import datetime, timedelta
import re

# ----------------------------------------------------------------------
# 1. تنظیمات عمومی
# ----------------------------------------------------------------------
TOKEN = "400667838:vjEuCZCtfBs7brlc0SJAkmOq-LPSnTMBdLo"
BOT_USERNAME = "Tablighat_bale_bot"
ADMIN_ID = 1715537314
ADMIN_PASSWORD = "Amirali1387"
INVITE_REWARD = 5000
WELCOME_BONUS = 10000
TAX_RATE = 0.10
CHANNELS_FOR_AD = ["@promt", "@chatbot1404", "@sipadsupport"]
REQUIRED_CHANNEL = "@promt"

# ----------------------------------------------------------------------
# 2. ساختار ذخیره‌سازی
# ----------------------------------------------------------------------
user_states = {}
ads_list = []
gift_codes = {}
pending_channels = []
tickets = []
earnings_requests = []
current_page = {}
pending_ads = {}

# ----------------------------------------------------------------------
# 3. توابع کمکی
# ----------------------------------------------------------------------
def make_keyboard(rows, resize=True, one_time=False):
    return {
        "keyboard": rows,
        "resize_keyboard": resize,
        "one_time_keyboard": one_time
    }

def is_member(user_id):
    try:
        return True
    except:
        return False

def main_menu(chat_id):
    if chat_id == ADMIN_ID:
        return make_keyboard([
            ["📢 سفارش تبلیغات"],
            ["💰 کیف پول", "👤 پروفایل"],
            ["👑 پنل ادمین", "📺 پیشنهاد کانال"],
            ["🎫 تیکت پشتیبانی"]
        ])
    else:
        return make_keyboard([
            ["📢 سفارش تبلیغات"],
            ["💰 کیف پول", "👤 پروفایل"],
            ["📺 پیشنهاد کانال", "🎫 تیکت پشتیبانی"]
        ])

def admin_menu():
    return make_keyboard([
        ["📊 آمار کاربران", "🔍 جستجوی کاربر"],
        ["📋 سفارش‌ها", "🎁 مدیریت کد هدیه"],
        ["📢 ارسال همگانی", "📺 مدیریت کانال‌ها"],
        ["💸 درخواست‌های برداشت", "🎫 مدیریت تیکت‌ها"],
        ["✅ کانال‌های پیشنهادی", "➕ انتقال اعتبار"],
        ["🚪 خروج از پنل"]
    ])

def channels_menu():
    return make_keyboard([
        ["📺 لیست کانال‌ها"],
        ["➕ اضافه کردن کانال جدید"],
        ["✅ تایید کانال", "❌ حذف کانال"],
        ["⏳ کانال‌های منتظر تایید"],
        ["🔙 بازگشت به پنل"]
    ])

def withdraws_menu():
    return make_keyboard([
        ["💸 مشاهده درخواست‌های برداشت"],
        ["🔙 بازگشت به پنل"]
    ])

def tickets_menu():
    return make_keyboard([
        ["🎫 مشاهده تیکت‌های باز"],
        ["🔙 بازگشت به پنل"]
    ])

# ----------------------------------------------------------------------
# 4. ربات اصلی
# ----------------------------------------------------------------------
bot = Client(TOKEN)

@bot.on_message()
async def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""
    
    if not is_member(chat_id) and chat_id != ADMIN_ID:
        await message.reply(
            f"🔒 **برای استفاده از ربات باید در کانال زیر عضو شوید:**\n\n"
            f"{REQUIRED_CHANNEL}\n\n"
            f"پس از عضویت، دوباره /start را بزنید.",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    if chat_id not in user_states:
        user_states[chat_id] = {
            "wallet": WELCOME_BONUS,
            "invite_count": 0,
            "invited_by": None,
            "name": message.chat.first_name or "کاربر",
            "username": message.chat.username or "",
            "step": None,
            "temp_data": {},
            "is_admin": (chat_id == ADMIN_ID),
            "earnings": 0,
            "admin_auth": False,
            "ads_count": 0,
            "total_spent": 0
        }
        await message.reply(f"🎁 **تبریک!** {WELCOME_BONUS:,} تومان اعتبار هدیه به کیف پول شما اضافه شد!")
    
    state = user_states[chat_id]
    step = state.get("step")
    
    # ==============================================================
    # شروع ربات
    # ==============================================================
    if text == "/start":
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            inviter_id = int(parts[1])
            if inviter_id != chat_id and inviter_id in user_states and not state.get("invited_by"):
                inviter = user_states[inviter_id]
                inviter["wallet"] += INVITE_REWARD
                inviter["invite_count"] += 1
                state["invited_by"] = inviter_id
                await bot.send_message(inviter_id, f"🎉 کاربر {state['name']} با لینک شما دعوت شد! {INVITE_REWARD:,} تومان به کیف پول شما اضافه شد.")
                await message.reply(f"🎉 شما توسط {inviter['name']} دعوت شدید! {WELCOME_BONUS:,} تومان اعتبار هدیه دریافت کردید.")
        
        channels_text = "\n".join(CHANNELS_FOR_AD)
        await message.reply(
            f"🤖 **به ربات تبلیغات خوش آمدید!**\n\n"
            f"🎁 **اعتبار هدیه:** {WELCOME_BONUS:,} تومان\n"
            f"📢 **تبلیغات شما در کانال‌های زیر انجام می‌شود:**\n{channels_text}\n\n"
            f"🔗 **لینک دعوت شما:**\n`https://ble.ir/{BOT_USERNAME}?start={chat_id}`\n\n"
            f"💰 **با هر دعوت {INVITE_REWARD:,} تومان دریافت کنید!**\n\n"
            f"طراحي و ساخت توسط شرکت [نوآوران بات](https://ble.ir/innovarbots) \n"
            f"از منوی زیر استفاده کنید:",
            reply_markup=main_menu(chat_id)
        )
        state["step"] = None
        return
    
    # ==============================================================
    # دکمه بازگشت
    # ==============================================================
    if text == "🔙 بازگشت":
        state["step"] = None
        await message.reply("به منوی اصلی بازگشتید.", reply_markup=main_menu(chat_id))
        return
    
    if text == "🔙 بازگشت به پنل":
        state["step"] = None
        await message.reply("به پنل ادمین بازگشتید.", reply_markup=admin_menu())
        return
    
    # ==============================================================
    # پروفایل
    # ==============================================================
    if text == "👤 پروفایل":
        username_display = f"@{state['username']}" if state['username'] else "ندارد"
        await message.reply(
            f"👤 **پروفایل شما**\n\n"
            f"📛 نام: {state['name']}\n"
            f"🆔 آیدی عددی: `{chat_id}`\n"
            f"🔖 نام کاربری: {username_display}\n"
            f"🤝 تعداد دعوت‌ها: {state['invite_count']}\n"
            f"💰 کیف پول: {state['wallet']:,} تومان\n"
            f"📊 تعداد تبلیغات ثبت شده: {state['ads_count']}\n"
            f"💸 کل هزینه شده: {state['total_spent']:,} تومان\n\n"
            f"🔗 **لینک دعوت شما:**\n`https://ble.ir/{BOT_USERNAME}?start={chat_id}`\n\n"
            f"با دعوت دوستان خود {INVITE_REWARD:,} تومان دریافت کنید.",
            reply_markup=make_keyboard([["🤝 دعوت دوستان"], ["🔙 بازگشت"]])
        )
        return
    
    # ==============================================================
    # دعوت دوستان
    # ==============================================================
    if text == "🤝 دعوت دوستان":
        invite_link = f"https://ble.ir/{BOT_USERNAME}?start={chat_id}"
        await message.reply(
            f"🔗 **لینک دعوت شما:**\n`{invite_link}`\n\n"
            f"به ازای هر دعوت {INVITE_REWARD:,} تومان به کیف پول شما اضافه می‌شود.\n"
            f"⚠️ هر کاربر فقط یک بار می‌تواند دعوت شود.\n\n"
            f"📊 **تعداد دعوت‌های شما:** {state['invite_count']} نفر",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    # ==============================================================
    # کیف پول
    # ==============================================================
    if text == "💰 کیف پول":
        await message.reply(
            f"💰 **کیف پول شما**\n\n"
            f"💰 موجودی: {state['wallet']:,} تومان\n"
            f"📊 درآمد از کانال‌ها: {state['earnings']:,} تومان\n"
            f"💎 مجموع: {state['wallet'] + state['earnings']:,} تومان\n"
            f"📊 تعداد تبلیغات: {state['ads_count']}\n"
            f"💸 کل هزینه: {state['total_spent']:,} تومان\n\n"
            f"💡 مالیات تراکنش‌ها {int(TAX_RATE*100)}% است.\n"
            f"🎁 اعتبار هدیه: {WELCOME_BONUS:,} تومان\n"
            f"🤝 پاداش هر دعوت: {INVITE_REWARD:,} تومان",
            reply_markup=make_keyboard([
                ["➕ افزایش موجودی", "💸 برداشت درآمد"],
                ["🔄 انتقال سکه", "🎁 استفاده از کد هدیه"],
                ["🔙 بازگشت"]
            ])
        )
        return
    
    # ==============================================================
    # افزایش موجودی
    # ==============================================================
    if text == "➕ افزایش موجودی":
        await message.reply(
            f"💳 **برای افزایش اعتبار با ادمین تماس بگیرید:**\n\n"
            f"👤 **ادمین:** @AF87_ir\n"
            f"🆔 **آیدی عددی ادمین:** `{ADMIN_ID}`\n\n"
            f"💰 **حداقل شارژ:** 50,000 تومان\n"
            f"💳 **روش‌های پرداخت:** کارت به کارت، رمز دوم",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    # ==============================================================
    # برداشت درآمد
    # ==============================================================
    if text == "💸 برداشت درآمد":
        if state["earnings"] <= 0:
            await message.reply("❌ شما درآمدی برای برداشت ندارید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            return
        state["step"] = "earnings_withdraw_amount"
        await message.reply("💰 مبلغ مورد نظر برای برداشت (تومان) را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "earnings_withdraw_amount":
        try:
            amount = int(text)
            if amount <= 0 or amount > state["earnings"]:
                raise ValueError
            state["temp_data"]["withdraw_earnings"] = amount
            state["step"] = "earnings_withdraw_card"
            await message.reply("💳 شماره کارت مقصد را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        except:
            await message.reply("❌ مبلغ نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "earnings_withdraw_card":
        card = text.replace(" ", "")
        if not card.isdigit() or len(card) < 12:
            await message.reply("❌ شماره کارت نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            return
        amount = state["temp_data"]["withdraw_earnings"]
        earnings_requests.append({
            "user_id": chat_id,
            "amount": amount,
            "card": card,
            "name": state["name"],
            "username": state["username"],
            "status": "pending"
        })
        await bot.send_message(
            ADMIN_ID,
            f"📢 **درخواست برداشت درآمد جدید**\n\n"
            f"👤 کاربر: {state['name']} (@{state['username']}) - `{chat_id}`\n"
            f"💰 مبلغ: {amount:,} تومان\n"
            f"💳 کارت: `{card}`"
        )
        await message.reply("✅ درخواست شما ثبت شد و پس از تایید ادمین پرداخت می‌شود.", reply_markup=main_menu(chat_id))
        state["step"] = None
        return
    
    # ==============================================================
    # انتقال سکه
    # ==============================================================
    if text == "🔄 انتقال سکه":
        state["step"] = "transfer_target"
        await message.reply("👤 آیدی عددی کاربر مقصد را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "transfer_target":
        try:
            target_id = int(text)
            if target_id not in user_states:
                await message.reply("❌ کاربر مورد نظر یافت نشد.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
                return
            state["temp_data"]["transfer_target"] = target_id
            state["step"] = "transfer_amount"
            await message.reply("💰 مبلغ انتقال (تومان) را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        except:
            await message.reply("❌ آیدی عددی معتبر وارد کنید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "transfer_amount":
        try:
            amount = int(text)
            if amount <= 0:
                raise ValueError
            tax = int(amount * TAX_RATE)
            total = amount + tax
            if state["wallet"] < total:
                await message.reply(f"❌ موجودی کافی نیست. نیاز: {total:,} تومان (مالیات {tax:,} تومان)", reply_markup=make_keyboard([["🔙 بازگشت"]]))
                return
            target_id = state["temp_data"]["transfer_target"]
            state["wallet"] -= total
            user_states[target_id]["wallet"] += amount
            await message.reply(f"✅ انتقال {amount:,} تومان به کاربر {target_id} انجام شد. مالیات {tax:,} تومان کسر گردید.", reply_markup=main_menu(chat_id))
            await bot.send_message(target_id, f"💰 کاربر {chat_id} مبلغ {amount:,} تومان به شما انتقال داد.")
            state["step"] = None
        except:
            await message.reply("❌ مبلغ نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    # ==============================================================
    # کد هدیه
    # ==============================================================
    if text == "🎁 استفاده از کد هدیه":
        state["step"] = "gift_code"
        await message.reply("🎫 کد هدیه خود را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "gift_code":
        code = text.strip()
        if code not in gift_codes:
            await message.reply("❌ کد هدیه نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            state["step"] = None
            return
        
        gift = gift_codes[code]
        if datetime.now() > gift["expire"]:
            await message.reply("❌ این کد هدیه منقضی شده است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            state["step"] = None
            return
        
        if gift["count"] <= 0:
            await message.reply("❌ این کد هدیه قبلاً استفاده شده است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            state["step"] = None
            return
        
        if chat_id in gift["used"]:
            await message.reply("❌ شما قبلاً از این کد استفاده کرده‌اید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            state["step"] = None
            return
        
        gift["count"] -= 1
        gift["used"].append(chat_id)
        state["wallet"] += gift["amount"]
        await message.reply(f"✅ کد هدیه با موفقیت استفاده شد! {gift['amount']:,} تومان به کیف پول شما اضافه شد.", reply_markup=main_menu(chat_id))
        state["step"] = None
        return
    
    # ==============================================================
    # پیشنهاد کانال
    # ==============================================================
    if text == "📺 پیشنهاد کانال":
        state["step"] = "suggest_channel"
        await message.reply(
            "📢 **لطفاً اطلاعات کانال خود را وارد کنید:**\n\n"
            "فرمت: `@username`\n"
            "مثال: `@my_channel`\n\n"
            "کانال شما پس از تایید ادمین به لیست کانال‌های تبلیغاتی اضافه می‌شود.",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    if step == "suggest_channel":
        channel = text.strip()
        if not channel.startswith("@"):
            channel = "@" + channel
        
        pending_channels.append({
            "channel": channel,
            "added_by": chat_id,
            "user_name": state["name"],
            "user_username": state["username"],
            "status": "pending"
        })
        
        await bot.send_message(
            ADMIN_ID,
            f"📺 **پیشنهاد کانال جدید از کاربر**\n\n"
            f"👤 کاربر: {state['name']} (@{state['username']}) - `{chat_id}`\n"
            f"📺 کانال: {channel}\n\n"
            f"برای تایید از پنل ادمین اقدام کنید."
        )
        
        await message.reply(
            f"✅ کانال {channel} با موفقیت ثبت شد.\n"
            f"⏳ منتظر تایید ادمین بمانید.",
            reply_markup=main_menu(chat_id)
        )
        state["step"] = None
        return
    
    # ==============================================================
    # تیکت پشتیبانی
    # ==============================================================
    if text == "🎫 تیکت پشتیبانی":
        state["step"] = "ticket_text"
        await message.reply(
            "✏️ **متن تیکت خود را وارد کنید:**\n\n"
            "مشکل یا سوال خود را به طور کامل توضیح دهید.\n"
            "پس از ثبت، ادمین در اسرع وقت پاسخ خواهد داد.",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    if step == "ticket_text":
        ticket_id = str(uuid.uuid4())[:8]
        tickets.append({
            "id": ticket_id,
            "user_id": chat_id,
            "user_name": state["name"],
            "user_username": state["username"],
            "text": text,
            "status": "open",
            "date": datetime.now(),
            "response": None
        })
        await bot.send_message(
            ADMIN_ID,
            f"🎫 **تیکت جدید**\n\n"
            f"🆔 شناسه: `{ticket_id}`\n"
            f"👤 کاربر: {state['name']} (@{state['username']}) - `{chat_id}`\n"
            f"📝 متن: {text}\n"
            f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await message.reply(
            f"✅ **تیکت شما با موفقیت ثبت شد.**\n\n"
            f"🆔 شناسه تیکت: `{ticket_id}`\n"
            f"⏳ در اسرع وقت پاسخ داده می‌شود.\n\n"
            f"برای پیگیری، از بخش تیکت‌های پشتیبانی استفاده کنید.",
            reply_markup=main_menu(chat_id)
        )
        state["step"] = None
        return
    
    # ==============================================================
    # سفارش تبلیغات
    # ==============================================================
    if text == "📢 سفارش تبلیغات":
        state["step"] = "ad_type"
        await message.reply(
            "📢 **نوع تبلیغات را انتخاب کنید:**\n\n"
            "📸 **تبلیغ با عکس** - هزینه: ۱۰۰,۰۰۰ تومان\n"
            "📝 **تبلیغ بدون عکس** - هزینه: ۵۰,۰۰۰ تومان\n\n"
            f"💰 **موجودی کیف پول شما:** {state['wallet']:,} تومان\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=make_keyboard([["📸 تبلیغ با عکس", "📝 تبلیغ بدون عکس"], ["🔙 بازگشت"]])
        )
        return
    
    if step == "ad_type":
        if text == "📸 تبلیغ با عکس":
            price = 100000
            if state["wallet"] < price:
                await message.reply(
                    f"❌ **موجودی کافی نیست!**\n\n"
                    f"💰 هزینه تبلیغ با عکس: {price:,} تومان\n"
                    f"💰 موجودی شما: {state['wallet']:,} تومان\n\n"
                    f"❌ موجودی ناکافی: {price - state['wallet']:,} تومان کم دارید.\n\n"
                    f"لطفاً ابتدا کیف پول خود را شارژ کنید.",
                    reply_markup=make_keyboard([["➕ افزایش موجودی"], ["🔙 بازگشت"]])
                )
                state["step"] = None
                return
            
            state["temp_data"]["ad_price"] = price
            state["temp_data"]["ad_type"] = "image"
            state["step"] = "ad_text_image"
            await message.reply(
                "✏️ **لطفاً متن تبلیغ خود را ارسال کنید:**\n\n"
                "متن می‌تواند شامل توضیحات محصول، لینک کانال، شماره تماس و ... باشد.\n"
                "پس از ارسال متن، یک کد پیگیری دریافت خواهید کرد.",
                reply_markup=make_keyboard([["🔙 بازگشت"]])
            )
            return
        elif text == "📝 تبلیغ بدون عکس":
            price = 50000
            if state["wallet"] < price:
                await message.reply(
                    f"❌ **موجودی کافی نیست!**\n\n"
                    f"💰 هزینه تبلیغ بدون عکس: {price:,} تومان\n"
                    f"💰 موجودی شما: {state['wallet']:,} تومان\n\n"
                    f"❌ موجودی ناکافی: {price - state['wallet']:,} تومان کم دارید.\n\n"
                    f"لطفاً ابتدا کیف پول خود را شارژ کنید.",
                    reply_markup=make_keyboard([["➕ افزایش موجودی"], ["🔙 بازگشت"]])
                )
                state["step"] = None
                return
            
            state["temp_data"]["ad_price"] = price
            state["temp_data"]["ad_type"] = "text"
            state["step"] = "ad_text_only"
            await message.reply(
                "✏️ **لطفاً متن تبلیغ خود را ارسال کنید:**\n\n"
                "متن می‌تواند شامل توضیحات محصول، لینک کانال، شماره تماس و ... باشد.",
                reply_markup=make_keyboard([["🔙 بازگشت"]])
            )
            return
        else:
            await message.reply("❌ لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            return
    
    # دریافت متن تبلیغ با عکس (فقط ذخیره موقت، بدون کسر موجودی)
    if step == "ad_text_image":
        tracking_code = str(uuid.uuid4())[:8].upper()
        
        pending_ads[chat_id] = {
            "text": text,
            "price": state["temp_data"]["ad_price"],
            "type": "image",
            "tracking_code": tracking_code,
            "user_name": state["name"],
            "user_username": state["username"],
            "user_id": chat_id,
            "status": "waiting_for_image"
        }
        
        await message.reply(
            f"✅ **متن تبلیغ شما با موفقیت دریافت شد.**\n\n"
            f"🔑 **کد پیگیری شما:** `{tracking_code}`\n\n"
            f"📸 **لطفاً عکس تبلیغ خود را به همراه کد پیگیری به آیدی زیر ارسال کنید:**\n\n"
            f"👤 **ایدی ادمین:** @AF87_ir\n"
            f"🆔 **آیدی عددی ادمین:** `{ADMIN_ID}`\n\n"
            f"💰 **مبلغ قابل پرداخت:** {state['temp_data']['ad_price']:,} تومان\n"
            f"💸 **مالیات (۱۰%):** {int(state['temp_data']['ad_price'] * TAX_RATE):,} تومان\n"
            f"💎 **جمع قابل پرداخت:** {int(state['temp_data']['ad_price'] * (1 + TAX_RATE)):,} تومان\n\n"
            f"⚠️ **توجه:** پس از ارسال عکس و کد پیگیری برای ادمین، مبلغ از کیف پول شما کسر و سفارش ثبت خواهد شد.\n\n"
            f"برای لغو سفارش، دکمه 🔙 بازگشت را بزنید.",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        
        await bot.send_message(
            ADMIN_ID,
            f"📢 **درخواست تبلیغ جدید (با عکس)**\n\n"
            f"👤 کاربر: {state['name']} (@{state['username']}) - `{chat_id}`\n"
            f"🔑 کد پیگیری: `{tracking_code}`\n"
            f"💰 مبلغ: {state['temp_data']['ad_price']:,} تومان\n"
            f"📄 متن تبلیغ:\n{text}\n\n"
            f"⚠️ کاربر باید عکس را به همراه کد پیگیری برای شما ارسال کند."
        )
        
        state["step"] = None
        return
    
    # دریافت متن تبلیغ بدون عکس (کسر موجودی و ثبت)
    if step == "ad_text_only":
        price = state["temp_data"]["ad_price"]
        tax = int(price * TAX_RATE)
        total = price + tax
        
        if state["wallet"] < total:
            await message.reply(
                f"❌ **موجودی کافی نیست!**\n\n"
                f"💰 هزینه تبلیغ: {price:,} تومان\n"
                f"💸 مالیات: {tax:,} تومان\n"
                f"💎 جمع قابل پرداخت: {total:,} تومان\n"
                f"💰 موجودی شما: {state['wallet']:,} تومان\n\n"
                f"❌ موجودی ناکافی: {total - state['wallet']:,} تومان کم دارید.\n\n"
                f"لطفاً ابتدا کیف پول خود را شارژ کنید.",
                reply_markup=main_menu(chat_id)
            )
            state["step"] = None
            return
        
        # کسر موجودی
        state["wallet"] -= total
        
        ad_id = str(uuid.uuid4())[:8]
        ads_list.append({
            "id": ad_id,
            "user_id": chat_id,
            "user_name": state["name"],
            "user_username": state["username"],
            "type": "text",
            "text": text,
            "price": price,
            "tax": tax,
            "status": "pending",
            "date": datetime.now(),
            "amount_deducted": total  # مقدار کسر شده
        })
        
        await bot.send_message(
            ADMIN_ID,
            f"📢 **سفارش تبلیغ جدید (متنی)**\n\n"
            f"👤 کاربر: {state['name']} (@{state['username']}) - `{chat_id}`\n"
            f"💰 مبلغ: {price:,} تومان\n"
            f"💸 مالیات: {tax:,} تومان\n"
            f"📄 متن: {text}\n"
            f"🆔 شناسه سفارش: `{ad_id}`\n\n"
            f"برای تایید/رد از پنل ادمین اقدام کنید."
        )
        
        await message.reply(
            f"✅ **سفارش شما با موفقیت ثبت شد.**\n\n"
            f"🆔 **شناسه سفارش:** `{ad_id}`\n"
            f"💰 **مبلغ کسر شده:** {total:,} تومان (مالیات {tax:,} تومان)\n"
            f"⏳ **وضعیت:** در انتظار تایید ادمین\n\n"
            f"پس از تایید، تبلیغ شما در کانال‌ها منتشر خواهد شد.\n"
            f"در صورت رد، مبلغ به کیف پول شما برگشت داده می‌شود.",
            reply_markup=main_menu(chat_id)
        )
        state["step"] = None
        return
    
    # ==============================================================
    # دریافت عکس از ادمین و ثبت سفارش
    # ==============================================================
    if chat_id == ADMIN_ID and message.photo:
        caption = message.caption if message.caption else ""
        code_match = re.search(r'[A-Z0-9]{8}', caption)
        
        if code_match:
            tracking_code = code_match.group()
            
            found_user = None
            for uid, pending in pending_ads.items():
                if pending.get("tracking_code") == tracking_code and pending.get("status") == "waiting_for_image":
                    found_user = uid
                    break
            
            if found_user:
                file_id = message.photo[-1].file_id
                pending = pending_ads[found_user]
                
                price = pending["price"]
                tax = int(price * TAX_RATE)
                total = price + tax
                
                if user_states[found_user]["wallet"] < total:
                    await bot.send_message(
                        found_user,
                        f"❌ **موجودی کیف پول شما کافی نیست!**\n\n"
                        f"💰 هزینه تبلیغ: {price:,} تومان\n"
                        f"💸 مالیات: {tax:,} تومان\n"
                        f"💎 جمع قابل پرداخت: {total:,} تومان\n"
                        f"💰 موجودی شما: {user_states[found_user]['wallet']:,} تومان\n\n"
                        f"لطفاً ابتدا کیف پول خود را شارژ کنید.\n"
                        f"سفارش شما لغو شد."
                    )
                    await message.reply(f"❌ موجودی کاربر ناکافی است. سفارش لغو شد.\nکاربر: {pending['user_name']}")
                    del pending_ads[found_user]
                    return
                
                # کسر مبلغ
                user_states[found_user]["wallet"] -= total
                
                ad_id = str(uuid.uuid4())[:8]
                ads_list.append({
                    "id": ad_id,
                    "user_id": found_user,
                    "user_name": pending["user_name"],
                    "user_username": pending["user_username"],
                    "type": "image",
                    "text": pending["text"],
                    "image": file_id,
                    "price": price,
                    "tax": tax,
                    "status": "pending",
                    "date": datetime.now(),
                    "tracking_code": tracking_code,
                    "amount_deducted": total
                })
                
                await bot.send_message(
                    found_user,
                    f"✅ **عکس تبلیغ شما دریافت و سفارش ثبت شد.**\n\n"
                    f"🆔 **شناسه سفارش:** `{ad_id}`\n"
                    f"💰 **مبلغ کسر شده:** {total:,} تومان (مالیات {tax:,} تومان)\n"
                    f"⏳ **وضعیت:** در انتظار تایید نهایی ادمین\n\n"
                    f"پس از تایید، تبلیغ شما در کانال‌ها منتشر خواهد شد.\n"
                    f"در صورت رد، مبلغ به کیف پول شما برگشت داده می‌شود."
                )
                
                await message.reply(
                    f"✅ **سفارش با موفقیت ثبت شد.**\n\n"
                    f"👤 کاربر: {pending['user_name']} (@{pending['user_username']}) - `{found_user}`\n"
                    f"🆔 شناسه سفارش: `{ad_id}`\n"
                    f"💰 مبلغ: {price:,} تومان\n"
                    f"💸 مالیات: {tax:,} تومان\n\n"
                    f"برای تایید/رد از بخش سفارش‌های پنل ادمین اقدام کنید."
                )
                
                del pending_ads[found_user]
                return
            else:
                await message.reply("❌ کد پیگیری معتبر نیست یا سفارش منقضی شده است.")
                return
        else:
            await message.reply(
                "❌ **لطفاً کد پیگیری را به همراه عکس ارسال کنید.**\n\n"
                "فرمت صحیح:\n"
                "`ABC12345`\n\n"
                "کد پیگیری باید در کپشن عکس نوشته شود."
            )
            return
    
    # ==============================================================
    # پنل ادمین
    # ==============================================================
    if text == "👑 پنل ادمین" and chat_id == ADMIN_ID:
        if not state.get("admin_auth"):
            state["step"] = "admin_login"
            await message.reply("🔐 رمز عبور پنل ادمین را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        else:
            await message.reply("👑 به پنل ادمین خوش آمدید.", reply_markup=admin_menu())
        return
    
    if step == "admin_login":
        if text == ADMIN_PASSWORD:
            state["admin_auth"] = True
            state["step"] = None
            await message.reply("✅ ورود موفق. به پنل ادمین خوش آمدید.", reply_markup=admin_menu())
        else:
            await message.reply("❌ رمز اشتباه است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    # ==============================================================
    # منوی ادمین
    # ==============================================================
    if chat_id == ADMIN_ID and state.get("admin_auth"):
        
        # آمار کاربران (فقط آیدی عددی)
        if text == "📊 آمار کاربران":
            users_list = "\n".join([f"• `{uid}`" for uid in user_states.keys()])
            await message.reply(
                f"📊 **لیست آیدی عددی کاربران ({len(user_states)} نفر)**\n\n"
                f"{users_list}\n\n"
                f"برای مشاهده اطلاعات کامل یک کاربر، از گزینه «🔍 جستجوی کاربر» استفاده کنید.",
                reply_markup=admin_menu()
            )
            return
        
        # جستجوی کاربر
        if text == "🔍 جستجوی کاربر":
            state["step"] = "search_user"
            await message.reply(
                "🔍 **لطفاً آیدی عددی کاربر را وارد کنید:**\n\n"
                "مثال: `123456789`",
                reply_markup=make_keyboard([["🔙 بازگشت به پنل"]])
            )
            return
        
        if step == "search_user":
            try:
                target_id = int(text)
                if target_id not in user_states:
                    await message.reply("❌ کاربر یافت نشد.", reply_markup=admin_menu())
                    state["step"] = None
                    return
                
                target = user_states[target_id]
                username_display = f"@{target['username']}" if target['username'] else "ندارد"
                
                # محاسبه تعداد تبلیغات کاربر
                user_ads = [ad for ad in ads_list if ad["user_id"] == target_id]
                approved_ads = [ad for ad in user_ads if ad["status"] == "approved"]
                rejected_ads = [ad for ad in user_ads if ad["status"] == "rejected"]
                pending_ads_count = [ad for ad in user_ads if ad["status"] == "pending"]
                
                await message.reply(
                    f"👤 **اطلاعات کاربر**\n\n"
                    f"📛 نام: {target['name']}\n"
                    f"🆔 آیدی عددی: `{target_id}`\n"
                    f"🔖 نام کاربری: {username_display}\n"
                    f"🤝 تعداد دعوت‌ها: {target['invite_count']}\n"
                    f"💰 موجودی کیف پول: {target['wallet']:,} تومان\n"
                    f"📊 درآمد از کانال‌ها: {target['earnings']:,} تومان\n"
                    f"📈 تعداد کل تبلیغات ثبت شده: {len(user_ads)}\n"
                    f"✅ تبلیغات تایید شده: {len(approved_ads)}\n"
                    f"❌ تبلیغات رد شده: {len(rejected_ads)}\n"
                    f"⏳ تبلیغات در انتظار: {len(pending_ads_count)}\n"
                    f"💸 کل هزینه شده: {target['total_spent']:,} تومان\n"
                    f"📅 تاریخ عضویت: {target.get('join_date', 'نامشخص')}",
                    reply_markup=make_keyboard([
                        ["➕ انتقال اعتبار به این کاربر"],
                        ["🔙 بازگشت به پنل"]
                    ])
                )
                state["step"] = None
            except:
                await message.reply("❌ آیدی عددی نامعتبر است.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        # انتقال اعتبار به کاربر جستجو شده
        if text == "➕ انتقال اعتبار به این کاربر":
            state["step"] = "transfer_to_searched"
            await message.reply("💰 مبلغ (تومان) را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "transfer_to_searched" and "temp_data" in state and "searched_user" in state["temp_data"]:
            try:
                amount = int(text)
                target_id = state["temp_data"]["searched_user"]
                user_states[target_id]["wallet"] += amount
                await message.reply(f"✅ {amount:,} تومان به کاربر {target_id} اضافه شد.", reply_markup=admin_menu())
                await bot.send_message(target_id, f"👑 ادمین {amount:,} تومان به کیف پول شما اضافه کرد.")
                state["step"] = None
            except:
                await message.reply("❌ مبلغ نامعتبر.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        # سفارش‌ها (نمایش همه سفارشات)
        if text == "📋 سفارش‌ها":
            all_ads = [ad for ad in ads_list]
            if not all_ads:
                await message.reply("📋 هیچ سفارشی وجود ندارد.", reply_markup=admin_menu())
                return
            
            if chat_id not in current_page:
                current_page[chat_id] = 0
            
            page = current_page[chat_id]
            total_pages = len(all_ads)
            
            if page >= total_pages:
                page = total_pages - 1
                current_page[chat_id] = page
            
            if page < 0:
                page = 0
                current_page[chat_id] = page
            
            ad = all_ads[page]
            
            status_emoji = {
                "pending": "⏳",
                "approved": "✅",
                "rejected": "❌"
            }
            
            keyboard_rows = []
            if ad["status"] == "pending":
                keyboard_rows.append([f"✅ تایید|{ad['id']}", f"❌ رد|{ad['id']}"])
            
            nav_buttons = []
            if page > 0:
                nav_buttons.append("◀️ قبلی")
            if page < total_pages - 1:
                nav_buttons.append("بعدی ▶️")
            if nav_buttons:
                keyboard_rows.append(nav_buttons)
            
            keyboard_rows.append(["🔙 بازگشت به پنل"])
            
            message_text = (
                f"📋 **سفارش {page+1} از {total_pages}**\n\n"
                f"🆔 شناسه: `{ad['id']}`\n"
                f"👤 کاربر: {ad['user_name']} (@{ad['user_username']})\n"
                f"🆔 آیدی کاربر: `{ad['user_id']}`\n"
                f"📝 نوع: {'📸 با عکس' if ad['type'] == 'image' else '📝 متنی'}\n"
                f"💰 مبلغ: {ad['price']:,} تومان\n"
                f"💸 مالیات: {ad['tax']:,} تومان\n"
                f"💎 جمع کسر شده: {ad.get('amount_deducted', ad['price'] + ad['tax']):,} تومان\n"
                f"📊 وضعیت: {status_emoji[ad['status']]} {ad['status']}\n"
                f"📄 متن: {ad['text'][:300]}\n"
                f"📅 تاریخ: {ad['date'].strftime('%Y-%m-%d %H:%M')}"
            )
            
            if ad['type'] == 'image' and 'image' in ad:
                await bot.send_photo(chat_id, ad['image'], caption=message_text, reply_markup=make_keyboard(keyboard_rows))
            else:
                await message.reply(message_text, reply_markup=make_keyboard(keyboard_rows))
            return
        
        if text == "◀️ قبلی":
            if chat_id in current_page:
                current_page[chat_id] -= 1
            else:
                current_page[chat_id] = 0
            all_ads = [ad for ad in ads_list]
            if all_ads:
                page = current_page[chat_id]
                if page < 0:
                    page = 0
                    current_page[chat_id] = page
                ad = all_ads[page]
                
                status_emoji = {
                    "pending": "⏳",
                    "approved": "✅",
                    "rejected": "❌"
                }
                
                keyboard_rows = []
                if ad["status"] == "pending":
                    keyboard_rows.append([f"✅ تایید|{ad['id']}", f"❌ رد|{ad['id']}"])
                
                nav_buttons = []
                if page > 0:
                    nav_buttons.append("◀️ قبلی")
                if page < len(all_ads) - 1:
                    nav_buttons.append("بعدی ▶️")
                if nav_buttons:
                    keyboard_rows.append(nav_buttons)
                keyboard_rows.append(["🔙 بازگشت به پنل"])
                
                message_text = (
                    f"📋 **سفارش {page+1} از {len(all_ads)}**\n\n"
                    f"🆔 شناسه: `{ad['id']}`\n"
                    f"👤 کاربر: {ad['user_name']} (@{ad['user_username']})\n"
                    f"🆔 آیدی کاربر: `{ad['user_id']}`\n"
                    f"📝 نوع: {'📸 با عکس' if ad['type'] == 'image' else '📝 متنی'}\n"
                    f"💰 مبلغ: {ad['price']:,} تومان\n"
                    f"💸 مالیات: {ad['tax']:,} تومان\n"
                    f"📊 وضعیت: {status_emoji[ad['status']]} {ad['status']}\n"
                    f"📄 متن: {ad['text'][:300]}"
                )
                
                if ad['type'] == 'image' and 'image' in ad:
                    await bot.send_photo(chat_id, ad['image'], caption=message_text, reply_markup=make_keyboard(keyboard_rows))
                else:
                    await message.reply(message_text, reply_markup=make_keyboard(keyboard_rows))
            return
        
        if text == "بعدی ▶️":
            if chat_id in current_page:
                current_page[chat_id] += 1
            else:
                current_page[chat_id] = 1
            all_ads = [ad for ad in ads_list]
            if all_ads:
                page = current_page[chat_id]
                if page >= len(all_ads):
                    page = len(all_ads) - 1
                    current_page[chat_id] = page
                ad = all_ads[page]
                
                status_emoji = {
                    "pending": "⏳",
                    "approved": "✅",
                    "rejected": "❌"
                }
                
                keyboard_rows = []
                if ad["status"] == "pending":
                    keyboard_rows.append([f"✅ تایید|{ad['id']}", f"❌ رد|{ad['id']}"])
                
                nav_buttons = []
                if page > 0:
                    nav_buttons.append("◀️ قبلی")
                if page < len(all_ads) - 1:
                    nav_buttons.append("بعدی ▶️")
                if nav_buttons:
                    keyboard_rows.append(nav_buttons)
                keyboard_rows.append(["🔙 بازگشت به پنل"])
                
                message_text = (
                    f"📋 **سفارش {page+1} از {len(all_ads)}**\n\n"
                    f"🆔 شناسه: `{ad['id']}`\n"
                    f"👤 کاربر: {ad['user_name']} (@{ad['user_username']})\n"
                    f"🆔 آیدی کاربر: `{ad['user_id']}`\n"
                    f"📝 نوع: {'📸 با عکس' if ad['type'] == 'image' else '📝 متنی'}\n"
                    f"💰 مبلغ: {ad['price']:,} تومان\n"
                    f"💸 مالیات: {ad['tax']:,} تومان\n"
                    f"📊 وضعیت: {status_emoji[ad['status']]} {ad['status']}\n"
                    f"📄 متن: {ad['text'][:300]}"
                )
                
                if ad['type'] == 'image' and 'image' in ad:
                    await bot.send_photo(chat_id, ad['image'], caption=message_text, reply_markup=make_keyboard(keyboard_rows))
                else:
                    await message.reply(message_text, reply_markup=make_keyboard(keyboard_rows))
            return
        
        # تایید سفارش
        if text.startswith("✅ تایید|"):
            ad_id = text.split("|")[1]
            for ad in ads_list:
                if ad["id"] == ad_id and ad["status"] == "pending":
                    ad["status"] = "approved"
                    
                    # به روز رسانی آمار کاربر
                    user_states[ad["user_id"]]["ads_count"] += 1
                    user_states[ad["user_id"]]["total_spent"] += ad.get("amount_deducted", ad["price"] + ad["tax"])
                    
                    await bot.send_message(
                        ad["user_id"],
                        f"✅ **سفارش تبلیغ شما تایید شد!**\n\n"
                        f"🆔 شناسه سفارش: `{ad_id}`\n"
                        f"📢 تبلیغ شما در کانال‌ها منتشر خواهد شد.\n\n"
                        f"با تشکر از اعتماد شما."
                    )
                    await message.reply(f"✅ سفارش {ad_id} تایید شد.", reply_markup=admin_menu())
                    if chat_id in current_page:
                        current_page[chat_id] = 0
                    return
            await message.reply("❌ شناسه نامعتبر است.", reply_markup=admin_menu())
            return
        
        # رد سفارش (برگشت موجودی)
        if text.startswith("❌ رد|"):
            ad_id = text.split("|")[1]
            for ad in ads_list:
                if ad["id"] == ad_id and ad["status"] == "pending":
                    ad["status"] = "rejected"
                    
                    # برگشت مبلغ به کاربر
                    refund_amount = ad.get("amount_deducted", ad["price"] + ad["tax"])
                    user_states[ad["user_id"]]["wallet"] += refund_amount
                    
                    await bot.send_message(
                        ad["user_id"],
                        f"❌ **سفارش تبلیغ شما رد شد.**\n\n"
                        f"🆔 شناسه سفارش: `{ad_id}`\n"
                        f"💰 مبلغ {refund_amount:,} تومان به کیف پول شما برگشت داده شد.\n\n"
                        f"در صورت نیاز با پشتیبانی تماس بگیرید."
                    )
                    await message.reply(f"❌ سفارش {ad_id} رد شد. مبلغ به کاربر برگشت داده شد.", reply_markup=admin_menu())
                    if chat_id in current_page:
                        current_page[chat_id] = 0
                    return
            await message.reply("❌ شناسه نامعتبر است.", reply_markup=admin_menu())
            return
        
        # مدیریت کد هدیه
        if text == "🎁 مدیریت کد هدیه":
            state["step"] = "gift_admin"
            await message.reply(
                "🎁 **مدیریت کد هدیه**\n\n"
                "1️⃣ ایجاد کد جدید\n"
                "2️⃣ حذف کد\n"
                "3️⃣ لیست کدها\n\n"
                "عدد مورد نظر را وارد کنید:",
                reply_markup=make_keyboard([["🔙 بازگشت به پنل"]])
            )
            return
        
        if step == "gift_admin":
            if text == "1":
                state["step"] = "gift_create_amount"
                await message.reply("💰 مبلغ کد هدیه (تومان):", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            elif text == "2":
                state["step"] = "gift_delete"
                await message.reply("🎫 کد هدیه را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            elif text == "3":
                if not gift_codes:
                    await message.reply("هیچ کد هدیه‌ای وجود ندارد.", reply_markup=admin_menu())
                    state["step"] = None
                    return
                codes_text = "\n".join([f"🔑 {code}: {g['amount']:,} تومان - باقیمانده: {g['count']} - انقضا: {g['expire'].strftime('%Y-%m-%d')}" for code, g in gift_codes.items()])
                await message.reply(f"🎫 **لیست کدها:**\n\n{codes_text}", reply_markup=admin_menu())
                state["step"] = None
            else:
                await message.reply("❌ گزینه نامعتبر.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        if step == "gift_create_amount":
            try:
                amount = int(text)
                state["temp_data"]["gift_amount"] = amount
                state["step"] = "gift_create_count"
                await message.reply("🔢 تعداد دفعات قابل استفاده:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            except:
                await message.reply("❌ مبلغ نامعتبر.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        if step == "gift_create_count":
            try:
                count = int(text)
                state["temp_data"]["gift_count"] = count
                state["step"] = "gift_create_days"
                await message.reply("📅 تعداد روز اعتبار:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            except:
                await message.reply("❌ تعداد نامعتبر.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        if step == "gift_create_days":
            try:
                days = int(text)
                code = str(uuid.uuid4())[:8].upper()
                gift_codes[code] = {
                    "amount": state["temp_data"]["gift_amount"],
                    "count": state["temp_data"]["gift_count"],
                    "expire": datetime.now() + timedelta(days=days),
                    "used": []
                }
                await message.reply(f"✅ کد هدیه ایجاد شد:\n🔑 `{code}`\n💰 مبلغ: {state['temp_data']['gift_amount']:,} تومان\n🔢 تعداد: {state['temp_data']['gift_count']}\n📅 اعتبار: {days} روز", reply_markup=admin_menu())
                state["step"] = None
            except:
                await message.reply("❌ تعداد روز نامعتبر.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        if step == "gift_delete":
            if text in gift_codes:
                del gift_codes[text]
                await message.reply(f"✅ کد {text} حذف شد.", reply_markup=admin_menu())
            else:
                await message.reply("❌ کد یافت نشد.", reply_markup=admin_menu())
            state["step"] = None
            return
        
        # ارسال همگانی
        if text == "📢 ارسال همگانی":
            state["step"] = "broadcast_msg"
            await message.reply("✏️ متن پیام همگانی را ارسال کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "broadcast_msg":
            count = 0
            for uid in user_states:
                try:
                    await bot.send_message(uid, text)
                    count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
            await message.reply(f"✅ پیام به {count} کاربر ارسال شد.", reply_markup=admin_menu())
            state["step"] = None
            return
        
        # مدیریت کانال‌ها
        if text == "📺 مدیریت کانال‌ها":
            await message.reply("📺 **مدیریت کانال‌های تبلیغاتی**", reply_markup=channels_menu())
            return
        
        if text == "📺 لیست کانال‌ها":
            if not CHANNELS_FOR_AD:
                await message.reply("❌ هیچ کانالی ثبت نشده است.", reply_markup=channels_menu())
            else:
                channels_text = "\n".join([f"• {ch}" for ch in CHANNELS_FOR_AD])
                await message.reply(f"📺 **کانال‌های فعال:**\n\n{channels_text}", reply_markup=channels_menu())
            return
        
        if text == "➕ اضافه کردن کانال جدید":
            state["step"] = "admin_add_channel"
            await message.reply("📢 لطفاً آیدی کانال جدید را وارد کنید (مثال: @mychannel):", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "admin_add_channel":
            channel = text.strip()
            if not channel.startswith("@"):
                channel = "@" + channel
            pending_channels.append({
                "channel": channel,
                "added_by": chat_id,
                "status": "pending"
            })
            await message.reply(f"✅ کانال {channel} برای تایید اضافه شد.", reply_markup=channels_menu())
            state["step"] = None
            return
        
        if text == "✅ تایید کانال":
            if not pending_channels:
                await message.reply("❌ هیچ کانالی در انتظار تایید نیست.", reply_markup=channels_menu())
                return
            for i, ch in enumerate(pending_channels):
                await message.reply(
                    f"{i+1}. کانال: {ch['channel']} - پیشنهاد دهنده: {ch.get('user_name', 'ادمین')}",
                    reply_markup=make_keyboard([[f"✅ تایید کانال|{i}"]])
                )
            state["step"] = "admin_approve_channel"
            return
        
        if step == "admin_approve_channel" and text.startswith("✅ تایید کانال|"):
            try:
                index = int(text.split("|")[1])
                if 0 <= index < len(pending_channels):
                    channel = pending_channels[index]["channel"]
                    CHANNELS_FOR_AD.append(channel)
                    
                    if "added_by" in pending_channels[index] and pending_channels[index]["added_by"] != ADMIN_ID:
                        await bot.send_message(
                            pending_channels[index]["added_by"],
                            f"✅ **کانال شما تایید شد!**\n\n"
                            f"📺 کانال: {channel}\n"
                            f"🎉 کانال شما به لیست کانال‌های تبلیغاتی اضافه شد.\n"
                            f"اکنون تبلیغات در کانال شما نیز منتشر می‌شود."
                        )
                    
                    await message.reply(f"✅ کانال {channel} با موفقیت تایید شد.", reply_markup=channels_menu())
                    pending_channels.pop(index)
                else:
                    await message.reply("❌ شماره نامعتبر است.", reply_markup=channels_menu())
            except:
                await message.reply("❌ خطا در تایید کانال.", reply_markup=channels_menu())
            state["step"] = None
            return
        
        if text == "❌ حذف کانال":
            if not CHANNELS_FOR_AD:
                await message.reply("❌ هیچ کانالی برای حذف وجود ندارد.", reply_markup=channels_menu())
                return
            for i, ch in enumerate(CHANNELS_FOR_AD):
                await message.reply(
                    f"{i+1}. کانال: {ch}",
                    reply_markup=make_keyboard([[f"❌ حذف کانال|{i}"]])
                )
            state["step"] = "admin_remove_channel"
            return
        
        if step == "admin_remove_channel" and text.startswith("❌ حذف کانال|"):
            try:
                index = int(text.split("|")[1])
                if 0 <= index < len(CHANNELS_FOR_AD):
                    removed = CHANNELS_FOR_AD.pop(index)
                    await message.reply(f"✅ کانال {removed} با موفقیت حذف شد.", reply_markup=channels_menu())
                else:
                    await message.reply("❌ شماره نامعتبر است.", reply_markup=channels_menu())
            except:
                await message.reply("❌ خطا در حذف کانال.", reply_markup=channels_menu())
            state["step"] = None
            return
        
        if text == "⏳ کانال‌های منتظر تایید":
            if not pending_channels:
                await message.reply("❌ هیچ کانالی در انتظار تایید نیست.", reply_markup=channels_menu())
            else:
                pending_text = "\n".join([f"• {ch['channel']} - پیشنهاد: {ch.get('user_name', 'ادمین')}" for ch in pending_channels])
                await message.reply(f"⏳ **کانال‌های منتظر تایید:**\n\n{pending_text}", reply_markup=channels_menu())
            return
        
        # کانال‌های پیشنهادی کاربران
        if text == "✅ کانال‌های پیشنهادی":
            if not pending_channels:
                await message.reply("❌ هیچ کانال پیشنهادی وجود ندارد.", reply_markup=admin_menu())
            else:
                pending_text = "\n".join([f"• {ch['channel']} - پیشنهاد: {ch.get('user_name', 'ناشناس')} (@{ch.get('user_username', '')})" for ch in pending_channels])
                await message.reply(f"✅ **کانال‌های پیشنهادی کاربران:**\n\n{pending_text}\n\nبرای تایید از بخش «✅ تایید کانال» استفاده کنید.", reply_markup=admin_menu())
            return
        
        # انتقال اعتبار
        if text == "➕ انتقال اعتبار":
            state["step"] = "admin_transfer_user"
            await message.reply("👤 آیدی عددی کاربر مقصد:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "admin_transfer_user":
            try:
                target_id = int(text)
                if target_id not in user_states:
                    await message.reply("❌ کاربر یافت نشد.", reply_markup=admin_menu())
                    state["step"] = None
                    return
                state["temp_data"]["admin_target"] = target_id
                state["step"] = "admin_transfer_amount"
                await message.reply("💰 مبلغ (تومان):", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            except:
                await message.reply("❌ آیدی نامعتبر.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        if step == "admin_transfer_amount":
            try:
                amount = int(text)
                target_id = state["temp_data"]["admin_target"]
                user_states[target_id]["wallet"] += amount
                await message.reply(f"✅ {amount:,} تومان به کاربر {target_id} اضافه شد.", reply_markup=admin_menu())
                await bot.send_message(target_id, f"👑 ادمین {amount:,} تومان به کیف پول شما اضافه کرد.")
                state["step"] = None
            except:
                await message.reply("❌ مبلغ نامعتبر.", reply_markup=admin_menu())
                state["step"] = None
            return
        
        # درخواست‌های برداشت
        if text == "💸 درخواست‌های برداشت":
            await message.reply("💸 **مدیریت درخواست‌های برداشت**", reply_markup=withdraws_menu())
            return
        
        if text == "💸 مشاهده درخواست‌های برداشت":
            pending_req = [r for r in earnings_requests if r["status"] == "pending"]
            if not pending_req:
                await message.reply("هیچ درخواست در انتظاری وجود ندارد.", reply_markup=withdraws_menu())
                return
            for req in pending_req:
                await message.reply(
                    f"👤 کاربر: {req['name']} (@{req['username']}) - `{req['user_id']}`\n"
                    f"💰 مبلغ: {req['amount']:,} تومان\n"
                    f"💳 کارت: `{req['card']}`",
                    reply_markup=make_keyboard([
                        [f"✅ تایید برداشت|{req['user_id']}"],
                        [f"❌ رد برداشت|{req['user_id']}"],
                        ["🔙 بازگشت به پنل"]
                    ])
                )
            return
        
        if text.startswith("✅ تایید برداشت|"):
            user_id = int(text.split("|")[1])
            for req in earnings_requests:
                if req["user_id"] == user_id and req["status"] == "pending":
                    req["status"] = "approved"
                    user_states[user_id]["earnings"] -= req["amount"]
                    await bot.send_message(user_id, f"✅ درخواست برداشت {req['amount']:,} تومان تایید شد.\nمبلغ به کارت {req['card']} واریز خواهد شد.")
                    await message.reply("✅ برداشت تایید شد.", reply_markup=withdraws_menu())
                    return
            await message.reply("❌ کاربر یافت نشد.", reply_markup=withdraws_menu())
            return
        
        if text.startswith("❌ رد برداشت|"):
            user_id = int(text.split("|")[1])
            for req in earnings_requests:
                if req["user_id"] == user_id and req["status"] == "pending":
                    req["status"] = "rejected"
                    await bot.send_message(user_id, f"❌ درخواست برداشت {req['amount']:,} تومان رد شد.")
                    await message.reply("❌ برداشت رد شد.", reply_markup=withdraws_menu())
                    return
            await message.reply("❌ کاربر یافت نشد.", reply_markup=withdraws_menu())
            return
        
        # مدیریت تیکت‌ها
        if text == "🎫 مدیریت تیکت‌ها":
            await message.reply("🎫 **مدیریت تیکت‌ها**", reply_markup=tickets_menu())
            return
        
        if text == "🎫 مشاهده تیکت‌های باز":
            open_tickets = [t for t in tickets if t["status"] == "open"]
            if not open_tickets:
                await message.reply("هیچ تیکت باز وجود ندارد.", reply_markup=tickets_menu())
                return
            for t in open_tickets:
                await message.reply(
                    f"🆔 شناسه: `{t['id']}`\n"
                    f"👤 کاربر: {t['user_name']} (@{t['user_username']}) - `{t['user_id']}`\n"
                    f"📝 متن: {t['text']}\n"
                    f"📅 تاریخ: {t['date'].strftime('%Y-%m-%d %H:%M')}",
                    reply_markup=make_keyboard([
                        [f"📝 پاسخ به تیکت|{t['id']}"],
                        ["🔙 بازگشت به پنل"]
                    ])
                )
            return
        
        if text.startswith("📝 پاسخ به تیکت|"):
            ticket_id = text.split("|")[1]
            state["step"] = "reply_ticket"
            state["temp_data"]["ticket_id"] = ticket_id
            await message.reply("✏️ پاسخ خود را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "reply_ticket":
            ticket_id = state["temp_data"]["ticket_id"]
            for t in tickets:
                if t["id"] == ticket_id and t["status"] == "open":
                    t["status"] = "closed"
                    t["response"] = text
                    await bot.send_message(t["user_id"], f"🎫 **پاسخ تیکت شما:**\n\n{text}\n\n✅ تیکت شما بسته شد.\n\nدر صورت نیاز می‌توانید تیکت جدید ثبت کنید.")
                    await message.reply("✅ پاسخ ارسال شد.", reply_markup=tickets_menu())
                    state["step"] = None
                    return
            await message.reply("❌ تیکت یافت نشد.", reply_markup=tickets_menu())
            state["step"] = None
            return
        
        # خروج از پنل
        if text == "🚪 خروج از پنل":
            state["admin_auth"] = False
            await message.reply("🚪 از پنل ادمین خارج شدید.", reply_markup=main_menu(chat_id))
            return
        
        if not text.startswith("/"):
            await message.reply("❌ دستور نامعتبر. از دکمه‌های منو استفاده کنید.", reply_markup=admin_menu())
        return
    
    # ==============================================================
    # دستور ناشناخته
    # ==============================================================
    if step is None:
        await message.reply("❌ دستور نامعتبر است. از دکمه‌های منو استفاده کنید.", reply_markup=main_menu(chat_id))
    else:
        await message.reply("❌ لطفاً طبق راهنمایی پیش بروید یا از دکمه بازگشت استفاده کنید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))

# ----------------------------------------------------------------------
# اجرای ربات
# ----------------------------------------------------------------------
if __name__ == "__main__":
    bot.run()
