from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json

from app.models.user import User, UserRole
from app.models.trade import Trade, TradeStatus
from app.models.notification import Notification, NotificationType
from app.models.account import Account, AccountType
from app.models.portfolio import Portfolio

# Setup logger
logger = logging.getLogger(__name__)

# Using the Enum from the notification model instead
# Note: We'll need to update references to this class throughout this file


class NotificationService:
    """
    Service for sending notifications to users through various channels
    """

    def __init__(
        self, db: Session, email_service=None, push_service=None, sms_service=None
    ):
        self.db = db
        self.email_service = email_service
        self.push_service = push_service
        self.sms_service = sms_service
        self.notification_preferences = {}  # This would be loaded from the database

    def send_trade_request_notification(self, trade: Trade) -> Notification:
        """
        Send a notification to a guardian when a minor requests a trade
        """
        if trade.status != TradeStatus.PENDING:
            return None

        # Get the minor user through portfolio relationship
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == trade.portfolio_id).first()
        )
        if not portfolio:
            logger.error(f"Portfolio not found for trade {trade.id}")
            return None

        minor = portfolio.owner
        if not minor or minor.role != UserRole.MINOR:
            logger.warning(
                f"Trade {trade.id} marked for approval but user is not a minor"
            )
            return None

        # Find the guardian using the custodial account relationship
        custodial_account = (
            self.db.query(Account)
            .filter(
                Account.user_id == minor.id,
                Account.account_type == AccountType.CUSTODIAL,
            )
            .first()
        )

        if not custodial_account:
            logger.error(f"No custodial account found for minor user {minor.id}")
            return None

        guardian = (
            self.db.query(User).filter(User.id == custodial_account.guardian_id).first()
        )
        if not guardian:
            logger.error(f"Guardian not found for minor user {minor.id}")
            return None

        # Create the notification content
        minor_name = minor.full_name.split()[0] if minor.full_name else "User"
        title = f"Trade Request from {minor_name}"
        message = f"{minor_name} wants to {trade.trade_type.value} {trade.quantity} shares of {trade.symbol} at ${trade.price:.2f}. Please review and approve or reject this trade."

        # Create the notification data
        notification_data = {
            "type": NotificationType.TRADE_REQUEST.value,
            "title": title,
            "message": message,
            "requires_action": True,
            "trade_id": trade.id,
            "data": {
                "symbol": trade.symbol,
                "quantity": trade.quantity,
                "price": trade.price,
                "trade_type": trade.trade_type.value,
                "minor_id": minor.id,
                "minor_name": minor.full_name,
                "minor_account_id": custodial_account.id,
            },
        }

        # Send through all enabled channels
        return self._send_notification(guardian, notification_data)

    def send_trade_status_notification(self, trade: Trade) -> Notification:
        """
        Send a notification about trade status changes
        """
        # Get the user through portfolio relationship
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == trade.portfolio_id).first()
        )
        if not portfolio:
            logger.error(f"Portfolio not found for trade {trade.id}")
            return None

        user = portfolio.owner
        if not user:
            logger.error(f"User not found for trade {trade.id}")
            return None

        # Handle different status notifications
        if trade.status == TradeStatus.FILLED:
            title = "Trade Executed"
            message = f"Your order to {trade.trade_type.value} {trade.quantity} shares of {trade.symbol} has been executed at ${trade.price:.2f}."
            notification_type = NotificationType.TRADE_EXECUTED.value
            requires_action = False
        elif trade.status == TradeStatus.REJECTED:
            title = "Trade Rejected"
            message = f"Your order to {trade.trade_type.value} {trade.quantity} shares of {trade.symbol} has been rejected."
            if trade.rejection_reason:
                message += f" Reason: {trade.rejection_reason}"
            notification_type = NotificationType.TRADE_REJECTED.value
            requires_action = False
        elif trade.status == TradeStatus.PENDING:
            title = "Trade Submitted"
            message = f"Your request to {trade.trade_type.value} {trade.quantity} shares of {trade.symbol} has been submitted and is pending execution."
            notification_type = NotificationType.TRADE_APPROVED.value
            requires_action = False
        else:
            # No notification for other statuses
            return None

        # Create notification data
        notification_data = {
            "type": notification_type,
            "title": title,
            "message": message,
            "requires_action": requires_action,
            "data": {
                "symbol": trade.symbol,
                "quantity": trade.quantity,
                "price": trade.price,
                "trade_type": trade.trade_type.value,
                "status": trade.status.value,
            },
            "trade_id": trade.id,
        }

        # Send through all enabled channels
        return self._send_notification(user, notification_data)

    def send_new_recommendations_notification(
        self, user_id: int, count: int = 0
    ) -> Notification:
        """
        Notify a user about new investment recommendations
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return None

        title = "New Investment Recommendations"
        message = f"We have {count} new investment recommendations for you based on your portfolio and market conditions."

        # Create the notification data
        notification_data = {
            "type": NotificationType.NEW_RECOMMENDATION.value,
            "title": title,
            "message": message,
            "requires_action": False,
            "data": {"count": count},
        }

        # Send through all enabled channels
        return self._send_notification(user, notification_data)

    def send_security_alert(
        self, user_id: int, alert_type: str, details: Dict[str, Any]
    ) -> Notification:
        """
        Send a security alert notification
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return None

        title = f"Security Alert: {alert_type}"
        message = f"We detected {alert_type.lower()} on your account. Please review your account activity."

        notification_data = {
            "type": NotificationType.SECURITY_ALERT.value,
            "title": title,
            "message": message,
            "requires_action": True,
            "data": {"alert_type": alert_type, **details},
        }

        # Security alerts should go through all channels
        return self._send_notification(user, notification_data)

    def send_portfolio_rebalance_notification(
        self, user_id: int, changes: List[Dict[str, Any]]
    ) -> Notification:
        """
        Send a notification about portfolio rebalancing
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return None

        title = "Portfolio Rebalanced"
        message = f"Your portfolio has been automatically rebalanced based on your investment strategy. {len(changes)} positions were adjusted."

        notification_data = {
            "type": NotificationType.PORTFOLIO_REBALANCE.value,
            "title": title,
            "message": message,
            "requires_action": False,
            "data": {"changes": changes, "change_count": len(changes)},
        }

        return self._send_notification(user, notification_data)

    def send_account_linked_notification(
        self, user_id: int, account_name: str, institution: str
    ) -> Notification:
        """
        Send a notification when a new account is linked
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return None

        title = "New Account Linked"
        message = f"Your {account_name} account from {institution} has been successfully linked to your Elson portfolio."

        notification_data = {
            "type": NotificationType.ACCOUNT_LINKED.value,
            "title": title,
            "message": message,
            "requires_action": False,
            "data": {"account_name": account_name, "institution": institution},
        }

        return self._send_notification(user, notification_data)

    def mark_notification_as_read(self, notification_id: str, user_id: int) -> bool:
        """
        Mark a specific notification as read
        """
        try:
            notification = (
                self.db.query(Notification)
                .filter(
                    Notification.id == notification_id, Notification.user_id == user_id
                )
                .first()
            )

            if not notification:
                logger.warning(
                    f"Notification {notification_id} not found for user {user_id}"
                )
                return False

            notification.is_read = True
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    def mark_all_notifications_as_read(self, user_id: int) -> bool:
        """
        Mark all notifications as read for a user
        """
        try:
            self.db.query(Notification).filter(
                Notification.user_id == user_id, ~Notification.is_read
            ).update({"is_read": True})

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False

    def get_unread_notifications_count(self, user_id: int) -> int:
        """
        Get the count of unread notifications for a user
        """
        try:
            count = (
                self.db.query(Notification)
                .filter(Notification.user_id == user_id, ~Notification.is_read)
                .count()
            )

            return count

        except Exception as e:
            logger.error(f"Error getting unread notifications count: {e}")
            return 0

    def get_user_notifications(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user with pagination
        """
        try:
            notifications = (
                self.db.query(Notification)
                .filter(Notification.user_id == user_id)
                .order_by(Notification.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return notifications

        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    def delete_notification(self, notification_id: str, user_id: int) -> bool:
        """
        Delete a specific notification
        """
        try:
            notification = (
                self.db.query(Notification)
                .filter(
                    Notification.id == notification_id, Notification.user_id == user_id
                )
                .first()
            )

            if not notification:
                logger.warning(
                    f"Notification {notification_id} not found for user {user_id}"
                )
                return False

            self.db.delete(notification)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            return False

    def update_notification_preferences(
        self, user_id: int, preferences: Dict[str, bool]
    ) -> bool:
        """
        Update user's notification preferences
        """
        try:
            # In a real implementation, this would update a user_preferences table
            # For now, we'll store it in memory
            self.notification_preferences[user_id] = preferences
            logger.info(
                f"Updated notification preferences for user {user_id}: {preferences}"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return False

    def get_notification_preferences(self, user_id: int) -> Dict[str, bool]:
        """
        Get user's notification preferences
        """
        return self.notification_preferences.get(
            user_id,
            {
                "email": True,
                "push": True,
                "sms": False,  # SMS disabled by default
                "in_app": True,
            },
        )

    def _send_notification(
        self, user: User, notification_data: Dict[str, Any]
    ) -> Notification:
        """
        Send a notification through all enabled channels for the user and save to database
        """
        try:
            # Create notification record in database
            notification = Notification(
                user_id=user.id,
                type=notification_data["type"],
                message=notification_data["message"],
                requires_action=notification_data.get("requires_action", False),
                is_read=False,
                data=notification_data.get("data", {}),
                trade_id=notification_data.get("trade_id"),
            )

            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)

            # Check user's notification preferences
            preferences = self.notification_preferences.get(user.id, {})

            # Send email if enabled
            if preferences.get("email", True) and self.email_service:
                self._send_email(user, notification_data)

            # Send push if enabled
            if preferences.get("push", True) and self.push_service:
                self._send_push(user, notification_data)

            # Send SMS if enabled (for critical notifications)
            if (
                preferences.get("sms", False)
                and self.sms_service
                and notification_data.get("requires_action", False)
            ):
                self._send_sms(user, notification_data)

            # For minors, also notify guardians about important events
            if user.role == UserRole.MINOR and notification.type in [
                NotificationType.TRADE_EXECUTED.value,
                NotificationType.SECURITY_ALERT.value,
            ]:
                self._notify_guardian_about_minor(user.id, notification_data)

            return notification

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return None

    def _send_email(self, user: User, notification_data: Dict[str, Any]) -> None:
        """
        Send an email notification
        """
        if not self.email_service:
            return

        try:
            # This would call your email service
            # self.email_service.send_email(
            #     to=user.email,
            #     subject=notification_data.get("title", "New Notification"),
            #     body=notification_data["message"]
            # )
            logger.info(
                f"Email notification sent to {user.email}: {notification_data.get('title', 'New Notification')}"
            )
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")

    def _send_push(self, user: User, notification_data: Dict[str, Any]) -> None:
        """
        Send a push notification
        """
        if not self.push_service:
            return

        try:
            # This would call your push notification service
            # self.push_service.send_push(
            #     user_id=user.id,
            #     title=notification_data.get("title", "New Notification"),
            #     body=notification_data["message"],
            #     data=notification_data.get("data", {})
            # )
            logger.info(
                f"Push notification sent to user {user.id}: {notification_data.get('title', 'New Notification')}"
            )
        except Exception as e:
            logger.error(f"Failed to send push notification to user {user.id}: {e}")

    def _send_sms(self, user: User, notification_data: Dict[str, Any]) -> None:
        """
        Send an SMS notification
        """
        if not self.sms_service:
            return

        try:
            # This would call your SMS service
            # self.sms_service.send_sms(
            #     to=user.phone_number,
            #     message=f"{notification_data.get('title', 'Alert')}: {notification_data['message']}"
            # )
            logger.info(
                f"SMS notification sent to user {user.id}: {notification_data.get('title', 'Alert')}"
            )
        except Exception as e:
            logger.error(f"Failed to send SMS notification to user {user.id}: {e}")

    def _notify_guardian_about_minor(
        self, minor_user_id: int, original_notification: Dict[str, Any]
    ) -> None:
        """
        Forward important notifications about a minor to their guardian
        """
        # Find the guardian for this minor using the custodial account relationship
        minor = self.db.query(User).filter(User.id == minor_user_id).first()
        if not minor:
            logger.error(f"Minor not found for user ID {minor_user_id}")
            return

        # Find the custodial account and guardian
        custodial_account = (
            self.db.query(Account)
            .filter(
                Account.user_id == minor_user_id,
                Account.account_type == AccountType.CUSTODIAL,
            )
            .first()
        )

        if not custodial_account:
            logger.error(f"No custodial account found for minor user {minor_user_id}")
            return

        guardian = (
            self.db.query(User).filter(User.id == custodial_account.guardian_id).first()
        )
        if not guardian:
            logger.error(f"Guardian not found for minor user {minor_user_id}")
            return

        # Create a modified notification data for the guardian
        minor_name = minor.full_name.split()[0] if minor.full_name else "User"
        title = f"{minor_name}'s Activity: {original_notification.get('title', 'Notification')}"
        message = (
            f"Activity on {minor_name}'s account: {original_notification['message']}"
        )

        guardian_notification = {
            "type": original_notification["type"],
            "title": title,
            "message": message,
            "requires_action": original_notification.get("requires_action", False),
            "data": {
                **(original_notification.get("data", {})),
                "minor_id": minor_user_id,
                "minor_name": minor.full_name,
                "minor_account_id": custodial_account.id,
            },
            "trade_id": original_notification.get("trade_id"),
        }

        # Send through all enabled channels
        self._send_notification(guardian, guardian_notification)
