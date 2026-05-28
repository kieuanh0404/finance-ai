from pydantic import BaseModel
from typing import Optional

class TransactionRequest(BaseModel):
    username: str
    type: str
    amount: float
    category: str
    date: str
    note: Optional[str] = ""

class TransactionResponse(BaseModel):
    id: int
    username: str
    type: str
    amount: float
    category: str
    date: str
    note: Optional[str] = ""