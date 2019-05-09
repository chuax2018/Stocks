from Stock import *
import os
import sys
import shutil
import numpy as np
import matplotlib.pyplot as plt
from operator import attrgetter
sys.path.append(os.path.abspath(".."))
from Tools.File import *


min_days = 10  # csv file lines less than this, too less data, skip


class StockAssayer:
    def __init__(self, database_path):
        self.database_path = database_path
        self.stocks = []

    def interactive_mode(self):
        while True:
            print("give me your cmd quit: 0, show_volume: 1, print stockname: "
                  "2. show updowns: 3, change_sorted: 4, continues: 5")
            choice = input("your choice: ")
            if choice == "0":
                break
            elif choice == "1":
                stock_number = input("the stock number: ")
                found = False
                for stock in self.stocks:
                    if stock.stock_number == stock_number:
                        stock.show_nearest_ndays_volume()
                        found = True
                        break
                if not found:
                    print("could not find the stock you want: %s" % stock_number)
            elif choice == "2":
                for stock in self.stocks:
                    print("StockNumber: %s" % stock.stock_number)
            elif choice == "3":
                stock_number = input("the stock number: ")
                while True:
                    print("rise, fall, vibrate, change, break")
                    choice = input("your choice:")
                    if choice == "break":
                        break
                    else:
                        found = False
                        for stock in self.stocks:
                            if stock.stock_number == stock_number:
                                stock.show_nearest_ndays_updown(choice)
                                found = True
                                break
                        if not found:
                            print("could not find the stock you want: %s" % stock_number)
            elif choice == "4":
                stock_number = input("the stock number: ")
                found = False
                for stock in self.stocks:
                    if stock.stock_number == stock_number:
                        stock.show_nearest_ndays_change_sorted()
                        found = True
                        break
                if not found:
                    print("could not find the stock you want: %s" % stock_number)
            elif choice == "5":
                stock_number = input("the stock number: ")
                while True:
                    print("positive_continue_days: 0, positive_continue_change_percent: 1, "
                          "negative_continue_days: 2, negative_continue_change_percent: 3, break")
                    choice = input("your choice:")
                    if choice == "break":
                        break
                    else:
                        found = False
                        for stock in self.stocks:
                            if stock.stock_number == stock_number:
                                stock.show_nearest_ndays_continues(choice)
                                found = True
                                break
                        if not found:
                            print("could not find the stock you want: %s" % stock_number)

    def load_Stocks_internally(self, stock_target_list_path):
        lines = open(stock_target_list_path, "r", encoding="utf-8").readlines()
        stock_target_list = []
        for line in lines:
            stock_target_list.append(line.strip('\n').split(',', 2)[1])
        database_checker = File(self.database_path)
        target_stocks_num = len(stock_target_list)
        if not database_checker.exists():
            return False
        else:
            stock_folderpaths = database_checker.get_folderpath_in_dir()
            for stock_folderpath in stock_folderpaths:
                stock_number = File(stock_folderpath).get_foldername_by_path()
                if stock_number in stock_target_list:
                    stock_csv_path = os.path.join(stock_folderpath, stock_number + ".csv")
                    if not os.path.exists(stock_csv_path):
                        print("Warnning: %s does not exists, this stock skipped." % stock_csv_path)
                        continue
                    else:
                        stock = Stock()
                        stock.stock_number = stock_number
                        stock.stock_csv_path = stock_csv_path
                        stock.stock_folder_path = stock_folderpath
                        stock.parse_csv_fill_data()
                        if len(stock.stock_daily_data) < min_days:
                            print("Warning: Stock %s contains less than %d days data, skip it" % (stock_number, min_days))
                        else:
                            self.stocks.append(stock)
                            current_stocks_num = len(self.stocks)
                            if len(self.stocks) % 100 == 0:
                                print("%s stocks in %d have been loaded to mem" % (current_stocks_num, target_stocks_num))
            print("chosen Stocks have been load to mem.")
            return True

    def load_Stocks_2_Mem_for_thirdparty(self, target_stock_number_list):
        database_checker = File(self.database_path, verbose=False)
        if not database_checker.exists():
            return False
        else:
            stocks = []
            stock_folder_paths = database_checker.get_folderpath_in_dir()
            database_stock_numbers = []
            for stock_folder_path in stock_folder_paths:
                stock_number = File(stock_folder_path).get_foldername_by_path()
                database_stock_numbers.append(stock_number)

            target_stocks_num = len(target_stock_number_list)
            for target_stock_number in target_stock_number_list:
                if target_stock_number in database_stock_numbers:
                    database_stock_dir = os.path.join(self.database_path, target_stock_number)
                    stock_csv_path = os.path.join(database_stock_dir, target_stock_number + ".csv")
                    if not os.path.exists(stock_csv_path):
                        print("Warnning: %s does not exists, this stock skipped." % stock_csv_path)
                        continue
                    else:
                        stock = Stock()
                        stock.stock_number = target_stock_number
                        stock.stock_csv_path = stock_csv_path
                        stock.stock_folder_path = database_stock_dir
                        stock.parse_csv_fill_data()
                        if len(stock.stock_daily_data) < min_days:
                            print("Warning: Stock %s contains less than %d days data, skip it" % (stock_number, min_days))
                        else:
                            stocks.append(stock)
                            current_stocks_num = len(stocks)
                            if len(stocks) % 100 == 0:
                                print("%s stocks in %d have been loaded to mem" % (current_stocks_num, target_stocks_num))
            print("chosen Stocks have been load to mem.")
            return stocks

    def refresh_internal_stocks_by_ndays(self, ndays):  # do the ndays data calculation.
        self.ndays = ndays
        for stock in self.stocks:
            stock.init_value(ndays)

    def refresh_third_party_stocks_by_ndays(self, ndays, stocks):  # do the ndays data calculation.
        for stock in stocks:
            stock.init_value(ndays)
        return stocks

    # this method parse dir to get foldernames (stock numbers) to update.
    # goto database dir update the target stocks, then copy them to out dst_dir to get ndays data.
    def update_the_dir(self, need_update_dir, ndays):
        stock_numbers = []
        folderpaths = File(need_update_dir).get_folderpath_in_dir()
        for folderpath in folderpaths:
            stock_number = File(folderpath).get_foldername_by_path()
            stock_numbers.append(stock_number)

        stocks = self.load_Stocks_2_Mem_for_thirdparty(stock_numbers)
        for stock in stocks:
            stock.init_value(ndays)
            stock.write_the_data()
            src_dir = stock.stock_folder_path
            dst_dir = os.path.join(need_update_dir, stock.stock_number)
            if File(dst_dir).exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)

    # this method write inited stocks data to dst dir
    def dump_stocks_to_dir(self, stocks, dir): # these stocks should have been inited the value.
        for stock in stocks:
            stock.write_the_data()
            src_dir = stock.stock_folder_path
            dst_dir = os.path.join(dir, stock.stock_number)
            if File(dst_dir).exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)

    def sort_stocks_by_attr_return_n(self, stocks, attribute, max_num=0, ele_percent=0.5):
        def get_valid_num(list, max_num, ele_percent):
            num = 0
            list_num = len(list)
            if max_num > 0:
                if list_num < max_num:
                    num = list_num
                else:
                    num = max_num
            elif max_num == 0:
                num = int(ele_percent * list_num)
            else:
                print("max_num: %d is invalid." % max_num)
            return num

        num = get_valid_num(stocks, max_num, ele_percent)
        if attribute in ["growth", "rise_ratio", "pcd_cov", "pcc_cov", "ncd_cov", "ncc_cov"]:
            if attribute == "growth":
                attribute_fullname = "growth_in_ndays"
                sorted_stocks = sorted(stocks, key=(attrgetter(attribute_fullname)), reverse=True)
                return sorted_stocks[:num]
            elif attribute == "rise_ratio":
                attribute_fullname = "rise_ratio_in_ndays"
                sorted_stocks = sorted(stocks, key=(attrgetter(attribute_fullname)), reverse=True)
                return sorted_stocks[:num]
            elif attribute == "pcd_cov":
                attribute_fullname = "positive_continue_days_cov"
                sorted_stocks = sorted(stocks, key=(attrgetter(attribute_fullname)), reverse=False)
                return sorted_stocks[:num]
            elif attribute == "pcc_cov":
                attribute_fullname = "positive_continue_change_percent_cov"
                sorted_stocks = sorted(stocks, key=(attrgetter(attribute_fullname)), reverse=False)
                return sorted_stocks[:num]
            elif attribute == "ncd_cov":
                attribute_fullname = "negative_continue_days_cov"
                sorted_stocks = sorted(stocks, key=(attrgetter(attribute_fullname)), reverse=False)
                return sorted_stocks[:num]
            elif attribute == "ncc_cov":
                attribute_fullname = "negative_continue_change_percent_cov"
                sorted_stocks = sorted(stocks, key=(attrgetter(attribute_fullname)), reverse=False)
                return sorted_stocks[:num]
        else:
            print("Error: sort unsupported attribute \"%s\"" % attribute)
            return None

    def show_package_stocks_info(self, stocks, ndays, show=True):
        self.show_section_stocks_rise_counts_ndays(stocks, ndays, show)
        self.show_section_stocks_rise_percent_ndays(stocks, ndays, show)

    def show_section_stocks_rise_counts_ndays(self, stocks, ndays, show=True):

        stock_daily_rise_ndays = []
        for i in range(ndays):
            stock_daily_rise_ndays.append(0)

        valid_stocks =[]
        for stock in stocks:
            if len(stock.stock_daily_data) > ndays:
                valid_stocks.append(stock)

        total_stocks_num = len(valid_stocks)
        for stock in valid_stocks:
            ndays_daily_data_list = stock.stock_daily_data[-ndays:]
            for i in range(ndays):
                if ndays_daily_data_list[i].change_percent >= 0:
                    stock_daily_rise_ndays[i] = stock_daily_rise_ndays[i] + 1

        # do the plot.
        fig, ax = plt.subplots()
        positions = np.arange(1, ndays + 1)
        ax.bar(positions, stock_daily_rise_ndays, 0.5)
        plt.title(f"{total_stocks_num} stocks rise counts")
        plt.xlabel('nearest ' + str(ndays) + " days")
        plt.ylabel('stock daily rise counts')
        if show:
            plt.show()
        else:
            plot_filename = "nearest_" + str(ndays) + "_days_" + "stocks_rise_counts.pdf"
            dir_up = os.path.abspath(os.path.join(self.database_path, ".."))
            database_output_folder_path = os.path.join(dir_up, "StockDataBase_OUTPUT")
            File(database_output_folder_path).mkdirs()
            plot_path = os.path.join(database_output_folder_path, plot_filename)
            plt.savefig(plot_path)
        plt.close()

    def show_section_stocks_rise_percent_ndays(self, stocks, ndays, show=True):

        stock_daily_rise_percent_ndays = []
        for i in range(ndays):
            stock_daily_rise_percent_ndays.append(0.0)

        valid_stocks =[]
        for stock in stocks:
            if len(stock.stock_daily_data) > ndays:
                valid_stocks.append(stock)

        total_stocks_num = len(valid_stocks)
        for stock in valid_stocks:
            ndays_daily_data_list = stock.stock_daily_data[-ndays:]
            for i in range(ndays):
                stock_daily_rise_percent_ndays[i] = \
                    stock_daily_rise_percent_ndays[i] + ndays_daily_data_list[i].change_percent

        # do the plot.
        fig, ax = plt.subplots()
        positions = np.arange(1, ndays + 1)
        ax.bar(positions, stock_daily_rise_percent_ndays, 0.5)
        plt.title(f"{total_stocks_num} stocks rise percent")
        plt.xlabel('nearest ' + str(ndays) + " days")
        plt.ylabel('stock daily rise percent')
        if show:
            plt.show()
        else:
            plot_filename = "nearest_" + str(ndays) + "_days_" + "stocks_rise_counts.pdf"
            dir_up = os.path.abspath(os.path.join(self.database_path, ".."))
            database_output_folder_path = os.path.join(dir_up, "StockDataBase_OUTPUT")
            File(database_output_folder_path).mkdirs()
            plot_path = os.path.join(database_output_folder_path, plot_filename)
            plt.savefig(plot_path)
        plt.close()


if __name__ == "__main__":
    database_path = r"C:\Data\Stock\StockDataBase"
    a = StockAssayer(database_path)
    a.update_the_dir(r"C:\Data\Stock\my_stock_list", 30)
    chosen_stock_list_path = r"C:\Data\Stock\chosen_stock_list.txt"
    # chosen_stock_list_path = r"C:\Data\Stock\TargetStocks\monitor_stocks.csv"
    a.load_Stocks_internally(chosen_stock_list_path)
    a.refresh_internal_stocks_by_ndays(30)
    # a.show_package_stocks_info(a.stocks, 10)
    stocks_rise_ratio = a.sort_stocks_by_attr_return_n(a.stocks, "rise_ratio", max_num=10)
    # stocks_pcd_cov = a.sort_stocks_by_attr_return_n(a.stocks, "pcd_cov", max_num=10)
    # stocks_pcc_cov = a.sort_stocks_by_attr_return_n(stocks_pcd_cov, "pcc_cov")
    # stocks_ncd_cov = a.sort_stocks_by_attr_return_n(a.stocks, "ncd_cov", max_num=50)
    # stocks_ncc_cov = a.sort_stocks_by_attr_return_n(a.stocks, "ncc_cov", max_num=10)
    # stocks_growth = a.sort_stocks_by_attr_return_n(a.stocks, "growth", max_num=10)
    # stocks_ncc_cov_0 = a.sort_stocks_by_attr_return_n(stocks_growth, "ncc_cov")
    # stocks_pcc_cov_1 = a.sort_stocks_by_attr_return_n(stocks_ncc_cov_0, "pcc_cov")
    dst_dir = r"C:\Data\Stock\copyhere_30day_riseratio_stocks"
    a.update_the_dir(dst_dir, 30)
    a.dump_stocks_to_dir(stocks_rise_ratio, dst_dir)

    dst_dir2 = r"C:\Data\Stock\copyhere_top10_ncc_cov"
    # a.dump_stocks_to_dir(stocks_ncc_cov, dst_dir2)

    print("done")
    # a.interactive_mode()