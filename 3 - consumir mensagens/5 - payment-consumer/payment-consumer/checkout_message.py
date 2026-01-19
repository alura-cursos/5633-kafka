from typing import Any, Dict

from pydantic import BaseModel


class CheckoutMessage(BaseModel):
    checkout_id: int
    customer_email: str
    total_amount: float
    payment_method: Dict[str, Any]
