from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .schemas import WalletResponse, OperationType
from .models import Wallet
import logging
from redis.asyncio import Redis
import uuid

logging.basicConfig(level=logging.INFO)

async def get_wallet(db: AsyncSession, wallet_uuid: str) -> Wallet:
    """Поиск кошелька по его айди c кешированием в Redis."""
    query = select(Wallet).filter(Wallet.id == wallet_uuid)
    result = await db.execute(query)
    wallet = await result.scalar_one_or_none()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Кошелек не найден")
    
    return wallet

async def create_new_wallet(db: AsyncSession, balance) -> WalletResponse:
    """Создание нового кошелька."""
    wallet = Wallet(id=str(uuid.uuid4()), balance=balance)
    try:
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return WalletResponse(id=wallet.id, balance=wallet.balance)

async def transactions(wallet_uuid: str, operation_type: OperationType, amount: float, db: AsyncSession):
    """Проведение транзакции."""
    try:
        wallet = await get_wallet(db, wallet_uuid)

        if operation_type == OperationType.DEPOSIT:
            wallet.balance += amount
        elif operation_type == OperationType.WITHDRAW:
            if wallet.balance >= amount:
                wallet.balance -= amount
            else:
                raise HTTPException(status_code=400, detail='Недостаточно средств на балансе')
        else:
            raise HTTPException(status_code=400, detail='Некорректный тип операции')

        await db.commit()

        return JSONResponse(status_code=200, content={'message': 'Операция прошла успешно'})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def wallet_report(wallet_uuid: str, db: AsyncSession, redis: Redis) -> WalletResponse:
    """Баланс определенного кошелька по его айди."""
    cache_key = f'wallet_balance:{wallet_uuid}'

    cached_balance = await redis.get(cache_key)
    if cached_balance:
        logging.info("Баланс кошелька из кэша")
        return WalletResponse(id = wallet_uuid, balance = float(cached_balance))
    try:
        wallet = await get_wallet(db, wallet_uuid)
        await redis.setex(cache_key, 300, wallet.balance)
    
        return WalletResponse(id = wallet.id, balance = wallet.balance)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    