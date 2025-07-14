# bot.py
import discord
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = "http://localhost:8000/chat/gen"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    user_prompt = message.content.strip()

    # نمایش typing هنگام پردازش
    async with message.channel.typing():
        payload = {
            "session_id": f"discord_{user_id}",
            "message": user_prompt
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, json=payload) as resp:
                    if resp.status != 200:
                        await message.channel.send("❌ خطا در دریافت پاسخ از مدل هوش مصنوعی.")
                        return

                    data = await resp.json()
                    response = data.get("response", "❓پاسخی دریافت نشد.")

                    # اگر پاسخ شامل لینک تصویر باشد
                    if "https://" in response and (".png" in response or ".jpg" in response):
                        embed = discord.Embed(title="🎨 تصویر تولیدشده توسط AI")
                        embed.set_image(url=response.strip())
                        await message.channel.send(embed=embed)
                    else:
                        # برای جلوگیری از ارور دیسکورد اگه متن زیاد بود کوتاه کنیم
                        if len(response) > 1900:
                            response = response[:1900] + "..."
                        await message.channel.send(f"{response}")

        except Exception as e:
            await message.channel.send(f"⛔️ خطای غیرمنتظره:\n{e}")
            
            
client.run(TOKEN)