from enum import Enum


class PaymentTransactionStatus(Enum):
    NEEDS_REVIEW = "NEEDS_REVIEW"
    RESOLVED = "RESOLVED"