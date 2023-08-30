import asyncio
import aiomqtt


async def listen():
    async with aiomqtt.Client("test.mosquitto.org") as client:
        async with client.messages() as messages:
            await client.subscribe("temperature/#")
            async for message in messages:
                print(message.payload)


async def main():
    loop = asyncio.get_event_loop()
    # Listen for MQTT messages in (unawaited) asyncio task
    task = loop.create_task(listen())
    # Do something else for a while
    await asyncio.sleep(5)
    # Cancel the task
    task.cancel()
    # Wait for the task to be cancelled
    try:
        await task
    except asyncio.CancelledError:
        pass


asyncio.run(main())