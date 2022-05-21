import asyncio
import typing as tp


import apds9930


apds9930.APDS9930_IDs = [0x29, 0x39]


class BrightnessScheduler():
    def __init__(self, refresh_rate=.05):
        self.refresh_rate=refresh_rate
        # self.history = np.zeros((20,))
        self.current_brightness = None
        self.sensor:tp.Optional[apds9930.APDS9930] = None
        self._mem = 100
        self._HS = 1.2  # hysteresis sensity, _HS <= 0.5 means no hysteresis

    def _init_sensor(self) -> None:
        try:
            self.sensor = apds9930.APDS9930(1)
            self.sensor.set_mode(apds9930.ALL, True)
        except:
            pass

    def lux_to_brightness(self, lux:float) -> float:
        brightness = 3*lux**.6
        brightness = min(100, brightness)
        brightness = max(1, brightness)
        return brightness

    async def brightness_generator(self) -> tp.AsyncGenerator[tp.Optional[int], None]:
        while True:
            try:
                lux = self.sensor.ambient_light
                if lux < 0:
                    lux = 1500
                brightness = self.lux_to_brightness(lux)
                if not self._mem - self._HS <= brightness <= self._mem + self._HS:
                    self._mem = round(brightness)
            except:
                self._init_sensor()
            finally:
                yield self._mem
