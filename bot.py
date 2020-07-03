#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import json
from ombiserver import OmbiServer
import sys, traceback

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.utils.helpers import mention_html

sys.path.append('/usr/local/bin')

import logging
log = logging.getLogger(__name__)

#select one option below:

#1
#init custom log with colors
#
#from customlog import initlog
#initlog('ombibot')

#2
#use basicconfig
#
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig()

#load config
# users consist of pairs of <telegram-user-id> : <ombi-user-name>. Use telegram id-bot https://telegram.me/myidbot to find you own telegram user id.
with open('config.json') as json_data_file:
    data = json.load(json_data_file)
ombi_api                = data.get('apiKey')
botToken                = data.get('botToken')
server                  = data.get('server')
port                    = data.get('port')
baseUrl                 = data.get('baseUrl')

#servers
ombi                    = OmbiServer(server,ombi_api,port,baseUrl)
#usernames
userNames               = {}

# Stages
FIRST, TYPING, TYPING2, SELECT_MOVIE, MOVIE_DETAILS, REQUEST_COMPLETED = range(6)
# Callback data
ONE, TWO, THREE, FOUR, BACK, ACTOR, TITLE = range(7)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

#@bot.message_handler(commands=["start"])
def start(update, context):
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user

    log.info("User %s started the conversation.", user.first_name)
    log.info("Users: {}".format(userNames))

    if not user.id in userNames:
        #load config again
        with open('config.json') as json_data_file:
            data =  json.load(json_data_file)
            if 'users' in data: 
                users = data.get("users")
        if str(user.id) in users:
            name = users.get(str(user.id))
            userNames[user.id] = name
            log.info("Assigned user {} with id {} to username {}".format(user.first_name,user.id,name))
        else:
            userNames[user.id] = 'guest'
            log.info("Assigned user {} with id {} to guest".format(user.first_name,user.id))

    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    keyboard = [
        [InlineKeyboardButton("Movie", callback_data=str(ONE)),
         InlineKeyboardButton("Series", callback_data=str(TWO))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(
        text="What are you looking for?",
        reply_markup=reply_markup
    )
    # Tell ConversationHandler that we're in state `FIRST` now
    return FIRST

def start_over(update, context):
    log.info("Start over")
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    query = update.callback_query
    # Get Bot from CallbackContext
    bot = context.bot
    keyboard = [
        [InlineKeyboardButton("Movie", callback_data=str(ONE)),
         InlineKeyboardButton("Series", callback_data=str(TWO))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Instead of sending a new message, edit the message that
    # originated the CallbackQuery. This gives the feeling of an
    # interactive menu.
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="What are you looking for?",
        reply_markup=reply_markup
    )
    if "last_keyboard" in context.user_data:
        del context.user_data["last_keyboard"]

    return FIRST

def new_request(update, context):
    log.info("New request")
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    query = update.callback_query
    # Get Bot from CallbackContext
    bot = context.bot
    keyboard = [
        [InlineKeyboardButton("Movie", callback_data=str(ONE)),
         InlineKeyboardButton("Series", callback_data=str(TWO))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=query.message.chat_id,
        text="What are you looking for?",
        reply_markup=reply_markup
    )

    return FIRST

def help(update, context):
    """Send a message when the command /help is issued."""
    log.info("Help")
    update.message.reply_text('Help!')

def search_movie(update, context):
    """Send a message when the command /search_movies is issued."""
    log.info("Search movie called")
    log.info("Callback data = {}".format(update.callback_query.data if update.callback_query else "N/A"))
    last_keyboard = context.user_data.get('last_keyboard')
    if last_keyboard:
        log.debug("User data, last keyboard = {} rows".format(len(last_keyboard)))

    try:
        text = update.message.text if update.message else None
        title = text if text else context.args[0] if context.args else None
        log.debug("update: {}, context args = {}".format(update.message,context.args))

    except Exception as e:
        log.error("Error with search_movie: {}".format(e))
        return

    if not title:
        log.info("Search movie called without title")
        text = 'Enter movie title:'

        if 'last_keyboard' in context.user_data:
            keyboard = context.user_data.get('last_keyboard')
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
            return SELECT_MOVIE
        else:
            keyboard = [
                [InlineKeyboardButton("... or search by actor instead", callback_data=str(ACTOR))],
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
        return TYPING

    else:
        movies = ombi.search_movies(title)
        update.message.reply_text('Found {} results for term {}'.format(len(movies),title))

        keyboard = [
            [InlineKeyboardButton("Back", callback_data=str(BACK)), InlineKeyboardButton("By actor", callback_data=str(ACTOR))],
        ]

        log.debug("Movies found: {}".format(len(movies)))

        for title, data in movies.items():
            year = data.get('releaseDate').split('-')[0] if data.get('releaseDate') else 'N/A'
            text = '{} ({})'.format(title, year)

            if data.get('available'):
                text = text + b'\xE2\x9C\x85'.decode('utf-8')
            elif data.get('requested'):
                text = text + b'\xE2\x9E\xA1'.decode('utf-8')

            log.debug("Parsing {}, type = {}".format(data,type(data)))
            #log.info("Title: {} id = {}".format(title,data.get('id')))

            keyboard.append([InlineKeyboardButton( text, callback_data=data.get('id'))])
        context.user_data["last_keyboard"] =  keyboard

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "Choose one title (or go back):",
        reply_markup=reply_markup
    )
    return SELECT_MOVIE

def toggle_search_actor(update, context):
    log.info("Toggle search to actor")
    log.info("Callback data = {}".format(update.callback_query.data if update.callback_query else "N/A"))
    last_keyboard = context.user_data.get('last_keyboard')
    if last_keyboard:
        log.info("User data, last keyboard = {} rows".format(len(last_keyboard)))

    keyboard = [
            [InlineKeyboardButton("Back", callback_data=str(BACK)), InlineKeyboardButton("By title", callback_data=str(TITLE))],
            ]


    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text="Enter actor name (or go back):", reply_markup=reply_markup)

    return TYPING2

def toggle_search_title(update, context):
    log.info("Toggle search to title")
    log.info("Callback data = {}".format(update.callback_query.data if update.callback_query else "N/A"))
    last_keyboard = context.user_data.get('last_keyboard')
    if last_keyboard:
        log.info("User data, last keyboard = {} rows".format(len(last_keyboard)))

    keyboard = [
            [InlineKeyboardButton("Back", callback_data=str(BACK)), InlineKeyboardButton("By actor", callback_data=str(ACTOR))],
            ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text="Enter movie title (or go back):", reply_markup=reply_markup)

    return TYPING

def search_movie_actor(update, context):
    """Send a message when the command /search_movies is issued."""
    log.info("Search movie by actor called")
    log.info("Callback data = {}".format(update.callback_query.data if update.callback_query else "N/A"))
    last_keyboard = context.user_data.get('last_keyboard')
    if last_keyboard:
        log.info("User data, last keyboard = {} rows".format(len(last_keyboard)))

    try:
        text = update.message.text if update.message else None
        actor = text if text else context.args[0] if context.args else None
        log.debug("update: {}, context args = {}".format(update.message,context.args))

    except Exception as e:
        log.error("Error with search_movie: {}".format(e))
        return

    if not actor:
        text = 'Enter search term (actor):'
        update.callback_query.edit_message_text(text=text)
        return TYPING

    else:
        movies = ombi.search_movies_actor(actor)
        update.message.reply_text('Found {} results for {}'.format(len(movies),actor))

        keyboard = [
            [InlineKeyboardButton("Back", callback_data=str(BACK)), InlineKeyboardButton("By title", callback_data=str(TITLE))],
        ]

        log.debug("Movies found: {}".format(len(movies)))

        for title, data in movies.items():
            year = data.get('releaseDate').split('-')[0] if data.get('releaseDate') else 'N/A'
            text = '{} ({})'.format(title, year)

            if data.get('available'):
                text = text + b'\xE2\x9C\x85'.decode('utf-8')
            elif data.get('requested'):
                text = text + b'\xE2\x9E\xA1'.decode('utf-8')

            log.debug("Parsing {}, type = {}".format(data,type(data)))
            #log.info("Title: {} id = {}".format(title,data.get('id')))

            keyboard.append([InlineKeyboardButton( text, callback_data=data.get('id'))])
        context.user_data["last_keyboard"] =  keyboard
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "Choose one title (or go back):",
        reply_markup=reply_markup
    )
    return SELECT_MOVIE

def find_similar(update, context):
    """Send a message when the command /search_movies is issued."""
    log.info("Find similar called")
    log.info("Callback data = {}".format(update.callback_query.data if update.callback_query else "N/A"))
    last_keyboard = context.user_data.get('last_keyboard')
    if last_keyboard:
        log.info("User data, last keyboard = {} rows".format(len(last_keyboard)))

    try:
        data = update.callback_query.data
        movie_id = int(data.split('-')[1])
        log.info("data: {}, movie-id = {}".format(data,movie_id))

    except Exception as e:
        log.error("Error finding similars: {}".format(e))
        text = 'Error finding similar movies: {}. Try searching for it instead.'.format(e)
        update.callback_query.edit_message_text(text=text)
        return TYPING

    if not movie_id:
        log.error("No movie id")
        text = 'Error finding similar movies: {}. Try searching for it instead.'.format(e)
        update.callback_query.edit_message_text(text=text)
        return TYPING
    else:
        movies = ombi.find_similar(movie_id)
        log.info("Found {} similar movies to {}".format(len(movies), movie_id))

        text = 'Found {} similar movies. Choose one (or go back):'.format(len(movies))

        keyboard = [
            [InlineKeyboardButton("Back", callback_data=str(BACK))]
        ]

        log.info("Movies found: {}".format(len(movies)))

        for title, data in movies.items():
            year = data.get('releaseDate').split('-')[0] if data.get('releaseDate') else 'N/A'
            text = '{} ({})'.format(title, year)

            if data.get('available'):
                text = text + b'\xE2\x9C\x85'.decode('utf-8')
            elif data.get('requested'):
                text = text + b'\xE2\x9E\xA1'.decode('utf-8')

            log.debug("Parsing {}, type = {}".format(data,type(data)))
            keyboard.append([InlineKeyboardButton( text, callback_data=data.get('id'))])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.edit_message_text(text=text,reply_markup=reply_markup)
        return SELECT_MOVIE

def get_movie_info(update, context):
    """Send a message when the command /search_movies is issued."""
    log.info("Get movie info called")
    #log.info("Callback data = {}".format(update.callback_query.data if update.callback_query else "N/A"))
    last_keyboard = context.user_data.get('last_keyboard')
    if last_keyboard:
        log.info("User data, last keyboard = {} rows".format(len(last_keyboard)))

    try:
        movie_id = update.callback_query.data
    except Exception as e:
        log.error("Error with getting movie info, try with another title: {}".format(e))
        return TYPING

    movie_info = ombi.get_movie_info(movie_id)
    log.debug("Got: {}".format(len(movie_info)))

    log.debug("Movie info: {}".format(movie_info))
    text = "{}\t {} ({} votes)\r\n\r\n Released: {}\r\n\r\n {}".format(
            movie_info.get('title'),
            round(movie_info.get('voteAverage'),1),
            movie_info.get('voteCount'),
            movie_info.get('releaseDate').split('T')[0] if len(movie_info) > 0 else "N/A",
            movie_info.get('overView') if len(movie_info) > 0 else "Unable to retrieve movie info")

    keyboard = [
        [InlineKeyboardButton("Back", callback_data=str(BACK)),
         InlineKeyboardButton("Find similar ones", callback_data=str(TWO)+'-'+str(movie_id)),
         InlineKeyboardButton("Request this one", callback_data=str(movie_id))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with text and appended InlineKeyboard
    update.callback_query.edit_message_text(text=text,reply_markup=reply_markup)


    return MOVIE_DETAILS

def get_movie(update, context):
    """Send a message when the command /search_movies is issued."""
    log.info("Get movie called")
    #log.info("Update = {}, context = {}".format(update,context))
    last_keyboard = context.user_data.get('last_keyboard')
    if last_keyboard:
        log.info("User data, last keyboard = {} rows".format(len(last_keyboard)))

    try:
        movie_id = update.callback_query.data if update.callback_query else context.args[0] if context.args else None
        effective_user = update._effective_user if update._effective_user.id else None
        
        if not effective_user.id in userNames:
            #load config again
            with open('config.json') as json_data_file:
                data =  json.load(json_data_file)
                if 'users' in data: 
                    users = data.get("users")
            if str(effective_user.id) in users:
                name = users.get(str(effective_user.id))
                userNames[effective_user.id] = name
                log.info("Assigned effective user {} with id {} to username {}".format(effective_user.first_name,effective_user.id,name))
            else:
                userNames[effective_user.id] = 'guest'
                log.info("Assigned user {} with id {} to guest".format(effective_user.first_name,effective_user.id))
    except IndexError as e:
        log.error("Error requesting movie with ombi username because of index error: {}".format(e))
        return TYPING
    except Exception as e:
        log.error("Error requesting movie with ombi user account: {}".format(e))
        return TYPING

    log.info("Movie = {}, effective-user = {}".format(movie_id,effective_user.id))

    keyboard = [
        [   InlineKeyboardButton("Back", callback_data=str(BACK)),
            InlineKeyboardButton("Request another", callback_data=str(ONE)),
            InlineKeyboardButton("End", callback_data=str(TWO))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    #request movie
    try:
        result = ombi.request_movie(movie_id, user=userNames[effective_user.id])
    except Exception as e:
        log.error("Unable to request movie: {}".format(e))
        return REQUEST_COMPLETED

    # Send message with text and appended InlineKeyboard
    text = 'Result: {}'.format(result)

    update.callback_query.edit_message_text(text=text,reply_markup=reply_markup)


    return REQUEST_COMPLETED

# this is a general error handler function. If you need more information about specific type of update, add it to the
# payload in the respective if clause
def error(update, context):
    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    devs = [101632749]
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an 
    # callback or inline query, or a poll update. In case you want this, keep in mind that sending the message 
    # could fail
    if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
               "My developer(s) will be notified.\r\n\r\nUse /start to begin a new search."
        update.effective_message.reply_text(text)
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    # but only one where you have an empty payload by now: A poll (buuuh)
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    # and send it to the dev(s)
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it. If you don't use the logger module, use it.
    raise

def end(update, context):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over"""
    log.info("End")
    query = update.callback_query
    bot = context.bot
    try:
        chat_id = query.message.chat.id if query else update.message.chat.id
    except Exception as e:
        log.error("Error: {}, object = {}".format(e,update))
        return ConversationHandler.END

    text = "See you next time!\r\n\r\n(Type /start to begin another request)"

    bot.send_message(chat_id=chat_id, text=text)

    return ConversationHandler.END

def search_series(update, context):
    """Show new choice of buttons"""
    log.info("Search series")
    query = update.callback_query
    bot = context.bot
    keyboard = [
        [InlineKeyboardButton("Back", callback_data=str(BACK))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Series search has not yet been implemented",
        reply_markup=reply_markup
    )
    return FIRST

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(botToken, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST:              [CallbackQueryHandler(search_movie,                 pattern='^' + str(ONE) + '$'),
                                 CallbackQueryHandler(search_series,                pattern='^' + str(TWO) + '$'),
                                 CallbackQueryHandler(start_over,                   pattern='^' + str(BACK) + '$')],

            TYPING:             [MessageHandler(Filters.text,search_movie),
                                 CallbackQueryHandler(toggle_search_actor,          pattern='^' + str(ACTOR) + '$'),
                                 CallbackQueryHandler(start_over,                   pattern='^' + str(BACK) + '$')],

            TYPING2:            [MessageHandler(Filters.text,search_movie_actor),
                                 CallbackQueryHandler(toggle_search_title,          pattern='^' + str(TITLE) + '$'),
                                 CallbackQueryHandler(start_over,                   pattern='^' + str(BACK) + '$')],


            SELECT_MOVIE:       [CommandHandler("end", end),
                                 CallbackQueryHandler(start_over,                   pattern='^' + str(BACK) + '$'),
                                 CallbackQueryHandler(toggle_search_actor,          pattern='^' + str(ACTOR) + '$'),
                                 CallbackQueryHandler(toggle_search_title,          pattern='^' + str(TITLE) + '$'),
                                 CallbackQueryHandler(get_movie_info,               pattern='^.+\d+.+$'),
                                 MessageHandler(Filters.text,search_movie)],

            MOVIE_DETAILS:      [CallbackQueryHandler(search_movie,                 pattern='^' + str(BACK)+ '$'),
                                 CallbackQueryHandler(find_similar,                 pattern='^' + str(TWO) + '\-.+$'),
                                 CallbackQueryHandler(get_movie,                    pattern='^\d+$')],


            REQUEST_COMPLETED:  [CallbackQueryHandler(new_request,                  pattern='^' + str(ONE) + '$'),
                                 CallbackQueryHandler(end,                          pattern='^' + str(TWO) + '$'),
                                 CallbackQueryHandler(search_movie,                 pattern='^' + str(BACK) + '$')]
        },
        fallbacks=[CommandHandler('start', start)],
        per_message = False,
        allow_reentry = True,
        conversation_timeout = 86400
    )

    # on different commands - answer in Telegram
    #dp.add_handler(CommandHandler("start", start))
    #dp.add_handler(CommandHandler("help", help))
    #dp.add_handler(CommandHandler("end", end))
    #dp.add_handler(CommandHandler("quit", end))

    dp.add_handler(conv_handler)

    # on noncommand i.e message - echo the message on Telegram
    #dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
