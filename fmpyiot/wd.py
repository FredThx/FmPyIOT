from machine import Timer
import machine
import time


class WDT:
    """A soft Watchdog
    """

    def __init__(self, timeout = 10):
        """timeout      :   secondes
        """
        self.timeout = timeout
        self.timer = Timer(-1)
        self.time_timer_start = None

    def enable(self):
        """Enable the watchdog
        """
        self.timer.init(mode = Timer.ONE_SHOT, period = self.timeout*1000, callback =self.reset)
        self.time_timer_start = time.time()

    def reset(self, tim):
        print("Watchdog timeout : machine reset!")
        machine.reset()
    
    def feed(self):
        print("Watchodg feeded.")
        self.timer.deinit()
        self.enable()

    def disable(self):
        self.timer.deinit()
        self.time_timer_start = None
    
    def time_left(self):
        if self.time_timer_start:
            return self.time_timer_start + self.timeout - time.time()

    def __repr__(self):
        return f"WDT({self.timeout} seconds). Time left : {self.time_left()}"