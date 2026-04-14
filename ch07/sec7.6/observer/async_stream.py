"""
async_stream.py - Stage 3: Observer via asyncio

No subscribe() function.
No listeners list.
No notifyAll() loop.

The producer puts values into channels; consumers read with async for.
The runtime (asyncio event loop) handles scheduling and dispatch.

Run:  python3 async_stream.py
"""

import asyncio


# -- Producer
# Generates temperature readings. Knows nothing about who is listening.

async def temperature_sensor(channels):
    readings = [22.1, 22.3, 22.8, 23.5, 22.9, 22.6]
    for temp in readings:
        await asyncio.sleep(0.05)
        for ch in channels:
            await ch.put(temp)
    for ch in channels:
        await ch.put(None)              # sentinel: stream is done


# -- Consumers
# Each consumer owns a channel. No shared mutable listener list.

async def logger(channel):
    while True:
        temp = await channel.get()
        if temp is None:
            break
        print(f"  log:    {temp:.1f} °C")


async def alerter(channel):
    while True:
        temp = await channel.get()
        if temp is None:
            break
        if temp > 23.0:
            print(f"  ALERT:  {temp:.1f} °C exceeds threshold")


# -- Wiring
# The only place that knows about both producer and consumers.
# In a framework this disappears into the event bus configuration.

async def main():
    log_ch   = asyncio.Queue()
    alert_ch = asyncio.Queue()

    await asyncio.gather(
        temperature_sensor([log_ch, alert_ch]),
        logger(log_ch),
        alerter(alert_ch),
    )


asyncio.run(main())
