#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread

PATH = os.path.dirname(os.path.realpath(__file__))
TOKEN = open(os.path.join(PATH, "token.txt")).read().strip()

import logging
import json
import random
import re
from string import Template
import greedy
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import BaseFilter
from telegram import ParseMode


# conversation states
YESNOPROMPT, CONVERSATION_ONGOING = range(2)


class ScheissFilter(BaseFilter):
    """
    class to filter messages that contain bad words
    """
    # get the forbidden words
    def __init__(self):
        super().__init__()
        badwords_file = os.path.join(PATH, "templates", "badwords.txt")
        with open(badwords_file) as f:
            self.scheisse = f.read().split()

    def filter(self, message):
        for shit in self.scheisse:
            if shit.upper() in message.text.upper():
                return True
        return False


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hallo, ich bin der Einkaufs-Heini. Schick mir den /help befehl um mehr zu lernen.")


def answer_shit(bot, update):
    answers = ["das sagt man nicht", "language",
        "so kannst du mit deinen Freunderln reden aber ned mit mir",
        "was kennst du für wörter", "freundlich bleiben"]
    bot.send_message(chat_id=update.message.chat_id, text="{}, {}!"\
        .format(update.message.from_user.first_name, random.choice(answers)))


# function to read the zettel of a given id
def read_zettel(id):
    filename = os.path.join(PATH, "zettel", str(id)+".json")
    # read filecontents if already exists
    if os.path.isfile(filename):
        with open(filename) as f:
            zettel = json.load(f)
    else:
        zettel = {"liste": [], "payments": {}}
    return zettel


# function to save zettel of given id
def save_zettel(zettel, id):
    filename = os.path.join(PATH, "zettel", str(id)+".json")
    with open(filename, "w") as f:
        json.dump(zettel, f, sort_keys=True, indent=4)


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
    if len(zettel["liste"])==0:
        bot.send_message(chat_id=update.message.chat_id,
            text="Die liste ist eh leer!")
        return ConversationHandler.END

    zettel["liste"] = []
    save_zettel(zettel, update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id,
        text="ok, hab die einkaufsliste gelöscht. willst du gleich angeben wieviel du gezahlt hast (falls du zufällig grad einkaufen warst)?")

    # return conversation status yesno
    return YESNOPROMPT


def yes_no(reply):
    """
    checks if reply is yes or no or nothing
    """
    yes = ["yes", "ja", "jo", "jep", "jes", "jawohl", "jup", "yip", "ya"]
    no = ["no", "nö", "nein", "ne"]

    # check if yes or no is conatained in reply
    for y in yes:
        if y in reply:
            return True
    for n in no:
        if n in reply:
            return False
    # if not understood
    return None


def ask_for_payment(bot, update):
    reply = update.message.text
    # first check if user wants to do this
    if yes_no(reply) is None:
        # nothing was understood
        update.message.reply_text("hab jetzt nicht verstanden ob das ein ja oder ein nein war...")
        return ConversationHandler.END
    elif yes_no(reply):
        update.message.reply_text("ok dann gib jetzt dein geld ein")
        return CONVERSATION_ONGOING
    else:
        update.message.reply_text("gut dann nicht :)\n"\
            "wenn du doch noch speichern willst, wie viel du gezahlt hast,"\
            " mach's einfach so:\n"\
            "/addpayment 12,34€ (mit oder ohne €)")
        return ConversationHandler.END


def add_payment(bot, update, args=None):
    """
    extract a number from the reply and save the data to zettel
    """
    if not args:
        # check if addpayment was called without arguments
        if "/addpayment" in update.message.text:
            bot.send_message(chat_id=update.message.chat_id,
                text="Bitte benutze den Befehl so: /addpayment 34,99€")
            return
        # meaning that this gets called during conversation
        reply = update.message.text
    else:
        # gets called by command
        reply = args[0]
    # match a floating point number
    matches = re.findall(r"[-+]?\d*[\.,]\d+|[-+]?\d+", reply)
    if len(matches)!=1:
        update.message.reply_text("hab ich nicht verstanden... nochmal versuchen pls!\n"\
            "Bitte benutze den Befehl so: /addpayment 34,99€")
        return ConversationHandler.END
    else:
        try:
            # first and only match for float
            payment = float(matches[0].replace(",", "."))
        except ValueError:
            update.message.reply_text("hab ich nicht verstanden... nochmal versuchen pls!\n"\
                "Bitte benutze den Befehl so: /addpayment 34,99€")
            return ConversationHandler.END

    # get current userinfo
    username = update.message.from_user.first_name
    userid = str(update.message.from_user.id)
    # get zettel
    zettel = read_zettel(update.message.chat_id)
    # check if there is already data and create it if not
    if userid not in zettel["payments"]:
        zettel["payments"][userid] = {"name": username, "paid": 0.0}
    zettel["payments"][userid]["paid"] += payment

    save_zettel(zettel, update.message.chat_id)
    update.message.reply_text("ok, hab {}€ für {} aufgeschrieben. Du bist jetzt"\
        " bei {}€.".format(payment, username, zettel["payments"][userid]["paid"]))
    return ConversationHandler.END


def payments(bot, update):
    """
    list all payments
    """
    zettel = read_zettel(update.message.chat_id)

    # if no information is given
    if not zettel["payments"]:
        bot.send_message(chat_id=update.message.chat_id,
            text="niemand hat irgendwas gezahlt.")
        return

    message = "*Die Ausgaben*\n"
    gesamt = 0.
    N = 0  # how many users
    for userid in zettel["payments"]:
        user = zettel["payments"][userid]
        message += "{}: {}€\n".format(user["name"], user["paid"])
        gesamt += user["paid"]
        N += 1

    # do the rest only in groups
    if update.message.chat.type=="group":
        # calculate cash flow
        cashflow = calculate_cashflow(zettel["payments"])
        # format message via template
        payments_templatefile = os.path.join(PATH, "templates", "payments.txt")
        with open(payments_templatefile) as f:
            template = Template(f.read())
        # create json to fill template
        data = {"gesamt":gesamt, "jeder": gesamt/float(N), "cashflow":"\n".join(cashflow) }
        message += template.substitute(data)


    bot.send_message(chat_id=update.message.chat_id, text=message,
        parse_mode=ParseMode.MARKDOWN)


def calculate_cashflow(payments):
    # create lists that are meaningful to functions from greedy
    N = len(payments)
    gezahlt = [0 for i in range(N)]
    user = {}
    i=0
    for userid in payments:
        gezahlt[i] = payments[userid]["paid"]
        user[i] = payments[userid]["name"]
        i+=1

    # calculate schulden-graph
    graph = greedy.calc_graph(N, gezahlt)
    return greedy.minCashFlow(graph, user)


def reset_payments(bot, update):
    zettel = read_zettel(update.message.chat_id)

    for userid in zettel["payments"]:
        zettel["payments"][userid]["paid"] = 0.0

    save_zettel(zettel, update.message.chat_id)

    bot.send_message(chat_id=update.message.chat_id, text="ok, habs zurückgesetzt.")


def cancel(bot, update):
    update.message.reply_text("ok dieses gespräch scheint vorbei zu sein.")
    return ConversationHandler.END


def help(bot, update):
    help_templatefile = os.path.join(PATH, "templates", "help.txt")
    with open(help_templatefile) as f:
        message = f.read()
    # message = "*Hallo ich bin der Einkauf-Heini!*\n"\
    #             "Das kann ich alles:\n\n"\
    #             "/add füge zeugs zur einkaufsliste hinzu. mehrere Sachen"\
    #             " mit leerzeichen trennen!\n"\
    #             "/remove lösche zeugs von der einkaufsliste, genauso wie bei add\n"\
    #             "/list lass dir die gesamte einkaufsliste anzeigen\n"\
    #             "/resetlist lösche die ganze einkaufsliste\n"\
    #             "/addpayment speichere wieviel du für einen Einkauf gezahlt hast\n"\
    #             "/payments sieh nach wieviel wer für Einkäufe gezahlt hat\n"\
    #             "/resetpayments setze alle Beträge auf 0€"
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
    addpayment_handler = CommandHandler('addpayment', add_payment, pass_args=True)
    dispatcher.add_handler(addpayment_handler)
    payments_handler = CommandHandler('payments', payments)
    dispatcher.add_handler(payments_handler)
    resetpayments_handler = CommandHandler('resetpayments', reset_payments)
    dispatcher.add_handler(resetpayments_handler)

    resetlist_handler = ConversationHandler(
        # command that triggers the conversation
        entry_points = [CommandHandler('resetlist', resetlist)],
        # states of the conversation
        states = {
            YESNOPROMPT: [MessageHandler(Filters.text, ask_for_payment)],
            CONVERSATION_ONGOING: [MessageHandler(Filters.text, add_payment)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(resetlist_handler)

    # restart the bot, but only allow me to do this
    restart_handler = CommandHandler('restart', restart,
        filters=Filters.user(username='@davekch'))
    dispatcher.add_handler(restart_handler)

    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    # scheisse handler
    scheisse = ScheissFilter()
    scheisse_handler = MessageHandler(Filters.text & scheisse, answer_shit)
    dispatcher.add_handler(scheisse_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__=="__main__":
    main()
