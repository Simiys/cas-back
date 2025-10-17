from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from models import LotteryTicket
from schemas.lottery_ticket import LotteryTicketCreate, LotteryTicketUpdate  # Пайдант схемы

# ===========================
# CREATE
# ===========================
async def create_lottery_ticket(db: AsyncSession, ticket_in: LotteryTicketCreate) -> LotteryTicket:
    ticket = LotteryTicket(
        user_id=ticket_in.user_id,
        ticket_type=ticket_in.ticket_type,
        currency = ticket_in.currency,
        price=ticket_in.price,
        won_gift_ids=ticket_in.won_gift_ids,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket

# ===========================
# READ по ID
# ===========================
async def get_lottery_ticket(db: AsyncSession, ticket_id: int) -> Optional[LotteryTicket]:
    result = await db.execute(select(LotteryTicket).where(LotteryTicket.id == ticket_id))
    return result.scalar_one_or_none()

# ===========================
# READ все билеты
# ===========================
async def get_all_lottery_tickets(db: AsyncSession) -> List[LotteryTicket]:
    result = await db.execute(select(LotteryTicket).order_by(LotteryTicket.created_at.desc()))
    return result.scalars().all()

# ===========================
# READ все билеты конкретного пользователя
# ===========================
async def get_user_lottery_tickets(db: AsyncSession, user_id: int) -> List[LotteryTicket]:
    result = await db.execute(
        select(LotteryTicket)
        .where(LotteryTicket.user_id == user_id)
        .order_by(LotteryTicket.created_at.desc())
    )
    return result.scalars().all()

# ===========================
# UPDATE
# ===========================
async def update_lottery_ticket(
    db: AsyncSession, ticket_id: int, ticket_in: LotteryTicketUpdate
) -> Optional[LotteryTicket]:
    ticket = await get_lottery_ticket(db, ticket_id)
    if not ticket:
        return None

    if ticket_in.ticket_type is not None:
        ticket.ticket_type = ticket_in.ticket_type
    if ticket_in.price is not None:
        ticket.price = ticket_in.price
    if ticket_in.won_gift_ids is not None:
        ticket.won_gift_ids = ticket_in.won_gift_ids

    await db.commit()
    await db.refresh(ticket)
    return ticket

# ===========================
# DELETE
# ===========================
async def delete_lottery_ticket(db: AsyncSession, ticket_id: int) -> bool:
    ticket = await get_lottery_ticket(db, ticket_id)
    if not ticket:
        return False
    await db.delete(ticket)
    await db.commit()
    return True
