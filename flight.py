import os
import time
import configparser
import pygame
import random
from plyer import notification
from lxml import etree
from colorama import init, Fore, Style
from mylib.utils import get_url

# 初始化colorama
init()
# 变量
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILENAME = "config.ini"
INTERVAL_RANDOM_MAX = 1
# 说明
PROMPT_FROM_AIRPORT = f"{Fore.GREEN}1.输入起飞机场IATA代码（例：SZX表示深圳宝安机场）{Style.RESET_ALL}"
PROMPT_TO_AIRPORT = f"{Fore.GREEN}2.输入降落机场IATA代码{Style.RESET_ALL}"
PROMPT_DATAS = f"{Fore.GREEN}3.输入飞行日期 (格式yyyy-mm-dd，多个日期用小写逗号,分隔){Style.RESET_ALL}"
PROMPT_FLIGHTS = f"{Fore.GREEN}4.需要查询的航班号 (留空时表示监测全部，多个航班用小写逗号,分隔){Style.RESET_ALL}"
PROMPT_PRICE = f"{Fore.GREEN}5.低于多少票价时进行提醒{Style.RESET_ALL}"
PROMPT_INTERVAL = f"{Fore.GREEN}6.每次刷新间隔多长时间/秒 (过短的刷新间隔可能会被票务网站屏蔽){Style.RESET_ALL}"


class Checker:
    def __init__(self):
        # 创建ConfigParser对象
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FILENAME)

        # 使用之前的配置或询问用户输入
        self.from_airport = self.get_or_input("from_airport", PROMPT_FROM_AIRPORT)
        self.to_airport = self.get_or_input("to_airport", PROMPT_TO_AIRPORT)
        self.dates = self.get_or_input("datas", PROMPT_DATAS).split(",")
        self.flights = self.get_or_input("flights", PROMPT_FLIGHTS).split(",")
        self.price = int(self.get_or_input("price", PROMPT_PRICE))
        self.interval = float(self.get_or_input("interval", PROMPT_INTERVAL))

        print("已完成配置，开始监测...")
        print(f"如有需要, 可确认以下网址是否正常加载, 避免配置有误:")
        for date in self.dates:
            print(self.get_airfare_url(date))

    def get_or_input(self, key, prompt):
        section = "Settings"
        if section not in self.config:
            self.config[section] = {}

        def modify_value(prompt):
            value = input(prompt).strip()
            self.config.set(section, key, value)
            with open(CONFIG_FILENAME, "w") as configfile:
                self.config.write(configfile)
            return value

        # 从配置文件中获取值，如果不存在或用户需要修改则让用户输入
        if self.config.has_option(section, key):
            value = self.config.get(section, key)
            modify = input(
                f"{prompt}\n{Fore.GREEN} - 当前设置为: {value} 是否修改? (y:需要修改){Style.RESET_ALL}\n"
            )
            if modify.strip() == "y":
                value = modify_value(f"输入后按回车键确认:")
            return value
        else:
            value = modify_value(f"{prompt}\n输入后按回车键确认:")
            return value

    def get_airfare_url(self, date):
        return f"https://www.ly.com/flights/itinerary/oneway/{self.from_airport}-{self.to_airport}?date={date}"

    def check_tongcheng(self):
        for date in self.dates:
            url = self.get_airfare_url(date)
            response = get_url(url)
            if not response:
                print(f"连接超时，航班信息查询失败")
                continue

            html = etree.HTML(response.text)
            contents = html.xpath('//div[@class="flight-item"]')
            for content in contents:
                try:
                    flight_name = content.xpath(
                        './/p[@class="flight-item-name" and @data-v-55ab452e]/text()'
                    )[0]
                    price = int(
                        content.xpath(
                            './/div[@class="head-prices" and @data-v-55ab452e]//strong/em/text()'
                        )[0][
                            1:
                        ]  # 去掉第一个币种符号
                    )
                    start_time = content.xpath(
                        './/div[@class="f-startTime f-times-con" and @data-v-55ab452e]/strong/text()'
                    )[0]
                    start_airport = content.xpath(
                        './/div[@class="f-startTime f-times-con" and @data-v-55ab452e]/em/text()'
                    )[0]
                    end_time = content.xpath(
                        './/div[@class="f-endTime f-times-con" and @data-v-55ab452e]/strong/text()'
                    )[0]
                    end_airport = content.xpath(
                        './/div[@class="f-endTime f-times-con" and @data-v-55ab452e]/em/text()'
                    )[0]
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

    def on_target_price(self, content):
        self.play_sound()
        self.write_history(content)
        self.show_notification("机票监测", f"航班的票价已低于设定值！{content}")
        print(f"{Fore.RED}航班的票价已低于设定值！{Style.RESET_ALL}")

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


if __name__ == "__main__":
    checker = Checker()

    try_count = 0

    while True:
        time.sleep(checker.interval + random.uniform(0, INTERVAL_RANDOM_MAX))
        try_count += 1
        print(f"第{try_count}次刷新")
        checker.check_tongcheng()
