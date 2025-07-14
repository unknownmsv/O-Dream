# 🌌 O₂Dream AI Gateway

**O₂Dream** is a lightweight, multi-model AI gateway powered by Google's Gemini models and OpenAI's DALL·E 3.  
It provides a smart, fast, and secure API for:

- 🤖 Chat
- 💻 Code generation (with verbosity control)
- 🎨 Image generation (via DALL·E 3)
- 🌐 Automatic prompt translation (Persian → English)

---

## ✨ Features

- ✅ **Chat with memory** via `gemini-1.5-flash-latest`
- 💡 **Code generation** via `gemini-1.5-pro-latest`, with `low`, `medium`, and `high` verbosity levels
- 🖼️ **Image generation** via OpenAI's `DALL·E 3`
- 🌐 **Auto translation**: Persian prompts are automatically translated into English before sending
- 🔐 **.env configuration** for secure API key management
- ⚡ Built with `FastAPI` (blazing fast and easy to extend)

---

## 📦 Requirements

- Python 3.10+
- Google Gemini API Key
- OpenAI API Key (for image generation)
- `uvicorn` for local server

---

## 🔧 Installation

```bash
git clone https://github.com/unknownmsv/O2Dream.git
cd O2Dream
pip install -r requirements.txt
```

---

Create a .env file with the following content:

GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here


---

🚀 Run the Server

uvicorn main:app --reload --host 0.0.0.0 --port 8000

> Visit http://localhost:8000/docs to explore the API with Swagger UI.




---

🧠 Chat Endpoint

POST /chat/gen

Body:
```
{
  "session_id": "your-session-id",
  "message": "Hello, how are you?"
}
```
You can also use:

img: [description] → to generate images

code: [prompt] verbosity: [low|medium|high] → to generate code



---

💻 Code Generation Endpoint

POST /code/gen

Body:

```
{
  "prompt": "Create a Python script that sorts a list using bubble sort.",
  "verbosity": "medium"
}
```

---

🎨 Image Generation

Just send a message to the /chat/gen endpoint with the format:

img: یک درخت در زیر باران در شب

The Persian text will be automatically translated and sent to DALL·E 3.


---

📁 Project Structure

O2Dream/
├── main.py                 # Main FastAPI application
├── .env                    # Environment config (not committed)
├── requirements.txt        # Python dependencies
├── function/
│   └── image.py            # DALL·E image generation logic


---

⚖️ License

This project is released under the MIT License.
However, commercial use of advanced (Premium) versions is subject to additional terms.


---

🔮 Coming Soon

🔐 Authentication & API rate limits

📊 Usage dashboard

🧠 Local model fallbacks (LLaMA, Mistral, etc.)

🎯 Telegram & Discord Bot Integration

💎 Premium early-access builds (via unknownmsv.ir)

💎 buy Premium in https://donutmsv.ir

---

🚀 Creator

Unknownmsv (aka Sina)
🚀 Website: https://unknownmsv.ir


---

> Build smart. Dream big. Welcome to O₂Dream.
