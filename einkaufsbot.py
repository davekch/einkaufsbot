#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread

PATH = os.path.dirname(os.path.realpath(__file__))
TOKEN = open("token.txt").read().strip()

import logging
import json
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
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
    bot.send_message(chat_id=update.message.chat_id, text="Hallo, ich bin der Einkaufs-Heini. Schick mir den /help befehl um mehr zu lernen.")


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

    # if no arguments were given
    if len(args)==0:
        bot.send_message(chat_id=update.message.chat_id, text="was soll auf die einkaufsliste drauf? Mach's so: \n/add tomaten mozarella ...")
        return

    # get the einkaufszettel
    zettel = read_zettel(update.message.chat_id)

    # check if items are already in list and add them/write message
    message = ""
    for item in args:
        if item.upper() not in zettel["liste"]:
            zettel["liste"].append(item.upper())
        else:
            if message=="":
                message += "{} steht schon auf der einkaufsliste.\n".format(item)
            else:
                message += "{} auch.\n".format(item)

    # send message if zettel was altered
    if message=="":
        message = "ok, hab's auf die liste geschrieben"
    else:
        message += "hab den rest aufgeschrieben!"

    bot.send_message(chat_id=update.message.chat_id, text=message)
    save_zettel(zettel, update.message.chat_id)


def remove(bot, update, args):
    """
    remove args from einkaufszettel
    """

    # if no arguments were given
    if len(args)==0:
        bot.send_message(chat_id=update.message.chat_id, text="was soll von der einkaufsliste runter? Mach's so: \n/remove tomaten mozarella ...")
        return

    zettel = read_zettel(update.message.chat_id)

    # remove args from zettel
    message = ""
    for item in args:
        try:
            zettel["liste"].remove(item.upper())
        except ValueError:
            if message=="":
                message += "{} steht eh nicht auf dem zettel!\n".format(item)
            else:
                message += "{} auch nicht.\n".format(item)

    if message=="":
        message = "ok, hab's runter von der liste"
    else:
        message += "hab den rest runter von der liste."

    bot.send_message(chat_id=update.message.chat_id, text=message)
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


def help(bot, update):
    message = "*Hallo ich bin der Einkauf-Heini!*\n"\
                "Das kann ich alles:\n\n"\
                "/add füge zeugs zur einkaufsliste hinzu. mehrere Sachen"\
                " mit leerzeichen trennen!\n"\
                "/remove lösche zeugs von der einkaufsliste, genauso wie bei add\n"\
                "/list lass dir die gesamte einkaufsliste anzeigen\n"\
                "/resetlist lösche die ganze einkaufsliste\n"
    bot.send_message(chat_id=update.message.chat_id, text=message,
        parse_mode=ParseMode.MARKDOWN)


# to be fired on unknown commands
def unknown(bot, update):
    message = "Den befehl kenn ich nicht! 😱\nnimm den /help befehl um mehr zu erfahren"
    bot.send_message(chat_id=update.message.chat_id, text=message)


def main():

    # setup logging info
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
    logger = logging.getLogger(__name__)
    # bot itself
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    def stop_and_restart():
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(bot, update):
        update.message.reply_text("Starte Bot neu ...")
        logger.info("Restart bot ...")
        Thread(target=stop_and_restart).start()

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

    # restart the bot, but only allow me to do this
    restart_handler = CommandHandler('restart', restart,
        filters=Filters.user(username='@davekch'))
    dispatcher.add_handler(restart_handler)

    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    # scheisse handler
    scheisse = ScheissFilter()
    scheisse_handler = MessageHandler(scheisse, answer_shit)
    dispatcher.add_handler(scheisse_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__=="__main__":
    main()
