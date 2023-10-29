import time
import uasyncio as asyncio

def gen():
    while True:
        yield from range(5)
        yield from range(5,0,-1)
        return "hop"



for i in gen():
    print(i)


async def big_loop(n):
    for i in range(n):
        print(i)
        await asyncio.sleep(1)

async def test():
    asyncio.create_task(big_loop(5))
    print("*******")
    while True:
        await asyncio.sleep(1)
        print('----')


async def get_val2(x):
    await asyncio.sleep(1)
    print(f"{x}?")
    await asyncio.sleep(1)
    print(f"{x}??")
    await asyncio.sleep(1)
    print(f"{x}??")
    await asyncio.sleep(1)
    return x

async def get_val(x):
    return await get_val2(x)

async def test():
    a= await get_val(42)
    b= await get_val(3)
    print(f"a={a},b={b}")
    #print(f"a={await get_val(42)}, b={await get_val(3)}")

asyncio.run(test())



'''

async def blink(led, period_ms):
    while True:
        led.on()
        await asyncio.sleep_ms(10)
        led.off()
        await asyncio.sleep_ms(period_ms)

async def main(led1, led2):
    asyncio.create_task(blink(led1, 400))
    asyncio.create_task(blink(led2, 230))
    await asyncio.sleep_ms(10_000)


from machine import Pin
l1=Pin(16, Pin.OUT)
l2=Pin(17,Pin.OUT)

detect = Pin(15, Pin.IN)
detect.irq(lambda pin:asyncio.run(main(l1, l2)), Pin.IRQ_RISING)
'''