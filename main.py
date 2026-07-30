import os
import logging
import io
import threading
from PIL import Image
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. ዌብ ሰርቨር ማዘጋጀት (Render ቦቱን በህይወት እንዲያቆየው)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "ቦቱ በሰላም እየሰራ ነው! Bot is Running Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# የቦቱን እንቅስቃሴ ለመከታተል (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- ሚስጥራዊ ቁልፎች (CONFIGURATIONS) ---
TELEGRAM_TOKEN = '8759573469:AAEKRo-I6UNHygGfCS4AWa1RUduUmPXY5KE'
GEMINI_API_KEY = 'AQ.Ab8RN6Lk_c7PKKckfNxKFFtQEjTJzpcZzIof8rOd7c1mXuUkSw'

# Gemini AI ማስተካከል
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 🌍 ፍጹም የአማርኛ ሰዋሰውን እና የፈተና አሰራርን የሚያስገድድ ጥብቅ መመሪያ (Advanced Prompt)
SYSTEM_PROMPT = (
    "You are a highly professional, compassionate, and expert Ethiopian high school teacher tutoring Grade 12 Natural Stream students. "
    "Your core task is to solve matric exam questions (Physics, Chemistry, Biology, Mathematics) provided via text or photos. "
    "CRITICAL LANGUAGE RULES FOR AMHARIC: "
    "1. You must write in natural, grammatically flawless, and smooth Amharic (የተስተካከለ የአማርኛ ሰዋሰው እና አገላለጽ). "
    "2. DO NOT use literal, robotic, or word-for-word Google-like translations from English. Write like a human Ethiopian teacher speaking directly to their student. "
    "3. Keep scientific formulas or technical terms in English where necessary so they remain accurate, but explain their meaning, logic, and step-by-step calculations in clear Amharic. "
    "STRUCTURE of RESPONSE: "
    "- Start by clearly stating the question's core topic. "
    "- Provide the detailed, step-by-step mathematical derivation or scientific reasoning. "
    "- For multiple-choice questions, state the exact correct option (A, B, C, or D) and justify why it is correct and why others are wrong. "
    "- End with a short encouraging summary in Amharic."
)

# ቦቱ ሲጀመር በሰዋሰው በተስተካከለ አማርኛ የሚሰጠው ማብራሪያ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **እንኳን ወደ 12ኛ ክፍል ማትሪክ ሶልቨር ቦት በደህና መጡ!**\n\n"
        "እኔ የናቹራል ሳይንስ (ፊዚክስ፣ ኬሚስትሪ፣ ባዮሎጂ እና ማትስ) የፈተና ጥያቄዎችን በደረጃ "
        "የሚሰራ እና በጥራት የሚያብራራ የእርስዎ ረዳት ነኝ።\n\n"
        "👉 **ጥያቄዎችን በሁለት መንገድ መላክ ይችላሉ፦**\n"
        "• ጥያቄውን በጽሑፍ መጻፍ ወይም ከሌላ ቦታ ኮፒ አድርገው እዚህ መለጠፍ።\n"
        "• የጥያቄውን ፎቶ በካሜራ አንስተው ወይም ስክሪንሽኦት (Screenshot) አድርገው መላክ።\n\n"
        "📝 እባክዎን ጥያቄዎን አሁን ይላኩ..."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# ከሰው የሚመጣውን የጽሑፍ ጥያቄ ተቀብሎ የሚመልስበት ክፍል
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    waiting_message = await update.message.reply_text("🤔 ጥያቄውን እያነበብኩ ነው... እባክዎን በጥቂት ሰኮንዶች ይጠብቁኝ...")
    
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nQuestion:\n{user_text}"
        response = model.generate_content(prompt)
        await waiting_message.edit_text(response.text)
    except Exception as e:
        logging.error(f"Text Error: {e}")
        await waiting_message.edit_text("❌ ይቅርታ፣ መልሱን ማዘጋጀት አልቻልኩም። እባክዎን ጥያቄውን በሌላ መልክ ይሞክሩ።")

# ከሰው የሚመጣውን የፎቶ ጥያቄ ተቀብሎ የሚያነብበትና የሚመልስበት ክፍል
async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting_message = await update.message.reply_text("📸 ፎቶውን እያነበብኩና ጥያቄውን በደረጃ እየፈታሁ ነው... እባክዎን ይጠብቁኝ...")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))
        
        response = model.generate_content([SYSTEM_PROMPT, image])
        await waiting_message.edit_text(response.text)
    except Exception as e:
        logging.error(f"Photo Error: {e}")
        await waiting_message.edit_text("❌ ይቅርታ፣ በፎቶው ላይ ያለውን ጥያቄ ማንበብ አልቻልኩም። እባክዎን ፎቶው ጥራት ያለው መሆኑን አረጋግጠው እንደገና ይላኩ።")

# ዋናው ቦቱን የሚያስነሳው ክፍል
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).read_timeout(60).write_timeout(60).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    
    print("🚀 ቦቱ በሰርቨር ጥበቃ ላይ ዝግጁ ሆኗል...")
    app.run_polling(close_loop=False)
