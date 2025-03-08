from argparse import ArgumentParser
from pathlib import Path
import os
import logging


def main():# setup logging info
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    parser = ArgumentParser()
    parser.add_argument("token", help="path to token")
    parser.add_argument("--db", help="path to sqlite DB")
    args = parser.parse_args()
    
    with open(args.token) as f:
        token = f.read().strip()

    if not args.db:
        # db.sqlite in the current directory is default
        db_path = Path().absolute() / "db.sqlite"
    else:
        db_path = Path(args.db).resolve().absolute()

    os.environ["EINKAUFSBOT_DB_PATH"] = str(db_path)
    # db.py reads einkaufsbot_db_path, so we have to import it
    # after we set the value
    from . import bot
    bot.main(token)
