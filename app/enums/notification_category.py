from enum import Enum


class NotificationCategory(str, Enum):
    MAINTENANCE = "MAINTENANCE"
    PAYMENTS = "PAYMENTS"
    APPROVALS = "APPROVALS"
