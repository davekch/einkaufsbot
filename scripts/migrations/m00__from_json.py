from pathlib import Path
import json
import os

PROJECT_DIR = Path(__file__).absolute().parent.parent.parent

from einkaufsbot import db


def migrate_zettel(path: str | Path):
    path = Path(path)
    chat_id = int(path.stem)
    with open(path) as f:
        zettel_data = json.load(f)
    with db.SessionLocal() as session:
        group = db.Group(chat_id=chat_id, grocery_list=zettel_data["liste"])
        session.add(group)
        for user_id, data in zettel_data["payments"].items():
            user = session.get(db.User, user_id)
            if not user:
                user = db.User(telegram_id=int(user_id), name=data["name"])
                session.add(user)
            usergroup = db.UserGroup(
                user_id=user.telegram_id,
                group_id=group.chat_id,
                credit=int(data["paid"] * 100)
            )
            session.add(usergroup)
        session.commit()


def migrate_all_zettels(basepath: str | Path):
    for zettel in os.listdir(basepath):
        migrate_zettel(Path(basepath) / zettel)


if __name__ == "__main__":
    migrate_all_zettels(PROJECT_DIR / "zettel")