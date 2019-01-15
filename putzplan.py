#!/usr/bin/python3
# -*- coding: utf-8 -*-
from telegram import ParseMode

class Putzplan:

    def __init__(self):
        self.folks = ["Johanna", "David", "Elli"]
        self.tasks = ["Küche & Müll", "Bad", "Boden"]
        self.index = 0

    def show_plan(self, bot, chat_id):
        text = "*Der Putzplan*\n"
        for i in range(3):
            text += "{}: {}\n".format(self.folks[i], self.tasks[(i+self.index)%3])
        bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

    def rearange(self):
        self.index = (self.index + 1) % 3


p = Putzplan()

def callback(bot, job):
    p.rearange()
    p.show_plan(bot, -295936069)
