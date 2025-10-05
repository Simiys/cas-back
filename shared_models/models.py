from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum, BigInteger
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


# ------------------------------
# Пользователи
# ------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    username = Column(String, unique=True, nullable=False)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    ref_code = Column(String, unique=True, nullable=False)
    ref_by = Column(BigInteger, nullable=True, default=None)
    ton_balance = Column(Float, default=0.0)
    coins_balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallets = relationship("Wallet", back_populates="user")
    games = relationship("MinesGame", back_populates="user")
    lottery_tickets = relationship("LotteryTicket", back_populates="user")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


    # отношение many-to-many через таблицу Inventory
    inventory = relationship("Inventory", back_populates="user", cascade="all, delete-orphan")

# ------------------------------
# Кошельки
# ------------------------------
class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallet_address = Column(String, unique=True, nullable=False)
    wallet_type = Column(String, nullable=False)  # ton, ethereum, etc
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="wallets")

# ------------------------------
# Инвентарь пользователя
# ------------------------------
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    gift_id = Column(Integer, ForeignKey("gifts.id", ondelete="CASCADE"))
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="inventory")
    gift = relationship("Gift", back_populates="owners")

# ------------------------------
# Доступные подарки
# ------------------------------
class Gift(Base):
    __tablename__ = "gifts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    telegram_gift_id = Column(String, nullable=False)
    cost_coins = Column(Float, nullable=False)
    cost_ton = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owners = relationship("Inventory", back_populates="gift", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="gift")


# ------------------------------
# Игры с минками
# ------------------------------
class MinesGame(Base):
    __tablename__ = "mines_games"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bet = Column(Float, nullable=False)
    num_mines = Column(Integer, nullable=False)
    won_amount = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    result_data = Column(String, nullable=True)  # JSON строка с состоянием игры

    user = relationship("User", back_populates="games")



# ------------------------------
# Лотерейные билеты
# ------------------------------
class TicketTypeEnum(str, enum.Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"


class LotteryTicket(Base):
    __tablename__ = "lottery_tickets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticket_type = Column(Enum(TicketTypeEnum), nullable=False)
    price = Column(Float, nullable=False)

    # массив id подарков (может быть пустым)
    won_gift_ids = Column(ARRAY(Integer), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="lottery_tickets")


# ------------------------------
# Запросы на вывод
# ------------------------------
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # deposit, ton_withdrawal, gift_withdrawal
    amount = Column(Float, nullable=True)  # TON сумма (если применимо)
    gift_id = Column(Integer, ForeignKey("gifts.id"), nullable=True)  # если это подарок
    status = Column(String, default="pending")  # pending, completed, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="transactions")
    gift = relationship("Gift", back_populates="transactions", lazy="joined")