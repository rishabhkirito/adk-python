import os
import logging
import requests
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google.genai import Client
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENMEMORY_API_URL = "http://localhost:8080"

# Initialize the Brain (Gemini)
client = Client(api_key=GOOGLE_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🧠 AI-POS Smart Link Online.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    print(f"📩 Received: {user_text}")
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # 1. SEARCH MEMORY (Get Top 5 matches to catch the resume even if it's #2 or #3)
        payload = {
            "query": user_text,
            "topK": 5, 
            "filter": {"sectors": ["episodic", "semantic", "procedural", "reflective"]} 
        }
        mem_response = requests.post(f"{OPENMEMORY_API_URL}/memory/query", json=payload)
        data = mem_response.json()
        matches = data.get("matches", [])
        
        if not matches:
            await context.bot.send_message(chat_id=chat_id, text="🤷‍♂️ My memory is blank on that topic.")
            return

        # 2. PREPARE CONTEXT (Combine all search results into one block)
        context_block = ""
        for m in matches:
            source = m.get('metadata', {}).get('source', 'Unknown')
            text = m.get('content', '')
            context_block += f"\n--- SOURCE: {os.path.basename(source)} ---\n{text}\n"

        # 3. THE BRAIN (Ask Gemini to answer using the context)
        prompt = f"""
        You are a helpful AI assistant with access to the user's personal documents.
        
        USER QUESTION: "{user_text}"
        
        CONTEXT FOUND IN MEMORY:
        {context_block[:10000]} # Limit context size
        
        INSTRUCTIONS:
        - Answer the user's question strictly based on the CONTEXT provided.
        - If the answer is in the context, give it directly.
        - Mention which document you found the answer in.
        - If the context is irrelevant, say "I found some documents (like [Source Names]), but they don't seem to contain the answer."
        """
        
        gemini_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        answer = gemini_response.text
        
        # 4. REPLY
        await context.bot.send_message(chat_id=chat_id, text=answer, parse_mode=None)

    except Exception as e:
        print(f"Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ Brain Connection Error.")

if __name__ == '__main__':
    print("🚀 Smart Telegram Bot Active.")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()