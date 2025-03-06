from sqlalchemy import JSON, ForeignKey, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    selectinload,
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
import itertools
from typing import List, Callable
import os
import logging


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


if os.environ.get("EINKAUFBOT_TEST"):
    DATABASE_PATH = "db-test.sqlite"
else:
    DATABASE_PATH = "db.sqlite"
logging.info(f"{DATABASE_PATH=}")

engine = create_engine("sqlite:///" + DATABASE_PATH)
SessionLocal = sessionmaker(bind=engine)
aengine = create_async_engine("sqlite+aiosqlite:///" + DATABASE_PATH)
ASessionLocal: Callable[[], AsyncSession] = async_sessionmaker(bind=aengine)


def init_db():
    Base.metadata.create_all(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UserGroup(Base):
    """
    represents a many-to-many relationship between User and Group
    also holds the credit the user has in this group
    """
    __tablename__ = "user_group"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.telegram_id", ondelete="CASCADE"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.chat_id", ondelete="CASCADE"), primary_key=True)
    user: Mapped["User"] = relationship("User", back_populates="user_groups")
    group: Mapped["Group"] = relationship("Group", back_populates="group_users")
    credit: Mapped[int] = mapped_column(default=0)   # what the user paid in this group in cents


class User(Base):
    __tablename__ = "user"

    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    user_groups: Mapped[List["UserGroup"]] = relationship(
        "UserGroup",
        back_populates="user",
        cascade="all, delete",
    )


class Group(Base):
    __tablename__ = "group"

    chat_id: Mapped[int] = mapped_column(primary_key=True)
    group_users: Mapped[List["UserGroup"]] = relationship(
        "UserGroup",
        back_populates="group",
        cascade="all, delete",
    )
    grocery_list: Mapped[List[str]] = mapped_column(JSON, default=list)
    putzplan: Mapped["Putzplan"] = relationship(
        "Putzplan",
        uselist=False,  # one-to-one
        cascade="all, delete",
    )


class Putzplan(Base):
    __tablename__ = "putzplan"

    group_id: Mapped[int] = mapped_column(
        ForeignKey("group.chat_id", ondelete="CASCADE"),
        primary_key=True
    )
    group: Mapped["Group"] = relationship("Group", back_populates="putzplan")
    tasks: Mapped[List[str]] = mapped_column(JSON)
    index: Mapped[int] = mapped_column(default=0)

    @classmethod
    async def aall(cls) -> List["Putzplan"]:
        async with ASessionLocal() as session:
            return (await session.execute(select(cls))).scalars().all()
        
    async def aget_assigned_tasks(self, session: AsyncSession) -> List[tuple[str, str]]:
        """
        returns a list of (username, task)
        """
        group = (
            await session.execute(
                select(Group).options(
                    selectinload(Group.group_users).selectinload(UserGroup.user)
                ).filter(Group.chat_id==self.group_id)
            )
        ).scalar_one()
        users = sorted([usergroup.user.name for usergroup in group.group_users])
        # map users to task with an offset of self.index
        N = min(len(users), len(self.tasks))
        return [
            (users[i], self.tasks[(i + self.index) % N])
            for i in range(N)
        ]

    async def arotate(self):
        async with ASessionLocal() as session:
            self.index = (self.index + 1) % len(self.tasks)
            session.add(self)
            await session.commit()


async def get_groceries(chat_id: int) -> list[str]:
    async with ASessionLocal() as session:
        group = await session.get(Group, chat_id)
        if not group:
            return []
        return group.grocery_list


async def save_groceries(groceries: list[str], chat_id: int):
    async with ASessionLocal() as session:
        group = await session.get(Group, chat_id)
        if not group:
            group = Group(chat_id=chat_id)
        group.grocery_list = groceries
        session.add(group)
        await session.commit()


async def get_credits(chat_id: int) -> list[tuple[str, int]]:
    """
    returns a list of (username, credit) tuples
    """
    async with ASessionLocal() as session:
        # we want iterate over the group's group_users so we need to load them
        group = (
            await session.execute(
                select(Group).options(
                    selectinload(Group.group_users).selectinload(UserGroup.user)
                ).filter(Group.chat_id==chat_id)
            )
        ).scalar_one_or_none()
        if not group:
            return []
        credits = []
        for usergroup in group.group_users:
            credits.append((usergroup.user.name, usergroup.credit))
        return credits


async def add_to_credit(user_id: int, user_name: str, chat_id: int, add_credit: int) -> int:
    async with ASessionLocal() as session:
        # get user and group, create if they don't exist yet
        user = await session.get(User, user_id)
        if not user:
            user = User(telegram_id=user_id, name=user_name)
            session.add(user)

        group = await session.get(Group, chat_id)
        if not group:
            group = Group(chat_id)
            session.add(group)

        usergroup = await session.get(UserGroup, (user_id, chat_id))
        if not usergroup:
            # add the user to the group
            usergroup = UserGroup(user_id=user_id, group_id=chat_id)
            session.add(usergroup)
            await session.commit()
            # fetch again for changes
            usergroup = await session.get(UserGroup, (user_id, chat_id))

        # increase credit
        new_credit = usergroup.credit + add_credit
        usergroup.credit = new_credit
        session.add(usergroup)
        await session.commit()
        return new_credit


async def reset_payments(chat_id: int):
    async with ASessionLocal() as session:
        group = (
            await session.execute(
                select(Group).options(selectinload(Group.group_users)).filter(Group.chat_id==chat_id)
            )
        ).scalar_one_or_none()
        if not group:
            return
        for usergroup in group.group_users:
            usergroup.credit = 0
            session.add(usergroup)
        await session.commit()


async def get_assigned_tasks(chat_id: int) -> List[tuple[str, str]]:
    async with ASessionLocal() as session:
        putzplan = await session.get(Putzplan, chat_id)
        if not putzplan:
            return []
        return await putzplan.aget_assigned_tasks(session)
