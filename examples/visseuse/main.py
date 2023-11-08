from machine import Pin



proxi = Pin(17, Pin.IN)
led = Pin(16,Pin.OUT)
led_verte = Pin(12, Pin.OUT)
relais = Pin(14,Pin.OUT)
buzzer = Pin(15, Pin.OUT)
bt_reset = Pin(13,Pin.IN)


def on_pin_change(pin):
    print(pin)
    if pin == bt_reset:
        led.off()
        relais.off()
        buzzer.off()
    else:
        led.on()
        relais.on()
        buzzer.on()

proxi.irq(
    on_pin_change,
    Pin.IRQ_FALLING
    )

bt_reset.irq(
    on_pin_change,
    Pin.IRQ_FALLING
    )
