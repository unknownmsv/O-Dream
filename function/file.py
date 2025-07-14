import os

def create_file(name, format):
    """
    ساخت فایل با نام و فرمت مشخص. اگر فایل وجود داشته باشد، اخطار می‌دهد.
    """
    filename = f"{name}.{format}"
    if os.path.exists(filename):
        print(f"⚠️ فایل '{filename}' از قبل وجود دارد.")
        return

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("")  # فایل خالی ایجاد می‌شود
        print(f"📄 فایل '{filename}' ساخته شد.")
    except Exception as e:
        print(f"❌ خطا در ساخت فایل: {e}")

def show_file(name, format):
    """
    نمایش محتوای فایل با نام و فرمت مشخص.
    """
    filename = f"{name}.{format}"
    if not os.path.exists(filename):
        print(f"❌ فایل '{filename}' پیدا نشد.")
        return

    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"📄 محتوای فایل '{filename}':\n{'-'*40}\n{content}\n{'-'*40}")
    except Exception as e:
        print(f"❌ خطا در خواندن فایل: {e}")

def edit_file(name, format):
    """
    جایگزینی محتوای فایل با ورودی جدید از کاربر.
    """
    filename = f"{name}.{format}"
    if not os.path.exists(filename):
        print(f"❌ فایل '{filename}' برای ویرایش وجود ندارد.")
        return

    new_content = input(f"📝 محتوای جدید برای '{filename}':\n")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ محتوای فایل '{filename}' بروزرسانی شد.")
    except Exception as e:
        print(f"❌ خطا در ویرایش فایل: {e}")