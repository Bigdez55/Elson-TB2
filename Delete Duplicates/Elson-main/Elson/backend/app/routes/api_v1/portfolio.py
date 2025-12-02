from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ...db.database import get_db
from ...models.user import User
from ...models.portfolio import Portfolio, Position
from ...core.auth import get_current_user
from ...schemas.portfolio import (
    PortfolioResponse,
    PositionResponse,
    PortfolioStats,
    PortfolioHistory
)
from ...services.portfolio import PortfolioService

router = APIRouter()

@router.get("/summary", response_model=PortfolioResponse)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current portfolio summary"""
    portfolio_service = PortfolioService(db)
    try:
        return await portfolio_service.get_portfolio(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/positions", response_model=List[PositionResponse])
async def get_portfolio_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all current positions"""
    portfolio_service = PortfolioService(db)
    try:
        return await portfolio_service.get_positions(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats", response_model=PortfolioStats)
async def get_portfolio_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio performance statistics"""
    portfolio_service = PortfolioService(db)
    try:
        return await portfolio_service.get_stats(
            user_id=current_user.id,
            days=days
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[PortfolioHistory])
async def get_portfolio_history(
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio value history"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    portfolio_service = PortfolioService(db)
    try:
        return await portfolio_service.get_history(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/deposit")
async def deposit_funds(
    amount: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deposit funds into portfolio"""
    portfolio_service = PortfolioService(db)
    try:
        await portfolio_service.deposit_funds(current_user.id, amount)
        return {"message": f"Successfully deposited ${amount:,.2f}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/withdraw")
async def withdraw_funds(
    amount: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Withdraw funds from portfolio"""
    portfolio_service = PortfolioService(db)
    try:
        await portfolio_service.withdraw_funds(current_user.id, amount)
        return {"message": f"Successfully withdrew ${amount:,.2f}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))