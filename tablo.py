#!//usr/bin/env python3.7
# %%
# import aiohttp  # instead of requests
import asyncio
import datetime
# import zoneinfo
import json
# import logging
import math
# import numpy as np
import requests
import time
import typing as tp
# from functools import singledispatch
# from pyowm.owm import OWM

import apds9930
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions


apds9930.APDS9930_IDs = [0x29, 0x39]


class Tablo:
    def __init__(self, brightness: int = 30) -> None:
        options = RGBMatrixOptions()
        options.drop_privileges = False
        options.rows = 64
        options.cols = 128
        options.chain_length = 1
        options.led_rgb_sequence = 'RBG'
        options.panel_type = 'FM6126A'
        options.hardware_mapping = 'regular'
        options.gpio_slowdown = 2
        options.pwm_bits = 14
        options.pwm_dither_bits = 1
        options.pwm_lsb_nanoseconds = 50
        # options.scan_mode = 1

        self.image = Image.new('RGB', (128, 64), 'black')

        self.matrix = None
        self.options = options
        self.start_matrix(options, brightness)

    def start_matrix(self, options=None, brightness=30):
        if options is None:
            options = self.options
        if self.matrix is not None:
            del self.matrix
            # time.sleep(.5)
        self.matrix = RGBMatrix(options=options)
        self.matrix.brightness = brightness
        self.update()

    def update(self, brightness: tp.Optional[int] = None) -> None:
        if brightness is not None:
            self.matrix.brightness = brightness
        self.matrix.SetImage(self.image)

    def clear(self) -> None:
        self.image = Image.new('RGB', (128, 64), 'black')
        self.update()


Widget = tp.TypeVar('Widget')


class Widget:
    running_set: tp.Set[Widget] = set()

    @staticmethod
    async def stop_all():
        for w in Widget.running_set.copy():
            await w.stop()

    def __init__(self, size: tp.Tuple[int, int], position=(0, 0), *, rr:float=5, alpha=False):
        self.w, self.h = self.size = size
        self.x, self.y = self.position = position
        self.rr = rr
        self.task: tp.Optional[asyncio.Task] = None

        self.alpha = alpha
        if alpha:
            self.image = Image.new("RGBA", self.size, '#00000000')
        else:
            self.image = Image.new("RGB", self.size, '#000000')
        self.draw = ImageDraw.Draw(self.image)

    def clear(self) -> None:
        self.draw.rectangle((0, 0)+self.size, fill='#000000')
        # self.place()

    def _place(self) -> None:
        if self.alpha:
            mask = self.image
        else:
            mask = None
        tablo.image.paste(self.image, box=self.position, mask=mask)
        tablo.update()

    def update_frame(self):
        pass
        # to be defined in subclasses individually

    async def run(self) -> None:
        if self in Widget.running_set:
            raise Warning(
                "Trying to start smth already running. Nothing is done.")
            return
        Widget.running_set.add(self)
        while self in Widget.running_set:
            self.update_frame()
            self._place()
            await asyncio.sleep(self.rr - time.time() % self.rr)

    def start(self) -> None:
        self.task = asyncio.create_task(self.run(), name=self.__class__.__name__)

    def stop(self) -> None:
        Widget.running_set.remove(self)


class Container_W(Widget):
    def __init__(self, *args, widgets:tp.Sequence[Widget], alpha=True, **kwargs):
        kwargs['alpha'] = alpha
        super().__init__(*args, **kwargs)
        self.widgets = widgets
        assert all(w.rr == widgets[0].rr for w in widgets)
        self.rr = widgets[0].rr
        # container self.rr overwrites widgets' rr 

    def update_frame(self):
        for w in self.widgets:
            w.update_frame()
            self.image.paste(w.image, box=w.position)


class Test_W(Widget):
    colors = ["yellow", "red", "green", "blue", "white"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = 0

    def update_frame(self):
        y = self.n % self.h
        color = self.colors[self.n//self.h]
        self.draw.line((0, y, self.w, y), fill=color)
        self.n += 1
        self.n %= self.h*len(self.colors)


# %%
DEFAULT_FONT = '/home/pi/tablo/fonts/OCRAStd.otf'


class Text_W(Widget):
    def __init__(self, *args,
                 text_gen: tp.Optional[tp.Callable[[], str]] = None,
                 font_name: str = DEFAULT_FONT, font_color="#ffffff",
                 **kwargs
                 ) -> None:
        super().__init__(*args, **kwargs)
        self._text_gen = text_gen
        self.font_obj = ImageFont.truetype(font_name, self.h)
        self.font_color = font_color

    def text_gen(self):
        if isinstance(self._text_gen, tp.Callable):
            return self._text_gen()
        else:
            return 'text'

    def update_frame(self) -> None:
        self.clear()
        text = self.text_gen()
        self.draw.multiline_text(
            (0, 0), text, fill=self.font_color, font=self.font_obj)


class Time_W(Text_W):
    def __init__(self, *args,
                 timezone: datetime.tzinfo = None, t_format: str = "%p %I:%M:%S",
                 **kwargs
                 ) -> None:
        self.timezone = timezone
        self.t_format = t_format
        super().__init__(*args, **kwargs)

    def text_gen(self) -> str:
        t = datetime.datetime.now().astimezone(self.timezone)
        return t.strftime(self.t_format)


class Time_Arrows_W(Widget):
    def __init__(self, *args, timezone: int = +3, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timezone = timezone

    def update_frame(self) -> None:
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


class BrightnessScheduler():

    def __init__(self, rr=.05):
        self.rr=rr
        self.task = None
        # self.history = np.zeros((20,))
        self.current_brightness = None
        self._running = False
        self.sensor:tp.Optional[apds9930.APDS9930] = None
        self._mem = 100
        self._HS = 0.9  # hysteresis sensity, _HS <= 0.5 means no hysteresis

    def _init_sensor(self) -> None:
        self.sensor = apds9930.APDS9930(1)
        self.sensor.set_mode(apds9930.ALL, True)

    def get_new_brightness(self) -> int:
        if self.sensor is None:
            self._init_sensor()
        lux = self.sensor.ambient_light
        if lux < 0:
            lux = 1500
        brightness = self.lux_to_brightness(lux)
        if not self._mem - self._HS <= brightness <= self._mem + self._HS:
            self._mem = round(brightness)
        return self._mem

    def lux_to_brightness(self, lux:float) -> float:
        brightness = 1.5*lux**.65
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


class AmbientSensor_W(Text_W):
    def __init__(self, *args,
                 bs_:tp.Optional[BrightnessScheduler]=None,
                 font_color='#808080', err_color="#F03030",
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.bs = bs_ if bs_ is not None else bs
        self.font_color = self.normal_color = font_color
        self.err_color = err_color

    def text_gen(self):
        text = f" {tablo.matrix.brightness}"
        try:
            text = f"{round(self.bs.sensor.ambient_light)}" + text
            self.font_color = self.normal_color
        except:
            text = f"Err" + text
            self.font_color = self.err_color
        return text

#%%
class OWM_Data_Provider:
    one_call_api = 'http://api.openweathermap.org/data/2.5/onecall'
    default_args = {
        "lang": "ru",
        "lat": "55.927305",
        "lon": "37.523576",
        "units": "metric"
    }

    def __init__(self):
        with open("owm.key") as file:
            token = file.readline().rstrip()
        self.args = {"appid": token} | self.default_args
        self.data: tp.Dict[str, tp.Any] = self.update_data(True)
        self.timeout = datetime.timedelta(minutes=2)

    def last_upd(self) -> tp.Optional[datetime.datetime]:
        if self.data is None:
            return
        else:
            return datetime.datetime.fromtimestamp(self.data["current"]["dt"]).astimezone()

    def update_data(self, force=False) -> tp.Dict[str, tp.Any]:
        if force or datetime.datetime.now().astimezone() > self.last_upd() + self.timeout:
            responce = requests.get(
                self.one_call_api+'?'+'&'.join(k+'='+v for k, v in self.args.items()))
            self.data = json.loads(responce.content)
        return self.data

# owm_data = OWM_Data_Provider()

#%%
    
class Picture_W(Widget):
    def __init__(self, *args,
                 img_gen: tp.Optional[tp.Callable[[], Image.Image]]=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._img_gen = img_gen

    def img_gen(self):
        if isinstance(self._img_gen, tp.Callable):
            return self._img_gen()
        else:
            return Image.new("RGB", self.size, "white")

    def update_frame(self):
        img = self.img_gen()
        if self.alpha and img.mode=='RGBA':
            mask=img
        else:
            mask=None
        self.image.paste(img, mask=mask)


class OWM_Pic_W(Picture_W):
    PREFIX = '/home/pi/tablo/icons/'
    def __init__(self, *args, data_provider=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_provider = OWM_Data_Provider() if data_provider is None else data_provider
        assert self.w == self.h, "Squared imgs only"
        self.offset = round(self.w // 4)

    def img_gen(self):
        weathers = self.data_provider.update_data()["current"]["weather"]
        i = round(time.time()) // self.rr % len(weathers)
        weather = weathers[i]
        path = self.PREFIX + weather["icon"] + ".png"
        img = Image.open(path).resize((self.w+2*self.offset, self.h+2*self.offset))
        img = img.crop((self.offset, self.offset, self.w+self.offset, self.h+self.offset))
        return img

#%%
async def main():
    bs.start()

    if False:
        test = Test_W((128,64), rr=.003)
        test.start()
        await asyncio.sleep(3)
        test.stop()
        await test.task
        tablo.clear()
    # tablo.image=Image.new('RGB', (128,64), 'green')
    
    time_HH = Time_W((40, 28), (2,  3), rr=1, t_format="%H", font_color='#ffffff')
    time_de = Text_W((20, 28), (37,  3), rr=1, text_gen=lambda: ":", font_color='#ffffff')
    time_MM = Time_W((40, 28), (52,  3), rr=1, t_format="%M", font_color='#ffffff')
    time_SS = Time_W((20, 12), (94, 1), rr=1, t_format="%S", font_color='#ffffff', alpha=True)
    time = Container_W((114,28), (0,0), widgets=[time_de, time_HH, time_MM, time_SS])

    date_m = Time_W((35, 16), (0, 0), rr=5, t_format="%b", font_color='#787878')
    date_d = Time_W((22, 16), (42, 0), rr=5, t_format="%d", font_color='#787878')
    date_dow = Time_W((35, 16), (0, 16), rr=5, t_format="%a",    font_color='#787878')
    date = Container_W((64,32), (0,28), widgets=[date_dow, date_m, date_d])

    owm_data_provider = OWM_Data_Provider()
    owm_pic = OWM_Pic_W((16,16), (0,0), rr=2, data_provider=owm_data_provider)
    owm_temp = Text_W((35,16), (19,0), rr=2, text_gen=lambda:"%+d" % round(owm_data_provider.update_data()["current"]["temp"]))
    owm = Container_W((54,16), (71, 44), widgets=[owm_pic, owm_temp])

    amb = AmbientSensor_W(size=(32, 8), position=(94, 20), rr=.05)

    await asyncio.gather(*(w.run() for w in [time, date, amb, owm]))

#%%

bs = BrightnessScheduler(rr=.02)
bs.get_new_brightness()
tablo = Tablo(100)

asyncio.run(main())
