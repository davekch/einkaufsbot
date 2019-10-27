#!/usr/bin/python3
# -*- coding: utf-8 -*-
from telegram import ParseMode
import json

class Putzplan:

    def __init__(self):
        with open("putzplan.json") as f:
            self.putzplan = json.load(f)

    def show_plan(self, bot, chat_id):
        if not str(chat_id) in self.putzplan:
            return
        plan = self.putzplan[str(chat_id)]
        n = len(plan["folks"])
        text = "*Der Putzplan*\n"
        for i in range(n):
            text += "{}: {}\n".format(plan["folks"][i], plan["tasks"][(i+plan["index"])%n])
        bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

    def rearange(self):
        for plan in self.putzplan.values():
            plan["index"] = (plan["index"] + 1) % (len(plan["folks"]))
        with open("putzplan.json", "w") as f:
            json.dump(self.putzplan, f, indent=4)


p = Putzplan()

def callback(bot, job):
    p.rearange()
    for chat_id in p.putzplan:
        p.show_plan(bot, int(chat_id))
