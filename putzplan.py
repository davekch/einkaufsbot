#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram.constants import ParseMode
import json
import os

PATH = os.path.dirname(os.path.realpath(__file__))

class Putzplan:

    def __init__(self):
        with open(os.path.join(PATH, "putzplan.json")) as f:
            self.putzplan = json.load(f)

    async def show_plan(self, bot, chat_id):
        if not str(chat_id) in self.putzplan:
            return
        plan = self.putzplan[str(chat_id)]
        n = len(plan["folks"])
        text = "*Der Putzplan*\n"
        for i in range(n):
            text += "{}: {}\n".format(plan["folks"][i], plan["tasks"][(i+plan["index"])%n])
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

    def rearange(self):
        for plan in self.putzplan.values():
            plan["index"] = (plan["index"] + 1) % (len(plan["folks"]))
        with open(os.path.join(PATH, "putzplan.json"), "w") as f:
            json.dump(self.putzplan, f, indent=4)


p = Putzplan()

async def callback(context):
    p.rearange()
    for chat_id in p.putzplan:
        await p.show_plan(context.bot, int(chat_id))

async def callback_show(bot, job):
    for chat_id in p.putzplan:
        await p.show_plan(bot, int(chat_id))
