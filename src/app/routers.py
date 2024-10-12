from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from .schemas import WalletResponse, OperationType
from .database import get_db
from .crud import create_new_wallet, transactions, wallet_report
import redis.asyncio as aioredis
from app.config import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)
router = APIRouter(prefix='/api/v1/wallets')

@router.get('health/ready')
async def health_check():
    return JSONResponse(status_code=200, content={'message': 'success'})

@router.post('/wallet_creation', response_model=WalletResponse)
async def api_create_new_wallet(balance: float, db: Annotated[AsyncSession, Depends(get_db)]):
    return await create_new_wallet(balance=balance, db=db)

@router.post('/{wallet_uuid}/operation')
async def api_transactions(wallet_uuid: str, operation: OperationType, amount: float, db: Annotated[AsyncSession, Depends(get_db)]):
    return await transactions(wallet_uuid=wallet_uuid, operation_type=operation, amount=amount, db=db)

@router.get('/{wallet_uuid}', response_model=WalletResponse)
async def api_report_wallet(wallet_uuid: str, db: Annotated[AsyncSession, Depends(get_db)]):
    return await wallet_report(wallet_uuid=wallet_uuid, db=db, redis=redis)