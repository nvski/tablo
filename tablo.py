#!//usr/bin/env python3.9

# %%
import aiohttp  # instead of requests
import asyncio
import logging
import PIL.Image as Image

from tablo import *
from tablo.base import Layout, Node


def gen_layout():

    # layout = Layout([Node(Test_W((256,64)), (0,0), 0.05)])
        
    # tablo.image=Image.new('RGB', (256,64), 'green')
    
    time_HH = Time_W((44, 33), t_format="%H", font_color='#ffffff')
    time_de = Text_W((22, 33), text_func=lambda: ":", font_color='#ffffff')
    time_MM = Time_W((44, 33), t_format="%M", font_color='#ffffff')
    time_SS = Time_W((21, 15), t_format="%S", font_color='#ffffff', alpha=True)
    time_layout = Layout([
        Node(time_de, (41, 2)),
        Node(time_HH, (2, 2)),
        Node(time_MM, (58, 2)),
        Node(time_SS, (104,1)),
    ])
    time = Container_W((126,30), time_layout)

    date_m = Time_W((33, 17), t_format="%b", font_color='#787878')
    date_d = Time_W((20, 17), t_format="%d", font_color='#787878')
    date_dow = Time_W((33, 17), t_format="%a", font_color='#787878')
    date_layout = Layout([
        Node(date_m, (0,0)),
        Node(date_d, (39,0)),
        Node(date_dow, (0,16)),
    ])
    date = Container_W((59,36), layout=date_layout)  #0,28
    
    owm_data_provider = OWM_Data_Provider()
    # owm_data_provider.timeout = datetime.timedelta(minutes=5)
    owm_pic = OWM_Icon_W((26,26), icon_path='/home/anton/tablo/icons', data_provider=owm_data_provider)
    owm_temp = Text_W((33,17), text_func=lambda:"%+d" % round(
        owm_data_provider.data["main"]["temp"]) if owm_data_provider.data else "E"
        )
    owm_layout = Layout([
        Node(owm_pic, (0,0)),
        Node(owm_temp, (28,8))
    ])

    owm = Container_W((66,29), layout=owm_layout)  #60, 38

    # rasp_data_provider = YaRasp_Data_Provider(session)
    # rasp = YaRasp_W((110,26), data_provider=rasp_data_provider, n_lines=2, per_line_limit=4, space=4)


    # layout = Layout([
    #     Node(Layout([
    #         Node(time, (0, 0), 1),
    #         Node(owm, (68,36), 10),
    #         Node(date, (0, 28), 10),
    #     ]), position=(120,0)),
    #     Node(rasp, (2,1), 10)
    # ])

    layout = Layout([
        Node(Layout([
            Node(time, (0, 0), 1),
            Node(owm, (65,36), 10),
            Node(date, (1, 32), 10),
        ])),
    ])
    return layout



tablo = Tablo(3)
bs = BrightnessScheduler(.05)
layout = gen_layout()
try:
    asyncio.run(
        tablo.run(layout, bs)
    )
except asyncio.TimeoutError as e:
    from subprocess import run, PIPE
    logging.critical("tracerout:")
    completed = run(["traceroute", "api.rasp.yandex.net"], stdout=PIPE, stderr=PIPE)
    logging.critical(completed.stdout.decode("UTF8"))
    logging.critical(completed.stderr.decode("UTF8"))

    logging.critical("tracerout -6:")
    completed = run(["traceroute", "-6", "api.rasp.yandex.net"], stdout=PIPE, stderr=PIPE)
    logging.critical(completed.stdout.decode("UTF8"))
    logging.critical(completed.stderr.decode("UTF8"))

    logging.critical("ip route show:")
    completed = run(["ip", "route", "show"], stdout=PIPE, stderr=PIPE)
    logging.critical(completed.stdout.decode("UTF8"))
    logging.critical(completed.stderr.decode("UTF8"))

    logging.critical("ip -6 route show:")
    completed = run(["ip", "-6", "route", "show"], stdout=PIPE, stderr=PIPE)
    logging.critical(completed.stdout.decode("UTF8"))
    logging.critical(completed.stderr.decode("UTF8"))

    raise e

