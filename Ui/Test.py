# main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
# --- 1. Import CORSMiddleware ---
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from typing import Dict, List, Any, Literal

# Import your image creation function
from function.image import create_img 

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found. Image generation might not work.")

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# --- Initialize FastAPI App ---
app = FastAPI(
    title="O₂Dream AI Gateway (Requests Version)",
    description="An API gateway to communicate with Gemini models for chat/code and DALL·E 3 for images.",
    version="0.1.0"
)

# --- 2. Add CORS Middleware ---
# This is the crucial part that fixes the "Method Not Allowed" error.
# It tells the browser that it's safe for your frontend to make requests to this API.
origins = [
    # Allows all origins. For development, this is fine.
    # For production, you should restrict this to your actual frontend domain.
    # e.g., "https://your-website.com"
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Model Names ---
CHAT_MODEL_NAME = 'gemini-1.5-flash-latest'
CODE_MODEL_NAME = 'gemini-2.5-pro' 

# --- In-memory Chat History Storage ---
chat_sessions: Dict[str, List[Dict[str, Any]]] = {}

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    session_id: str
    message: str

class CodeRequest(BaseModel):
    prompt: str
    verbosity: Literal["low", "medium", "high"] = "medium" 

class ChatResponse(BaseModel):
    session_id: str
    response: str
    history: List[Dict[str, Any]]

class CodeResponse(BaseModel):
    prompt: str
    code_output: str
    verbosity: str

# --- Helper Function to Call Gemini API ---
async def call_gemini_api(model_name: str, payload: Dict[str, Any]) -> str:
    url = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        json_response = response.json()
        if 'candidates' in json_response and len(json_response['candidates']) > 0 and \
           'content' in json_response['candidates'][0] and \
           'parts' in json_response['candidates'][0]['content'] and \
           len(json_response['candidates'][0]['content']['parts']) > 0 and \
           'text' in json_response['candidates'][0]['content']['parts'][0]:
            return json_response['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Unexpected response from Gemini: {json_response}")
            return "No text response received from the model."
    except requests.exceptions.RequestException as e:
        print(f"Error requesting Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"Error communicating with Gemini API: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Translation Functions ---
async def translate_prompt_if_needed(prompt: str) -> str:
    if not prompt.isascii():
        print(f"[🌐] Translating prompt: '{prompt}'")
        translation = await translate_with_gemini(prompt)
        print(f"[🌐] Translated prompt: '{translation}'")
        return translation
    return prompt

async def translate_with_gemini(prompt: str) -> str:
    translation_prompt = f"Translate the following text to English. Respond only with the translation, no extra explanations or greetings:\n{prompt}"
    payload = {"contents": [{"role": "user", "parts": [{"text": translation_prompt}]}], "generationConfig": {"responseMimeType": "text/plain"}}
    return await call_gemini_api(CHAT_MODEL_NAME, payload)

# --- Dynamic System Instruction for Code Model ---
def get_code_system_instruction(verbosity: str) -> str:
    base_instruction = "You are an intelligent language model specifically designed to generate clean, executable code..." # Truncated for brevity
    if verbosity == "high": return base_instruction + " Explain the code in full detail..."
    elif verbosity == "medium": return base_instruction + " Provide brief explanations..."
    elif verbosity == "low": return base_instruction + " Provide no extra explanations or comments..."
    else: return get_code_system_instruction("medium")

# --- System Instruction for Chat Model ---
chat_system_instruction_text = "You are an AI assistant designed for general chat and conversation..." # Truncated for brevity

# --- Chat Endpoint (/chat/gen) ---
@app.post("/chat/gen", response_model=ChatResponse)
async def generate_chat_response(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message

    if user_message.lower().startswith("img:"):
        original_image_prompt = user_message[len("img:"):].strip()
        if not OPENAI_API_KEY:
            return ChatResponse(session_id=session_id, response="❌ OpenAI API key is not configured.", history=chat_sessions.get(session_id, []))
        try:
            translated_image_prompt = await translate_prompt_if_needed(original_image_prompt)
            image_url = await create_img(translated_image_prompt, openai_api_key=OPENAI_API_KEY)
            return ChatResponse(session_id=session_id, response=f"🔗 Generated Image:\n{image_url}", history=chat_sessions.get(session_id, []))
        except Exception as e:
            return ChatResponse(session_id=session_id, response=f"❌ Error generating image: {e}", history=chat_sessions.get(session_id, []))

    elif user_message.lower().startswith("code:"):
        parts = user_message[len("code:"):].strip().split("verbosity:")
        code_prompt = parts[0].strip()
        verbosity_level = "medium"
        if len(parts) > 1:
            requested_verbosity = parts[1].strip().lower()
            if requested_verbosity in ["low", "medium", "high"]: verbosity_level = requested_verbosity
            else: return ChatResponse(session_id=session_id, response=f"⚠️ Invalid verbosity. Using 'medium'.", history=chat_sessions.get(session_id, []))
        try:
            code_response_obj = await generate_code_response(CodeRequest(prompt=code_prompt, verbosity=verbosity_level))
            formatted_code_output = f"**Code Response (verbosity: {code_response_obj.verbosity}):**\n```\n{code_response_obj.code_output}\n```"
            return ChatResponse(session_id=session_id, response=formatted_code_output, history=chat_sessions.get(session_id, []))
        except Exception as e:
            return ChatResponse(session_id=session_id, response=f"Sorry, an error occurred while generating code: {e}", history=chat_sessions.get(session_id, []))

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    current_history = chat_sessions[session_id]
    current_history.append({"role": "user", "parts": [{"text": user_message}]})
    payload = {"contents": current_history, "systemInstruction": {"parts": [{"text": chat_system_instruction_text}]}}
    try:
        gemini_response_text = await call_gemini_api(CHAT_MODEL_NAME, payload)
        current_history.append({"role": "model", "parts": [{"text": gemini_response_text}]})
        return ChatResponse(session_id=session_id, response=gemini_response_text, history=current_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {e}")

# --- Code Endpoint (/code/gen) ---
@app.post("/code/gen", response_model=CodeResponse)
async def generate_code_response(request: CodeRequest):
    user_prompt = request.prompt
    verbosity_level = request.verbosity
    dynamic_code_system_instruction = get_code_system_instruction(verbosity_level)
    payload = {"contents": [{"role": "user", "parts": [{"text": user_prompt}]}],"generationConfig": {"responseMimeType": "text/plain"},"systemInstruction": {"parts": [{"text": dynamic_code_system_instruction}]}}
    try:
        gemini_response_text = await call_gemini_api(CODE_MODEL_NAME, payload)
        return CodeResponse(prompt=user_prompt, code_output=gemini_response_text, verbosity=verbosity_level)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing code request: {e}")
