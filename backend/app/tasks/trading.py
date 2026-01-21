"""Trading-related background tasks.

This module contains tasks for executing trades, processing recurring investments,
and other trading-related background operations.
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.alerts import alert_manager
from app.core.config import settings
from app.core.metrics import metrics
from app.core.redis_service import redis_service
from app.core.task_queue import TaskQueueError, task
from app.db.database import get_db
from app.models.account import Account
from app.models.subscription import RecurringInvestment, RecurringInvestmentStatus
from app.models.trade import Trade, TradeStatus
from app.models.user import User

logger = logging.getLogger(__name__)


@task(max_retries=3, queue="high_priority")
def process_recurring_investments(self, date: Optional[str] = None) -> Dict[str, Any]:
    """Process all due recurring investments.

    This task identifies all recurring investments that are due for execution
    and creates the appropriate trades.

    Args:
        date: Optional date string in ISO format (YYYY-MM-DD). Defaults to today.

    Returns:
        Summary of processed recurring investments
    """
    logger.info("Processing recurring investments")
    start_time = time.time()

    # Parse date or use today
    if date:
        process_date = datetime.fromisoformat(date).date()
    else:
        process_date = datetime.utcnow().date()

    result = {
        "date": process_date.isoformat(),
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
        "trades_created": 0,
        "failures": [],
    }

    db = next(get_db())
    try:
        # Find recurring investments due today
        recurring_investments = (
            db.query(RecurringInvestment)
            .filter(
                RecurringInvestment.status == RecurringInvestmentStatus.ACTIVE,
                RecurringInvestment.next_execution_date <= process_date,
            )
            .all()
        )

        logger.info(
            f"Found {len(recurring_investments)} recurring investments to process"
        )

        for investment in recurring_investments:
            try:
                # Process this recurring investment
                result["processed"] += 1

                # Check if account is active
                account = (
                    db.query(Account)
                    .filter(Account.id == investment.account_id)
                    .first()
                )
                if not account or not account.is_active:
                    logger.warning(
                        f"Skipping recurring investment {investment.id}: Account {investment.account_id} inactive"
                    )
                    result["skipped"] += 1
                    continue

                # Check if user is active
                user = db.query(User).filter(User.id == account.user_id).first()
                if not user or not user.is_active:
                    logger.warning(
                        f"Skipping recurring investment {investment.id}: User {account.user_id} inactive"
                    )
                    result["skipped"] += 1
                    continue

                # Check if user has active subscription
                if settings.REQUIRE_SUBSCRIPTION_FOR_RECURRING:
                    has_active_sub = db.execute(
                        "SELECT EXISTS(SELECT 1 FROM subscriptions WHERE user_id = :user_id AND status = 'ACTIVE')",
                        {"user_id": user.id},
                    ).scalar()

                    if not has_active_sub:
                        logger.warning(
                            f"Skipping recurring investment {investment.id}: No active subscription"
                        )
                        result["skipped"] += 1
                        continue

                # Create trade record
                trade = Trade(
                    user_id=user.id,
                    account_id=account.id,
                    symbol=investment.symbol,
                    investment_amount=Decimal(str(investment.amount)),
                    is_fractional=True,
                    order_type="MARKET",
                    side="BUY",
                    status=TradeStatus.PENDING,
                    source="RECURRING",
                    metadata={
                        "recurring_investment_id": investment.id,
                        "frequency": investment.frequency,
                    },
                )

                db.add(trade)
                db.flush()  # Get the ID without committing

                # Update the recurring investment with new execution date
                if investment.frequency == "DAILY":
                    next_date = process_date + timedelta(days=1)
                elif investment.frequency == "WEEKLY":
                    next_date = process_date + timedelta(weeks=1)
                elif investment.frequency == "MONTHLY":
                    # Add a month (approximately)
                    next_date = process_date.replace(
                        month=process_date.month + 1 if process_date.month < 12 else 1,
                        year=process_date.year
                        if process_date.month < 12
                        else process_date.year + 1,
                    )
                elif investment.frequency == "BIWEEKLY":
                    next_date = process_date + timedelta(weeks=2)
                else:
                    # Default to monthly
                    next_date = process_date + timedelta(days=30)

                investment.last_execution_date = process_date
                investment.next_execution_date = next_date
                investment.execution_count += 1

                # Log successful processing
                logger.info(
                    f"Created trade {trade.id} for recurring investment {investment.id}: "
                    f"{investment.symbol} ${investment.amount:.2f}"
                )

                result["succeeded"] += 1
                result["trades_created"] += 1

                # Submit trade for execution (async)
                submit_trade_for_execution.delay(trade.id)

            except Exception as e:
                logger.error(
                    f"Error processing recurring investment {investment.id}: {e}"
                )
                result["failed"] += 1
                result["failures"].append(
                    {
                        "investment_id": investment.id,
                        "symbol": investment.symbol,
                        "amount": float(investment.amount),
                        "error": str(e),
                    }
                )

                # Record metrics
                metrics.increment(
                    "recurring_investment.error",
                    labels={
                        "symbol": investment.symbol,
                        "frequency": investment.frequency,
                    },
                )

        # Commit all changes
        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error in recurring investment processing: {e}")
        raise TaskQueueError(f"Recurring investment processing failed: {e}")
    finally:
        db.close()

    # Calculate execution time
    execution_time = time.time() - start_time
    result["execution_time"] = execution_time

    # Log summary
    logger.info(
        f"Recurring investment processing completed in {execution_time:.2f}s: "
        f"Processed {result['processed']}, succeeded {result['succeeded']}, "
        f"failed {result['failed']}, skipped {result['skipped']}"
    )

    # Record metrics
    metrics.gauge("recurring_investment.processed", result["processed"])
    metrics.gauge("recurring_investment.succeeded", result["succeeded"])
    metrics.gauge("recurring_investment.failed", result["failed"])
    metrics.gauge("recurring_investment.skipped", result["skipped"])
    metrics.gauge("recurring_investment.trades_created", result["trades_created"])

    return result


@task(max_retries=5, retry_backoff=True, queue="high_priority")
def submit_trade_for_execution(self, trade_id: int) -> Dict[str, Any]:
    """Submit a trade for execution through the appropriate broker.

    This task handles the actual submission of trade orders to the broker API,
    with error handling and retry logic for transient errors.

    Args:
        trade_id: ID of the trade to execute

    Returns:
        Details of trade execution
    """
    logger.info(f"Submitting trade {trade_id} for execution")
    start_time = time.time()

    db = next(get_db())
    result = {"trade_id": trade_id, "status": "unknown", "broker_order_id": None}

    try:
        # Get the trade record
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise TaskQueueError(f"Trade {trade_id} not found")

        # Check if already executed or cancelled
        if trade.status in [
            TradeStatus.FILLED,
            TradeStatus.CANCELED,
            TradeStatus.REJECTED,
        ]:
            logger.warning(
                f"Trade {trade_id} already in terminal state: {trade.status}"
            )
            return {
                "trade_id": trade_id,
                "status": trade.status,
                "message": "Trade already in terminal state",
                "broker_order_id": trade.broker_order_id,
            }

        # Get the broker service
        from app.services.broker.factory import get_resilient_broker

        broker = get_resilient_broker(db=db)

        # Execute the trade
        execution_result = broker.execute_trade(trade)

        # Update trade with broker information
        trade.broker_order_id = execution_result.get("broker_order_id")
        trade.status = execution_result.get("status", TradeStatus.PENDING)
        trade.submitted_at = datetime.utcnow()
        trade.metadata = {
            **(trade.metadata or {}),
            "broker_response": execution_result.get("broker_response"),
        }

        # Save changes
        db.commit()

        result["status"] = trade.status
        result["broker_order_id"] = trade.broker_order_id

        # Schedule trade status check
        schedule_trade_status_check(trade_id)

        # Log successful submission
        logger.info(
            f"Trade {trade_id} submitted successfully: "
            f"broker_order_id={trade.broker_order_id}, status={trade.status}"
        )

        # Record metrics
        metrics.increment(
            "trade.submitted",
            labels={
                "symbol": trade.symbol,
                "side": trade.side,
                "source": trade.source or "manual",
            },
        )

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting trade {trade_id}: {e}")

        # Record metrics
        metrics.increment("trade.submission_error", labels={"trade_id": str(trade_id)})

        # Update trade status to error if it's a permanent failure
        if not self.request.retries:
            try:
                trade = db.query(Trade).filter(Trade.id == trade_id).first()
                if trade and trade.status not in [
                    TradeStatus.FILLED,
                    TradeStatus.CANCELED,
                    TradeStatus.REJECTED,
                ]:
                    trade.status = TradeStatus.REJECTED
                    trade.metadata = {
                        **(trade.metadata or {}),
                        "error": str(e),
                        "final_retry": True,
                    }
                    db.commit()

                    # Send alert about failed trade
                    alert_manager.send_alert(
                        f"Trade Execution Failed: {trade.symbol}",
                        f"Trade {trade_id} for {trade.symbol} failed after {self.request.retries} retries: {e}",
                        level="error",
                    )
            except Exception as update_e:
                logger.error(
                    f"Error updating trade {trade_id} status after failure: {update_e}"
                )

        # Raise for retry
        raise TaskQueueError(f"Trade submission failed: {e}", task_id=str(trade_id))

    finally:
        db.close()

        # Calculate execution time
        execution_time = time.time() - start_time
        result["execution_time"] = execution_time


def schedule_trade_status_check(trade_id: int) -> None:
    """Schedule a series of status checks for a trade.

    This function creates multiple delayed tasks to check the status
    of a trade at increasing intervals.

    Args:
        trade_id: ID of the trade to check
    """
    # Schedule immediate check (5 seconds)
    check_trade_status.apply_async(args=[trade_id], countdown=5)

    # Schedule short-term check (30 seconds)
    check_trade_status.apply_async(args=[trade_id], countdown=30)

    # Schedule medium-term check (2 minutes)
    check_trade_status.apply_async(args=[trade_id], countdown=120)

    # Schedule long-term check (10 minutes)
    check_trade_status.apply_async(args=[trade_id], countdown=600)


@task(max_retries=3, queue="normal_priority")
def check_trade_status(self, trade_id: int) -> Dict[str, Any]:
    """Check the status of a previously submitted trade.

    This task queries the broker API to get the current status of a trade
    and updates the local database record.

    Args:
        trade_id: ID of the trade to check

    Returns:
        Current status of the trade
    """
    logger.info(f"Checking status for trade {trade_id}")

    db = next(get_db())
    result = {
        "trade_id": trade_id,
        "current_status": None,
        "previous_status": None,
        "updated": False,
    }

    try:
        # Get the trade record
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise TaskQueueError(f"Trade {trade_id} not found")

        # Capture previous status
        result["previous_status"] = trade.status

        # Check if already in a terminal state
        if trade.status in [
            TradeStatus.FILLED,
            TradeStatus.CANCELED,
            TradeStatus.REJECTED,
        ]:
            logger.info(
                f"Trade {trade_id} already in terminal state: {trade.status}, no update needed"
            )
            result["current_status"] = trade.status
            return result

        # Check if broker_order_id exists
        if not trade.broker_order_id:
            logger.warning(
                f"Trade {trade_id} has no broker_order_id, cannot check status"
            )
            return result

        # Get the broker service
        from app.services.broker.factory import get_resilient_broker

        broker = get_resilient_broker(db=db)

        # Check trade status
        status_result = broker.get_trade_status(trade.broker_order_id)

        # Update trade status
        if status_result["status"] != trade.status:
            trade.status = status_result["status"]
            trade.updated_at = datetime.utcnow()

            # Update filled details if available
            if "filled_quantity" in status_result and status_result["filled_quantity"]:
                trade.filled_quantity = status_result["filled_quantity"]

            if "filled_price" in status_result and status_result["filled_price"]:
                trade.filled_price = status_result["filled_price"]

            if "filled_at" in status_result and status_result["filled_at"]:
                trade.filled_at = status_result["filled_at"]

            # Update metadata
            trade.metadata = {
                **(trade.metadata or {}),
                "status_updates": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "previous_status": result["previous_status"],
                        "new_status": trade.status,
                        "broker_response": status_result.get("broker_response"),
                    }
                ],
            }

            # Save changes
            db.commit()
            result["updated"] = True

            # Log status change
            logger.info(
                f"Trade {trade_id} status updated: {result['previous_status']} -> {trade.status}"
            )

            # Record metrics
            metrics.increment(
                "trade.status_change",
                labels={
                    "symbol": trade.symbol,
                    "previous_status": result["previous_status"],
                    "new_status": trade.status,
                },
            )

            # If filled, trigger post-execution processing
            if trade.status == TradeStatus.FILLED:
                process_filled_trade.delay(trade_id)

        result["current_status"] = trade.status
        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Error checking status for trade {trade_id}: {e}")

        # Record metrics
        metrics.increment("trade.status_check_error", labels={"trade_id": str(trade_id)})

        # Raise for retry if not the final attempt
        if self.request.retries < self.max_retries:
            raise TaskQueueError(
                f"Trade status check failed: {e}", task_id=str(trade_id)
            )
        else:
            # On final attempt, log but don't raise to avoid retrying
            logger.warning(
                f"Final attempt to check trade {trade_id} status failed: {e}"
            )
            return {"trade_id": trade_id, "error": str(e), "updated": False}

    finally:
        db.close()


@task(queue="normal_priority")
def process_filled_trade(self, trade_id: int) -> Dict[str, Any]:
    """Process a filled trade and update portfolio positions.

    This task handles the post-execution processing of a successful trade,
    updating portfolio positions and triggering any necessary notifications.

    Args:
        trade_id: ID of the filled trade to process

    Returns:
        Results of trade processing
    """
    logger.info(f"Processing filled trade {trade_id}")

    db = next(get_db())
    result = {"trade_id": trade_id, "portfolio_updated": False, "notifications_sent": 0}

    try:
        # Get the trade record
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise TaskQueueError(f"Trade {trade_id} not found")

        # Verify trade is filled
        if trade.status != TradeStatus.FILLED:
            logger.warning(
                f"Trade {trade_id} not filled (status: {trade.status}), skipping processing"
            )
            return result

        # Update portfolio position
        from app.services.portfolio import update_portfolio_position

        position_result = update_portfolio_position(db, trade)
        result["portfolio_updated"] = position_result["updated"]
        result["position_id"] = position_result.get("position_id")

        # Send trade executed notification
        from app.services.notifications import send_notification

        notification = send_notification(
            db,
            user_id=trade.user_id,
            notification_type="TRADE_EXECUTED",
            title=f"Trade Executed: {trade.symbol}",
            message=(
                f"Your {trade.side} order for {trade.symbol} has been executed. "
                f"Filled {trade.filled_quantity} shares at ${float(trade.filled_price):.2f} per share."
            ),
            data={
                "trade_id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "filled_quantity": float(trade.filled_quantity),
                "filled_price": float(trade.filled_price),
                "total_value": float(trade.filled_quantity * trade.filled_price),
            },
        )

        if notification:
            result["notifications_sent"] += 1

        # Log successful processing
        logger.info(
            f"Successfully processed filled trade {trade_id} for {trade.symbol}"
        )

        # Record metrics
        metrics.increment(
            "trade.processed",
            labels={
                "symbol": trade.symbol,
                "side": trade.side,
                "source": trade.source or "manual",
            },
        )

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing filled trade {trade_id}: {e}")

        # Record metrics
        metrics.increment("trade.processing_error", labels={"trade_id": str(trade_id)})

        # Raise error
        raise TaskQueueError(f"Trade processing failed: {e}", task_id=str(trade_id))

    finally:
        db.close()
