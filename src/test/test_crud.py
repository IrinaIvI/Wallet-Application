import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
from src.app.crud import create_new_wallet, transactions, wallet_report
from src.app.models import Wallet
from src.app.schemas import WalletResponse, OperationType

@pytest.mark.asyncio
async def test_create_new_wallet():
    mock_db = AsyncMock(spec=AsyncSession)
    balance = 100.0

    response = await create_new_wallet(mock_db, balance)

    assert response.id is not None
    assert response.balance == balance
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "initial_balance, deposit_amount, expected_balance, should_raise",
    [
        (100.0, 50.0, 150.0, False),  
        (100.0, -50.0, 50.0, False),  
        (100.0, -150.0, 100.0, True),
    ]
)
async def test_transactions(initial_balance, deposit_amount, expected_balance, should_raise):
    mock_db = AsyncMock(spec=AsyncSession)
    wallet = Wallet(id="test-wallet", balance=initial_balance)
    
    mock_db.execute.return_value.scalar_one_or_none.return_value = wallet

    operation_type = OperationType.DEPOSIT if deposit_amount > 0 else OperationType.WITHDRAW

    if should_raise:
        with pytest.raises(HTTPException) as excinfo:
            await transactions(wallet.id, operation_type, abs(deposit_amount), mock_db)
        assert excinfo.value.status_code == 400
        assert "Недостаточно средств на балансе" in excinfo.value.detail
    else:
        await transactions(wallet.id, operation_type, abs(deposit_amount), mock_db)
        assert wallet.balance == expected_balance

@pytest.mark.asyncio
async def test_wallet_report():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_redis = AsyncMock()
    wallet_uuid = "test-wallet"
    expected_balance = 100.0

    wallet = Wallet(id=wallet_uuid, balance=expected_balance)
    mock_db.execute.return_value.scalar_one_or_none.return_value = wallet

    mock_redis.get.return_value = None

    response = await wallet_report(wallet_uuid, mock_db, mock_redis)

    expected_response = WalletResponse(id=wallet_uuid, balance=expected_balance)

    assert response == expected_response 
    assert response.id == wallet_uuid
    assert response.balance == expected_balance
    mock_redis.setex.assert_called_once_with(f'wallet_balance:{wallet_uuid}', 300, expected_balance)