import enum


class QuotationStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"


class ArtworkStatus(str, enum.Enum):
    not_provided = "not_provided"
    approved = "approved"
    needs_revision = "needs_revision"


class DeliveryMethod(str, enum.Enum):
    pickup = "pickup"
    delivery = "delivery"