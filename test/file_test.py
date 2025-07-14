import os

BASE_DIR = "workspace"  # همه فایل‌ها اینجا ذخیره می‌شن

def safe_path(name, format):
    """
    تولید مسیر امن برای فایل.
    """
    os.makedirs(BASE_DIR, exist_ok=True)
    return os.path.join(BASE_DIR, f"{name}.{format}")

def create_file(name: str, format: str) -> bool:
    """
    ایجاد فایل در پوشه workspace. اگر وجود داشته باشه، کاری نمی‌کنه.
    """
    path = safe_path(name, format)
    if os.path.exists(path):
        print(f"⚠️ فایل '{path}' از قبل وجود دارد.")
        return False

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        print(f"📄 فایل '{path}' ساخته شد.")
        return True
    except Exception as e:
        print(f"❌ خطا در ساخت فایل: {e}")
        return False

def edit_file(name: str, format: str, content: str) -> bool:
    """
    جایگزینی محتوای فایل با مقدار داده شده.
    """
    path = safe_path(name, format)
    if not os.path.exists(path):
        print(f"❌ فایل '{path}' برای ویرایش وجود ندارد.")
        return False

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ محتوای فایل '{path}' ویرایش شد.")
        return True
    except Exception as e:
        print(f"❌ خطا در ویرایش فایل: {e}")
        return False

def show_file(name: str, format: str) -> str:
    """
    نمایش محتوای فایل. اگر فایل وجود نداشته باشد، پیام خطا بازمی‌گرداند.
    """
    path = safe_path(name, format)
    if not os.path.exists(path):
        return f"❌ فایل '{path}' پیدا نشد."

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"📂 محتویات فایل '{path}':\n{'-'*40}\n{content}\n{'-'*40}"
    except Exception as e:
        return f"❌ خطا در خواندن فایل: {e}"