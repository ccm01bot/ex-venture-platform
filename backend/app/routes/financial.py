from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.schemas import FinancialAccountCreate, FinancialAccountResponse, FinancialTransactionCreate, FinancialTransactionResponse
from app.models import FinancialAccount, FinancialTransaction

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.get("/accounts", response_model=list[FinancialAccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
):
    """List financial accounts."""
    stmt = select(FinancialAccount)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/accounts", response_model=FinancialAccountResponse)
async def create_account(
    account_data: FinancialAccountCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create financial account."""
    account = FinancialAccount(
        account_name=account_data.account_name,
        account_type=account_data.account_type,
        currency=account_data.currency,
        current_balance=account_data.current_balance,
        institution=account_data.institution,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/transactions", response_model=list[FinancialTransactionResponse])
async def list_transactions(
    account_id: UUID = None,
    db: AsyncSession = Depends(get_db),
):
    """List transactions."""
    if account_id:
        stmt = select(FinancialTransaction).where(FinancialTransaction.account_id == account_id)
    else:
        stmt = select(FinancialTransaction).order_by(FinancialTransaction.date.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/transactions", response_model=FinancialTransactionResponse)
async def create_transaction(
    transaction_data: FinancialTransactionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create transaction."""
    transaction = FinancialTransaction(
        account_id=transaction_data.account_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        category=transaction_data.category,
        description=transaction_data.description,
        date=transaction_data.date,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.get("/summary")
async def get_financial_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get financial summary."""
    stmt = select(FinancialAccount)
    result = await db.execute(stmt)
    accounts = result.scalars().all()

    total_balance = sum(acc.current_balance for acc in accounts)

    return {
        "total_balance": total_balance,
        "account_count": len(accounts),
        "accounts": accounts,
    }
