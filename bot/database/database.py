import os
import random
from datetime import date
from os.path import dirname, join

from dotenv import load_dotenv
from sqlalchemy import exc, select
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from .models import Balance, Base, User

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

HOST = os.getenv("HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
PGUSER = os.getenv("PGUSER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PORT = os.getenv("PORT")
url = f"postgresql+asyncpg://{PGUSER}:{POSTGRES_PASSWORD}@{HOST}:{PORT}/{POSTGRES_DB}"


class Database:
    def __init__(self):
        self.engine = create_async_engine(
            url,
            echo=True,
        )
        self.session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_metadata(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def create_user(self, user_id: int, username: str, full_name: str):
        async with self.session() as db:
            try:
                new_user = User(id=str(user_id), username=username, full_name=full_name)
                db.add(new_user)
                await db.flush()

                new_balance = Balance(owner_id=str(user_id), amount=0)
                db.add(new_balance)
                await db.flush()

                new_user.balance_id = new_balance.id
                await db.flush()
                await db.commit()
                return False
            except exc.IntegrityError:
                await db.rollback()
                return True

    async def get_user(self, db: AsyncSession = None, user_id: int = None):
        close_db = False
        if db is None:
            db = self.session()
            close_db = True
        try:
            user = await db.scalar(select(User).where(User.id == str(user_id)))
            return user
        finally:
            if close_db:
                await db.close()

    async def get_balance(self, db: AsyncSession = None, user_id: int = None):
        close_db = False
        if db is None:
            db = self.session()
            close_db = True
        try:
            user = await self.get_user(db, user_id)
            if user is None:
                return None
            balance = await db.scalar(
                select(Balance).where(Balance.id == user.balance_id)
            )
            return balance
        finally:
            if close_db:
                await db.close()

    async def increase_balance(self, user_id: int, amount: int):
        async with self.session() as db:
            balance = await self.get_balance(db, user_id)
            balance.amount += amount
            await db.flush()
            await db.commit()

    async def decrease_balance(self, user_id: int):
        async with self.session() as db:
            balance = await self.get_balance(db, user_id)
            balance.amount -= 1
            await db.flush()
            await db.commit()
            return True

    async def get_balance_by_uniq_code(self, uniq_code: int):
        async with self.session() as db:
            try:
                balance = await db.scalar(
                    select(Balance).where(Balance.uniq_code == uniq_code)
                )
                return balance if balance else False
            except Exception as e:
                return False

    async def link_user_to_balance(self, user_id: int, balance_id: int):
        async with self.session() as db:
            user = await self.get_user(db, user_id)
            user.balance_id = balance_id
            await db.flush()
            await db.commit()

    async def create_uniq_code(self, user_id: int):
        async with self.session() as db:
            uniq_code = random.choices(
                population=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], k=4
            )
            balance = await self.get_balance(db, user_id)
            if not balance.uniq_code:
                balance.uniq_code = "".join(uniq_code)
                await db.flush()
                await db.commit()
            return True

    async def get_uniq_code(self, user_id: int):
        async with self.session() as db:
            balance = await self.get_balance(db, user_id)
            return balance.uniq_code

    async def get_users_by_balance(self, balance_id: int):
        async with self.session() as db:
            users = await db.execute(select(User).where(User.balance_id == balance_id))
            return users.scalars().all()
        
    async def unlink_user_from_balance(self, user: User):
        async with self.session() as db:
            try:    
                user = await self.get_user(db, user_id=user.id)
                user_balance = await db.scalar(
                    select(Balance).where(Balance.owner_id == user.id)
                )
                user.balance = user_balance
                await db.commit()
            except Exception as e:
                print(e)
                await db.rollback()
    
    async def subscribe(self, id: str, amount: int, unit: str):
        async with self.session() as db:
            try:
                balance = await self.get_balance(db, id)
                today = date.today()
                if unit == 'y':
                    balance.subscription_end = today.replace(year=today.year + amount)
                elif unit == 'm':
                    balance.subscription_end = today.replace(month=today.month + amount)

                await db.commit()
            except Exception as e:
                print(e)
                await db.rollback()
