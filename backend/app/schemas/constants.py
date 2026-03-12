# Payment Status
PAYMENT_STATUS_PENDING = "Pending"
PAYMENT_STATUS_SUCCESS = "Success"
PAYMENT_STATUS_FAILED = "Failed"

VALID_PAYMENT_STATUSES = [
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_SUCCESS,
    PAYMENT_STATUS_FAILED,
]

# Payment precondition
# Order must be Confirmed before payment can be initiated
# Feat7-FR1, Feat7-FR3
PAYMENT_REQUIRED_ORDER_STATUS = "Confirmed"
