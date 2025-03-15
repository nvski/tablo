import asyncio
from time import time
import typing as tp
from math import exp

import apds9930


apds9930.APDS9930_IDs = [0x29, 0x39]

T = tp.TypeVar("T", int, float)

def clip(x:T, minimal:T, maximal:T) -> T:
    assert minimal <= maximal
    x = max(x, minimal)
    x = min(x, maximal)
    return x


class BrightnessScheduler():
    _HS = 1.  # hysteresis sensivity

    def __init__(self, refresh_rate=.05):
        self.refresh_rate = refresh_rate
        # self.history = np.zeros((20,))
        self.current_brightness = None
        self.sensor:tp.Optional[apds9930.APDS9930] = None
        self.last_brigtness = 10.

    def _init_sensor(self) -> None:
        try:
            self.sensor = apds9930.APDS9930(1)
            self.sensor.set_mode(apds9930.ALL, True)
        except:
            pass

    def lux_to_brightness(self, lux:float) -> float:
        assert lux >= 0, f"expected lux>=0, got {lux}"
        brightness = 3*lux**.6
        brightness = clip(brightness, 0., 100.)
        return brightness

    async def brightness_generator(self) -> tp.AsyncIterable[tp.Optional[int]]:
        while True:
            try:
                assert self.sensor is not None, "sensor is not initialized"
                lux:float = self.sensor.ambient_light
                if lux < 0:
                    lux = -lux
                brightness = self.lux_to_brightness(lux)
                brightness = clip(self.last_brigtness, brightness-self._HS, brightness+self._HS)
                self.last_brigtness = brightness
            except Exception:
                self._init_sensor()
            finally:
                yield round(self.last_brigtness)
