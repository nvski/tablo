import asyncio
import typing as tp


import apds9930
from .base import Tablo, Singleton


apds9930.APDS9930_IDs = [0x29, 0x39]
tablo = Tablo()


class BrightnessScheduler(Singleton):
    def __init__(self, rr=.05):
        self.rr=rr
        self.task = None
        # self.history = np.zeros((20,))
        self.current_brightness = None
        self._running = False
        self.sensor:tp.Optional[apds9930.APDS9930] = None
        self._mem = 100
        self._HS = 1.2  # hysteresis sensity, _HS <= 0.5 means no hysteresis

    def _init_sensor(self) -> None:
        self.sensor = apds9930.APDS9930(1)
        self.sensor.set_mode(apds9930.ALL, True)

    def get_new_brightness(self) -> int:
        if self.sensor is None:
            try:
                self._init_sensor()
            except: pass
        if self.sensor is not None:
            lux = self.sensor.ambient_light
            if lux < 0:
                lux = 1500
            brightness = self.lux_to_brightness(lux)
            if not self._mem - self._HS <= brightness <= self._mem + self._HS:
                self._mem = round(brightness)
            return self._mem

    def lux_to_brightness(self, lux:float) -> float:
        brightness = 3*lux**.6
        brightness = min(100, brightness)
        brightness = max(1, brightness)
        return brightness

    async def run(self):
        while self._running:
            try:
                new_brightness = self.get_new_brightness()
                if self.current_brightness != new_brightness:
                    self.current_brightness = new_brightness
                    tablo.update(new_brightness)
            except:
                try:
                    self._init_sensor()
                except:
                    pass
            await asyncio.sleep(self.rr)

    def start(self, *args, **kwargs):
        self._running = True
        self.task = asyncio.create_task(self.run(*args, **kwargs), name=self.__class__.__name__)
        return self

    def stop(self):
        self._running = False
