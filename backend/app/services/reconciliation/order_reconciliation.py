"""Order Reconciliation Service.

This module handles the reconciliation of order status between the application
database and the broker's records, ensuring consistency and proper tracking
of all trades.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.alerts_manager import alert_manager
from app.core.metrics import metrics
from app.models.holding import Position
from app.models.portfolio import Portfolio
from app.models.trade import Trade, TradeStatus
from app.services.broker.factory import BrokerType, get_resilient_broker
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class OrderReconciliationService:
    """
    Service for reconciling trade status between application database and broker.

    This service ensures that all trades have accurate status information
    by comparing local records with broker data and resolving discrepancies.
    """

    def __init__(
        self, db: Session, notification_service: Optional[NotificationService] = None
    ):
        """Initialize the reconciliation service."""
        self.db = db
        self.broker = get_resilient_broker(db)
        self.notification_service = notification_service or NotificationService(db)

        # Statistics
        self.reconciled_count = 0
        self.error_count = 0
        self.mismatch_count = 0
        self.updated_count = 0

    async def reconcile_recent_orders(self, hours: int = 24) -> Dict[str, Any]:
        """
        Reconcile all orders from the last specified hours.

        Args:
            hours: Number of hours to look back for orders

        Returns:
            Dictionary with reconciliation results
        """
        start_time = datetime.utcnow()
        cutoff_time = start_time - timedelta(hours=hours)

        # Find trades that need reconciliation
        trades_to_reconcile = (
            self.db.query(Trade)
            .filter(
                and_(
                    Trade.created_at >= cutoff_time,
                    or_(
                        # Orders that are in a non-terminal state
                        Trade.status.in_(
                            [TradeStatus.PENDING, TradeStatus.PARTIALLY_FILLED]
                        ),
                        # Orders that were executed recently
                        and_(
                            Trade.executed_at >= cutoff_time,
                            Trade.broker_order_id.isnot(None),
                        ),
                    ),
                )
            )
            .all()
        )

        logger.info(f"Found {len(trades_to_reconcile)} trades to reconcile")

        # Process trades in parallel
        reconciliation_tasks = [
            self.reconcile_single_order(trade) for trade in trades_to_reconcile
        ]

        results = await asyncio.gather(*reconciliation_tasks, return_exceptions=True)

        # Count errors
        for result in results:
            if isinstance(result, Exception):
                self.error_count += 1

        # Commit any pending changes
        self.db.commit()

        # Record metrics
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        metrics.timing("reconciliation.execution_time", elapsed_time * 1000)
        metrics.gauge("reconciliation.trade_count", len(trades_to_reconcile))
        metrics.gauge("reconciliation.error_count", self.error_count)
        metrics.gauge("reconciliation.mismatch_count", self.mismatch_count)
        metrics.gauge("reconciliation.updated_count", self.updated_count)

        return {
            "reconciled_count": self.reconciled_count,
            "error_count": self.error_count,
            "mismatch_count": self.mismatch_count,
            "updated_count": self.updated_count,
            "total_count": len(trades_to_reconcile),
            "execution_time_seconds": elapsed_time,
        }

    async def reconcile_single_order(self, trade: Trade) -> Dict[str, Any]:
        """
        Reconcile a single trade with broker data.

        Args:
            trade: Trade object to reconcile

        Returns:
            Dictionary with reconciliation results
        """
        try:
            # Skip trades without broker order ID
            if not trade.broker_order_id:
                logger.debug(
                    f"Skipping reconciliation for trade {trade.id} with no broker_order_id"
                )
                return {"status": "skipped", "reason": "no_broker_id"}

            # Get current status from broker
            broker_status = await self._get_broker_status(trade)

            # Increment counter
            self.reconciled_count += 1

            # Check if status matches
            if self._needs_status_update(trade, broker_status):
                self.mismatch_count += 1
                logger.info(
                    f"Status mismatch for trade {trade.id}: app={trade.status.value}, broker={broker_status['status']}"
                )

                # Update trade with broker information
                await self._update_trade_from_broker(trade, broker_status)
                self.updated_count += 1

                return {
                    "status": "updated",
                    "trade_id": trade.id,
                    "old_status": trade.status.value,
                    "new_status": broker_status["status"],
                }
            else:
                return {
                    "status": "matched",
                    "trade_id": trade.id,
                    "status": trade.status.value,
                }

        except Exception as e:
            logger.error(f"Error reconciling trade {trade.id}: {str(e)}", exc_info=True)
            metrics.increment("reconciliation.error")
            return {"status": "error", "trade_id": trade.id, "error": str(e)}

    async def _get_broker_status(self, trade: Trade) -> Dict[str, Any]:
        """
        Get the current status of a trade from the broker.

        Args:
            trade: Trade to check

        Returns:
            Dictionary with broker status information
        """
        try:
            # Use the resilient broker to get trade status
            status_info = self.broker.get_trade_status(trade.broker_order_id)

            # For filled orders, get detailed execution information
            if status_info.get("status") in [
                "filled",
                "FILLED",
                "executed",
                "EXECUTED",
            ]:
                execution_info = self.broker.get_trade_execution(trade.broker_order_id)
                status_info.update(execution_info)

            return status_info

        except Exception as e:
            logger.error(f"Error getting broker status for trade {trade.id}: {str(e)}")
            metrics.increment("reconciliation.broker_status_error")
            raise

    def _needs_status_update(self, trade: Trade, broker_status: Dict[str, Any]) -> bool:
        """
        Determine if a trade needs status update based on broker data.

        Args:
            trade: Trade to check
            broker_status: Status information from broker

        Returns:
            True if update is needed, False otherwise
        """
        # Map broker status to application status
        broker_app_status = self._map_broker_status_to_app_status(
            broker_status.get("status")
        )

        # Check for status mismatch
        if broker_app_status != trade.status:
            return True

        # For filled orders, check fill details
        if broker_app_status == TradeStatus.FILLED:
            # Check if filled quantity or price differs
            broker_filled_qty = broker_status.get("filled_quantity")
            broker_avg_price = broker_status.get("filled_price")

            if (
                broker_filled_qty
                and abs(float(broker_filled_qty) - float(trade.filled_quantity or 0))
                > 0.0001
            ):
                return True

            if (
                broker_avg_price
                and abs(float(broker_avg_price) - float(trade.average_price or 0))
                > 0.0001
            ):
                return True

        return False

    def _map_broker_status_to_app_status(self, broker_status: str) -> TradeStatus:
        """
        Map broker-specific status to application status.

        Args:
            broker_status: Status string from broker

        Returns:
            Corresponding TradeStatus enum value
        """
        if not broker_status:
            return TradeStatus.PENDING

        status_lower = broker_status.lower()

        # Map common broker status terms to our application statuses
        if (
            "filled" in status_lower
            or "executed" in status_lower
            or "completed" in status_lower
        ):
            return TradeStatus.FILLED
        elif "partial" in status_lower:
            return TradeStatus.PARTIALLY_FILLED
        elif "cancel" in status_lower:
            return TradeStatus.CANCELLED
        elif "reject" in status_lower:
            return TradeStatus.REJECTED
        elif (
            "pending" in status_lower or "open" in status_lower or "new" in status_lower
        ):
            return TradeStatus.PENDING
        elif "expire" in status_lower:
            return TradeStatus.EXPIRED
        else:
            logger.warning(
                f"Unknown broker status: {broker_status}, defaulting to PENDING"
            )
            return TradeStatus.PENDING

    async def _update_trade_from_broker(
        self, trade: Trade, broker_status: Dict[str, Any]
    ) -> None:
        """
        Update trade with information from broker.

        Args:
            trade: Trade to update
            broker_status: Status information from broker
        """
        # Previous status for change detection
        previous_status = trade.status

        # Update status
        new_status = self._map_broker_status_to_app_status(broker_status.get("status"))
        trade.status = new_status

        # If now filled, update fill details
        if new_status in [TradeStatus.FILLED, TradeStatus.PARTIALLY_FILLED]:
            if "filled_quantity" in broker_status and broker_status["filled_quantity"]:
                trade.filled_quantity = broker_status["filled_quantity"]

            if "filled_price" in broker_status and broker_status["filled_price"]:
                trade.average_price = broker_status["filled_price"]

            if "commission" in broker_status and broker_status["commission"]:
                trade.commission = broker_status["commission"]

            if "settlement_date" in broker_status and broker_status["settlement_date"]:
                trade.settlement_date = broker_status["settlement_date"]

            # If newly filled, set execution time
            if (
                previous_status != TradeStatus.FILLED
                and new_status == TradeStatus.FILLED
            ):
                trade.executed_at = datetime.utcnow()

                # Update portfolio as well
                await self._update_portfolio_for_filled_trade(trade)

        # Always update broker status and last update time
        trade.broker_status = broker_status.get("status")
        trade.updated_at = datetime.utcnow()

        # Save changes
        self.db.add(trade)

        # If status changed to a terminal state, send notifications
        if previous_status != new_status and new_status in [
            TradeStatus.FILLED,
            TradeStatus.CANCELLED,
            TradeStatus.REJECTED,
            TradeStatus.EXPIRED,
        ]:
            await self._send_status_notification(trade, previous_status)

    async def _update_portfolio_for_filled_trade(self, trade: Trade) -> None:
        """
        Update portfolio positions and cash for a newly filled trade.

        Args:
            trade: Filled trade to process
        """
        # Get portfolio
        portfolio = self.db.query(Portfolio).get(trade.portfolio_id)
        if not portfolio:
            logger.error(
                f"Portfolio {trade.portfolio_id} for trade {trade.id} not found"
            )
            return

        # Process based on trade type
        if trade.trade_type == "buy":
            # Find or create position
            position = (
                self.db.query(Position)
                .filter(
                    Position.portfolio_id == portfolio.id,
                    Position.symbol == trade.symbol,
                )
                .first()
            )

            if not position:
                # Create new position
                position = Position(
                    portfolio_id=portfolio.id,
                    symbol=trade.symbol,
                    quantity=trade.filled_quantity,
                    average_price=trade.average_price,
                    current_price=trade.average_price,
                    is_fractional=trade.is_fractional,
                )
                self.db.add(position)
            else:
                # Update existing position
                total_value = float(position.quantity) * float(position.average_price)
                new_value = float(trade.filled_quantity) * float(trade.average_price)
                position.quantity += trade.filled_quantity

                # Recalculate average price
                if position.quantity > 0:
                    position.average_price = (total_value + new_value) / float(
                        position.quantity
                    )

                position.current_price = trade.average_price
                position.is_fractional = position.is_fractional or trade.is_fractional
                self.db.add(position)

            # Update cash balance (deduct cost)
            total_cost = float(trade.filled_quantity) * float(trade.average_price)
            commission = float(trade.commission or 0)
            portfolio.cash_balance -= total_cost + commission

        elif trade.trade_type == "sell":
            # Find position
            position = (
                self.db.query(Position)
                .filter(
                    Position.portfolio_id == portfolio.id,
                    Position.symbol == trade.symbol,
                )
                .first()
            )

            if position:
                # Update position quantity
                position.quantity -= trade.filled_quantity
                position.current_price = trade.average_price

                # If quantity is zero or negative, remove position
                if position.quantity <= 0:
                    self.db.delete(position)
                else:
                    self.db.add(position)
            else:
                logger.warning(
                    f"Position for {trade.symbol} not found when processing sell trade {trade.id}"
                )

            # Update cash balance (add proceeds)
            total_proceeds = float(trade.filled_quantity) * float(trade.average_price)
            commission = float(trade.commission or 0)
            portfolio.cash_balance += total_proceeds - commission

        # Save portfolio changes
        self.db.add(portfolio)

    async def _send_status_notification(
        self, trade: Trade, previous_status: TradeStatus
    ) -> None:
        """
        Send notification about trade status change.

        Args:
            trade: Trade with updated status
            previous_status: Previous status before update
        """
        # Build notification message
        if trade.status == TradeStatus.FILLED:
            # For filled trades
            message = f"Trade {trade.id} for {trade.quantity} {trade.symbol} has been filled at ${trade.average_price}"
            notification_type = "trade_filled"
        elif trade.status == TradeStatus.CANCELLED:
            message = f"Trade {trade.id} for {trade.symbol} has been cancelled"
            notification_type = "trade_cancelled"
        elif trade.status == TradeStatus.REJECTED:
            message = f"Trade {trade.id} for {trade.symbol} has been rejected"
            notification_type = "trade_rejected"
        else:
            message = f"Trade {trade.id} for {trade.symbol} status changed from {previous_status.value} to {trade.status.value}"
            notification_type = "trade_status_change"

        # Send notification
        await self.notification_service.send_notification(
            user_id=trade.user_id,
            message=message,
            notification_type=notification_type,
            data={"trade_id": trade.id, "status": trade.status.value},
        )

    async def reconcile_all_active_positions(self) -> Dict[str, Any]:
        """
        Reconcile all active positions with broker data.

        This performs a deeper reconciliation by checking all positions
        against broker records to ensure consistency.

        Returns:
            Dictionary with reconciliation results
        """
        start_time = datetime.utcnow()
        positions_reconciled = 0
        positions_updated = 0
        errors = 0

        # Get all portfolios
        portfolios = self.db.query(Portfolio).all()

        for portfolio in portfolios:
            try:
                # Get account from broker (using first linked account)
                account_id = portfolio.account_id
                if not account_id:
                    continue

                # Get positions from broker
                broker_positions = self.broker.get_positions(account_id)

                # Get positions from database
                db_positions = (
                    self.db.query(Position)
                    .filter(Position.portfolio_id == portfolio.id)
                    .all()
                )

                # Reconcile positions
                result = await self._reconcile_portfolio_positions(
                    portfolio, db_positions, broker_positions
                )

                positions_reconciled += result["reconciled"]
                positions_updated += result["updated"]
                errors += result["errors"]

            except Exception as e:
                logger.error(f"Error reconciling portfolio {portfolio.id}: {str(e)}")
                errors += 1

        # Commit changes
        self.db.commit()

        # Calculate metrics
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        metrics.timing("reconciliation.positions.execution_time", elapsed_time * 1000)
        metrics.gauge("reconciliation.positions.count", positions_reconciled)
        metrics.gauge("reconciliation.positions.updated", positions_updated)
        metrics.gauge("reconciliation.positions.errors", errors)

        return {
            "positions_reconciled": positions_reconciled,
            "positions_updated": positions_updated,
            "errors": errors,
            "execution_time_seconds": elapsed_time,
        }

    async def _reconcile_portfolio_positions(
        self,
        portfolio: Portfolio,
        db_positions: List[Position],
        broker_positions: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """
        Reconcile portfolio positions with broker data.

        Args:
            portfolio: Portfolio to reconcile
            db_positions: Database positions
            broker_positions: Broker positions

        Returns:
            Dictionary with reconciliation counts
        """
        reconciled = 0
        updated = 0
        errors = 0

        # Build lookup by symbol
        db_positions_map = {p.symbol: p for p in db_positions}
        broker_positions_map = {p["symbol"]: p for p in broker_positions}

        # Set of all symbols for iteration
        all_symbols = set(db_positions_map.keys()) | set(broker_positions_map.keys())

        for symbol in all_symbols:
            try:
                reconciled += 1

                db_position = db_positions_map.get(symbol)
                broker_position = broker_positions_map.get(symbol)

                # Case 1: Position in both DB and broker
                if db_position and broker_position:
                    if self._position_needs_update(db_position, broker_position):
                        self._update_position_from_broker(db_position, broker_position)
                        updated += 1

                # Case 2: Position in DB but not in broker
                elif db_position and not broker_position:
                    # This is unusual - either the position was closed or there's an issue
                    # Mark for review but don't automatically remove
                    logger.warning(
                        f"Position {symbol} found in DB but not in broker for portfolio {portfolio.id}"
                    )
                    alert_manager.send_alert(
                        "Position reconciliation issue",
                        f"Position {symbol} found in DB but not in broker for portfolio {portfolio.id}",
                        level="warning",
                    )

                # Case 3: Position in broker but not in DB
                elif broker_position and not db_position:
                    # Create missing position
                    new_position = Position(
                        portfolio_id=portfolio.id,
                        symbol=broker_position["symbol"],
                        quantity=broker_position["quantity"],
                        average_price=broker_position.get("average_price", 0),
                        current_price=broker_position.get("current_price", 0),
                        is_fractional=broker_position.get("quantity", 0) % 1 != 0,
                    )
                    self.db.add(new_position)
                    updated += 1
                    logger.info(
                        f"Created missing position {symbol} for portfolio {portfolio.id}"
                    )

            except Exception as e:
                logger.error(f"Error reconciling position {symbol}: {str(e)}")
                errors += 1

        return {"reconciled": reconciled, "updated": updated, "errors": errors}

    def _position_needs_update(
        self, db_position: Position, broker_position: Dict[str, Any]
    ) -> bool:
        """
        Check if position needs update based on broker data.

        Args:
            db_position: Database position
            broker_position: Broker position data

        Returns:
            True if update is needed, False otherwise
        """
        # Check quantity difference (with small tolerance for floating point comparison)
        quantity_diff = abs(
            float(db_position.quantity) - float(broker_position["quantity"])
        )
        if quantity_diff > 0.0001:
            return True

        # Check price difference if available (with 1% tolerance)
        if "current_price" in broker_position and broker_position["current_price"]:
            price_diff_pct = abs(
                float(db_position.current_price)
                - float(broker_position["current_price"])
            ) / float(broker_position["current_price"])
            if price_diff_pct > 0.01:  # 1% difference
                return True

        return False

    def _update_position_from_broker(
        self, db_position: Position, broker_position: Dict[str, Any]
    ) -> None:
        """
        Update database position with broker data.

        Args:
            db_position: Database position to update
            broker_position: Broker position data
        """
        # Update quantity
        db_position.quantity = broker_position["quantity"]

        # Update prices if available
        if "current_price" in broker_position and broker_position["current_price"]:
            db_position.current_price = broker_position["current_price"]

        if "average_price" in broker_position and broker_position["average_price"]:
            db_position.average_price = broker_position["average_price"]

        # Update fractional status
        if broker_position["quantity"] % 1 != 0:
            db_position.is_fractional = True

        # Save changes
        self.db.add(db_position)
