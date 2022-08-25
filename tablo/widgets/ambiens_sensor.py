from ..base import Tablo
from ..brightness import BrightnessScheduler
from .text import Text_W


class AmbientSensor_W(Text_W):
    def __init__(self, *args,
                 font_color='#808080', err_color="#F03030",
                 tablo:Tablo, bs:BrightnessScheduler,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.font_color = self.normal_color = font_color
        self.err_color = err_color
        self.tablo = tablo
        self.bs = bs

    async def text_gen(self):
        text = f" {self.tablo.matrix.brightness}"
        try:
            assert self.bs.sensor is not None
            text = f"{round(self.bs.sensor.ambient_light)}" + text
            self.font_color = self.normal_color
        except:
            text = f"Err" + text
            self.font_color = self.err_color
        return text
