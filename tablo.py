#!//usr/bin/env python3.9

# %%
import aiohttp  # instead of requests
import asyncio
import PIL.Image as Image

from tablo import *
from tablo.base import Layout, Node


async def main():
    bs = BrightnessScheduler(.05)
    tablo = Tablo(100)

    if False:
        test = Test_W((128,64), rr=.003)
        test.start()
        await asyncio.sleep(3)
        test.stop()
        await test.task
        tablo.clear()
    # tablo.image=Image.new('RGB', (256,64), 'green')
    
    time_HH = Time_W((40, 30), t_format="%H", font_color='#ffffff')
    time_de = Text_W((20, 30), text_gen=lambda: ":", font_color='#ffffff')
    time_MM = Time_W((40, 30), t_format="%M", font_color='#ffffff')
    time_SS = Time_W((20, 14), t_format="%S", font_color='#ffffff', alpha=True)
    time_layout = Layout([
        Node(time_de, (37, 3)),
        Node(time_HH, (2, 3)),
        Node(time_MM, (52, 3)),
        Node(time_SS, (94,1)),
    ])
    time = Container_W((114,28), time_layout)

    date_m = Time_W((35, 18), t_format="%b", font_color='#787878')
    date_d = Time_W((22, 18), t_format="%d", font_color='#787878')
    date_dow = Time_W((35, 18), t_format="%a", font_color='#787878')
    date_layout = Layout([
        Node(date_m, (0,0)),
        Node(date_d, (40,0)),
        Node(date_dow, (0,18)),
    ])
    date = Container_W((62,36), layout=date_layout)  #0,28
    
    # text = Text_W((100,16), (128,28), text_gen=lambda:"Mon 01 Dow", font_color='#787878')

    async with aiohttp.ClientSession() as session:
        owm_data_provider = OWM_Data_Provider(session)
        owm_pic = OWM_Icon_W((28,28), icon_path='/home/pi/tablo/icons', data_provider=owm_data_provider)
        owm_temp = Text_W((35,18), text_gen=lambda:"%+d" % round(
            owm_data_provider.data["current"]["temp"]) if owm_data_provider.data else "E"
            )
        owm_layout = Layout([
            Node(owm_pic, (0,0)),
            Node(owm_temp, (30,8))
        ])

        owm = Container_W((66,30), layout=owm_layout)  #60, 38

        rasp_data_provider = YaRasp_Data_Provider(session)
        rasp = YaRasp_W((110,26), data_provider=rasp_data_provider, n_lines=2, per_line_limit=4, space=4)
        # rasp0 = YaRasp_Simple_W((54,15), (0,0), k=0, rr=5, data_provider=rasp_data_provider)
        # rasp1 = YaRasp_Simple_W((54,15), (0,15), k=1, rr=5, data_provider=rasp_data_provider)
        # rasp = Container_W((64,30), (65,1), widgets=[rasp0, rasp1])


        layout = Layout([
            Node(Layout([
                Node(time, (0, 0), 1),
                Node(owm, (68,36), 10),
                Node(date, (0, 28), 10),
            ]), position=(120,0)),
            Node(rasp, (2,1), 10)
        ])
        returns = await tablo.run(layout, bs)
    print(repr(returns))


# bs = BrightnessScheduler(rr=.5)
# bs.get_new_brightness()
# tablo = Tablo(100)

asyncio.run(main())
