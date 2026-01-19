import asyncio
import json

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from checkout_message import CheckoutMessage


class Consumer:
    def __init__(self, servers: str, group_id: str, topic: str):
        self.servers = servers
        self.group_id = group_id
        self.topic = topic
        self.topic_dead_letter = f"{topic}-dead-letter"
        self.consumer = None
        self.producer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.servers,
            group_id=self.group_id,
            auto_offset_reset="latest",
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()

        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.servers,
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )

        await self.producer.start()

        print("Consumer started and listening to topic:", self.topic)

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            print("Consumer stopped.")

        if self.producer:
            await self.producer.stop()
            print("Producer stopped.")

    async def send_to_dead_letter(self, message, error: str):
        dead_letter_message = {
            "original_message": message,
            "error": error,
        }
        await self.producer.send_and_wait(self.topic_dead_letter, dead_letter_message)
        print("Sent message to dead-letter topic:", self.topic_dead_letter)

    async def process_message(self, message: CheckoutMessage):
        # Placeholder for message processing logic
        print("Processing message:", message)

    async def consume(self):
        async for msg in self.consumer:
            try:
                success = False
                last_error = None
                for attempt in range(3):
                    try:
                        checkout_message = CheckoutMessage(**msg.value)
                        await self.process_message(checkout_message)
                        await self.consumer.commit()
                        success = True
                        break
                    except Exception as e:
                        await asyncio.sleep(2 * attempt)  # Exponential backoff
                        last_error = e
                        print(f"Error processing message, attempt {attempt + 1}: {e}")
                if not success:
                    print("Failed to process message after 3 attempts:", msg.value)
                    await self.send_to_dead_letter(msg.value, str(last_error))
                    await self.consumer.commit()
            except Exception as e:
                print("Error while consuming messages:", e)

    async def run(self):
        await self.start()
        try:
            await self.consume()
        finally:
            await self.stop()
