#/usr/bin/python
# -*- coding: utf-8 -*-

TOKEN = "647874132:AAFvPB0zgldLDIUrDgATh8oogvkyKjXiYS4"

import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import BaseFilter


class ScheissFilter(BaseFilter):
    """
    class to filter messages that contain bad words
    """

    def filter(self, message):
        scheisse = ["scheiss", "scheiß", "scheis", "shit"]
        for shit in scheisse:
            if shit.decode('utf8').upper() in message.text.upper():
                return True
        return False



def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="hello me blubu")

def answer_shit(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="{}, das sagt man nicht!"\
        .format(update.effective_user["first_name"]))

# setup logging info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)


# bot itself
updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# scheisse handler
scheisse = ScheissFilter()
scheisse_handler = MessageHandler(scheisse, answer_shit)
dispatcher.add_handler(scheisse_handler)


if __name__=="__main__":
    updater.start_polling()
    updater.idle()
