from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from app.db.base import Base


class NotificationType(enum.Enum):
    """Types of notifications for users."""

    TRADE_REQUEST = "trade_request"
    TRADE_EXECUTED = "trade_executed"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    LOGIN = "login"
    SETTINGS_CHANGE = "settings_change"
    REQUEST = "request"
    TRADE_APPROVED = "trade_approved"
    TRADE_REJECTED = "trade_rejected"
    NEW_RECOMMENDATION = "new_recommendation"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    ACCOUNT_LINKED = "account_linked"
    SECURITY_ALERT = "security_alert"


class Notification(Base):
    """Notification model for storing user notifications."""

    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    requires_action = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    # Optional trade-related fields
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    trade_id = Column(String, ForeignKey("trades.id"), nullable=True)

    def __repr__(self):
        return f"<Notification(id='{self.id}', user_id={self.user_id}, type='{self.type}', is_read={self.is_read})>"
