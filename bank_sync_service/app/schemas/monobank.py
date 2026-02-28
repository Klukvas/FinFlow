from pydantic import BaseModel
from typing import Optional


class MonobankAccount(BaseModel):
    id: str
    sendId: Optional[str] = None
    balance: int
    creditLimit: int = 0
    type: Optional[str] = None
    currencyCode: int
    cashbackType: Optional[str] = None
    maskedPan: Optional[list[str]] = None
    iban: Optional[str] = None


class MonobankJar(BaseModel):
    id: str
    sendId: Optional[str] = None
    title: str
    description: Optional[str] = None
    currencyCode: int
    balance: int
    goal: Optional[int] = None


class MonobankClientInfo(BaseModel):
    clientId: Optional[str] = None
    name: Optional[str] = None
    webHookUrl: Optional[str] = None
    permissions: Optional[str] = None
    accounts: list[MonobankAccount] = []
    jars: Optional[list[MonobankJar]] = None


class MonobankStatementItem(BaseModel):
    id: str
    time: int
    description: str
    mcc: int
    originalMcc: Optional[int] = None
    hold: bool = False
    amount: int
    operationAmount: int
    currencyCode: int
    commissionRate: int = 0
    cashbackAmount: int = 0
    balance: int
    comment: Optional[str] = None
    receiptId: Optional[str] = None
    invoiceId: Optional[str] = None
    counterEdrpou: Optional[str] = None
    counterIban: Optional[str] = None
    counterName: Optional[str] = None
