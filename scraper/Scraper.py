import selenium
import datetime, time, sys, os
from datetime import datetime, timedelta
from selenium import webdriver
from bs4 import BeautifulSoup
from IPython.display import clear_output, display
import ipywidgets as widgets
from tqdm import tqdm, trange
import pickle
import random
import telegram

bot_token="set_your_token"

def bot_message(text):
    """Send telegram bot message [text]
    before use this function, you must install python-telegram-bot
    using
    pip install python-telegram-bot
    """
    bot=telegram.Bot(token=bot_token)
    chat_id="539372326"
    bot.sendMessage(chat_id=chat_id, text=text)
    print(text)
    return

def click_element(browser,element):
    browser.execute_script("$(arguments[0]).click();", element)
    return

def wait_until_target_time(target_datetime):
    target_t=target_datetime
    t=datetime.now()
    t_delta=target_t-t # <- target_t (공지 예정 시각)
    sleep_time=t_delta.total_seconds()
    with tqdm(total=int(sleep_time)) as pbar:
        while sleep_time>0:        
            if sleep_time>=1:
                time.sleep(1)
            else:
                time.sleep(sleep_time-int(sleep_time))
                break
            t=datetime.now()
            pbar.set_description(str(t))
            pbar.update()
            t_delta=target_t-t
            sleep_time=t_delta.total_seconds()
    print(datetime.now())
    return

def get_target_datetime(h_hour):
    time_now=datetime.now()
    if time_now.hour<h_hour:
        target_datetime=datetime(time_now.year,time_now.month,time_now.day,h_hour)
    else:
        time_now+=timedelta(days=1)
        target_datetime=datetime(time_now.year,time_now.month,time_now.day,h_hour)
    return target_datetime

