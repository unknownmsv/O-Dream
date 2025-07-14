import os

def create_doc(name):
    """
    یک پوشه جدید با نام داده‌شده ایجاد می‌کند.
    اگر پوشه از قبل وجود داشته باشد، پیامی نمایش داده می‌شود.
    """
    try:
        os.makedirs(name)
        print(f"📁 فولدر '{name}' ساخته شد.")
    except FileExistsError:
        print(f"⚠️ فولدر '{name}' از قبل وجود دارد.")
    except Exception as e:
        print(f"❌ خطا در ساخت فولدر: {e}")