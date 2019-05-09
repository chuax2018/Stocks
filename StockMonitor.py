from StockAssayer import StockAssayer
from Tracker import StockTracker
from Tools.File import File
from StockDataBaseManager import StockDataBaseManager
import itchat
import time
import os
import sys
import datetime
import socket
sys.path.append(os.path.abspath(".."))


def isNetOK(testserver):
    s = socket.socket()
    s.settimeout(3)
    try:
        status = s.connect_ex(testserver)
        if status == 0:
            s.close()
            return True
        else:
            return False
    except Exception as e:
        return False


def isNetChinaOK(testserver=('www.baidu.com', 443)):
    isOK = isNetOK(testserver)
    return isOK


def check_monitor_stocks_dir_validation(monitor_stocks_dir):
    # check all stocks listed in monitor_stocks.csv are in the dir.
    file_paths = File(monitor_stocks_dir).get_filepath_in_dir()
    monitor_stocks_csv_file = os.path.join(monitor_stocks_dir, "monitor_stocks.csv")
    if not os.path.exists(monitor_stocks_csv_file):
        return False
    else:
        stock_lines = open(monitor_stocks_csv_file, "r", encoding="utf-8").readlines()
        stock_lines.pop(0)  # delete the header
        for stock_line in stock_lines:
            stock_number = stock_line.split(",", 2)[1]
            stock_json_path = os.path.join(monitor_stocks_dir, stock_number + ".json")
            if stock_json_path not in file_paths:
                print("%s list in monitor_stocks.csv do not have the json file." % stock_number)
                return False
        return True


def send_message_to_wechat_freind(message):
    users = itchat.search_friends(name="cc")
    username = users[0]["UserName"]
    itchat.send(message, toUserName=username)


def run_monitor():
    if not isNetChinaOK():
        print("Error: Net connection is invalid! Quit!")
        return

    itchat.auto_login(hotReload=True)

    monitor_stocks_dir = r"C:\Data\Stock\TargetStocks"
    if not check_monitor_stocks_dir_validation(monitor_stocks_dir):
        print("monitor_stocks_dir validation check failed, quit...")
        return
    else:
        print("monitor_stocks_dir validation checked")

    database_path = r"C:\Data\Stock\StockDataBase"
    monitor_stocks_csv_file = os.path.join(monitor_stocks_dir, "monitor_stocks.csv")
    yesterday = datetime.date.today() + datetime.timedelta(-1)
    dbm = StockDataBaseManager()
    if not dbm.check_date_update_database(database_path, yesterday, monitor_stocks_csv_file): # todo
        print("update database failed.")
        return
    else:
        print("database has been updated.")

    ndays = 31
    chosen_stock_list_path = os.path.join(monitor_stocks_dir, "monitor_stocks.csv")
    stock_assayer = StockAssayer(database_path)
    stock_assayer.load_Stocks_internally(chosen_stock_list_path)
    stock_assayer.refresh_internal_stocks_by_ndays(ndays)
    print("target stocks have been loaded.")

    stock_trackers = []
    for stock in stock_assayer.stocks:
        st = StockTracker()
        st.init_value_by_config_dir(stock, monitor_stocks_dir)
        stock_trackers.append(st)
    print("%d stock trackers have been created." % len(stock_trackers))

    loop_index = 0
    while True:
        for stock_tracker in stock_trackers:
            stock_tracker.monitor_and_check()
        loop_index = loop_index + 1
        print("Monitoring %d loop done." % loop_index)
        time.sleep(10)

run_monitor()