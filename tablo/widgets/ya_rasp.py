import datetime
from PIL.ImageFont import truetype
import typing as tp


from .text import Text_W, DEFAULT_FONT
from .base import Widget


class YaRasp_Data_Provider:
    api = 'https://api.rasp.yandex.net/v3.0/search/'
    default_args = {
        "from": "s9601728",
        "to": "s9602218",
        "limit": "500"
    }

    def __init__(self, session):
        with open("ya_rasp.key") as file:
            token = file.readline().rstrip()
        self.session = session
        self.args = {"apikey": token} | self.default_args
        self.data: tp.Dict[str, tp.Any] = None
        self.search_datetime = None
        self.timeout = datetime.timedelta(minutes=10)

    async def update_data(self, force=False) -> tp.Dict[str, tp.Any]:
        if force or self.search_datetime is None or datetime.datetime.now() > self.search_datetime + self.timeout:
            today = datetime.date.today()
            tommorow = today + datetime.timedelta(days=1)
            try:
                async with self.session.get(
                    self.api,
                    params=self.args | {"date":today.isoformat()},
                    # raise_for_status=True
                ) as resp_today, self.session.get(
                    self.api,
                    params=self.args | {"date":tommorow.isoformat()},
                    # raise_for_status=True
                ) as resp_tommorow:
                    if resp_today.status == resp_tommorow.status == 200:
                        today_data = await resp_today.json()
                        self.data = today_data["segments"]
                        tommorow_data = await resp_tommorow.json()
                        self.data += tommorow_data["segments"]
                        self.preproc_data()
                        self.search_datetime = datetime.datetime.now()
                    else:
                        print(f"Got api response status {resp_today.status} and {resp_tommorow.status}")
            except Exception as e:
                print(e)
        return self.data
    

    def _convert(self, data):
        if isinstance(data, tp.Sequence) and not isinstance(data, str):
            for d in data:
                self._convert(d)
        elif isinstance(data, tp.Mapping):
            for key in data.keys():
                if key in ['arrival', 'departure']:
                    data[key] = datetime.datetime.fromisoformat(data[key])
                elif key == 'date':
                    data[key] = datetime.date.fromisoformat(data[key])
                else:
                    self._convert(data[key])

    def preproc_data(self):
        self._convert(self.data)


class YaRasp_Simple_W(Text_W):
    def __init__(self, *args, data_provider=None, k=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.k = k
        self.data_provider = YaRasp_Data_Provider() if data_provider is None else data_provider

    async def get_next_train(self, k=0):
        data = await self.data_provider.update_data()
        now = datetime.datetime.now(datetime.timezone.utc)
        next_train = sorted(filter(lambda d: d["departure"]>now, data), key=lambda x:x["departure"])[k]
        return next_train["departure"].strftime("%H:%M"), next_train["thread"]["transport_subtype"]["color"]

    async def text_gen(self):
        data = await self.data_provider.update_data()
        if data is not None:
            departure, color = await self.get_next_train(self.k)
            self.font_color = color
            return departure

class YaRasp_W(Widget):
    def __init__(self,
            size, position, rr, alpha=False,
            data_provider:YaRasp_Data_Provider = None,
            n_lines:int = 2, per_line_limit:int = 4, space=4,
            font_name: str = DEFAULT_FONT,
        ):
        super().__init__(size=size, position=position, rr=rr, alpha=alpha)
        if data_provider is None: raise ValueError
        self.data_provider = data_provider

        self.n_lines = n_lines
        self.per_line_limit = per_line_limit
        self.font_obj = truetype(font_name, self.h//n_lines)
        self.space = space


    async def get_line_data_generator(self) -> tp.List[tp.Mapping]:
        data = await self.data_provider.update_data()
        now = datetime.datetime.now(datetime.timezone.utc)
        ordered_data = sorted(filter(lambda d: d["departure"]>now, data), key=lambda x:x["departure"])
        batch = []
        for train in ordered_data:
            if len(batch) >= self.per_line_limit:
                yield batch
                batch = []
            if not batch:
                batch.append(train)
                continue
            prev_train_hour = batch[-1]["departure"].strftime("%Y-%m-%dT%H")
            curr_train_hour = train["departure"].strftime("%Y-%m-%dT%H")
            if prev_train_hour == curr_train_hour:
                batch.append(train)
            else:
                yield batch
                batch = [train]


    async def update_frame(self):
        await self.clear()
        i = -1
        async for line in self.get_line_data_generator():
            assert line
            i += 1
            offset_h = self.h * i // self.n_lines
            offset_w = 0
            for j, train in enumerate(line):
                text = train["departure"].strftime("%M" if j else "%H:%M")
                self.draw.multiline_text(
                    (offset_w, offset_h),
                    text, font=self.font_obj, fill=train["thread"]["transport_subtype"]["color"])
                w, h = self.draw.textsize(text, self.font_obj)
                offset_w += w+self.space
            if i == self.n_lines: break
            

