from telegram import Update
from itertools import groupby
import urllib.request
import re
import math
from html import escape 
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from Grabber import collection, user_collection, application

rarities_map = {
    1: '⚪️ Common',
    2: '🟣 Rare',
    3: '🟡 Legendary',
    4: '🟢 Medium',
    5: '💮 Special edition'
}

async def hmode(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton(rarity, callback_data=f"hmode:{rarity}") for rarity in rarities_map.values()]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a rarity:", reply_markup=reply_markup)

async def hmode_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    _, rarity = data.split(':')

    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})
    
    if not user:
        await query.answer("You haven't guessed any characters yet.", show_alert=True)
        return

    rarity_code = [key for key, value in rarities_map.items() if value == rarity]
    if not rarity_code:
        await query.answer("Invalid rarity.", show_alert=True)
        return

    rarity_code = rarity_code[0]

    characters_of_rarity = [character for character in user['characters'] if character['rarity'] == rarity_code]

    if characters_of_rarity:
        harem_message = f"<b>{escape(update.effective_user.first_name)}'s {rarity} Characters</b>\n"
        character_counts = {k: len(list(v)) for k, v in groupby(characters_of_rarity, key=lambda x: x['id'])}

        for character in characters_of_rarity:
            count = character_counts[character['id']]
            harem_message += f'{character["id"]} {character["name"]} ×{count}\n'

        total_count = len(characters_of_rarity)
        await query.message.reply_text(harem_message, parse_mode='HTML')

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You Have Not Guessed any Characters Yet..')
        else:
            await update.callback_query.edit_message_text('You Have Not Guessed any Characters Yet..')
        return

    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

    
    unique_characters = list({character['id']: character for character in characters}.values())

    
    total_pages = math.ceil(len(unique_characters) / 15)  

    if page < 0 or page >= total_pages:
        page = 0  

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"

    
    current_characters = unique_characters[page*15:(page+1)*15]

    
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, characters in current_grouped_characters.items():
        harem_message += f'\n<b>{anime} {len(characters)}/{await collection.count_documents({"anime": anime})}</b>\n'

        for character in characters:
            
            count = character_counts[character['id']]  
            harem_message += f'{character["id"]} {character["name"]} ×{count}\n'


    total_count = len(user['characters'])
    
    keyboard = [[InlineKeyboardButton(f"See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]


    if total_pages > 1:
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'favorites' in user and user['favorites']:
        
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
            else:
                
                if update.callback_query.message.caption != harem_message:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                
                if update.callback_query.message.text != harem_message:
                    await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        
        if user['characters']:
        
            random_character = random.choice(user['characters'])

            if 'img_url' in random_character:
                if update.message:
                    await update.message.reply_photo(photo=random_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
                else:
                    
                    if update.callback_query.message.caption != harem_message:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                if update.message:
                    await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                
                    if update.callback_query.message.text != harem_message:
                        await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text("Your List is Empty :)")


async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data


    _, page, user_id = data.split(':')


    page = int(page)
    user_id = int(user_id)

    
    if query.from_user.id != user_id:
        await query.answer("its Not Your Harem", show_alert=True)
        return

    
    await harem(update, context, page)




application.add_handler(CommandHandler(["harem", "collection"], harem,block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
    
application.add_handler(CommandHandler("hmode", hmode, block=False))
hmode_handler = CallbackQueryHandler(hmode_callback, pattern='^hmode:', block=False)
application.add_handler(hmode_handler)
