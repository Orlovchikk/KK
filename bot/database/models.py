from sqlalchemy import Column, Date, ForeignKey, Integer, String, BigInteger
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    balance_id = Column(Integer, ForeignKey("balances.id"))
    username = Column(String)
    full_name = Column(String)
    plan = Column(String)


class Balance(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    uniq_code = Column(String, nullable=True)
    subscription_end = Column(Date, nullable=True)
    users = relationship("User", backref="balance", foreign_keys=[User.balance_id])
