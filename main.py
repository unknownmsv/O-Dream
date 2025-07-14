# main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from typing import Dict, List, Any, Literal # اضافه کردن Literal برای تعریف نوع verbosity

# وارد کردن تابع create_img از فایل image.py
# مطمئن شوید که فایل image.py در کنار main.py قرار دارد و مسیر 'function.image' صحیح باشد.
from function.image import create_img 

# --- 1. Load Environment Variables ---
# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# --- 2. Configuration ---
# دریافت کلید API Gemini از متغیرهای محیطی
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
# دریافت کلید API OpenAI از متغیرهای محیطی
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY در متغیرهای محیطی یافت نشد. لطفاً آن را در فایل .env تنظیم کنید.")
# هشدار در مورد کلید OpenAI اگر تنظیم نشده باشد
if not OPENAI_API_KEY:
    print("هشدار: OPENAI_API_KEY در متغیرهای محیطی یافت نشد. قابلیت تولید تصویر ممکن است کار نکند.")


# آدرس پایه API برای Gemini
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# --- 3. Initialize FastAPI App ---
app = FastAPI(
    title="O₂Dream AI Gateway (Requests Version)",
    description="یک دروازه API برای ارتباط با مدل‌های مختلف Gemini برای چت و تولید کد، و DALL·E 3 برای تولید تصویر.",
    version="0.1.0"
)

# --- 4. Model Names ---
CHAT_MODEL_NAME = 'gemini-1.5-flash-latest'
# نام مدل برای کدنویسی. 'gemini-1.5-pro-latest' نام عمومی و معتبر است.
# 'gemini-2.5-pro' در حال حاضر یک نام مدل عمومی در API Gemini نیست.
CODE_MODEL_NAME = 'gemini-1.5-pro-latest' 

# --- 5. In-memory Chat History Storage ---
# این دیکشنری برای نگهداری تاریخچه چت برای هر session_id استفاده می‌شود.
# تاریخچه به فرمت مورد نیاز Gemini API (لیستی از دیکشنری‌های role و parts) ذخیره می‌شود.
chat_sessions: Dict[str, List[Dict[str, Any]]] = {}

# --- Pydantic Models for Request Bodies ---
class ChatRequest(BaseModel):
    session_id: str # یک شناسه برای هر جلسه چت برای حفظ تاریخچه
    message: str    # پیام کاربر

class CodeRequest(BaseModel):
    prompt: str     # درخواست کدنویسی از کاربر
    # اضافه کردن فیلد verbosity با مقادیر مجاز 'low', 'medium', 'high'
    verbosity: Literal["low", "medium", "high"] = "medium" 

class ChatResponse(BaseModel):
    session_id: str
    response: str
    history: List[Dict[str, Any]] # تاریخچه چت برای دیباگینگ یا نمایش در فرانت‌اند

class CodeResponse(BaseModel):
    prompt: str
    code_output: str
    verbosity: str # اضافه کردن verbosity به پاسخ کدنویسی

# --- Helper Function to Call Gemini API ---
async def call_gemini_api(model_name: str, payload: Dict[str, Any]) -> str:
    """
    یک درخواست POST به Gemini API ارسال می‌کند و پاسخ متنی را برمی‌گرداند.
    """
    url = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent?key={GEMINI_API_KEY}" # استفاده از GEMINI_API_KEY
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # اگر کد وضعیت HTTP خطا باشد، یک استثنا ایجاد می‌کند

        json_response = response.json()
        
        # بررسی ساختار پاسخ برای استخراج متن
        if 'candidates' in json_response and len(json_response['candidates']) > 0 and \
           'content' in json_response['candidates'][0] and \
           'parts' in json_response['candidates'][0]['content'] and \
           len(json_response['candidates'][0]['content']['parts']) > 0 and \
           'text' in json_response['candidates'][0]['content']['parts'][0]:
            return json_response['candidates'][0]['content']['parts'][0]['text']
        else:
            # اگر پاسخ متنی نباشد یا ساختار غیرمنتظره باشد
            print(f"پاسخ غیرمنتظره از Gemini API: {json_response}")
            return "پاسخ متنی از مدل دریافت نشد."

    except requests.exceptions.RequestException as e:
        print(f"خطا در درخواست به Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در ارتباط با Gemini API: {e}")
    except Exception as e:
        print(f"خطای غیرمنتظره: {e}")
        raise HTTPException(status_code=500, detail=f"خطای داخلی سرور: {e}")

# --- Translation Functions ---
async def translate_prompt_if_needed(prompt: str) -> str:
    """
    پرامپت را بررسی می‌کند و در صورت غیرانگلیسی بودن، آن را به انگلیسی ترجمه می‌کند.
    """
    # یک تست ساده برای اینکه ببینیم انگلیسیه یا نه (بررسی کاراکترهای ASCII)
    if not prompt.isascii():  
        print(f"[🌐] در حال ترجمه پرامپت: '{prompt}'")
        translation = await translate_with_gemini(prompt) 
        print(f"[🌐] پرامپت ترجمه شده: '{translation}'")
        return translation
    return prompt

async def translate_with_gemini(prompt: str) -> str:
    """
    پرامپت فارسی را با استفاده از Gemini Flash به انگلیسی ترجمه می‌کند.
    """
    translation_prompt = (
        f"Translate the following text to English. Respond only with the translation, no extra explanations or greetings:\n{prompt}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": translation_prompt}]}],
        "generationConfig": {"responseMimeType": "text/plain"},
    }
    # از مدل فلش برای ترجمه استفاده می‌شود
    return await call_gemini_api(CHAT_MODEL_NAME, payload) 

# --- Dynamic System Instruction for Code Model based on Verbosity ---
def get_code_system_instruction(verbosity: str) -> str:
    """
    بر اساس سطح verbosity، system instruction مناسب برای مدل کدنویسی را برمی‌گرداند.
    """
    base_instruction = (
        "شما یک مدل زبان هوشمند هستید که به طور خاص برای تولید کد تمیز و قابل اجرا طراحی شده‌اید. "
        "تنها مسئولیت شما تولید کد بر اساس ورودی کاربر است. "
        "پاسخ شما باید فقط شامل کد باشد و از توضیحات کلی یا مکالمه‌ای پرهیز شود. "
        "اگر کاربر درخواست غیر کدنویسی داشت، پاسخ دهید که فقط درخواست‌های مرتبط با تولید کد را می‌پذیرید. "
        "کد تولیدی شما باید با بهترین شیوه‌های برنامه‌نویسی مدرن (مانند تابع‌نویسی، متغیرهای معنادار) نوشته شده باشد. "
        "همیشه فرض کنید کاربر از شما انتظار دارد کدی واقعی، قابل اجرا و قابل استفاده در پروژه‌های عملیاتی دریافت کند."
    )

    if verbosity == "high":
        return (
            base_instruction + " کد را با جزئیات کامل توضیح دهید، هم در قالب متن قبل یا بعد از کد و هم با کامنت‌های فراوان در داخل کد. "
            "هدف شما این است که کاربر بتواند هر خط کد را به طور کامل درک کند."
        )
    elif verbosity == "medium":
        return (
            base_instruction + " توضیحات مختصری قبل یا بعد از کد ارائه دهید و از کامنت‌های کلیدی در داخل کد استفاده کنید. "
            "هدف شما ارائه کدی خوانا با توضیحات کافی برای درک منطق اصلی است."
        )
    elif verbosity == "low":
        return (
            base_instruction + " هیچ توضیحات اضافی قبل یا بعد از کد ارائه ندهید و هیچ کامنتی در داخل کد قرار ندهید. "
            "پاسخ شما باید صرفاً شامل کد خام باشد."
        )
    else: # Default to medium if an invalid verbosity is provided
        return get_code_system_instruction("medium")

# --- System Instruction for Chat Model ---
chat_system_instruction_text = (
    "شما یک دستیار هوش مصنوعی هستید که برای چت و مکالمات عمومی طراحی شده‌اید. "
    "وظیفه اصلی شما ارائه پاسخ‌های دوستانه، مفید و مرتبط با موضوعات عمومی است. "
    "اگر کاربر از شما درخواست کدنویسی کرد، لطفاً به او بگویید که شما مدلی نیستید که برای تولید کدهای تمیز و بهینه طراحی شده باشید "
    "و او را به بخش مربوط به کدنویسی (مثلاً با گفتن 'code: [درخواست کد شما] [verbosity: low/medium/high]') راهنمایی کنید. "
    "اگر کاربر از شما درخواست ساخت تصویر کرد، لطفاً به او بگویید که شما مدلی نیستید که مستقیماً تصاویر را بسازید "
    "و او را به بخش مربوط به تولید تصویر (مثلاً با گفتن 'img: [توضیحات تصویر شما]') راهنمایی کنید."
)

# --- 6. Chat Endpoint (/chat/gen) ---
@app.post("/chat/gen", response_model=ChatResponse)
async def generate_chat_response(request: ChatRequest):
    """
    دریافت پیام از کاربر و ارسال آن به مدل Gemini 1.5 Flash برای چت عادی.
    اگر پیام با 'code:' یا 'img:' شروع شود، درخواست را به مدل مربوطه ارسال می‌کند.
    """
    session_id = request.session_id
    user_message = request.message

    # --- بررسی درخواست تولید تصویر ---
    if user_message.lower().startswith("img:"):
        original_image_prompt = user_message[len("img:"):].strip()
        print(f"[🖼️] درخواست ساخت تصویر: '{original_image_prompt}' برای session_id: {session_id}")

        if not OPENAI_API_KEY:
            return ChatResponse(
                session_id=session_id,
                response="❌ متاسفم، کلید API برای تولید تصویر (OpenAI) تنظیم نشده است. لطفاً آن را در فایل .env اضافه کنید.",
                history=chat_sessions.get(session_id, [])
            )

        try:
            # ترجمه پرامپت در صورت نیاز قبل از ارسال به DALL-E
            translated_image_prompt = await translate_prompt_if_needed(original_image_prompt)
            
            # ارسال کلید API به تابع create_img
            image_url = await create_img(translated_image_prompt, openai_api_key=OPENAI_API_KEY) 
            return ChatResponse(
                session_id=session_id,
                response=f"🔗 تصویر ساخته شده:\n{image_url}",
                history=chat_sessions.get(session_id, [])
            )
        except Exception as e:
            return ChatResponse(
                session_id=session_id,
                response=f"❌ خطا در تولید تصویر: {e}",
                history=chat_sessions.get(session_id, [])
            )

    # --- بررسی درخواست کدنویسی ---
    elif user_message.lower().startswith("code:"): # از elif استفاده شده تا فقط یکی از شرط‌ها اجرا شود
        # استخراج پرامپت و verbosity از پیام کاربر
        parts = user_message[len("code:"):].strip().split("verbosity:")
        code_prompt = parts[0].strip()
        verbosity_level = "medium" # مقدار پیش‌فرض
        if len(parts) > 1:
            # اطمینان از اینکه verbosity یک مقدار معتبر است
            requested_verbosity = parts[1].strip().lower()
            if requested_verbosity in ["low", "medium", "high"]:
                verbosity_level = requested_verbosity
            else:
                # اگر مقدار نامعتبر بود، به کاربر اطلاع دهید و از پیش‌فرض استفاده کنید
                return ChatResponse(
                    session_id=session_id,
                    response=f"⚠️ سطح verbosity نامعتبر است ('{requested_verbosity}'). از 'medium' استفاده می‌شود. مقادیر مجاز: low, medium, high.",
                    history=chat_sessions.get(session_id, [])
                )

        print(f"[💻] درخواست کد از چت دریافت شد: '{code_prompt}' با verbosity: {verbosity_level} برای session_id: {session_id}")

        try:
            # فراخوانی generate_code_response با verbosity_level
            code_response_obj = await generate_code_response(CodeRequest(prompt=code_prompt, verbosity=verbosity_level))
            
            # فرمت کردن پاسخ بر اساس verbosity_level
            formatted_code_output = f"**پاسخ کدنویسی (verbosity: {code_response_obj.verbosity}):**\n```\n{code_response_obj.code_output}\n```"
            
            return ChatResponse(
                session_id=session_id,
                response=formatted_code_output,
                history=chat_sessions.get(session_id, [])
            )
        except HTTPException as e:
            return ChatResponse(
                session_id=session_id,
                response=f"متاسفم، در تولید کد مشکلی پیش آمد: {e.detail}",
                history=chat_sessions.get(session_id, [])
            )
        except Exception as e:
            return ChatResponse(
                session_id=session_id,
                response=f"متاسفم، خطای غیرمنتظره‌ای در پردازش درخواست کد شما رخ داد: {e}",
                history=chat_sessions.get(session_id, [])
            )

    # --- منطق چت عادی (اگر هیچ یک از دستورات خاص بالا نباشد) ---
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
        print(f"جلسه چت جدید برای session_id: {session_id} ایجاد شد.")

    current_history = chat_sessions[session_id]

    # اضافه کردن پیام کاربر به تاریخچه
    current_history.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "contents": current_history,
        "systemInstruction": {
            "parts": [{"text": chat_system_instruction_text}]
        }
    }

    try:
        gemini_response_text = await call_gemini_api(CHAT_MODEL_NAME, payload)
        
        current_history.append({"role": "model", "parts": [{"text": gemini_response_text}]})

        return ChatResponse(
            session_id=session_id,
            response=gemini_response_text,
            history=current_history
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"خطا در /chat/gen برای session_id {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در پردازش درخواست چت: {e}")

# --- 7. Code Endpoint (/code/gen) ---
@app.post("/code/gen", response_model=CodeResponse)
async def generate_code_response(request: CodeRequest):
    """
    دریافت درخواست کدنویسی از کاربر و ارسال آن به مدل Gemini 1.5 Pro.
    این مدل فقط کد تولید می‌کند و برای چت عادی نیست.
    """
    user_prompt = request.prompt
    verbosity_level = request.verbosity # دریافت سطح verbosity

    # دریافت system instruction بر اساس سطح verbosity
    dynamic_code_system_instruction = get_code_system_instruction(verbosity_level)

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ],
        "generationConfig": {
            "responseMimeType": "text/plain"
        },
        "systemInstruction": {
            "parts": [{"text": dynamic_code_system_instruction}] # استفاده از system instruction پویا
        }
    }

    try:
        gemini_response_text = await call_gemini_api(CODE_MODEL_NAME, payload)

        return CodeResponse(
            prompt=user_prompt,
            code_output=gemini_response_text,
            verbosity=verbosity_level # بازگرداندن سطح verbosity در پاسخ
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"خطا در /code/gen برای پرامپت '{user_prompt}': {e}")
        raise HTTPException(status_code=500, detail=f"خطا در پردازش درخواست کد: {e}")


# --- اجرای برنامه FastAPI ---
# برای اجرای این برنامه، در ترمینال خود (در پوشه حاوی main.py و .env) دستور زیر را اجرا کنید:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
# سپس می‌توانید از طریق آدرس http://localhost:8000/docs به مستندات API دسترسی پیدا کنید.
