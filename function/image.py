# image.py
import openai # کتابخانه رسمی OpenAI
import os # برای دسترسی به متغیرهای محیطی

# تابع create_img حالا کلید API را به عنوان آرگومان دریافت می‌کند
async def create_img(prompt: str, size: str = "1024x1024", openai_api_key: str = None) -> str:
    """
    تصویر ایجاد می‌کند با استفاده از DALL·E 3 بر اساس پرامپت.
    کلید API OpenAI باید به تابع ارسال شود.
    """
    if not openai_api_key:
        raise ValueError("کلید API OpenAI (openai_api_key) ارائه نشده است.")
    
    # مقداردهی کلید API OpenAI به صورت موقت برای این فراخوانی
    # این روش امن‌تر از تنظیم سراسری در ابتدای فایل است.
    openai.api_key = openai_api_key

    try:
        # فراخوانی API DALL·E 3
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard", # کیفیت تصویر (standard یا hd)
            n=1, # تعداد تصاویر (برای dall-e-3 همیشه 1 است)
        )
        return response.data[0].url # بازگرداندن URL تصویر ساخته شده
    except Exception as e:
        print(f"[❌] خطا در ساخت تصویر: {e}")
        # در صورت خطا، یک استثنا را مجدداً پرتاب می‌کند تا در main.py مدیریت شود
        raise Exception(f"خطا در تولید تصویر: {e}")

