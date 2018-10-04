#/usr/bin/python

TOKEN = "647874132:AAFvPB0zgldLDIUrDgATh8oogvkyKjXiYS4"

import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler


def start(bot, updater):
    bot.send_message(chat_id=updater.message.chat_id, text="hello me blubu")

# setup logging info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)


# bot itself
updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


if __name__=="__main__":
    updater.start_polling()
    updater.idle()
