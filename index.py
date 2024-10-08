import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import random
import time
import asyncio

# Logging settings
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API settings
client = OpenAI(api_key='GPT_API_KEY')

# List of words for the game
words = [
    "tree", 
    "sun", 
    "book", 
    "car", 
    "phone", 
    "dog", 
    "cat", 
    "ocean", 
    "river", 
    "plane", 
    "keyboard", 
    "ball", 
    "bicycle", 
    "moon", 
    "mountain", 
    "cup", 
    "bird", 
    "train", 
    "star", 
    "fish", 
    "computer", 
    "door", 
    "window", 
    "chair", 
    "school", 
    "house", 
    "city", 
    "zebra", 
    "elephant", 
    "rocket", 
    "station", 
    "planet", 
    "park", 
    "coffee", 
    "theater", 
    "store", 
    "pencil", 
    "forest", 
    "plane", 
    "hat", 
    "trolleybus"
]

# Storing game state
game_state = {}

# Variables for rate-limiting
last_request_time = 0
request_interval = 1  # minimum interval between requests in seconds

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! Let’s play "Crocodile". Use /play to start the game.')

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    word = random.choice(words)
    game_state[chat_id] = {'word': word, 'guessed': False}
    ai_response_set = await test(update, context)
    await update.message.reply_text(ai_response_set)

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in game_state or game_state[chat_id]['guessed']:
        return

    word = game_state[chat_id]['word']

    # Using ChatGPT to analyze the message
    response_set = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are helping to play the game 'Crocodile'. Your task is to describe the word without using it."},
                {"role": "user", "content": f"In the game 'Crocodile', the leader (you) describes the word '{word}'. Describe it in a way that's very difficult to guess using just 2-4 words."}
            ]
        )
    return response_set.choices[0].message.content.strip()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in game_state or game_state[chat_id]['guessed']:
        return

    user_message = update.message.text
    word = game_state[chat_id]['word']

    ai_response_set = await test(update, context)

    # Rate-limiting
    global last_request_time
    current_time = time.time()
    if current_time - last_request_time < request_interval:
        await asyncio.sleep(request_interval - (current_time - last_request_time))
    last_request_time = time.time()

    try:
        print("   ", update.message.date, update.message.from_user.first_name, user_message)
        # Using ChatGPT to analyze the message
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are helping to play the game 'Crocodile'. Your task is to determine if the word is described correctly."},
                {"role": "user", "content": f"In the game 'Crocodile', the player describes the word '{word}'. They said: '{user_message}'. Is the word described correctly, or does the characteristic they described fit this word? Respond briefly with 'Yes' or 'No', but if they guessed the word, respond with 'Guessed'."}
            ]
        )

        ai_response = response.choices[0].message.content.strip()

        if "guessed" in ai_response.lower():
            game_state[chat_id]['guessed'] = True
            await update.message.reply_text(f"Congratulations! You correctly guessed the word '{word}'.")
        else:
            await update.message.reply_text(ai_response_set)
    except Exception as e:
        logger.error(f"Error processing OpenAI request: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred while processing your message. Please try again later.")

def main() -> None:
    application = Application.builder().token('TELEGRAM_TOKEN').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
