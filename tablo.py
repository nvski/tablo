#!//usr/bin/env python3.9

# %%
import aiohttp  # instead of requests
import asyncio
import PIL.Image as Image

from tablo import *


async def main():
    bs = BrightnessScheduler(rr=.02)
    bs.get_new_brightness()
    tablo = Tablo(100)
    bs.start()

    if False:
        test = Test_W((128,64), rr=.003)
        test.start()
        await asyncio.sleep(3)
        test.stop()
        await test.task
        tablo.clear()
    # tablo.image=Image.new('RGB', (256,64), 'green')
    
    time_HH = Time_W((40, 28), (2, 3), rr=1, t_format="%H", font_color='#ffffff')
    time_de = Text_W((20, 28), (37, 3), rr=1, text_gen=lambda: ":", font_color='#ffffff')
    time_MM = Time_W((40, 28), (52, 3), rr=1, t_format="%M", font_color='#ffffff')
    time_SS = Time_W((20, 12), (94, 1), rr=1, t_format="%S", font_color='#ffffff', alpha=True)
    time = Container_W((114,28), (0,0), widgets=[time_de, time_HH, time_MM, time_SS])

    date_m = Time_W((35, 16), (0, 0), rr=1, t_format="%b", font_color='#787878')
    date_d = Time_W((22, 16), (40, 0), rr=1, t_format="%d", font_color='#787878')
    date_dow = Time_W((35, 16), (0, 16), rr=1, t_format="%a", font_color='#787878')
    date = Container_W((62,32), (0,28), widgets=[date_dow, date_m, date_d])
    
    # text = Text_W((100,16), (128,28), text_gen=lambda:"Mon 01 Dow", font_color='#787878')

    async with aiohttp.ClientSession() as session:
        owm_data_provider = OWM_Data_Provider(session)
        owm_pic = OWM_Icon_W((28,28), (0,0), rr=1, icon_path='/home/pi/tablo/icons', data_provider=owm_data_provider)
        owm_temp = Text_W((35,16), (30,6), rr=1, text_gen=lambda:"%+d" % round(
            owm_data_provider.data["current"]["temp"]) if owm_data_provider.data else "E"
            )
        owm = Container_W((66,30), (60, 38), widgets=[owm_pic,owm_temp])

        rasp_data_provider = YaRasp_Data_Provider(session)
        rasp = YaRasp_W((110,24), (2,3), rr=1, data_provider=rasp_data_provider, n_lines=2, per_line_limit=4, space=4)
        # rasp0 = YaRasp_Simple_W((54,15), (0,0), k=0, rr=5, data_provider=rasp_data_provider)
        # rasp1 = YaRasp_Simple_W((54,15), (0,15), k=1, rr=5, data_provider=rasp_data_provider)
        # rasp = Container_W((64,30), (65,1), widgets=[rasp0, rasp1])


        right = Container_W((128,64), (128,0), widgets=[owm,date,time])
        await asyncio.gather(*(w.run() for w in [right, rasp]))


bs = BrightnessScheduler(rr=.02)
bs.get_new_brightness()
tablo = Tablo(100)

asyncio.run(main())
