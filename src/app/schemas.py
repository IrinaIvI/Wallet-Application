from pydantic import BaseModel
from enum import Enum as PyEnum

class OperationType(PyEnum):
    DEPOSIT = 'DEPOSIT'
    WITHDRAW = 'WITHDRAW'

class Operation(BaseModel):
    operationType: OperationType
    amount: float 

class WalletResponse(BaseModel):
    id: str
    balance: float