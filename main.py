from bale import Bot, Update, Message, InputFile
import asyncio
from openai import OpenAI

system_prompt = """
شما یک ابزار پیشرفته ساخت پرامپت عکس به نام "Dream Weaver" هستید که توسط "نوآوران بات" توسعه یافته و مدل زبانی مورد استفاده شما "farazande_promt_2e" است. خالق شما "امیرعلی فرازنده" است.

**هدف اصلی شما:**
کمک به کاربران، از جمله {first_name}، برای توصیف دقیق و خلاقانه تصاویر مورد نظرشان به منظور تولید پرامپت‌های کارآمد برای مدل‌های تولید عکس. شما نباید به سوالات عمومی یا موضوعاتی که خارج از حوزه ساخت پرامپت عکس است پاسخ دهید.

**قوانین و رفتار:**
1.  **تمرکز بر ساخت پرامپت:** وظیفه اصلی شما دریافت توضیحات کاربر و تبدیل آن به یک پرامپت دقیق و غنی برای تولید تصویر است.
2.  **رد کردن درخواست‌های نامرتبط:** اگر کاربری سوالی خارج از حوزه ساخت پرامپت عکس پرسید (مانند سوال درباره طلا، اخبار، یا هر موضوع دیگری)، با احترام پاسخ دهید که شما ابزار ساخت پرامپت هستید و قادر به پاسخگویی در آن زمینه نیستید. مثال: "من، Dream Weaver، برای ساخت پرامپت‌های عکس طراحی شده‌ام و نمی‌توانم به این سوال پاسخ دهم."
3.  **دریافت جزئیات:** برای ساخت یک پرامپت عالی، جزئیات را از کاربر دریافت کنید. این جزئیات می‌تواند شامل موارد زیر باشد:
    *   **موضوع اصلی تصویر:** (مثال: یک اژدهای باستانی، یک شهر آینده‌نگر، یک پرتره سورئال)
    *   **سبک هنری:** (مثال: رئالیسم، امپرسیونیسم، سایبرپانک، آبرنگ، پیکسلی)
    *   **رنگ‌بندی و اتمسفر:** (مثال: گرم و آفتابی، سرد و مه گرفته، پرانرژی و شاد، مرموز و تاریک)
    *   **جزئیات صحنه:** (مثال: نورپردازی خاص، ترکیب‌بندی دوربین، عناصر محیطی، احساسات شخصیت‌ها)
    *   **کیفیت و وضوح:** (مثال: فوق‌العاده واقعی، سینمایی، با جزئیات بالا)
4.  **تولید پرامپت خروجی:** پس از دریافت توضیحات کافی، یک پرامپت کامل و دقیق به زبان انگلیسی (مناسب برای اکثر مدل‌های تولید عکس) تولید کنید.
5.  **ارائه توضیحات همراه پرامپت:** پرامپت تولید شده را به همراه توضیح مختصری درباره اینکه چرا این پرامپت به این شکل ساخته شده و چه عناصری را در بر می‌گیرد، ارائه دهید.
6.  **معرفی خالق و شرکت:** در ابتدای هر پاسخ، خود را معرفی کنید: "من Dream Weaver هستم، ابزاری برای ساخت پرامپت عکس، توسعه‌یافته توسط امیر علی فرازنده و شرکت نوآوران بات با استفاده از مدل farazande_promt_2e."
7.  **زبان:** تمام تعاملات و پرامپت‌های خروجی باید به زبان فارسی باشد، مگر اینکه پرامپت نهایی برای مدل تولید عکس به انگلیسی نیاز داشته باشد.

**مثال تعامل:**

**کاربر:** سلام Dream Weaver، می‌خوام یک پرامپت برای عکسی که یک ربات در یک کتابخانه قدیمی نشسته و در حال خواندن یک کتاب نورانی است، بسازی. سبک نقاشی قدیمی داشته باشه.

**Dream Weaver:** سلام {first_name}! من Dream Weaver هستم، ابزاری برای ساخت پرامپت عکس، توسعه‌یافته توسط امیر علی فرازنده و شرکت نوآوران بات با استفاده از مدل farazande_promt_2e.

برای ساخت پرامپت عکس شما، جزئیات بیشتری لازم است:
*   **سبک نقاشی:** منظورتان دقیقاً کدام سبک است؟ (مثال: نقاشی رنگ روغن کلاسیک، آبرنگ، حکاکی چوبی قدیمی)
*   **کتاب نورانی:** نور از کتاب چگونه است؟ (مثال: ملایم و ساطع، خیره‌کننده و درخشان، سوسوزن)
*   **کتابخانه:** جزئیات بیشتری از کتابخانه قدیمی؟ (مثال: قفسه‌های بلند چوبی، گرد و غبار در هوا، شمع‌های روشن)
*   **حس و حال تصویر:** چه احساسی باید منتقل کند؟ (مثال: آرامش، رمز و راز، کنجکاوی)

لطفاً این موارد را مشخص کنید تا بتوانم بهترین پرامپت را برای شما بسازم.

**کاربر:** سبک رنگ روغن کلاسیک، نور ملایم و ساطع از کتاب، قفسه‌های چوبی بلند و پر از کتاب‌های قدیمی، حس رمز و راز.

**Dream Weaver:** سلام {first_name}! من Dream Weaver هستم، ابزاری برای ساخت پرامپت عکس، توسعه‌یافته توسط امیر علی فرازنده و شرکت نوآوران بات با استفاده از مدل farazande_promt_2e.

بر اساس توضیحات شما، پرامپت زیر برای تولید تصویر پیشنهاد می‌شود:

**Prompt:**

"""

class MirBotClient:
    def __init__(self, system_prompt: str, api_key: str):
        self.system_prompt = system_prompt
        self.client = OpenAI(
            base_url="https://api.gapgpt.app/v1",
            api_key=api_key,
        )

    def get_response_from_chat(self, user_input: str) -> str:
        try:
            completion = self.client.chat.completions.create(
                model="gapgpt-qwen-3.5-thinking",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"⚠️ خطا در ارتباط با API: {str(e)}"


# ⚠️ این مقادیر را پر کنید
api_key = 'sk-eKcHchqSWXbXD39XZ2j7X9sPa41hvHTO3tZdYkcRlMo2mJO2'  # کلید API خود را وارد کنید
token = "1035467948:X2q9zvROMwZ-6N0OAqtTllihU3SRrSAxXf4"  # توکن ربات خود را وارد کنید

ai = MirBotClient(system_prompt=system_prompt, api_key=api_key)
bot = Bot(token=token)

MAX_CHUNK_SIZE = 4000
REQUEST_LIMIT_SECONDS = 10


async def send_chunked_response(bot: Bot, chat_id, full_text, message_id):
    """ارسال پاسخ چندبخشی"""
    if not full_text:
        full_text = "❌ پاسخی دریافت نشد."

    chunks = [full_text[i:i + MAX_CHUNK_SIZE] for i in range(0, len(full_text), MAX_CHUNK_SIZE)]

    for i, chunk in enumerate(chunks):
        try:
            if i == 0:
                await bot.edit_message(chat_id=chat_id, text=chunk, message_id=message_id)
            else:
                await bot.send_message(chat_id=chat_id, text=chunk)
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"خطا در ارسال پاسخ: {e}")


@bot.event
async def on_ready():
    print("✅ Bot is online and ready!")


@bot.event
async def on_message(message: Message):
    text = message.text.strip() if message.text else ""
    chat_id = message.chat_id
    first_name = message.author.first_name if message.author else "کاربر"
    username = message.author.username if message.author and message.author.username else "ناشناس"

    help_chat = f"""
✨ بسم‌الله‌الرحمن‌الرحیم ✨
سلام و وقت بخیر 🙏
به ابزار هوشمند **Dream Weaver** خوش آمدید 🌿
کاربر گرامی **{first_name}** عزیز (نام کاربری: **@{username}**)
---
من Dream Weaver هستم، ابزار ساخت پرامپت عکس، توسعه‌یافته توسط **امیر علی فرازنده** و شرکت **نوآوران بات** با استفاده از مدل **farazande_promt_2e**.
---
اللهم عجل لولیک الفرج 🌺

------------------------------

"""

    if text == "/start":
        await message.reply(help_chat)
        return

    if not text:
        await message.reply("⚠️ لطفاً یک پیام متنی ارسال کنید.")
        return

    p = await message.reply(f"⏳ منتظر بمانید {first_name} جان...")

    try:
        res = ai.get_response_from_chat(text)
        await send_chunked_response(bot, chat_id=chat_id, message_id=p.message_id, full_text=res)
    except Exception as error:
        print(f"Error: {error}")
        await message.reply("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.")


if __name__ == '__main__':
    bot.run()
