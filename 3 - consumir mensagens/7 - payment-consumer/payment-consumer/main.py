import asyncio
import os

from dotenv import load_dotenv

from consumer import Consumer

load_dotenv()


async def main():
    print("Starting payment-consumer!")
    server = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    topic = os.getenv("KAFKA_CHECKOUT_TOPIC")
    group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID")

    consumer = Consumer(servers=server, group_id=group_id, topic=topic)

    try:
        await consumer.run()
    except Exception as e:
        print("Error in consumer run:", e)


if __name__ == "__main__":
    asyncio.run(main())
