import os
import time
import configparser
import pygame
import random
import threading
from plyer import notification
from lxml import etree
import tkinter as tk
from tkinter import messagebox, simpledialog
from mylib.utils import get_url

# 变量
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILENAME = "config.ini"
INTERVAL_RANDOM_MAX = 1

# 创建ConfigParser对象
config = configparser.ConfigParser()
config.read(CONFIG_FILENAME)


class Checker:
    def __init__(self):
        pass

    def run(self):
        # 使用之前的配置或询问用户输入
        self.from_airport = self.get_or_input("from_airport", "起飞机场IATA代码")
        self.to_airport = self.get_or_input("to_airport", "降落机场IATA代码")
        self.dates = self.get_or_input("datas", "飞行日期","（格式yyyy-mm-dd，多个日期用逗号分隔）").split(",")
        self.flights = self.get_or_input("flights", "需要查询的航班号","（留空时表示监测全部，多个航班用逗号分隔）").split(",")
        self.price = int(self.get_or_input("price", "监测票价","（当票价低于该设定时进行提醒）"))
        self.interval = float(self.get_or_input("interval", "监测间隔/秒","（每轮监测的间隔，过短的时间可能会被网站屏蔽导致监测失效）"))
        print("已完成配置，开始监测...")
        print(f"如有需要, 可确认以下网址是否正常加载, 避免配置有误:")
        for date in self.dates:
            print(self.get_airfare_url(date))

    def get_or_input(self, key, title, prompt=""):
        section = "Settings"
        if section not in config:
            config[section] = {}

        def modify_value(prompt, current_value=""):
            new_value = simpledialog.askstring("配置", prompt,initialvalue=current_value)
            config.set(section, key, new_value)
            with open(CONFIG_FILENAME, "w") as configfile:
                config.write(configfile)
            return new_value

        # 从配置文件中获取值，如果不存在或用户需要修改则让用户输入
        if config.has_option(section, key):
            value = config.get(section, key)
            modify = messagebox.askyesno("确认", f"当前[{title}]为：[{value}]\n是否修改?")
            if modify:
                value = modify_value(f"请输入[{title}]：\n\n{prompt}", value)
            return value
        else:
            value = modify_value(f"请输入[{title}]：\n\n{prompt}")
            return value
        
    def get_airfare_url(self, date):
        return f"https://www.ly.com/flights/itinerary/oneway/{self.from_airport}-{self.to_airport}?date={date}"

    def check_tongcheng(self):
        # 记录监测到的航班数量
        flight_counts = {}

        for date in self.dates:
            url = self.get_airfare_url(date)
            response = get_url(url)
            if not response:
                print(f"连接超时，航班信息查询失败")
                continue

            html = etree.HTML(response.text)
            contents = html.xpath('//div[@class="flight-item"]')
            flight_counts[date] = len(contents)
            for content in contents:
                try:
                    flight_name = content.xpath('.//p[@class="flight-item-name" and @data-v-55ab452e]/text()')[0]
                    price = int(content.xpath('.//div[@class="head-prices" and @data-v-55ab452e]//strong/em/text()')[0][1:])
                    start_time = content.xpath('.//div[@class="f-startTime f-times-con" and @data-v-55ab452e]/strong/text()')[0]
                    start_airport = content.xpath('.//div[@class="f-startTime f-times-con" and @data-v-55ab452e]/em/text()')[0]
                    end_time = content.xpath('.//div[@class="f-endTime f-times-con" and @data-v-55ab452e]/strong/text()')[0]
                    end_airport = content.xpath('.//div[@class="f-endTime f-times-con" and @data-v-55ab452e]/em/text()')[0]
                except Exception as e:
                    print(f"错误：{e}")

                content = f"{flight_name} {start_airport}-{end_airport}({start_time}-{end_time}) {date} 当前价格{price}"
                print(content)

                # 判断是否监视该航班并检查是否低于用户设定的价格
                check_all = self.flights[0] == ""
                for flight in self.flights:
                    if check_all or flight_name in flight:
                        if price < self.price:
                            self.on_target_price(content)
            time.sleep(random.uniform(0.5, 1.5))
        return flight_counts

    def on_target_price(self, content):
        self.play_sound()
        self.write_history(content)
        self.show_notification("机票监测", f"航班的票价已低于设定值！{content}")
        print(f"航班的票价已低于设定值！")

    def play_sound(self):
        pygame.mixer.init()
        path = os.path.join(FILE_PATH, "sound", "warning.wav")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

    def show_notification(self, title, message):
        notification.notify(title=title, message=message, timeout=10)

    def write_history(self, content):
        path = os.path.join(FILE_PATH, "history.txt")
        with open(path, "a+") as file:
            # 移动到文件末尾
            file.seek(0, os.SEEK_END)
            # 如果文件不为空，添加换行符
            if file.tell() > 0:
                file.write("\n")

            # 获取当前时间戳
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            # 写入时间戳到文件
            file.write(f"{timestamp} {content}")

def stop_monitoring():
    running_label.config(text="监测已停止")
    global monitoring
    monitoring = False

def start_monitoring():
    checker.run()
    running_label.config(text="正在监测…")
    global monitoring
    monitoring = True
    thread = threading.Thread(target=check_flights)
    thread.start()

def check_flights():
    try_count = 0
    while monitoring:
        try_count += 1
        flight_counts = checker.check_tongcheng()

        print(f"第{try_count}次刷新")
        rounds_label.config(text=f"已经经过的轮次：{try_count}")

        flight_count_text = "监测到的航班数量"
        for date, count in flight_counts.items():
            flight_count_text += f"\n{date}：{count}个班次"
        flight_count_label.config(text=flight_count_text)

        time.sleep(random.uniform(0.5, 1.5))

def on_closing():
    stop_monitoring()
    stop_event.set()
    root.destroy()

def main_thread():
    while not stop_event.is_set():
        time.sleep(1)

# 初始化Tkinter
monitoring = False
checker = Checker()

root = tk.Tk()
root.title("机票价格监测")

# 注册窗口关闭事件
root.protocol("WM_DELETE_WINDOW", on_closing)

# 一些标签
running_label = tk.Label(root, text="尚未开始监测")
running_label.pack()
rounds_label = tk.Label(root, text="")
rounds_label.pack()
flight_count_label = tk.Label(root, text="")
flight_count_label.pack()

# 一些按钮
start_button = tk.Button(root, text="开始监测", command=start_monitoring)
start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)

stop_button = tk.Button(root, text="停止监测", command=stop_monitoring)
stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)

stop_event = threading.Event()

# 启动
thread = threading.Thread(target=main_thread)
thread.start()
root.mainloop()
thread.join()