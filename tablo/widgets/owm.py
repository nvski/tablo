import datetime
import math
import os
import pandas as pd
import PIL.Image as Image
import typing as tp
from functools import cache

from ..base import Widget
from .picture import Picture_W
from .text import Text_W


class OWM_Data_Provider:
    one_call_api = 'http://api.openweathermap.org/data/2.5/onecall'
    default_args = {
        "lang": "ru",
        "lat": "55.729270",
        "lon": "37.453360",
        "units": "metric"
    }

    def __init__(self, session):
        with open("owm.key") as file:
            token = file.readline().rstrip()
        self.session = session
        self.args = {"appid": token} | self.default_args
        self.data: tp.Dict[str, tp.Any] = None
        self.timeout = datetime.timedelta(minutes=2)
        self.err=None

    async def update_data(self, force=False) -> tp.Dict[str, tp.Any]:
        if force or self.data is None or datetime.datetime.now().astimezone() > self.data['current']['dt'] + self.timeout:
            try:
                async with self.session.get(
                    self.one_call_api,
                    params=self.args,
                    # raise_for_status=True
                ) as resp:
                    if (st:=resp.status) == 200:
                        self.data = await resp.json()
                        self.preproc_data()
                        self.err = None
                    else:
                        self.err = await resp.text()
                        print(f"Got api response status {st}.\n{self.err}")
            except Exception as e:
                print(e)
        return self.data
    
    def _convert(self, data, f):
        if not isinstance(data, tp.Mapping): return
        for key in data.keys():
            if key in ['dt', 'sunrise', 'sunset', 'start', 'end']:
                data[key] = f(data[key])
            elif isinstance(data[key], tp.Sequence):
                for d in data[key]:
                    self._convert(d, f)
            else:
                self._convert(data[key], f)

    def preproc_data(self):
        self.data['timezone'] = tz = datetime.timezone(
            datetime.timedelta(seconds=self.data['timezone_offset']),
            name=self.data['timezone']
            )
        del self.data['timezone_offset']

        f = lambda x: datetime.datetime.fromtimestamp(x, tz)
        self._convert(self.data, f)


class OWM_Emoji_Icon_W(Text_W):
    DICT = {"01d":"☀️", "01n":"🌑",
            "02d":"🌤️", "02n":"☁️",
            "03d":"⛅", "03n":"☁️",
            "04d":"🌥️", "04n":"☁️",
            "09d":"🌧️", "09n":"🌧️",
            "10d":"🌦️", "10n":"🌦️",
            "11d":"⛈️", "11n":"⛈️",
            "13d":"❄️", "13n":"❄️",
            "50d":"🌫", "50n":"🌫"}
    def __init__(self, *args, data_provider=None, font_name='fonts/seguiemj.ttf', move=(0,2), **kwargs):
        super().__init__(*args, font_name=font_name, move=move, **kwargs)
        self.draw.fontmode = "RGBA"
        self.data_provider = OWM_Data_Provider() if data_provider is None else data_provider

    async def text_gen(self):
        data = await self.data_provider.update_data()
        if data is not None:
            w = data["current"]["weather"][0]["icon"]
            self.draw.fontmode = "L" if w.startswith("5") else "RGBA"
            return self.DICT[w]
        return None

class OWM_Todays_Weather(Widget):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    async def update_frame(self):
        await self.data_provider.data_update()
        hourly = pd.DataFrame(self.data_provider.data['hourly'])
        temp = hourly['temp']
        a = temp.min()
        b = temp.max()
        c = self.data_provider.data['current']['temp']
        
        red_blue = Image.new("RGB", self.size, 'blue')
        red_blue.paste(Image.new("RGB", (self.h*(b-c)//(b-a), 0), 'red'), (0,0))

        scale_5 = Image.new("L", self.size, 1.)
        for t in range(math.floor(a/10)*10, b, 10):
            pass

class OWM_Icon_W(Picture_W):
    def __init__(self, *args, data_provider, icon_path, **kwargs):
        self.path = icon_path
        super().__init__(*args, **kwargs)
        self.data_provider = OWM_Data_Provider() if data_provider is None else data_provider

    @staticmethod
    @cache
    def get_image(path):
        bg = Image.new("RGB", (100,100), 'black')
        im = Image.open(path)
        bg.paste(im, mask=im)
        return bg.crop((16,16,84,84))
        
    async def img_gen(self):
        data = await self.data_provider.update_data()
        if data is not None:
            fname = data["current"]["weather"][0]["icon"] + ".png"
            path = os.path.join(self.path, fname)
            return self.get_image(path).resize(self.size, Image.BICUBIC)