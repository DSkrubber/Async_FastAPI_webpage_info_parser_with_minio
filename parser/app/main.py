import asyncio

from aiokafka.errors import KafkaError

from .logger import get_logger
from .parser_utils import (
    get_consumer,
    get_producer,
    load_pictures,
    user_agent_cycle,
)

main_logger = get_logger(__name__)


async def parser_script() -> None:
    consumer = await get_consumer()
    producer = await get_producer()
    user_agents = user_agent_cycle()
    try:
        async for msg in consumer:
            main_logger.info(
                f"Consumed message from {msg.topic=} at {msg.timestamp=} UTC"
            )
            urls = msg.value.get("urls", ())
            tasks = [
                load_pictures(url, producer, next(user_agents)) for url in urls
            ]
            await asyncio.gather(*tasks)
    except KafkaError as error:
        main_logger.error(f"Kafka consumer error: ({error})")
    finally:
        await producer.stop()
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(parser_script())
