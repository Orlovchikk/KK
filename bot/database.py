from sqlalchemy import Column, ForeignKey, Integer, create_engine, String, select
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
from sqlalchemy import exc
import random


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    balance_id = Column(Integer, ForeignKey("balances.id"))


class Balance(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    uniq_code = Column(Integer, nullable=True)
    users = relationship("User", backref="balance", foreign_keys=[User.balance_id])


engine = create_engine(
    "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres", echo=True
)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False)

with Session(engine) as session:
    db = session


def create_user(user_id: int):
    try:
        new_user = User(id=str(user_id))
        db.add(new_user)
        db.flush()

        new_balance = Balance(owner_id=str(user_id), amount=0)
        db.add(new_balance)
        db.flush()

        new_user.balance_id = new_balance.id
        db.commit()
        return False
    except exc.IntegrityError:
        db.rollback()
        return True


def get_user(user_id: int):
    return db.scalar(select(User).where(User.id == str(user_id)))


def increase_balance(user_id: int, amount: int):
    balance = get_balance(user_id)
    balance.amount += amount
    db.commit()


def decrerase_balance(user_id: int):
    balance = get_balance(user_id)
    balance.amount -= 1
    db.commit()
    return True


def get_balance(user_id: int):
    user = get_user(user_id)
    balance = db.scalar(select(Balance).where(Balance.id == user.balance_id))
    return balance


def get_balance_by_uniq_code(uniq_code: int):
    try:
        balance = db.scalar(select(Balance).where(Balance.uniq_code == uniq_code))
        return balance if balance else False
    except Exception as e:
        return False


def link_user_to_balance(user_id: int, balance_id: int):
    user = get_user(user_id)
    user.balance_id = balance_id
    db.commit()


def create_uniq_code(user_id: int):
    uniq_code = random.choices(
        population=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], k=4
    )
    balance = get_balance(user_id)
    if not balance.uniq_code:
        balance.uniq_code = "".join(uniq_code)
        db.commit()
    return True


def get_uniq_code(user_id: int):
    balance = get_balance(user_id)
    return balance.uniq_code
