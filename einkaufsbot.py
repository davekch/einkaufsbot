#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

PATH = os.path.dirname(os.path.realpath(__file__))
TOKEN = open("token.txt").read().strip()

import logging
import json
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import BaseFilter
from telegram import ParseMode


class ScheissFilter(BaseFilter):
    """
    class to filter messages that contain bad words
    """

    def filter(self, message):
        scheisse = ["scheiss", "scheiß", "scheis", "shit", "fuck", "kack"]
        for shit in scheisse:
            if shit.upper() in message.text.upper():
                return True
        return False


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="hello me blubu")


def answer_shit(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="{}, das sagt man nicht!"\
        .format(update.effective_user["first_name"]))


# function to read the zettel of a given id
def read_zettel(id):
    filename = os.path.join(PATH, "zettel", str(id)+".json")
    # read filecontents if already exists
    if os.path.isfile(filename):
        with open(filename) as f:
            zettel = json.load(f)
    else:
        zettel = {"liste": []}
    return zettel


# function to save zettel of given id
def save_zettel(zettel, id):
    filename = os.path.join(PATH, "zettel", str(id)+".json")
    with open(filename, "w") as f:
        json.dump(zettel, f)


def add(bot, update, args):
    """
    add args to einkaufszettel
    """
    # get the einkaufszettel
    zettel = read_zettel(update.message.chat_id)

    # check if items are already in list and add them/write message
    # added something is false if everything in args is already on list
    added_smth = False
    for item in args:
        if item.upper() not in zettel["liste"]:
            zettel["liste"].append(item.upper())
            added_smth = True
        else:
            bot.send_message(chat_id=update.message.chat_id,
                text="{} steht schon auf der einkaufsliste.".format(item))

    # send message if zettel was altered
    if added_smth:
        bot.send_message(chat_id=update.message.chat_id,
            text="ok, hab's auf die liste geschrieben")

    save_zettel(zettel, update.message.chat_id)


def remove(bot, update, args):
    """
    remove args from einkaufszettel
    """
    zettel = read_zettel(update.message.chat_id)

    # remove args from zettel
    removed_smth = False
    for item in args:
        try:
            zettel["liste"].remove(item.upper())
            removed_smth = True
        except ValueError:
            bot.send_message(chat_id=update.message.chat_id,
                text="{} steht eh nicht auf dem zettel!".format(item))

    if removed_smth:
        bot.send_message(chat_id=update.message.chat_id,
            text="ok, hab's runter von der liste")

    save_zettel(zettel, update.message.chat_id)


def list(bot, update):
    """
    list all items in einkaufsliste
    """
    zettel = read_zettel(update.message.chat_id)

    if len(zettel["liste"])==0:
        bot.send_message(chat_id=update.message.chat_id,
            text="hab keine einkaufsliste grad.")
    else:
        message = "*Die Einkaufsliste*\n"
        for item in zettel["liste"]:
            message += item.lower()+'\n'
        bot.send_message(chat_id=update.message.chat_id, text=message,
            parse_mode=ParseMode.MARKDOWN)


def resetlist(bot, update):
    """
    removes all items from zettel["liste"]
    """
    zettel = read_zettel(update.message.chat_id)
    zettel["liste"] = []
    save_zettel(zettel, update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id,
        text="ok, hab die einkaufsliste gelöscht")


# setup logging info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)


# bot itself
updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

add_handler = CommandHandler('add', add, pass_args=True)
dispatcher.add_handler(add_handler)
remove_handler = CommandHandler('remove', remove, pass_args=True)
dispatcher.add_handler(remove_handler)
list_handler = CommandHandler('list', list)
dispatcher.add_handler(list_handler)
resetlist_handler = CommandHandler('resetlist', resetlist)
dispatcher.add_handler(resetlist_handler)

# scheisse handler
scheisse = ScheissFilter()
scheisse_handler = MessageHandler(scheisse, answer_shit)
dispatcher.add_handler(scheisse_handler)


if __name__=="__main__":
    updater.start_polling()
    updater.idle()
