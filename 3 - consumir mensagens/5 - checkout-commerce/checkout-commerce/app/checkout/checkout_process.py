from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.checkout.checkout_model import Checkout, CheckoutStatus
from app.checkout.checkout_request import CheckoutRequest
from app.infra.database import get_db
from app.infra.kafka_manager import KafkaClient, get_kafka_client


async def checkout_process(
    checkout_request: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    kafka_client: KafkaClient = Depends(get_kafka_client),
):
    checkout = Checkout(
        customer_email=checkout_request.customer_email,
        total_amount=sum(item.price for item in checkout_request.items),
        status=CheckoutStatus.PENDING.value,
    )
    db.add(checkout)
    await db.commit()
    await db.refresh(checkout)

    body = {
        "checkout_id": checkout.id,
        "customer_email": checkout.customer_email,
        "total_amount": checkout.total_amount,
        "payment_method": checkout_request.payment_method.model_dump(),
    }

    await kafka_client.publish(
        topic="checkout.created",
        value=body,
        key=str(checkout.id),
    )

    return {"checkout_id": checkout.id, "status": checkout.status}
