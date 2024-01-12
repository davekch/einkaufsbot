from unittest.result import TestResult
import yaml
import os
from pathlib import Path
from telethon.sync import TelegramClient
from unittest import IsolatedAsyncioTestCase
import unittest
import asyncio
from telegram.ext import Application, ApplicationBuilder

import einkaufsbot

chat_id = 223200812

with open("secrets.yml") as f:
    secrets = yaml.safe_load(f)

def get_client() -> TelegramClient:
    return TelegramClient(
        "unittesting",
        secrets["test_api_id"],
        secrets["test_api_hash"]
    )


def get_testbot() -> Application:
    app = ApplicationBuilder().token(secrets["test_token"]).build()
    einkaufsbot.build_application(app)
    return app


class TestEinkaufHeini(IsolatedAsyncioTestCase):
    async def asyncSetUp(cls):
        # start the test bot
        cls.testbot = get_testbot()
        cls.testbot_username = "@blueinkaufbot_test_bot"
        await cls.testbot.initialize()
        await cls.testbot.updater.start_polling()
        await cls.testbot.start()
        # set up a telegram client
        cls.client = get_client()
        await cls.client.connect()
        if not (await cls.client.is_user_authorized()):
            await cls.client.send_code_request("")
            await cls.client.sign_in("", input("code: "))
        await cls.client.get_me()

    async def asyncTearDown(cls):
        cls.client.disconnect()
        await cls.testbot.updater.stop()
        await cls.testbot.stop()
        await cls.testbot.shutdown()
    
    async def test_list(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            # first make sure that there is no zettel
            zettel = Path("zettel") / f"{chat_id}.json"
            if zettel.exists():
                os.remove(str(zettel))

            await c.send_message("/list")
            response = await c.get_response()
            self.assertEqual(response.raw_text, "hab keine einkaufsliste grad.")

            await c.send_message("/add tomaten")
            _ = await c.get_response()

            await c.send_message("/list")
            response = await c.get_response()
            self.assertIn("tomaten", response.raw_text)
        
    async def test_add(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            await c.send_message("/add mozzarella quark")
            response = await c.get_response()
            self.assertEqual(response.raw_text, "ok, hab's auf die liste geschrieben")
            # check that both mozarella and quark are on the list now
            await c.send_message("/list")
            response = await c.get_response()
            self.assertTrue(all(item in response.raw_text.splitlines() for item in ["mozzarella", "quark"]))

            # check the same again but with comma separated list
            await c.send_message("/add eisenkuchen, salat")
            response = await c.get_response()
            self.assertEqual(response.raw_text, "ok, hab's auf die liste geschrieben")
            # check that both mozarella and quark are on the list now
            await c.send_message("/list")
            response = await c.get_response()
            self.assertTrue(all(item in response.raw_text.splitlines() for item in ["mozzarella", "quark", "eisenkuchen", "salat"]))

            # check duplicates
            await c.send_message("/add eisenkuchen")
            response = await c.get_response()
            self.assertIn("eisenkuchen steht schon auf der einkaufsliste", response.raw_text)

    async def test_remove(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            await c.send_message("/add mozzarella")
            _ = await c.get_response()

            await c.send_message("/remove mozzarella")
            response = await c.get_response()
            self.assertIn("hab's runter", response.raw_text)

            await c.send_message("/remove ciniminis")
            response = await c.get_response()
            self.assertIn("eh nicht auf dem zettel", response.raw_text)
    
    async def test_payments(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            await c.send_message("/payments")
            response = await c.get_response()
            self.assertEqual(response.raw_text, "niemand hat irgendwas gezahlt.")

            await c.send_message("/addpayment 2,50€")
            response = await c.get_response()
            self.assertIn("ok", response.raw_text)
            self.assertIn("2.5", response.raw_text)

            await c.send_message("/payments")
            response = await c.get_response()
            self.assertIn("Die Ausgaben", response.raw_text)
            self.assertIn("2.5", response.raw_text)

            await c.send_message("/addpayment 3.4")
            response = await c.get_response()
            self.assertIn("3.4", response.raw_text)

            await c.send_message("/payments")
            response = await c.get_response()
            self.assertIn("5.9", response.raw_text)
        
    async def test_reset_conversation_1(self):
        async with self.client.conversation(self.testbot_username, timeout=10) as c:
            # just make sure something is on the list
            await c.send_message("/add quack")
            _ = await c.get_response()

            await c.send_message("/resetlist")
            response = await c.get_response()
            self.assertIn("ok", response.raw_text)
            self.assertIn("willst du gleich", response.raw_text)

            # say something invalid
            await c.send_message("weiss der geier")
            response = await c.get_response()
            self.assertIn("hab ich nicht verstanden", response.raw_text)

            # conversation is over
            await c.send_message("tschuess")
            with self.assertRaises(asyncio.exceptions.TimeoutError):
                response = await c.get_response()

    async def test_reset_conversation_2(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            # just make sure something is on the list
            await c.send_message("/add quack")
            _ = await c.get_response()
            await c.send_message("/resetlist")
            _ = await c.get_response()

            await c.send_message("nein")
            response = await c.get_response()
            self.assertIn("gut dann nicht", response.raw_text)

            # conversation is over
            await c.send_message("tschuess")
            with self.assertRaises(asyncio.exceptions.TimeoutError):
                response = await c.get_response()

    async def test_reset_conversation_3(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            # just make sure something is on the list
            await c.send_message("/add quack")
            _ = await c.get_response()
            await c.send_message("/resetlist")
            _ = await c.get_response()

            await c.send_message("ja")
            response = await c.get_response()
            self.assertEqual("ok dann gib jetzt dein geld ein", response.raw_text)

            # say something invalid
            await c.send_message("vier")
            response = await c.get_response()
            self.assertIn("hab ich nicht verstanden", response.raw_text)

            # conversation is over
            await c.send_message("tschuess")
            with self.assertRaises(asyncio.exceptions.TimeoutError):
                response = await c.get_response()

    async def test_reset_conversation_4(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            # just make sure something is on the list
            await c.send_message("/add quack")
            _ = await c.get_response()
            await c.send_message("/resetlist")
            _ = await c.get_response()
            await c.send_message("ja")
            _ = await c.get_response()

            await c.send_message("3,64")
            response = await c.get_response()
            self.assertIn("ok", response.raw_text)
            self.assertIn("3.64", response.raw_text)

            # conversation is over
            await c.send_message("tschuess")
            with self.assertRaises(asyncio.exceptions.TimeoutError):
                response = await c.get_response()

    async def test_reset_conversation_5(self):
        async with self.client.conversation(self.testbot_username, timeout=5) as c:
            # just make sure something is on the list
            await c.send_message("/add quack")
            _ = await c.get_response()
            await c.send_message("/resetlist")
            _ = await c.get_response()

            await c.send_message("30")
            response = await c.get_response()
            self.assertIn("ok", response.raw_text)
            self.assertIn("30", response.raw_text)

            # conversation is over
            await c.send_message("tschuess")
            with self.assertRaises(asyncio.exceptions.TimeoutError):
                response = await c.get_response()


if __name__ == "__main__":
    unittest.main()
