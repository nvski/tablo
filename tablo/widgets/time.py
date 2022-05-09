import datetime
import math
import time


from .base import Widget
from .text import Text_W

class Time_W(Text_W):
    def __init__(self, *args,
                 timezone: datetime.tzinfo = None, t_format: str = "%p %I:%M:%S",
                 **kwargs
                 ) -> None:
        self.timezone = timezone
        self.t_format = t_format
        super().__init__(*args, **kwargs)

    async def text_gen(self) -> str:
        t = datetime.datetime.now().astimezone(self.timezone)
        return t.strftime(self.t_format)


class Time_Arrows_W(Widget):
    def __init__(self, *args, timezone: int = +3, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timezone = timezone

    async def update_frame(self) -> None:
        self.clear()
        t = time.time()
        r = min(self.w, self.h)/2
        for i in range(12):
            x1 = r + r*math.cos(math.pi*i/6)
            y1 = r + r*math.sin(math.pi*i/6)
            x2 = r + 0.93*r*math.cos(math.pi*i/6)
            y2 = r + 0.93*r*math.sin(math.pi*i/6)
            fill = "#ffffff" if i % 3 == 0 else "#990000"
            self.draw.line((x1, y1, x2, y2), fill=fill)

        hx = 0.6*r*math.sin(math.pi*((t/3600) % 24+self.timezone)/6)
        hy = - 0.6*r*math.cos(math.pi*((t/3600) % 24+self.timezone)/6)
        self.draw.line((r, r, r+hx, r+hy), fill="#ffffff")

        mx = 0.9*r*math.sin(math.pi*((t/60) % 60)/30)
        my = - 0.9*r*math.cos(math.pi*((t/60) % 60)/30)
        self.draw.line((r, r, r+mx, r+my), fill="#ffffff")

        sx = r*math.sin(math.pi*(t % 60)/30)
        sy = - r*math.cos(math.pi*(t % 60)/30)
        self.draw.line((r+sx, r+sy, r+0.95*sx, r+0.95*sy), fill="#ffffff")
