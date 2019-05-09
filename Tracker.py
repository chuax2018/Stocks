import tushare as ts
import time
import os
import json
import itchat


class StockTracker:
    def __init__(self):
        # init by stock return by StockAssayer
        self.stock_number = ""
        self.p_continue_change_percent = 0.0
        self.n_continue_change_percent = 0.0
        self.p_continue_days = 0
        self.n_continue_days = 0
        self.rise_percent_avg = 0.0
        self.fall_percent_avg = 0.0

        self.check_mask = []
        # alarm value, parse from stock.json
        self.price_alarm_max = 0.0
        self.price_alarm_min = 0.0
        self.p_continue_change_percent_max = 0.0
        self.n_continue_change_percent_max = 0.0
        self.p_continue_days_max = 0
        self.n_continue_days_max = 0
        self.daily_rise_percent_max = 0.0
        self.daily_fall_percent_max = 0.0
        self.volume_alarm_max = 0

        # we want the message to be sent once a day, or will be too sensitive and annoying
        # (need restart this program every day.)
        self.price_alarm_max_sent = False
        self.price_alarm_min_sent = False
        self.p_continue_change_percent_max_sent = False
        self.n_continue_change_percent_max_sent = False
        self.p_continue_days_max_sent = False
        self.n_continue_days_max_sent = False
        self.daily_rise_percent_max_sent = False
        self.daily_fall_percent_max_sent = False
        self.volume_alarm_max_sent = False

        # from tushare
        self.today_open = 0.0
        self.current_price = 0.0
        self.current_percent = 0.0
        self.current_volume = 0
        self.today_rise = 0
        self.today_fall = 0

    def init_value_by_config_dir(self, stock, trace_folder_dir):
        self.init_by_stock(stock)
        if not self.init_by_json(trace_folder_dir):
            return False

    def init_by_stock(self, stock):
        self.stock_number = stock.stock_number
        if stock.stock_daily_data[-1].change_percent >= 0:  # check yesterday change percent to focus on p or n.
            self.n_continue_change_percent_max_sent = True
            self.n_continue_days_max_sent = True
        else:
            self.p_continue_change_percent_max_sent = True
            self.p_continue_days_max_sent = True
        self.p_continue_change_percent = stock.positive_continue_change_percent[-1]
        self.n_continue_change_percent = stock.negative_continue_change_percent[-1]
        self.p_continue_days = stock.positive_continue_days[-1]
        self.n_continue_days = stock.negative_continue_days[-1]
        self.rise_percent_avg = stock.rise_percent_avg
        self.fall_percent_avg = stock.fall_percent_avg

    def init_by_json(self, trace_folder_dir):
        stock_json_path = os.path.join(trace_folder_dir, self.stock_number + ".json")
        content_dict = {}
        with open(stock_json_path, "r", encoding="utf-8") as filehandle:
            content_dict = json.load(filehandle)

        stock_number_json = content_dict["stock_number"]
        if self.stock_number != stock_number_json:
            print("stock number %s is not the same with the number %s in json file" %
                  (self.stock_number, stock_number_json))
            return False
        self.price_alarm_max = content_dict["price_alarm_max"]
        self.price_alarm_min = content_dict["price_alarm_min"]
        self.p_continue_change_percent_max = content_dict["p_continue_change_percent_max"]
        self.n_continue_change_percent_max = content_dict["n_continue_change_percent_max"]
        self.p_continue_days_max = content_dict["p_continue_days_max"]
        self.n_continue_days_max = content_dict["n_continue_days_max"]
        self.daily_rise_percent_max = content_dict["daily_rise_percent_max"]
        self.daily_fall_percent_max = content_dict["daily_fall_percent_max"]
        self.volume_alarm_max = content_dict["volume_alarm_max"]

        if self.price_alarm_max != 0:
            self.check_mask.append("check_price_max")
        if self.price_alarm_min != 0:
            self.check_mask.append("check_price_min")
        if self.p_continue_change_percent_max != 0:
            self.check_mask.append("check_pcc_max")
        if self.n_continue_change_percent_max != 0:
            self.check_mask.append("check_ncc_max")
        if self.p_continue_days_max != 0:
            self.check_mask.append("check_pcd_max")
        if self.n_continue_days_max != 0:
            self.check_mask.append("check_ncd_max")
        if self.daily_rise_percent_max != 0:
            self.check_mask.append("check_rise_percent_max")
        if self.daily_fall_percent_max != 0:
            self.check_mask.append("check_fall_percent_max")
        if self.volume_alarm_max != 0:
            self.check_mask.append("check_volume_max")

        return True

    def send_message_to_wechat_friend(self, message):
        users = itchat.search_friends(name="cc")
        username = users[0]["UserName"]
        itchat.send(message, toUserName=username)

    def monitor_and_check(self):
        df = ts.get_realtime_quotes(self.stock_number)
        stock_name = df.loc[0, "name"]
        stock_pre_close = float(df.loc[0, "pre_close"])
        realtime_stock_number = df.loc[0, "code"]
        self.today_open = float(df.loc[0, "open"])
        self.current_price = float(df.loc[0, "price"])
        self.current_percent = round((self.current_price - stock_pre_close) / stock_pre_close, 4)
        self.current_volume = int(df.loc[0, "volume"])

        if self.stock_number != realtime_stock_number:
            print("Error: Tracking %s but get %s realtime data." % (self.stock_number, realtime_stock_number))
            return

        updated = self.p_continue_days_max_sent and self.n_continue_days_max_sent
        if not updated:
            if self.current_percent > self.rise_percent_avg:
                self.today_rise = 1
                self.today_fall = 0
            if self.current_percent < self.fall_percent_avg:
                self.today_rise = 0
                self.today_fall = 1

        for mask in self.check_mask:
            if mask == "check_price_max" and not self.price_alarm_max_sent:
                if self.current_price > self.price_alarm_max:
                    message = f"{stock_name} {self.stock_number} 当前价: {self.current_price} " \
                        f"已超过提醒价: {self.price_alarm_max}, 可以考虑卖出"
                    self.send_message_to_wechat_friend(message)
                    self.price_alarm_max_sent = True

            elif mask == "check_price_min" and not self.price_alarm_min_sent:
                if self.current_price < self.price_alarm_min:
                    message = f"{stock_name} {self.stock_number} 当前价: {self.current_price} " \
                        f"已低于提醒价: {self.price_alarm_min}, 可以考虑买入"
                    self.send_message_to_wechat_friend(message)
                    self.price_alarm_min_sent = True

            elif mask == "check_volume_max" and not self.volume_alarm_max_sent:
                if self.current_volume > self.volume_alarm_max:
                    message = f"{stock_name} {self.stock_number} 当前成交量: {self.current_volume} " \
                        f"已达到提醒阈值: {self.volume_alarm_max}, 可能有异常"
                    self.send_message_to_wechat_friend(message)
                    self.volume_alarm_max_sent = True

            elif mask == "check_rise_percent_max" and not self.daily_rise_percent_max_sent:
                if self.current_percent > self.daily_rise_percent_max:
                    message = f"{stock_name} {self.stock_number} 今日涨幅: {self.current_percent} " \
                        f"已达到每日阈值: {self.daily_rise_percent_max}, 可以考虑卖出"
                    self.send_message_to_wechat_friend(message)
                    self.daily_rise_percent_max_sent = True

            elif mask == "check_fall_percent_max" and not self.daily_fall_percent_max_sent:
                if self.current_percent < self.daily_fall_percent_max:
                    message = f"{stock_name} {self.stock_number} 今日跌幅: {self.current_percent} " \
                        f"已达到每日阈值: {self.daily_fall_percent_max}, 今天大趋势下跌, 可以考虑补仓或者卖出"
                    self.send_message_to_wechat_friend(message)
                    self.daily_fall_percent_max_sent = True

            elif mask == "check_pcc_max" and not self.p_continue_change_percent_max_sent:
                if self.p_continue_change_percent + self.current_percent > self.p_continue_change_percent_max:
                    message = f"{stock_name} {self.stock_number} 连续涨幅: " \
                        f"{round(self.p_continue_change_percent + self.current_percent, 4)} 已达到阈值:" \
                        f" {self.p_continue_change_percent_max}, 可以考虑卖出"
                    self.send_message_to_wechat_friend(message)
                    self.p_continue_change_percent_max_sent = True

            elif mask == "check_ncc_max" and not self.n_continue_change_percent_max_sent:
                if self.n_continue_change_percent + self.current_percent < self.n_continue_change_percent_max:
                    message = f"{stock_name} {self.stock_number} 连续跌幅: " \
                        f"{round(self.n_continue_change_percent + self.current_percent, 4)} 已达到阈值: " \
                        f"{self.n_continue_change_percent_max}, 可以考虑买入"
                    self.send_message_to_wechat_friend(message)
                    self.n_continue_change_percent_max_sent = True

            elif mask == "check_pcd_max" and not self.p_continue_days_max_sent:
                if self.p_continue_days + 1 >= self.p_continue_days_max:
                    if self.p_continue_days + self.today_rise == self.p_continue_days_max or \
                            self.p_continue_days >= self.p_continue_days_max:
                        message = f"{stock_name} {self.stock_number} 连续上涨天数: " \
                            f"{self.p_continue_days + self.today_rise} 已达到阈值: {self.p_continue_days_max}, 可以考虑卖出"
                        self.send_message_to_wechat_friend(message)
                        self.p_continue_days_max_sent = True

            elif mask == "check_ncd_max" and not self.n_continue_days_max_sent:
                if self.n_continue_days + 1 >= self.n_continue_days_max:
                    if self.n_continue_days + self.today_fall == self.n_continue_days_max or \
                            self.n_continue_days >= self.n_continue_days_max:
                        message = f"{stock_name} {self.stock_number} 连续下跌天数: " \
                            f"{self.n_continue_days + self.today_fall} 已达到阈值: {self.n_continue_days_max}, 可以考虑买入"
                        self.send_message_to_wechat_friend(message)
                        self.n_continue_days_max_sent = True
            # contibue fall and watch the day rise or ndays rise will be concidered


if __name__ == "__main__":
    t = StockTracker()
    t.monitor_and_check()

    # test()