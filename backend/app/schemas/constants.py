# User Roles
ROLE_ADMIN = "admin"
ROLE_OWNER = "owner"
ROLE_CUSTOMER = "customer"

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

# Notification types — Feat8-FR1, Feat8-FR2
NOTIF_ORDER_CREATED = "ORDER_CREATED"
NOTIF_ORDER_STATUS_CHANGED = "ORDER_STATUS_CHANGED"
NOTIF_PAYMENT_STATUS_CHANGED = "PAYMENT_STATUS_CHANGED"

VALID_NOTIFICATION_TYPES = [
    NOTIF_ORDER_CREATED,
    NOTIF_ORDER_STATUS_CHANGED,
    NOTIF_PAYMENT_STATUS_CHANGED,
]

# Review tags — Feat9-FR1
REVIEW_TAGS_FOOD = ["Delicious", "Just okay", "Disappointing"]
REVIEW_TAGS_DELIVERY = ["Fast delivery", "On time", "Late delivery"]
REVIEW_TAGS_VALUE = ["Great value", "Overpriced"]

VALID_REVIEW_TAGS = REVIEW_TAGS_FOOD + REVIEW_TAGS_DELIVERY + REVIEW_TAGS_VALUE

# Order must be Delivered before a review can be submitted — Feat9-FR2
REVIEW_REQUIRED_ORDER_STATUS = "Delivered"
