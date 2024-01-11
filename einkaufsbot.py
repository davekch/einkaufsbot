#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread
import logging

# setup logging info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

PATH = os.path.dirname(os.path.realpath(__file__))

import json
import random
import re
import shlex
from string import Template
import greedy
from telegram.ext import Application, ApplicationBuilder
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext.filters import BaseFilter, MessageFilter
from telegram.constants import ParseMode


def get_token():
    return open(os.path.join(PATH, "token.txt")).read().strip()


# conversation states
YESNOPROMPT, CONVERSATION_ONGOING = range(2)


class MyCommandHandler(CommandHandler):
    """
    commandhandler which doesnt always split args at " "
    """

    def collect_additional_context(self, context, update, application, check_result):
        super().collect_additional_context(context, update, application, check_result)
        # merge args back together
        args = " ".join(context.args)

        # split shlex if possible
        try:
            args = shlex.split(args)
        except:
            args = args.split()
        # remove trailing commas
        args = [a.strip(',') for a in args]
        context.args = args


class ScheissFilter(MessageFilter):
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


class PoltFilter(MessageFilter):
    """
    class to filter messages for "servus heini"
    """
    def filter(self, message):
        if "heini" in message.text.lower():
            return True
        return False


class PizzaFilter(MessageFilter):
    def filter(self, message):
        triggers = [
            "pizza",
            "was willst du",
            "was möchtest du",
            "bestellen?",
        ]
        return any(t in message.text.lower() for t in triggers)


class PastaFilter(MessageFilter):
    def filter(self, message):
        triggers = ["pasta", "nudel", "aldente", "al dente"]
        return any(t in message.text.lower() for t in triggers)


async def start(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Hallo, ich bin der Einkaufs-Heini. Schick mir den /help befehl um mehr zu lernen.")


async def answer_shit(update, context):
    answers = ["das sagt man nicht", "language",
        "so kannst du mit deinen Freunderln reden aber ned mit mir",
        "was kennst du für wörter", "freundlich bleiben"]
    await context.bot.send_message(chat_id=update.message.chat_id, text="{}, {}!"\
        .format(update.message.from_user.first_name, random.choice(answers)))


async def answer_polt(update, context):
    erwin = ["urlaub", "anrufen", "haha", "oisodannokay", "servus", "machen"]
    voicefile = os.path.join(PATH, "polt", random.choice(erwin)+".ogg")
    await context.bot.send_voice(chat_id=update.message.chat_id, voice=open(voicefile, "rb"))


def send_voice(voicename):
    voicefile = os.path.join(PATH, "polt", voicename)
    async def _send_voice(update, context):
        await context.bot.send_voice(chat_id=update.message.chat_id, voice=open(voicefile, "rb"))
    return _send_voice


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


async def add(update, context):
    """
    add args to einkaufszettel
    """

    args = context.args
    # if no arguments were given
    if len(args)==0:
        context.bot.send_message(chat_id=update.message.chat_id, text="was soll auf die einkaufsliste drauf? Mach's so: \n/add tomaten mozarella ...")
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

    await context.bot.send_message(chat_id=update.message.chat_id, text=message)
    save_zettel(zettel, update.message.chat_id)


async def remove(update, context):
    """
    remove args from einkaufszettel
    """

    args = context.args
    # if no arguments were given
    if len(args)==0:
        context.bot.send_message(chat_id=update.message.chat_id, text="was soll von der einkaufsliste runter? Mach's so: \n/remove tomaten mozarella ...")
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

    await context.bot.send_message(chat_id=update.message.chat_id, text=message)
    save_zettel(zettel, update.message.chat_id)


async def list(update, context):
    """
    list all items in einkaufsliste
    """
    zettel = read_zettel(update.message.chat_id)

    if len(zettel["liste"])==0:
        await context.bot.send_message(chat_id=update.message.chat_id,
            text="hab keine einkaufsliste grad.")
    else:
        message = "*Die Einkaufsliste*\n"
        for item in zettel["liste"]:
            # replace markdown special characters
            item = item.replace("*", "\\*").replace("_", "\\_")
            message += item.lower()+'\n'
        await context.bot.send_message(chat_id=update.message.chat_id, text=message,
            parse_mode=ParseMode.MARKDOWN)


async def resetlist(update, context):
    """
    removes all items from zettel["liste"]
    """
    zettel = read_zettel(update.message.chat_id)
    if len(zettel["liste"])==0:
        await context.bot.send_message(chat_id=update.message.chat_id,
            text="Die liste ist eh leer!")
        return ConversationHandler.END

    zettel["liste"] = []
    save_zettel(zettel, update.message.chat_id)
    await context.bot.send_message(chat_id=update.message.chat_id,
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
        if y.upper() in reply.upper():
            return True
    for n in no:
        if n.upper() in reply.upper():
            return False
    # if not understood
    return None


async def ask_for_payment(update, context):
    reply = update.message.text
    # first check if user wants to do this
    if yes_no(reply) is None:
        # nothing was understood, try to extract payment info from answer
        return await add_payment(update, context)
    elif yes_no(reply):
        await update.message.reply_text("ok dann gib jetzt dein geld ein")
        return CONVERSATION_ONGOING
    else:
        await update.message.reply_text("gut dann nicht :)\n"\
            "wenn du doch noch speichern willst, wie viel du gezahlt hast,"\
            " mach's einfach so:\n"\
            "/addpayment 12,34€ (mit oder ohne €)")
        return ConversationHandler.END


async def add_payment(update, context):
    """
    extract a number from the reply and save the data to zettel
    """
    args = context.args
    if not args:
        # meaning that this gets called during conversation
        reply = update.message.text
    else:
        # gets called by command
        reply = " ".join(args)
    # match a floating point number
    matches = re.findall(r"[-+]?\d*[\.,]\d+|[-+]?\d+", reply)
    if len(matches)!=1:
        await update.message.reply_text("hab ich nicht verstanden... nochmal versuchen pls!\n"\
            "Machs einfach so:\n /addpayment 34,99€ (mit oder ohne €)")
        return ConversationHandler.END
    else:
        try:
            # first and only match for float
            payment = float(matches[0].replace(",", "."))
        except ValueError:
            await update.message.reply_text("hab ich nicht verstanden... nochmal versuchen pls!\n"\
                "Machs einfach so: /addpayment 34,99€ (mit oder ohne €)")
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
    await update.message.reply_text("ok, hab {}€ für {} aufgeschrieben. Du bist jetzt"\
        " bei {}€.".format(payment, username, round(zettel["payments"][userid]["paid"],2)))
    return ConversationHandler.END


async def payments(update, context):
    """
    list all payments
    """
    zettel = read_zettel(update.message.chat_id)

    # if no information is given
    if not zettel["payments"]:
        await context.bot.send_message(chat_id=update.message.chat_id,
            text="niemand hat irgendwas gezahlt.")
        return

    message = "*Die Ausgaben*\n"
    gesamt = 0.
    N = 0  # how many users
    for userid in zettel["payments"]:
        user = zettel["payments"][userid]
        message += "{}: {}€\n".format(user["name"], round(user["paid"],2))
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
        data = {"gesamt":round(gesamt,2), "jeder": round(gesamt/float(N),2), "cashflow":"\n".join(cashflow) }
        message += template.substitute(data)


    await context.bot.send_message(chat_id=update.message.chat_id, text=message,
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


async def reset_payments(update, context):
    zettel = read_zettel(update.message.chat_id)

    for userid in zettel["payments"]:
        zettel["payments"][userid]["paid"] = 0.0

    save_zettel(zettel, update.message.chat_id)

    await context.bot.send_message(chat_id=update.message.chat_id, text="ok, habs zurückgesetzt.")


async def cancel(update, context):
    await update.message.reply_text("ok dieses gespräch scheint vorbei zu sein.")
    return ConversationHandler.END


async def help(update, context):
    help_templatefile = os.path.join(PATH, "templates", "help.txt")
    with open(help_templatefile) as f:
        message = f.read()
    await context.bot.send_message(chat_id=update.message.chat_id, text=message,
        parse_mode=ParseMode.MARKDOWN)


# to be fired on unknown commands
async def unknown(update, context):
    message = "Den befehl kenn ich nicht! 😱\nnimm den /help befehl um mehr zu erfahren"
    await context.bot.send_message(chat_id=update.message.chat_id, text=message)


def build_application(application: Application):
    """
    add all handlers, messagefilters and job queues to a bare application object
    """
    def stop_and_restart():
        application.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update, context):
        update.message.reply_text("Starte Bot neu ...")
        logger.info("Restart bot ...")
        Thread(target=stop_and_restart).start()

    start_handler = MyCommandHandler('start', start)
    application.add_handler(start_handler)

    add_handler = MyCommandHandler('add', add, has_args=True)
    application.add_handler(add_handler)
    remove_handler = MyCommandHandler('remove', remove, has_args=True)
    application.add_handler(remove_handler)
    list_handler = MyCommandHandler('list', list)
    application.add_handler(list_handler)
    addpayment_handler = MyCommandHandler('addpayment', add_payment, has_args=True)
    application.add_handler(addpayment_handler)
    payments_handler = MyCommandHandler('payments', payments)
    application.add_handler(payments_handler)
    resetpayments_handler = MyCommandHandler('resetpayments', reset_payments)
    application.add_handler(resetpayments_handler)

    resetlist_handler = ConversationHandler(
        # command that triggers the conversation
        entry_points = [MyCommandHandler('resetlist', resetlist)],
        # states of the conversation
        states = {
            YESNOPROMPT: [MessageHandler(filters.TEXT, ask_for_payment)],
            CONVERSATION_ONGOING: [MessageHandler(filters.TEXT, add_payment)]
        },
        fallbacks=[MyCommandHandler('cancel', cancel)]
    )
    application.add_handler(resetlist_handler)

    # restart the bot, but only allow me to do this
    restart_handler = MyCommandHandler('restart', restart,
        filters=filters.Chat(username='@davekch'))
    application.add_handler(restart_handler)

    help_handler = MyCommandHandler('help', help)
    application.add_handler(help_handler)

    # scheisse handler
    scheisse = ScheissFilter()
    scheisse_handler = MessageHandler(filters.TEXT & scheisse, answer_shit)
    application.add_handler(scheisse_handler)

    # polt handler
    polt = PoltFilter()
    polt_handler = MessageHandler(filters.TEXT & polt, answer_polt)
    application.add_handler(polt_handler)

    # pasta and pizza handlers
    pizza = PizzaFilter()
    pizza_handler = MessageHandler(filters.TEXT & pizza, send_voice("pizza.ogg"))
    application.add_handler(pizza_handler)
    pasta = PastaFilter()
    pasta_handler = MessageHandler(filters.TEXT & pasta, send_voice("aldente.ogg"))
    application.add_handler(pasta_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)


if __name__=="__main__":
    application = ApplicationBuilder().token(get_token()).build()
    build_application(application)
    application.run_polling()
