import importlib
import time
import random
import re
import asyncio
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from Grabber import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, Grabberu
from Grabber import application, LOGGER 
from Grabber.modules import ALL_MODULES


locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

rarities_order = {'⚪️': 1, '🟣': 2, '🟡': 3, '🟢': 4, '💮': 5}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Grabber.modules." + module_name)


last_user = {}
warned_users = {}
def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 100

        
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
            
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    
                    await update.message.reply_text(f"⚠️ Don't Spam {update.effective_user.first_name}...\nYour Messages Will be ignored for 10 Minutes...")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

    
        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

    
        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            
            message_counts[chat_id] = 0
            
async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    all_characters = list(await collection.find({}))
    
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    # Sort characters based on rarity
    sorted_characters = sorted(all_characters, key=lambda x: rarities_order.get(x['rarity'], 0))

    # You can adjust the ratio as per your preference
    common_ratio = 3
    rare_ratio = 1

    character = None
    for _ in range(common_ratio + rare_ratio):
        character = random.choice(sorted_characters)
        if character['id'] not in sent_characters[chat_id]:
            sent_characters[chat_id].append(character['id'])
            last_characters[chat_id] = character
            break

    if character:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=f"""A New {character['rarity']} Character Appeared...\n/guess Character Name and add in Your Harem""",
            parse_mode='Markdown'
        )
    
async def guess(update: Update, context: CallbackContext) -> None:
    # The rest of the 'guess' function remains unchanged
    pass
   
async def fav(update: Update, context: CallbackContext) -> None:
    # The rest of the 'fav' function remains unchanged
    pass
    

def main() -> None:
    """Run bot."""
    # The rest of the 'main' function remains unchanged
    pass
    
if __name__ == "__main__":
    Grabberu.start()
    LOGGER.info("Bot started")
    main()
