from ..base import Widget

from .ambiens_sensor import AmbientSensor_W
from .container import Container_W
from .owm import OWM_Data_Provider, OWM_Emoji_Icon_W, OWM_Icon_W, OWM_Todays_Weather
from .picture import Picture_W
from .text import Text_W
from .time import Time_W, Time_Arrows_W
from .ya_rasp import YaRasp_Data_Provider, YaRasp_W, YaRasp_Simple_W


class Test_W(Widget):
    colors = ["yellow", "red", "green", "blue", "white"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = 0

    async def update_frame(self):
        y = self.n % self.h
        color = self.colors[self.n//self.h]
        self.draw.line((0, y, self.w, y), fill=color)
        self.n += 1
        self.n %= self.h*len(self.colors)
