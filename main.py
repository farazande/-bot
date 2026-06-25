from balethon import Client
import asyncio
import uuid
from datetime import datetime, timedelta
import re
import sqlite3
import json
from pathlib import Path

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
DB_PATH = "bot_database.db"

# ----------------------------------------------------------------------
# 2. کلاس مدیریت پایگاه داده
# ----------------------------------------------------------------------
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """ایجاد جداول مورد نیاز"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول کاربران
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                wallet INTEGER DEFAULT 0,
                earnings INTEGER DEFAULT 0,
                invite_count INTEGER DEFAULT 0,
                invited_by INTEGER,
                ads_count INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                join_date TEXT,
                is_admin INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 0,
                premium_ads_count INTEGER DEFAULT 0,
                total_earnings INTEGER DEFAULT 0
            )
        ''')
        
        # جدول تبلیغات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                ad_id TEXT PRIMARY KEY,
                user_id INTEGER,
                user_name TEXT,
                user_username TEXT,
                type TEXT,
                text TEXT,
                image_id TEXT,
                price INTEGER,
                tax INTEGER,
                status TEXT,
                date TEXT,
                tracking_code TEXT,
                amount_deducted INTEGER,
                is_premium INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول کدهای هدیه
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gift_codes (
                code TEXT PRIMARY KEY,
                amount INTEGER,
                count INTEGER,
                expire TEXT,
                used_users TEXT
            )
        ''')
        
        # جدول کانال‌های پیشنهادی
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                added_by INTEGER,
                user_name TEXT,
                user_username TEXT,
                status TEXT,
                date TEXT
            )
        ''')
        
        # جدول تیکت‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                user_id INTEGER,
                user_name TEXT,
                user_username TEXT,
                text TEXT,
                status TEXT,
                date TEXT,
                response TEXT,
                response_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول درخواست‌های برداشت
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                card TEXT,
                name TEXT,
                username TEXT,
                status TEXT,
                date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول وضعیت‌های کاربران (برای استپ‌ها)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                step TEXT,
                temp_data TEXT,
                admin_auth INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول پیام‌های در انتظار عکس
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_ads (
                user_id INTEGER PRIMARY KEY,
                text TEXT,
                price INTEGER,
                ad_type TEXT,
                tracking_code TEXT,
                user_name TEXT,
                user_username TEXT,
                status TEXT,
                date TEXT,
                is_premium INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id):
        """دریافت اطلاعات کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['user_id', 'name', 'username', 'wallet', 'earnings', 'invite_count', 
                      'invited_by', 'ads_count', 'total_spent', 'join_date', 'is_admin',
                      'reputation', 'premium_ads_count', 'total_earnings']
            return dict(zip(columns, result))
        return None
    
    def create_user(self, user_id, name, username, invited_by=None):
        """ایجاد کاربر جدید"""
        conn = self.get_connection()
        cursor = conn.cursor()
        join_date = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (user_id, name, username, wallet, join_date, invited_by, is_admin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, username, WELCOME_BONUS, join_date, invited_by, 1 if user_id == ADMIN_ID else 0))
        
        # اضافه کردن وضعیت کاربر
        cursor.execute('''
            INSERT INTO user_states (user_id, step, temp_data, admin_auth)
            VALUES (?, ?, ?, ?)
        ''', (user_id, None, json.dumps({}), 1 if user_id == ADMIN_ID else 0))
        
        conn.commit()
        conn.close()
        return self.get_user(user_id)
    
    def update_user(self, user_id, **kwargs):
        """بروزرسانی اطلاعات کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        cursor.execute(f'UPDATE users SET {set_clause} WHERE user_id = ?', values)
        conn.commit()
        conn.close()
    
    def get_state(self, user_id):
        """دریافت وضعیت کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT step, temp_data, admin_auth FROM user_states WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'step': result[0],
                'temp_data': json.loads(result[1]) if result[1] else {},
                'admin_auth': bool(result[2])
            }
        return {'step': None, 'temp_data': {}, 'admin_auth': False}
    
    def update_state(self, user_id, step=None, temp_data=None, admin_auth=None):
        """بروزرسانی وضعیت کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if step is not None:
            updates.append('step = ?')
            values.append(step)
        
        if temp_data is not None:
            updates.append('temp_data = ?')
            values.append(json.dumps(temp_data))
        
        if admin_auth is not None:
            updates.append('admin_auth = ?')
            values.append(1 if admin_auth else 0)
        
        if updates:
            values.append(user_id)
            cursor.execute(f'UPDATE user_states SET {", ".join(updates)} WHERE user_id = ?', values)
            conn.commit()
        
        conn.close()
    
    def add_ad(self, ad_data):
        """افزودن تبلیغ جدید"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ads (
                ad_id, user_id, user_name, user_username, type, text, image_id,
                price, tax, status, date, tracking_code, amount_deducted, is_premium
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ad_data['id'], ad_data['user_id'], ad_data['user_name'], ad_data['user_username'],
            ad_data['type'], ad_data['text'], ad_data.get('image_id'),
            ad_data['price'], ad_data['tax'], ad_data['status'],
            ad_data['date'].isoformat(), ad_data.get('tracking_code'),
            ad_data.get('amount_deducted', ad_data['price'] + ad_data['tax']),
            ad_data.get('is_premium', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_ads(self, user_id=None, status=None):
        """دریافت لیست تبلیغات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ads'
        params = []
        
        conditions = []
        if user_id:
            conditions.append('user_id = ?')
            params.append(user_id)
        if status:
            conditions.append('status = ?')
            params.append(status)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        columns = ['ad_id', 'user_id', 'user_name', 'user_username', 'type', 'text', 'image_id',
                  'price', 'tax', 'status', 'date', 'tracking_code', 'amount_deducted', 'is_premium',
                  'views', 'clicks']
        
        return [dict(zip(columns, row)) for row in results]
    
    def update_ad_status(self, ad_id, status):
        """بروزرسانی وضعیت تبلیغ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE ads SET status = ? WHERE ad_id = ?', (status, ad_id))
        conn.commit()
        conn.close()
    
    def add_gift_code(self, code, amount, count, days):
        """افزودن کد هدیه"""
        conn = self.get_connection()
        cursor = conn.cursor()
        expire = (datetime.now() + timedelta(days=days)).isoformat()
        
        cursor.execute('''
            INSERT INTO gift_codes (code, amount, count, expire, used_users)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, amount, count, expire, json.dumps([])))
        
        conn.commit()
        conn.close()
    
    def use_gift_code(self, code, user_id):
        """استفاده از کد هدیه"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM gift_codes WHERE code = ?', (code,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        columns = ['code', 'amount', 'count', 'expire', 'used_users']
        gift = dict(zip(columns, result))
        
        used_users = json.loads(gift['used_users'])
        if user_id in used_users:
            conn.close()
            return 'already_used'
        
        if datetime.fromisoformat(gift['expire']) < datetime.now():
            conn.close()
            return 'expired'
        
        if gift['count'] <= 0:
            conn.close()
            return 'no_count'
        
        # بروزرسانی کد
        used_users.append(user_id)
        cursor.execute('''
            UPDATE gift_codes 
            SET count = ?, used_users = ? 
            WHERE code = ?
        ''', (gift['count'] - 1, json.dumps(used_users), code))
        
        # اضافه کردن به کیف پول کاربر
        self.update_user(user_id, wallet=self.get_user(user_id)['wallet'] + gift['amount'])
        
        conn.commit()
        conn.close()
        return gift['amount']
    
    def get_gift_codes(self):
        """دریافت لیست کدهای هدیه"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM gift_codes')
        results = cursor.fetchall()
        conn.close()
        
        columns = ['code', 'amount', 'count', 'expire', 'used_users']
        return [dict(zip(columns, row)) for row in results]
    
    def delete_gift_code(self, code):
        """حذف کد هدیه"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM gift_codes WHERE code = ?', (code,))
        conn.commit()
        conn.close()
    
    def add_pending_channel(self, channel, user_id, user_name, user_username):
        """افزودن کانال پیشنهادی"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pending_channels (channel, added_by, user_name, user_username, status, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (channel, user_id, user_name, user_username, 'pending', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_pending_channels(self):
        """دریافت کانال‌های در انتظار"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pending_channels WHERE status = "pending"')
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'channel', 'added_by', 'user_name', 'user_username', 'status', 'date']
        return [dict(zip(columns, row)) for row in results]
    
    def approve_channel(self, channel_id):
        """تایید کانال"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # دریافت اطلاعات کانال
        cursor.execute('SELECT * FROM pending_channels WHERE id = ?', (channel_id,))
        result = cursor.fetchone()
        
        if result:
            columns = ['id', 'channel', 'added_by', 'user_name', 'user_username', 'status', 'date']
            channel = dict(zip(columns, result))
            
            # بروزرسانی وضعیت
            cursor.execute('UPDATE pending_channels SET status = "approved" WHERE id = ?', (channel_id,))
            conn.commit()
            conn.close()
            return channel
        
        conn.close()
        return None
    
    def add_ticket(self, ticket_id, user_id, user_name, user_username, text):
        """افزودن تیکت جدید"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tickets (ticket_id, user_id, user_name, user_username, text, status, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_id, user_id, user_name, user_username, text, 'open', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_tickets(self, status=None):
        """دریافت تیکت‌ها"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM tickets WHERE status = ? ORDER BY date DESC', (status,))
        else:
            cursor.execute('SELECT * FROM tickets ORDER BY date DESC')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['ticket_id', 'user_id', 'user_name', 'user_username', 'text', 'status', 'date', 'response', 'response_date']
        return [dict(zip(columns, row)) for row in results]
    
    def reply_ticket(self, ticket_id, response):
        """پاسخ به تیکت"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tickets 
            SET status = "closed", response = ?, response_date = ? 
            WHERE ticket_id = ?
        ''', (response, datetime.now().isoformat(), ticket_id))
        
        conn.commit()
        conn.close()
    
    def add_withdraw_request(self, user_id, amount, card, name, username):
        """افزودن درخواست برداشت"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO withdraw_requests (user_id, amount, card, name, username, status, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, card, name, username, 'pending', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_withdraw_requests(self, status=None):
        """دریافت درخواست‌های برداشت"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM withdraw_requests WHERE status = ? ORDER BY date DESC', (status,))
        else:
            cursor.execute('SELECT * FROM withdraw_requests ORDER BY date DESC')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'user_id', 'amount', 'card', 'name', 'username', 'status', 'date']
        return [dict(zip(columns, row)) for row in results]
    
    def update_withdraw_status(self, request_id, status):
        """بروزرسانی وضعیت درخواست برداشت"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE withdraw_requests SET status = ? WHERE id = ?', (status, request_id))
        conn.commit()
        conn.close()
    
    def add_pending_ad(self, user_id, text, price, ad_type, tracking_code, user_name, user_username, is_premium=0):
        """افزودن تبلیغ در انتظار عکس"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pending_ads 
            (user_id, text, price, ad_type, tracking_code, user_name, user_username, status, date, is_premium)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, text, price, ad_type, tracking_code, user_name, user_username, 
              'waiting_for_image', datetime.now().isoformat(), is_premium))
        
        conn.commit()
        conn.close()
    
    def get_pending_ad(self, user_id):
        """دریافت تبلیغ در انتظار"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pending_ads WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['user_id', 'text', 'price', 'ad_type', 'tracking_code', 
                      'user_name', 'user_username', 'status', 'date', 'is_premium']
            return dict(zip(columns, result))
        return None
    
    def delete_pending_ad(self, user_id):
        """حذف تبلیغ در انتظار"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pending_ads WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        """دریافت لیست همه کاربران"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, username, wallet, earnings, ads_count, reputation FROM users ORDER BY reputation DESC')
        results = cursor.fetchall()
        conn.close()
        
        columns = ['user_id', 'name', 'username', 'wallet', 'earnings', 'ads_count', 'reputation']
        return [dict(zip(columns, row)) for row in results]
    
    def get_user_stats(self):
        """دریافت آمار کلی"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # تعداد کل کاربران
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # تعداد تبلیغات
        cursor.execute('SELECT COUNT(*) FROM ads')
        total_ads = cursor.fetchone()[0]
        
        # تعداد تبلیغات تایید شده
        cursor.execute('SELECT COUNT(*) FROM ads WHERE status = "approved"')
        approved_ads = cursor.fetchone()[0]
        
        # کل مبلغ تبلیغات
        cursor.execute('SELECT SUM(price) FROM ads WHERE status = "approved"')
        total_revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_ads': total_ads,
            'approved_ads': approved_ads,
            'total_revenue': total_revenue
        }

# ----------------------------------------------------------------------
# 3. مقداردهی اولیه
# ----------------------------------------------------------------------
db = Database(DB_PATH)

# اگر کاربر ادمین وجود ندارد، ایجاد کن
if not db.get_user(ADMIN_ID):
    db.create_user(ADMIN_ID, "Admin", "admin")

# ----------------------------------------------------------------------
# 4. توابع کمکی
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
            ["🎫 تیکت پشتیبانی"],
            ["🏆 رتبه بندی"]
        ])
    else:
        return make_keyboard([
            ["📢 سفارش تبلیغات"],
            ["💰 کیف پول", "👤 پروفایل"],
            ["📺 پیشنهاد کانال", "🎫 تیکت پشتیبانی"],
            ["🏆 رتبه بندی"]
        ])

def admin_menu():
    return make_keyboard([
        ["📊 آمار کاربران", "🔍 جستجوی کاربر"],
        ["📋 سفارش‌ها", "🎁 مدیریت کد هدیه"],
        ["📢 ارسال همگانی", "📺 مدیریت کانال‌ها"],
        ["💸 درخواست‌های برداشت", "🎫 مدیریت تیکت‌ها"],
        ["✅ کانال‌های پیشنهادی", "➕ انتقال اعتبار"],
        ["⭐ تبلیغات ویژه", "🚪 خروج از پنل"]
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
# 5. ربات اصلی
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
    
    # دریافت اطلاعات کاربر از دیتابیس
    user_data = db.get_user(chat_id)
    state = db.get_state(chat_id)
    
    if not user_data:
        # کاربر جدید
        invited_by = None
        if text.startswith("/start") and len(text.split()) == 2:
            try:
                invited_by = int(text.split()[1])
                if invited_by == chat_id:
                    invited_by = None
            except:
                pass
        
        user_data = db.create_user(chat_id, message.chat.first_name or "کاربر", 
                                   message.chat.username or "", invited_by)
        
        # اگر کاربر با لینک دعوت آمده باشد
        if invited_by and invited_by != chat_id:
            inviter = db.get_user(invited_by)
            if inviter:
                db.update_user(invited_by, wallet=inviter['wallet'] + INVITE_REWARD, 
                              invite_count=inviter['invite_count'] + 1)
                await bot.send_message(invited_by, f"🎉 کاربر {user_data['name']} با لینک شما دعوت شد! {INVITE_REWARD:,} تومان به کیف پول شما اضافه شد.")
                await message.reply(f"🎉 شما توسط {inviter['name']} دعوت شدید! {WELCOME_BONUS:,} تومان اعتبار هدیه دریافت کردید.")
        
        await message.reply(f"🎁 **تبریک!** {WELCOME_BONUS:,} تومان اعتبار هدیه به کیف پول شما اضافه شد!")
    
    step = state.get("step")
    temp_data = state.get("temp_data", {})
    is_admin = chat_id == ADMIN_ID
    
    # ==============================================================
    # شروع ربات
    # ==============================================================
    if text == "/start":
        channels_text = "\n".join(CHANNELS_FOR_AD)
        
        # بررسی امتیاز کاربر
        reputation = user_data.get('reputation', 0)
        rank = "🥉 برنز"
        if reputation >= 50:
            rank = "🥈 نقره"
        if reputation >= 100:
            rank = "🥇 طلا"
        if reputation >= 200:
            rank = "💎 پلاتینیوم"
        
        await message.reply(
            f"🤖 **به ربات تبلیغات خوش آمدید!**\n\n"
            f"🎁 **اعتبار هدیه:** {WELCOME_BONUS:,} تومان\n"
            f"📢 **تبلیغات شما در کانال‌های زیر انجام می‌شود:**\n{channels_text}\n\n"
            f"🔗 **لینک دعوت شما:**\n`https://ble.ir/{BOT_USERNAME}?start={chat_id}`\n\n"
            f"💰 **با هر دعوت {INVITE_REWARD:,} تومان دریافت کنید!**\n\n"
            f"🏅 **رتبه شما:** {rank} (امتیاز: {reputation})\n\n"
            f"طراحی و ساخت توسط شرکت [نوآوران بات](https://ble.ir/innovarbots)\n"
            f"از منوی زیر استفاده کنید:",
            reply_markup=main_menu(chat_id)
        )
        db.update_state(chat_id, step=None)
        return
    
    # ==============================================================
    # دکمه بازگشت
    # ==============================================================
    if text == "🔙 بازگشت":
        db.update_state(chat_id, step=None)
        await message.reply("به منوی اصلی بازگشتید.", reply_markup=main_menu(chat_id))
        return
    
    if text == "🔙 بازگشت به پنل":
        db.update_state(chat_id, step=None)
        await message.reply("به پنل ادمین بازگشتید.", reply_markup=admin_menu())
        return
    
    # ==============================================================
    # پروفایل
    # ==============================================================
    if text == "👤 پروفایل":
        username_display = f"@{user_data['username']}" if user_data['username'] else "ندارد"
        reputation = user_data.get('reputation', 0)
        
        rank = "🥉 برنز"
        if reputation >= 50:
            rank = "🥈 نقره"
        if reputation >= 100:
            rank = "🥇 طلا"
        if reputation >= 200:
            rank = "💎 پلاتینیوم"
        
        await message.reply(
            f"👤 **پروفایل شما**\n\n"
            f"📛 نام: {user_data['name']}\n"
            f"🆔 آیدی عددی: `{chat_id}`\n"
            f"🔖 نام کاربری: {username_display}\n"
            f"🤝 تعداد دعوت‌ها: {user_data['invite_count']}\n"
            f"💰 کیف پول: {user_data['wallet']:,} تومان\n"
            f"📊 تعداد تبلیغات ثبت شده: {user_data['ads_count']}\n"
            f"💸 کل هزینه شده: {user_data['total_spent']:,} تومان\n"
            f"🏅 رتبه: {rank} (امتیاز: {reputation})\n"
            f"⭐ تبلیغات ویژه: {user_data.get('premium_ads_count', 0)}\n\n"
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
            f"📊 **تعداد دعوت‌های شما:** {user_data['invite_count']} نفر",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    # ==============================================================
    # رتبه بندی
    # ==============================================================
    if text == "🏆 رتبه بندی":
        users = db.get_all_users()
        top_users = sorted(users, key=lambda x: x['reputation'], reverse=True)[:10]
        
        if not top_users:
            await message.reply("هنوز کاربری برای رتبه‌بندی وجود ندارد.", reply_markup=main_menu(chat_id))
            return
        
        ranking_text = "🏆 **رتبه‌بندی کاربران برتر**\n\n"
        for i, user in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            ranking_text += f"{medal} {user['name']} - امتیاز: {user['reputation']} - تبلیغات: {user['ads_count']}\n"
        
        ranking_text += f"\n📊 **رتبه شما:** {users.index(next((u for u in users if u['user_id'] == chat_id), {'user_id': 0})) + 1 if any(u['user_id'] == chat_id for u in users) else 'نامشخص'}"
        
        await message.reply(ranking_text, reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    # ==============================================================
    # کیف پول
    # ==============================================================
    if text == "💰 کیف پول":
        await message.reply(
            f"💰 **کیف پول شما**\n\n"
            f"💰 موجودی: {user_data['wallet']:,} تومان\n"
            f"📊 درآمد از کانال‌ها: {user_data['earnings']:,} تومان\n"
            f"💎 مجموع: {user_data['wallet'] + user_data['earnings']:,} تومان\n"
            f"📊 تعداد تبلیغات: {user_data['ads_count']}\n"
            f"💸 کل هزینه: {user_data['total_spent']:,} تومان\n\n"
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
        if user_data['earnings'] <= 0:
            await message.reply("❌ شما درآمدی برای برداشت ندارید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            return
        db.update_state(chat_id, step="earnings_withdraw_amount")
        await message.reply("💰 مبلغ مورد نظر برای برداشت (تومان) را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "earnings_withdraw_amount":
        try:
            amount = int(text)
            if amount <= 0 or amount > user_data['earnings']:
                raise ValueError
            temp_data['withdraw_earnings'] = amount
            db.update_state(chat_id, step="earnings_withdraw_card", temp_data=temp_data)
            await message.reply("💳 شماره کارت مقصد را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        except:
            await message.reply("❌ مبلغ نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "earnings_withdraw_card":
        card = text.replace(" ", "")
        if not card.isdigit() or len(card) < 12:
            await message.reply("❌ شماره کارت نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            return
        amount = temp_data["withdraw_earnings"]
        
        db.add_withdraw_request(chat_id, amount, card, user_data['name'], user_data['username'])
        
        await bot.send_message(
            ADMIN_ID,
            f"📢 **درخواست برداشت درآمد جدید**\n\n"
            f"👤 کاربر: {user_data['name']} (@{user_data['username']}) - `{chat_id}`\n"
            f"💰 مبلغ: {amount:,} تومان\n"
            f"💳 کارت: `{card}`"
        )
        await message.reply("✅ درخواست شما ثبت شد و پس از تایید ادمین پرداخت می‌شود.", reply_markup=main_menu(chat_id))
        db.update_state(chat_id, step=None)
        return
    
    # ==============================================================
    # انتقال سکه
    # ==============================================================
    if text == "🔄 انتقال سکه":
        db.update_state(chat_id, step="transfer_target")
        await message.reply("👤 آیدی عددی کاربر مقصد را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "transfer_target":
        try:
            target_id = int(text)
            if not db.get_user(target_id):
                await message.reply("❌ کاربر مورد نظر یافت نشد.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
                return
            temp_data['transfer_target'] = target_id
            db.update_state(chat_id, step="transfer_amount", temp_data=temp_data)
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
            if user_data['wallet'] < total:
                await message.reply(f"❌ موجودی کافی نیست. نیاز: {total:,} تومان (مالیات {tax:,} تومان)", reply_markup=make_keyboard([["🔙 بازگشت"]]))
                return
            target_id = temp_data['transfer_target']
            
            db.update_user(chat_id, wallet=user_data['wallet'] - total)
            target_user = db.get_user(target_id)
            db.update_user(target_id, wallet=target_user['wallet'] + amount)
            
            await message.reply(f"✅ انتقال {amount:,} تومان به کاربر {target_id} انجام شد. مالیات {tax:,} تومان کسر گردید.", reply_markup=main_menu(chat_id))
            await bot.send_message(target_id, f"💰 کاربر {chat_id} مبلغ {amount:,} تومان به شما انتقال داد.")
            db.update_state(chat_id, step=None)
        except:
            await message.reply("❌ مبلغ نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    # ==============================================================
    # کد هدیه
    # ==============================================================
    if text == "🎁 استفاده از کد هدیه":
        db.update_state(chat_id, step="gift_code")
        await message.reply("🎫 کد هدیه خود را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    if step == "gift_code":
        code = text.strip()
        result = db.use_gift_code(code, chat_id)
        
        if result is None:
            await message.reply("❌ کد هدیه نامعتبر است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        elif result == 'already_used':
            await message.reply("❌ شما قبلاً از این کد استفاده کرده‌اید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        elif result == 'expired':
            await message.reply("❌ این کد هدیه منقضی شده است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        elif result == 'no_count':
            await message.reply("❌ این کد هدیه قبلاً استفاده شده است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        else:
            await message.reply(f"✅ کد هدیه با موفقیت استفاده شد! {result:,} تومان به کیف پول شما اضافه شد.", reply_markup=main_menu(chat_id))
        
        db.update_state(chat_id, step=None)
        return
    
    # ==============================================================
    # پیشنهاد کانال
    # ==============================================================
    if text == "📺 پیشنهاد کانال":
        db.update_state(chat_id, step="suggest_channel")
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
        
        db.add_pending_channel(channel, chat_id, user_data['name'], user_data['username'])
        
        await bot.send_message(
            ADMIN_ID,
            f"📺 **پیشنهاد کانال جدید از کاربر**\n\n"
            f"👤 کاربر: {user_data['name']} (@{user_data['username']}) - `{chat_id}`\n"
            f"📺 کانال: {channel}\n\n"
            f"برای تایید از پنل ادمین اقدام کنید."
        )
        
        await message.reply(
            f"✅ کانال {channel} با موفقیت ثبت شد.\n"
            f"⏳ منتظر تایید ادمین بمانید.",
            reply_markup=main_menu(chat_id)
        )
        db.update_state(chat_id, step=None)
        return
    
    # ==============================================================
    # تیکت پشتیبانی
    # ==============================================================
    if text == "🎫 تیکت پشتیبانی":
        db.update_state(chat_id, step="ticket_text")
        await message.reply(
            "✏️ **متن تیکت خود را وارد کنید:**\n\n"
            "مشکل یا سوال خود را به طور کامل توضیح دهید.\n"
            "پس از ثبت، ادمین در اسرع وقت پاسخ خواهد داد.",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    if step == "ticket_text":
        ticket_id = str(uuid.uuid4())[:8]
        
        db.add_ticket(ticket_id, chat_id, user_data['name'], user_data['username'], text)
        
        await bot.send_message(
            ADMIN_ID,
            f"🎫 **تیکت جدید**\n\n"
            f"🆔 شناسه: `{ticket_id}`\n"
            f"👤 کاربر: {user_data['name']} (@{user_data['username']}) - `{chat_id}`\n"
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
        db.update_state(chat_id, step=None)
        return
    
    # ==============================================================
    # سفارش تبلیغات
    # ==============================================================
    if text == "📢 سفارش تبلیغات":
        db.update_state(chat_id, step="ad_type")
        await message.reply(
            "📢 **نوع تبلیغات را انتخاب کنید:**\n\n"
            "📸 **تبلیغ با عکس** - هزینه: ۱۰۰,۰۰۰ تومان\n"
            "📝 **تبلیغ بدون عکس** - هزینه: ۵۰,۰۰۰ تومان\n"
            "⭐ **تبلیغ ویژه (پریمیوم)** - هزینه: ۲۰۰,۰۰۰ تومان (نمایش در بالای لیست)\n\n"
            f"💰 **موجودی کیف پول شما:** {user_data['wallet']:,} تومان\n\n"
            f"🏅 **امتیاز شما:** {user_data.get('reputation', 0)}\n"
            f"💎 **تبلیغات ویژه ثبت شده:** {user_data.get('premium_ads_count', 0)}\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=make_keyboard([
                ["📸 تبلیغ با عکس", "📝 تبلیغ بدون عکس"],
                ["⭐ تبلیغ ویژه"],
                ["🔙 بازگشت"]
            ])
        )
        return
    
    if step == "ad_type":
        price = 0
        ad_type = ""
        is_premium = 0
        
        if text == "📸 تبلیغ با عکس":
            price = 100000
            ad_type = "image"
        elif text == "📝 تبلیغ بدون عکس":
            price = 50000
            ad_type = "text"
        elif text == "⭐ تبلیغ ویژه":
            price = 200000
            ad_type = "image"
            is_premium = 1
        else:
            await message.reply("❌ لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
            return
        
        if user_data['wallet'] < price:
            await message.reply(
                f"❌ **موجودی کافی نیست!**\n\n"
                f"💰 هزینه تبلیغ: {price:,} تومان\n"
                f"💰 موجودی شما: {user_data['wallet']:,} تومان\n\n"
                f"❌ موجودی ناکافی: {price - user_data['wallet']:,} تومان کم دارید.\n\n"
                f"لطفاً ابتدا کیف پول خود را شارژ کنید.",
                reply_markup=make_keyboard([["➕ افزایش موجودی"], ["🔙 بازگشت"]])
            )
            db.update_state(chat_id, step=None)
            return
        
        temp_data['ad_price'] = price
        temp_data['ad_type'] = ad_type
        temp_data['is_premium'] = is_premium
        db.update_state(chat_id, step="ad_text", temp_data=temp_data)
        
        await message.reply(
            "✏️ **لطفاً متن تبلیغ خود را ارسال کنید:**\n\n"
            "متن می‌تواند شامل توضیحات محصول، لینک کانال، شماره تماس و ... باشد.\n"
            "پس از ارسال متن، از شما درخواست عکس می‌شود (در صورت نیاز).",
            reply_markup=make_keyboard([["🔙 بازگشت"]])
        )
        return
    
    # دریافت متن تبلیغ
    if step == "ad_text":
        temp_data['text'] = text
        
        if temp_data.get('ad_type') == "image":
            db.update_state(chat_id, step="ad_image", temp_data=temp_data)
            await message.reply(
                "📸 **لطفاً عکس تبلیغ خود را ارسال کنید:**\n\n"
                "عکس باید با کیفیت مناسب باشد.\n"
                "می‌توانید یک عکس یا فایل ارسال کنید.",
                reply_markup=make_keyboard([["🔙 بازگشت"]])
            )
        else:
            # تبلیغ بدون عکس - کسر مستقیم
            await process_ad_without_image(message, chat_id, user_data, temp_data)
        return
    
    # دریافت عکس تبلیغ
    if step == "ad_image" and message.photo:
        file_id = message.photo[-1].file_id
        temp_data['image_id'] = file_id
        
        await process_ad_with_image(message, chat_id, user_data, temp_data)
        return
    
    # ==============================================================
    # پنل ادمین
    # ==============================================================
    if text == "👑 پنل ادمین" and chat_id == ADMIN_ID:
        if not state.get("admin_auth"):
            db.update_state(chat_id, step="admin_login")
            await message.reply("🔐 رمز عبور پنل ادمین را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        else:
            await message.reply("👑 به پنل ادمین خوش آمدید.", reply_markup=admin_menu())
        return
    
    if step == "admin_login":
        if text == ADMIN_PASSWORD:
            db.update_state(chat_id, admin_auth=True, step=None)
            await message.reply("✅ ورود موفق. به پنل ادمین خوش آمدید.", reply_markup=admin_menu())
        else:
            await message.reply("❌ رمز اشتباه است.", reply_markup=make_keyboard([["🔙 بازگشت"]]))
        return
    
    # ==============================================================
    # منوی ادمین
    # ==============================================================
    if chat_id == ADMIN_ID and state.get("admin_auth"):
        
        # آمار کاربران
        if text == "📊 آمار کاربران":
            stats = db.get_user_stats()
            users = db.get_all_users()
            
            await message.reply(
                f"📊 **آمار کلی ربات**\n\n"
                f"👥 تعداد کاربران: {stats['total_users']}\n"
                f"📋 کل تبلیغات: {stats['total_ads']}\n"
                f"✅ تبلیغات تایید شده: {stats['approved_ads']}\n"
                f"💰 درآمد کل: {stats['total_revenue']:,} تومان\n"
                f"🏅 کاربران با امتیاز بالا: {len([u for u in users if u['reputation'] >= 50])}\n\n"
                f"📊 **۱۰ کاربر برتر:**\n",
                reply_markup=admin_menu()
            )
            
            top_users = sorted(users, key=lambda x: x['reputation'], reverse=True)[:10]
            ranking_text = ""
            for i, u in enumerate(top_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                ranking_text += f"{medal} {u['name']} - امتیاز: {u['reputation']}\n"
            
            if ranking_text:
                await message.reply(ranking_text, reply_markup=admin_menu())
            return
        
        # جستجوی کاربر
        if text == "🔍 جستجوی کاربر":
            db.update_state(chat_id, step="search_user")
            await message.reply(
                "🔍 **لطفاً آیدی عددی کاربر را وارد کنید:**\n\n"
                "مثال: `123456789`",
                reply_markup=make_keyboard([["🔙 بازگشت به پنل"]])
            )
            return
        
        if step == "search_user":
            try:
                target_id = int(text)
                target = db.get_user(target_id)
                if not target:
                    await message.reply("❌ کاربر یافت نشد.", reply_markup=admin_menu())
                    db.update_state(chat_id, step=None)
                    return
                
                username_display = f"@{target['username']}" if target['username'] else "ندارد"
                
                # محاسبه تعداد تبلیغات کاربر
                user_ads = db.get_ads(user_id=target_id)
                approved_ads = [ad for ad in user_ads if ad['status'] == 'approved']
                rejected_ads = [ad for ad in user_ads if ad['status'] == 'rejected']
                pending_ads_count = [ad for ad in user_ads if ad['status'] == 'pending']
                
                rank = "🥉 برنز"
                if target.get('reputation', 0) >= 50:
                    rank = "🥈 نقره"
                if target.get('reputation', 0) >= 100:
                    rank = "🥇 طلا"
                if target.get('reputation', 0) >= 200:
                    rank = "💎 پلاتینیوم"
                
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
                    f"🏅 رتبه: {rank} (امتیاز: {target.get('reputation', 0)})\n"
                    f"⭐ تبلیغات ویژه: {target.get('premium_ads_count', 0)}\n"
                    f"📅 تاریخ عضویت: {target.get('join_date', 'نامشخص')}",
                    reply_markup=make_keyboard([
                        ["➕ انتقال اعتبار به این کاربر"],
                        ["⭐ افزودن امتیاز"],
                        ["🔙 بازگشت به پنل"]
                    ])
                )
                temp_data['searched_user'] = target_id
                db.update_state(chat_id, step=None, temp_data=temp_data)
            except:
                await message.reply("❌ آیدی عددی نامعتبر است.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        # انتقال اعتبار به کاربر جستجو شده
        if text == "➕ انتقال اعتبار به این کاربر":
            if 'searched_user' not in temp_data:
                await message.reply("❌ ابتدا یک کاربر را جستجو کنید.", reply_markup=admin_menu())
                return
            db.update_state(chat_id, step="transfer_to_searched", temp_data=temp_data)
            await message.reply("💰 مبلغ (تومان) را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "transfer_to_searched" and 'searched_user' in temp_data:
            try:
                amount = int(text)
                target_id = temp_data["searched_user"]
                target = db.get_user(target_id)
                db.update_user(target_id, wallet=target['wallet'] + amount)
                await message.reply(f"✅ {amount:,} تومان به کاربر {target_id} اضافه شد.", reply_markup=admin_menu())
                await bot.send_message(target_id, f"👑 ادمین {amount:,} تومان به کیف پول شما اضافه کرد.")
                db.update_state(chat_id, step=None)
            except:
                await message.reply("❌ مبلغ نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        # افزودن امتیاز
        if text == "⭐ افزودن امتیاز":
            if 'searched_user' not in temp_data:
                await message.reply("❌ ابتدا یک کاربر را جستجو کنید.", reply_markup=admin_menu())
                return
            db.update_state(chat_id, step="add_reputation", temp_data=temp_data)
            await message.reply("⭐ تعداد امتیاز را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "add_reputation" and 'searched_user' in temp_data:
            try:
                points = int(text)
                target_id = temp_data["searched_user"]
                target = db.get_user(target_id)
                db.update_user(target_id, reputation=target.get('reputation', 0) + points)
                await message.reply(f"✅ {points} امتیاز به کاربر {target_id} اضافه شد.", reply_markup=admin_menu())
                await bot.send_message(target_id, f"⭐ ادمین {points} امتیاز به شما اضافه کرد.")
                db.update_state(chat_id, step=None)
            except:
                await message.reply("❌ تعداد نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        # سفارش‌ها
        if text == "📋 سفارش‌ها":
            all_ads = db.get_ads()
            if not all_ads:
                await message.reply("📋 هیچ سفارشی وجود ندارد.", reply_markup=admin_menu())
                return
            
            if chat_id not in temp_data.get('current_page', {}):
                if 'current_page' not in temp_data:
                    temp_data['current_page'] = {}
                temp_data['current_page'][chat_id] = 0
            
            page = temp_data['current_page'].get(chat_id, 0)
            total_pages = len(all_ads)
            
            if page >= total_pages:
                page = total_pages - 1
                temp_data['current_page'][chat_id] = page
            
            if page < 0:
                page = 0
                temp_data['current_page'][chat_id] = page
            
            ad = all_ads[page]
            
            status_emoji = {
                "pending": "⏳",
                "approved": "✅",
                "rejected": "❌"
            }
            
            keyboard_rows = []
            if ad['status'] == "pending":
                keyboard_rows.append([f"✅ تایید|{ad['ad_id']}", f"❌ رد|{ad['ad_id']}"])
            
            nav_buttons = []
            if page > 0:
                nav_buttons.append("◀️ قبلی")
            if page < total_pages - 1:
                nav_buttons.append("بعدی ▶️")
            if nav_buttons:
                keyboard_rows.append(nav_buttons)
            
            keyboard_rows.append(["🔙 بازگشت به پنل"])
            
            premium_text = "⭐ ویژه" if ad.get('is_premium', 0) else "عادی"
            
            message_text = (
                f"📋 **سفارش {page+1} از {total_pages}**\n\n"
                f"🆔 شناسه: `{ad['ad_id']}`\n"
                f"👤 کاربر: {ad['user_name']} (@{ad['user_username']})\n"
                f"🆔 آیدی کاربر: `{ad['user_id']}`\n"
                f"📝 نوع: {'📸 با عکس' if ad['type'] == 'image' else '📝 متنی'}\n"
                f"⭐ نوع تبلیغ: {premium_text}\n"
                f"💰 مبلغ: {ad['price']:,} تومان\n"
                f"💸 مالیات: {ad['tax']:,} تومان\n"
                f"💎 جمع کسر شده: {ad.get('amount_deducted', ad['price'] + ad['tax']):,} تومان\n"
                f"📊 وضعیت: {status_emoji[ad['status']]} {ad['status']}\n"
                f"📄 متن: {ad['text'][:300]}\n"
                f"📅 تاریخ: {ad['date']}"
            )
            
            if ad['type'] == 'image' and ad.get('image_id'):
                await bot.send_photo(chat_id, ad['image_id'], caption=message_text, reply_markup=make_keyboard(keyboard_rows))
            else:
                await message.reply(message_text, reply_markup=make_keyboard(keyboard_rows))
            
            db.update_state(chat_id, temp_data=temp_data)
            return
        
        # تایید سفارش
        if text.startswith("✅ تایید|"):
            ad_id = text.split("|")[1]
            all_ads = db.get_ads()
            for ad in all_ads:
                if ad['ad_id'] == ad_id and ad['status'] == "pending":
                    db.update_ad_status(ad_id, "approved")
                    
                    # به روز رسانی آمار کاربر
                    user = db.get_user(ad['user_id'])
                    db.update_user(ad['user_id'], 
                                  ads_count=user['ads_count'] + 1,
                                  total_spent=user['total_spent'] + ad.get('amount_deducted', ad['price'] + ad['tax']),
                                  reputation=user.get('reputation', 0) + 5)
                    
                    # اگر تبلیغ ویژه بود
                    if ad.get('is_premium', 0):
                        db.update_user(ad['user_id'], 
                                      premium_ads_count=user.get('premium_ads_count', 0) + 1)
                    
                    await bot.send_message(
                        ad['user_id'],
                        f"✅ **سفارش تبلیغ شما تایید شد!**\n\n"
                        f"🆔 شناسه سفارش: `{ad_id}`\n"
                        f"⭐ {'تبلیغ ویژه' if ad.get('is_premium', 0) else 'تبلیغ عادی'}\n"
                        f"📢 تبلیغ شما در کانال‌ها منتشر خواهد شد.\n\n"
                        f"با تشکر از اعتماد شما.\n"
                        f"🏅 +۵ امتیاز به شما تعلق گرفت."
                    )
                    await message.reply(f"✅ سفارش {ad_id} تایید شد. +۵ امتیاز به کاربر تعلق گرفت.", reply_markup=admin_menu())
                    if 'current_page' in temp_data:
                        temp_data['current_page'][chat_id] = 0
                        db.update_state(chat_id, temp_data=temp_data)
                    return
            await message.reply("❌ شناسه نامعتبر است.", reply_markup=admin_menu())
            return
        
        # رد سفارش
        if text.startswith("❌ رد|"):
            ad_id = text.split("|")[1]
            all_ads = db.get_ads()
            for ad in all_ads:
                if ad['ad_id'] == ad_id and ad['status'] == "pending":
                    db.update_ad_status(ad_id, "rejected")
                    
                    # برگشت مبلغ
                    refund_amount = ad.get('amount_deducted', ad['price'] + ad['tax'])
                    user = db.get_user(ad['user_id'])
                    db.update_user(ad['user_id'], wallet=user['wallet'] + refund_amount)
                    
                    await bot.send_message(
                        ad['user_id'],
                        f"❌ **سفارش تبلیغ شما رد شد.**\n\n"
                        f"🆔 شناسه سفارش: `{ad_id}`\n"
                        f"💰 مبلغ {refund_amount:,} تومان به کیف پول شما برگشت داده شد.\n\n"
                        f"در صورت نیاز با پشتیبانی تماس بگیرید."
                    )
                    await message.reply(f"❌ سفارش {ad_id} رد شد. مبلغ به کاربر برگشت داده شد.", reply_markup=admin_menu())
                    if 'current_page' in temp_data:
                        temp_data['current_page'][chat_id] = 0
                        db.update_state(chat_id, temp_data=temp_data)
                    return
            await message.reply("❌ شناسه نامعتبر است.", reply_markup=admin_menu())
            return
        
        # مدیریت کد هدیه
        if text == "🎁 مدیریت کد هدیه":
            db.update_state(chat_id, step="gift_admin")
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
                db.update_state(chat_id, step="gift_create_amount")
                await message.reply("💰 مبلغ کد هدیه (تومان):", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            elif text == "2":
                db.update_state(chat_id, step="gift_delete")
                await message.reply("🎫 کد هدیه را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            elif text == "3":
                codes = db.get_gift_codes()
                if not codes:
                    await message.reply("هیچ کد هدیه‌ای وجود ندارد.", reply_markup=admin_menu())
                    db.update_state(chat_id, step=None)
                    return
                codes_text = "\n".join([f"🔑 {c['code']}: {c['amount']:,} تومان - باقیمانده: {c['count']} - انقضا: {c['expire']}" for c in codes])
                await message.reply(f"🎫 **لیست کدها:**\n\n{codes_text}", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            else:
                await message.reply("❌ گزینه نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        if step == "gift_create_amount":
            try:
                amount = int(text)
                temp_data['gift_amount'] = amount
                db.update_state(chat_id, step="gift_create_count", temp_data=temp_data)
                await message.reply("🔢 تعداد دفعات قابل استفاده:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            except:
                await message.reply("❌ مبلغ نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        if step == "gift_create_count":
            try:
                count = int(text)
                temp_data['gift_count'] = count
                db.update_state(chat_id, step="gift_create_days", temp_data=temp_data)
                await message.reply("📅 تعداد روز اعتبار:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            except:
                await message.reply("❌ تعداد نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        if step == "gift_create_days":
            try:
                days = int(text)
                code = str(uuid.uuid4())[:8].upper()
                db.add_gift_code(code, temp_data['gift_amount'], temp_data['gift_count'], days)
                await message.reply(f"✅ کد هدیه ایجاد شد:\n🔑 `{code}`\n💰 مبلغ: {temp_data['gift_amount']:,} تومان\n🔢 تعداد: {temp_data['gift_count']}\n📅 اعتبار: {days} روز", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            except:
                await message.reply("❌ تعداد روز نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        if step == "gift_delete":
            db.delete_gift_code(text)
            await message.reply(f"✅ کد {text} حذف شد.", reply_markup=admin_menu())
            db.update_state(chat_id, step=None)
            return
        
        # ارسال همگانی
        if text == "📢 ارسال همگانی":
            db.update_state(chat_id, step="broadcast_msg")
            await message.reply("✏️ متن پیام همگانی را ارسال کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "broadcast_msg":
            users = db.get_all_users()
            count = 0
            for user in users:
                try:
                    await bot.send_message(user['user_id'], text)
                    count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
            await message.reply(f"✅ پیام به {count} کاربر ارسال شد.", reply_markup=admin_menu())
            db.update_state(chat_id, step=None)
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
            db.update_state(chat_id, step="admin_add_channel")
            await message.reply("📢 لطفاً آیدی کانال جدید را وارد کنید (مثال: @mychannel):", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "admin_add_channel":
            channel = text.strip()
            if not channel.startswith("@"):
                channel = "@" + channel
            db.add_pending_channel(channel, chat_id, "ادمین", "admin")
            await message.reply(f"✅ کانال {channel} برای تایید اضافه شد.", reply_markup=channels_menu())
            db.update_state(chat_id, step=None)
            return
        
        if text == "✅ تایید کانال":
            pending = db.get_pending_channels()
            if not pending:
                await message.reply("❌ هیچ کانالی در انتظار تایید نیست.", reply_markup=channels_menu())
                return
            for ch in pending:
                await message.reply(
                    f"{ch['id']}. کانال: {ch['channel']} - پیشنهاد دهنده: {ch.get('user_name', 'ادمین')}",
                    reply_markup=make_keyboard([[f"✅ تایید کانال|{ch['id']}"]])
                )
            db.update_state(chat_id, step="admin_approve_channel")
            return
        
        if step == "admin_approve_channel" and text.startswith("✅ تایید کانال|"):
            try:
                channel_id = int(text.split("|")[1])
                channel = db.approve_channel(channel_id)
                if channel:
                    CHANNELS_FOR_AD.append(channel['channel'])
                    
                    if channel['added_by'] != ADMIN_ID:
                        await bot.send_message(
                            channel['added_by'],
                            f"✅ **کانال شما تایید شد!**\n\n"
                            f"📺 کانال: {channel['channel']}\n"
                            f"🎉 کانال شما به لیست کانال‌های تبلیغاتی اضافه شد.\n"
                            f"اکنون تبلیغات در کانال شما نیز منتشر می‌شود."
                        )
                    
                    await message.reply(f"✅ کانال {channel['channel']} با موفقیت تایید شد.", reply_markup=channels_menu())
                else:
                    await message.reply("❌ کانال یافت نشد.", reply_markup=channels_menu())
            except:
                await message.reply("❌ خطا در تایید کانال.", reply_markup=channels_menu())
            db.update_state(chat_id, step=None)
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
            db.update_state(chat_id, step="admin_remove_channel")
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
            db.update_state(chat_id, step=None)
            return
        
        if text == "⏳ کانال‌های منتظر تایید":
            pending = db.get_pending_channels()
            if not pending:
                await message.reply("❌ هیچ کانالی در انتظار تایید نیست.", reply_markup=channels_menu())
            else:
                pending_text = "\n".join([f"• {ch['channel']} - پیشنهاد: {ch.get('user_name', 'ادمین')}" for ch in pending])
                await message.reply(f"⏳ **کانال‌های منتظر تایید:**\n\n{pending_text}", reply_markup=channels_menu())
            return
        
        if text == "✅ کانال‌های پیشنهادی":
            pending = db.get_pending_channels()
            if not pending:
                await message.reply("❌ هیچ کانال پیشنهادی وجود ندارد.", reply_markup=admin_menu())
            else:
                pending_text = "\n".join([f"• {ch['channel']} - پیشنهاد: {ch.get('user_name', 'ناشناس')} (@{ch.get('user_username', '')})" for ch in pending])
                await message.reply(f"✅ **کانال‌های پیشنهادی کاربران:**\n\n{pending_text}\n\nبرای تایید از بخش «✅ تایید کانال» استفاده کنید.", reply_markup=admin_menu())
            return
        
        # انتقال اعتبار
        if text == "➕ انتقال اعتبار":
            db.update_state(chat_id, step="admin_transfer_user")
            await message.reply("👤 آیدی عددی کاربر مقصد:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "admin_transfer_user":
            try:
                target_id = int(text)
                if not db.get_user(target_id):
                    await message.reply("❌ کاربر یافت نشد.", reply_markup=admin_menu())
                    db.update_state(chat_id, step=None)
                    return
                temp_data['admin_target'] = target_id
                db.update_state(chat_id, step="admin_transfer_amount", temp_data=temp_data)
                await message.reply("💰 مبلغ (تومان):", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            except:
                await message.reply("❌ آیدی نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        if step == "admin_transfer_amount":
            try:
                amount = int(text)
                target_id = temp_data['admin_target']
                target = db.get_user(target_id)
                db.update_user(target_id, wallet=target['wallet'] + amount)
                await message.reply(f"✅ {amount:,} تومان به کاربر {target_id} اضافه شد.", reply_markup=admin_menu())
                await bot.send_message(target_id, f"👑 ادمین {amount:,} تومان به کیف پول شما اضافه کرد.")
                db.update_state(chat_id, step=None)
            except:
                await message.reply("❌ مبلغ نامعتبر.", reply_markup=admin_menu())
                db.update_state(chat_id, step=None)
            return
        
        # درخواست‌های برداشت
        if text == "💸 درخواست‌های برداشت":
            await message.reply("💸 **مدیریت درخواست‌های برداشت**", reply_markup=withdraws_menu())
            return
        
        if text == "💸 مشاهده درخواست‌های برداشت":
            pending_req = db.get_withdraw_requests(status="pending")
            if not pending_req:
                await message.reply("هیچ درخواست در انتظاری وجود ندارد.", reply_markup=withdraws_menu())
                return
            for req in pending_req:
                await message.reply(
                    f"🆔 شناسه: {req['id']}\n"
                    f"👤 کاربر: {req['name']} (@{req['username']}) - `{req['user_id']}`\n"
                    f"💰 مبلغ: {req['amount']:,} تومان\n"
                    f"💳 کارت: `{req['card']}`",
                    reply_markup=make_keyboard([
                        [f"✅ تایید برداشت|{req['id']}"],
                        [f"❌ رد برداشت|{req['id']}"],
                        ["🔙 بازگشت به پنل"]
                    ])
                )
            return
        
        if text.startswith("✅ تایید برداشت|"):
            request_id = int(text.split("|")[1])
            reqs = db.get_withdraw_requests()
            for req in reqs:
                if req['id'] == request_id and req['status'] == "pending":
                    db.update_withdraw_status(request_id, "approved")
                    user = db.get_user(req['user_id'])
                    db.update_user(req['user_id'], earnings=user['earnings'] - req['amount'])
                    await bot.send_message(req['user_id'], f"✅ درخواست برداشت {req['amount']:,} تومان تایید شد.\nمبلغ به کارت {req['card']} واریز خواهد شد.")
                    await message.reply("✅ برداشت تایید شد.", reply_markup=withdraws_menu())
                    return
            await message.reply("❌ درخواست یافت نشد.", reply_markup=withdraws_menu())
            return
        
        if text.startswith("❌ رد برداشت|"):
            request_id = int(text.split("|")[1])
            reqs = db.get_withdraw_requests()
            for req in reqs:
                if req['id'] == request_id and req['status'] == "pending":
                    db.update_withdraw_status(request_id, "rejected")
                    await bot.send_message(req['user_id'], f"❌ درخواست برداشت {req['amount']:,} تومان رد شد.")
                    await message.reply("❌ برداشت رد شد.", reply_markup=withdraws_menu())
                    return
            await message.reply("❌ درخواست یافت نشد.", reply_markup=withdraws_menu())
            return
        
        # مدیریت تیکت‌ها
        if text == "🎫 مدیریت تیکت‌ها":
            await message.reply("🎫 **مدیریت تیکت‌ها**", reply_markup=tickets_menu())
            return
        
        if text == "🎫 مشاهده تیکت‌های باز":
            open_tickets = db.get_tickets(status="open")
            if not open_tickets:
                await message.reply("هیچ تیکت باز وجود ندارد.", reply_markup=tickets_menu())
                return
            for t in open_tickets:
                await message.reply(
                    f"🆔 شناسه: `{t['ticket_id']}`\n"
                    f"👤 کاربر: {t['user_name']} (@{t['user_username']}) - `{t['user_id']}`\n"
                    f"📝 متن: {t['text']}\n"
                    f"📅 تاریخ: {t['date']}",
                    reply_markup=make_keyboard([
                        [f"📝 پاسخ به تیکت|{t['ticket_id']}"],
                        ["🔙 بازگشت به پنل"]
                    ])
                )
            return
        
        if text.startswith("📝 پاسخ به تیکت|"):
            ticket_id = text.split("|")[1]
            temp_data['ticket_id'] = ticket_id
            db.update_state(chat_id, step="reply_ticket", temp_data=temp_data)
            await message.reply("✏️ پاسخ خود را وارد کنید:", reply_markup=make_keyboard([["🔙 بازگشت به پنل"]]))
            return
        
        if step == "reply_ticket":
            ticket_id = temp_data['ticket_id']
            tickets = db.get_tickets()
            for t in tickets:
                if t['ticket_id'] == ticket_id and t['status'] == "open":
                    db.reply_ticket(ticket_id, text)
                    await bot.send_message(t['user_id'], f"🎫 **پاسخ تیکت شما:**\n\n{text}\n\n✅ تیکت شما بسته شد.\n\nدر صورت نیاز می‌توانید تیکت جدید ثبت کنید.")
                    await message.reply("✅ پاسخ ارسال شد.", reply_markup=tickets_menu())
                    db.update_state(chat_id, step=None)
                    return
            await message.reply("❌ تیکت یافت نشد.", reply_markup=tickets_menu())
            db.update_state(chat_id, step=None)
            return
        
        # تبلیغات ویژه
        if text == "⭐ تبلیغات ویژه":
            premium_ads = db.get_ads(status="approved")
            premium_ads = [ad for ad in premium_ads if ad.get('is_premium', 0)]
            
            if not premium_ads:
                await message.reply("هیچ تبلیغ ویژه‌ای وجود ندارد.", reply_markup=admin_menu())
                return
            
            text_list = "⭐ **لیست تبلیغات ویژه**\n\n"
            for ad in premium_ads[:10]:
                text_list += f"🆔 {ad['ad_id']} - {ad['user_name']} - {ad['price']:,} تومان\n"
            
            await message.reply(text_list, reply_markup=admin_menu())
            return
        
        # خروج از پنل
        if text == "🚪 خروج از پنل":
            db.update_state(chat_id, admin_auth=False)
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

# ==============================================================
# توابع کمکی برای پردازش تبلیغات
# ==============================================================

async def process_ad_without_image(message, chat_id, user_data, temp_data):
    """پردازش تبلیغ بدون عکس"""
    price = temp_data['ad_price']
    tax = int(price * TAX_RATE)
    total = price + tax
    
    if user_data['wallet'] < total:
        await message.reply(
            f"❌ **موجودی کافی نیست!**\n\n"
            f"💰 هزینه تبلیغ: {price:,} تومان\n"
            f"💸 مالیات: {tax:,} تومان\n"
            f"💎 جمع قابل پرداخت: {total:,} تومان\n"
            f"💰 موجودی شما: {user_data['wallet']:,} تومان\n\n"
            f"❌ موجودی ناکافی: {total - user_data['wallet']:,} تومان کم دارید.\n\n"
            f"لطفاً ابتدا کیف پول خود را شارژ کنید.",
            reply_markup=main_menu(chat_id)
        )
        db.update_state(chat_id, step=None)
        return
    
    # کسر موجودی
    db.update_user(chat_id, wallet=user_data['wallet'] - total)
    
    ad_id = str(uuid.uuid4())[:8]
    ad_data = {
        'id': ad_id,
        'user_id': chat_id,
        'user_name': user_data['name'],
        'user_username': user_data['username'],
        'type': 'text',
        'text': temp_data['text'],
        'price': price,
        'tax': tax,
        'status': 'pending',
        'date': datetime.now(),
        'amount_deducted': total,
        'is_premium': temp_data.get('is_premium', 0)
    }
    db.add_ad(ad_data)
    
    premium_text = "⭐ ویژه" if temp_data.get('is_premium', 0) else "عادی"
    
    await bot.send_message(
        ADMIN_ID,
        f"📢 **سفارش تبلیغ جدید (متنی)**\n\n"
        f"👤 کاربر: {user_data['name']} (@{user_data['username']}) - `{chat_id}`\n"
        f"⭐ نوع: {premium_text}\n"
        f"💰 مبلغ: {price:,} تومان\n"
        f"💸 مالیات: {tax:,} تومان\n"
        f"📄 متن: {temp_data['text']}\n"
        f"🆔 شناسه سفارش: `{ad_id}`\n\n"
        f"برای تایید/رد از پنل ادمین اقدام کنید."
    )
    
    await message.reply(
        f"✅ **سفارش شما با موفقیت ثبت شد.**\n\n"
        f"🆔 **شناسه سفارش:** `{ad_id}`\n"
        f"⭐ **نوع تبلیغ:** {premium_text}\n"
        f"💰 **مبلغ کسر شده:** {total:,} تومان (مالیات {tax:,} تومان)\n"
        f"⏳ **وضعیت:** در انتظار تایید ادمین\n\n"
        f"پس از تایید، تبلیغ شما در کانال‌ها منتشر خواهد شد.\n"
        f"در صورت رد، مبلغ به کیف پول شما برگشت داده می‌شود.",
        reply_markup=main_menu(chat_id)
    )
    db.update_state(chat_id, step=None)

async def process_ad_with_image(message, chat_id, user_data, temp_data):
    """پردازش تبلیغ با عکس"""
    price = temp_data['ad_price']
    tax = int(price * TAX_RATE)
    total = price + tax
    
    if user_data['wallet'] < total:
        await message.reply(
            f"❌ **موجودی کافی نیست!**\n\n"
            f"💰 هزینه تبلیغ: {price:,} تومان\n"
            f"💸 مالیات: {tax:,} تومان\n"
            f"💎 جمع قابل پرداخت: {total:,} تومان\n"
            f"💰 موجودی شما: {user_data['wallet']:,} تومان\n\n"
            f"❌ موجودی ناکافی: {total - user_data['wallet']:,} تومان کم دارید.\n\n"
            f"لطفاً ابتدا کیف پول خود را شارژ کنید.",
            reply_markup=main_menu(chat_id)
        )
        db.update_state(chat_id, step=None)
        return
    
    # کسر موجودی
    db.update_user(chat_id, wallet=user_data['wallet'] - total)
    
    ad_id = str(uuid.uuid4())[:8]
    tracking_code = str(uuid.uuid4())[:8].upper()
    
    ad_data = {
        'id': ad_id,
        'user_id': chat_id,
        'user_name': user_data['name'],
        'user_username': user_data['username'],
        'type': 'image',
        'text': temp_data['text'],
        'image_id': temp_data['image_id'],
        'price': price,
        'tax': tax,
        'status': 'pending',
        'date': datetime.now(),
        'tracking_code': tracking_code,
        'amount_deducted': total,
        'is_premium': temp_data.get('is_premium', 0)
    }
    db.add_ad(ad_data)
    
    premium_text = "⭐ ویژه" if temp_data.get('is_premium', 0) else "عادی"
    
    await bot.send_message(
        ADMIN_ID,
        f"📢 **سفارش تبلیغ جدید (با عکس)**\n\n"
        f"👤 کاربر: {user_data['name']} (@{user_data['username']}) - `{chat_id}`\n"
        f"⭐ نوع: {premium_text}\n"
        f"💰 مبلغ: {price:,} تومان\n"
        f"💸 مالیات: {tax:,} تومان\n"
        f"🔑 کد پیگیری: `{tracking_code}`\n"
        f"📄 متن: {temp_data['text']}\n"
        f"🆔 شناسه سفارش: `{ad_id}`\n\n"
        f"برای تایید/رد از پنل ادمین اقدام کنید."
    )
    
    await message.reply(
        f"✅ **سفارش شما با موفقیت ثبت شد.**\n\n"
        f"🆔 **شناسه سفارش:** `{ad_id}`\n"
        f"⭐ **نوع تبلیغ:** {premium_text}\n"
        f"🔑 **کد پیگیری:** `{tracking_code}`\n"
        f"💰 **مبلغ کسر شده:** {total:,} تومان (مالیات {tax:,} تومان)\n"
        f"⏳ **وضعیت:** در انتظار تایید ادمین\n\n"
        f"پس از تایید، تبلیغ شما در کانال‌ها منتشر خواهد شد.\n"
        f"در صورت رد، مبلغ به کیف پول شما برگشت داده می‌شود.",
        reply_markup=main_menu(chat_id)
    )
    db.update_state(chat_id, step=None)

# ----------------------------------------------------------------------
# اجرای ربات
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("ربات با پایگاه داده SQLite راه‌اندازی شد!")
    bot.run()
