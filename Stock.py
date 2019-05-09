import os
import sys
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath(".."))
from Tools.File import *


def calc_cov(list):
    mean = np.mean(list)
    std = np.std(list, ddof=1)
    cov = round(abs(std/mean), 5)
    return mean, cov


# skip first one
def calc_accum_percent(list):
    r = 1
    for i in range(len(list)):
        if i == 0:  # skip the first day
            continue
        r = r * (1 + list[i])
    return r


def get_continuous_interval(x_list, y_list):
    if len(x_list) != len(y_list):
        print("Error: two list not the same counts, quit...")
        return

    counts = len(x_list)

    x_list_split = []
    y_list_split = []
    x_temp_list = []
    y_temp_list = []
    for i in range(counts):
        if len(x_temp_list) == 0:
            x_temp_list.append(x_list[i])
            y_temp_list.append(y_list[i])
        else:
            if x_list[i] - x_temp_list[-1] == 1:
                x_temp_list.append(x_list[i])
                y_temp_list.append(y_list[i])
            else:
                # x_temp_list_copy = x_temp_list
                def copy_list(src_list):
                    temp_list = []
                    for each in src_list:
                        temp_list.append(each)
                    return temp_list

                x_list_split.append(copy_list(x_temp_list))
                x_temp_list.clear()
                x_temp_list.append(x_list[i])
                y_list_split.append(copy_list(y_temp_list))
                y_temp_list.clear()
                y_temp_list.append(y_list[i])
    if len(x_temp_list) != 0:
        x_list_split.append(x_temp_list)
        y_list_split.append(y_temp_list)

    if len(x_list_split) != len(y_list_split):
        print("Error: two list not the same counts, quit...")
        return

    return x_list_split, y_list_split


class StockDailyData:
    def __init__(self):
        self.date = ''
        self.open = 0
        self.close = 0
        self.high = 0
        self.low = 0
        self.volume = 0

        self.rise_percent = 0.0
        self.fall_percent = 0.0
        self.vibrate_percent = 0.0
        self.change_percent = 0.0


class Stock:
    def __init__(self):
        self.stock_number = 0
        self.stock_folder_path = ""
        self.stock_csv_path = ""
        self.stock_daily_data = []

        # this data will be filled by StockAssayer cmd.
        self.ndays = 0
        self.stock_daily_data_ndays = []
        self.growth_in_ndays = 0.0
        self.vibrate_percent_accum_ndays = 0.0
        self.rise_ratio_in_ndays = 0.0

        self.daily_rise_percent_ndays = []
        self.daily_rise_percent_ndays_mean = 0.0
        self.daily_rise_percent_ndays_cov = 0.0

        self.daily_fall_percent_ndays = []
        self.daily_fall_percent_ndays_mean = 0.0
        self.daily_fall_percent_ndays_cov = 0.0
        self.daily_vibrate_percent_ndays = []
        self.daily_vibrate_percent_ndays_mean = 0.0
        self.daily_vibrate_percent_ndays_cov = 0.0
        self.daily_change_percent_ndays = []
        self.daily_change_percent_ndays_mean = 0.0
        self.daily_change_percent_ndays_cov = 0.0

        self.rise_percent_avg = 0.0
        self.fall_percent_avg =0.0

        self.positive_day_regroup = []
        self.positive_change_percent_regroup = []
        self.negative_day_regroup = []
        self.negative_change_percent_regroup = []

        self.positive_continue_days = []
        self.positive_continue_days_cov = 0.0
        self.positive_continue_change_percent = []
        self.positive_continue_change_percent_cov = 0.0
        self.negative_continue_days = []
        self.negative_continue_days_cov = 0.0
        self.negative_continue_change_percent = []
        self.negative_continue_change_percent_cov = 0.0

    def parse_csv_fill_data(self):
        # the first row is label not data.
        valid_row_counts = len(open(self.stock_csv_path, "r", encoding="utf-8").readlines()) - 1
        stock = pd.read_csv(self.stock_csv_path, index_col=0)
        for row in range(valid_row_counts):
            stock_daily_data = StockDailyData()
            stock_daily_data.date = stock.loc[row, 'date']
            stock_daily_data.open = stock.loc[row, 'open']
            stock_daily_data.close = stock.loc[row, 'close']
            stock_daily_data.high = stock.loc[row, 'high']
            stock_daily_data.low = stock.loc[row, 'low']
            stock_daily_data.volume = stock.loc[row, 'volume']
            self.stock_daily_data.append(stock_daily_data)

    def continues_change_filter(self):
        pass

    def init_value(self, ndays):
        def get_continue_start_list(stockdailydata, ndays):
            if ndays >= len(stockdailydata):
                ndays = len(stockdailydata) - 1

            target_list = stockdailydata[-ndays:]
            rest_list = stockdailydata[:-ndays]
            rest_list.reverse()
            rise = False
            if target_list[0].close >= rest_list[0].close:
                rise = True
            # we get the list full of continue ones at start:
            for i in range(len(rest_list)):
                if i < len(rest_list) - 1:
                    result = False
                    if rest_list[i].close >= rest_list[i+1].close:
                        result = True
                    if result != rise:
                        break
                    if result == rise:
                        ndays = ndays + 1
            return ndays

        ndays = get_continue_start_list(self.stock_daily_data, ndays)
        self.ndays = ndays
        ndays_stock_data = self.stock_daily_data[-(ndays + 1):]
        for i in range(ndays + 1):
            if i == 0:
                continue  # the first day is added for the rest calculation, so skip it.
            else:
                yesterday_data = ndays_stock_data[i - 1]
                daily_data = ndays_stock_data[i]
                daily_data.rise_percent = round((daily_data.high - yesterday_data.close) / yesterday_data.close, 4)
                daily_data.fall_percent = round((daily_data.low - yesterday_data.close) / yesterday_data.close, 4)
                daily_data.vibrate_percent = round((daily_data.high - daily_data.low) / yesterday_data.close, 4)
                daily_data.change_percent = round((daily_data.close - yesterday_data.close) / yesterday_data.close, 4)

        nearest_ndays_list = self.stock_daily_data[-ndays:]
        self.stock_daily_data_ndays = nearest_ndays_list

        for daily_data in nearest_ndays_list:
            self.daily_rise_percent_ndays.append(daily_data.rise_percent)
            self.daily_fall_percent_ndays.append(daily_data.fall_percent)
            self.daily_vibrate_percent_ndays.append(daily_data.vibrate_percent)
            self.daily_change_percent_ndays.append(daily_data.change_percent)

        self.vibrate_percent_accum_ndays = calc_accum_percent(self.daily_vibrate_percent_ndays)
        self.daily_rise_percent_ndays_mean, self.daily_rise_percent_ndays_cov = \
            calc_cov(self.daily_rise_percent_ndays)
        self.daily_fall_percent_ndays_mean, self.daily_fall_percent_ndays_cov = \
            calc_cov(self.daily_fall_percent_ndays)
        self.daily_vibrate_percent_ndays_mean, self.daily_vibrate_percent_ndays_cov = \
            calc_cov(self.daily_vibrate_percent_ndays)
        self.daily_change_percent_ndays_mean, self.daily_change_percent_ndays_cov = \
            calc_cov(self.daily_change_percent_ndays)

        positions = np.arange(1, ndays + 1)
        change_percent_list = []
        for daily_data in nearest_ndays_list:
            change_percent_list.append(daily_data.change_percent)

        self.growth_in_ndays = round(
            (nearest_ndays_list[-1].close - nearest_ndays_list[0].close) / nearest_ndays_list[0].close + 1, 4)

        positive_change_percent = []
        positive_day = []

        negative_change_percent = []
        negative_day = []

        for i in range(ndays):
            if change_percent_list[i] >= 0:
                positive_change_percent.append(change_percent_list[i])
                positive_day.append(positions[i])
            else:
                negative_change_percent.append(change_percent_list[i])
                negative_day.append(positions[i])

        self.rise_percent_avg = round(np.mean(positive_change_percent),3)
        self.fall_percent_avg = round(np.mean(negative_change_percent),3)

        up_days = len(positive_change_percent)
        down_days = len(negative_change_percent)

        self.rise_ratio_in_ndays = round(up_days / (up_days + down_days), 2)

        self.positive_day_regroup, self.positive_change_percent_regroup = \
            get_continuous_interval(positive_day, positive_change_percent)
        self.negative_day_regroup, self.negative_change_percent_regroup = \
            get_continuous_interval(negative_day, negative_change_percent)

        def format_list_by_len(list):
            temp = []
            for each in list:
                temp.append(len(each))
            return temp

        def format_list_by_value(list):
            temp = []
            for each in list:
                temp.append(round(sum(each), 3))
            return temp

        self.positive_continue_days = format_list_by_len(self.positive_day_regroup)
        self.positive_continue_change_percent = format_list_by_value(self.positive_change_percent_regroup)
        self.negative_continue_days = format_list_by_len(self.negative_day_regroup)
        self.negative_continue_change_percent = format_list_by_value(self.negative_change_percent_regroup)

        _, self.positive_continue_days_cov = calc_cov(self.positive_continue_days)
        _, self.positive_continue_change_percent_cov = calc_cov(self.positive_continue_change_percent)
        _, self.negative_continue_days_cov = calc_cov(self.negative_continue_days)
        _, self.negative_continue_change_percent_cov = calc_cov(self.negative_continue_change_percent)
        # self.negative_continue_change_percent_cov = - self.negative_continue_change_percent_cov

    def show_nearest_ndays_change_sorted(self, show=True):
        nearest_ndays_list = self.stock_daily_data_ndays
        start_date = nearest_ndays_list[0].date
        end_date = nearest_ndays_list[-1].date
        period = self.stock_number + " " + start_date + " ~ " + end_date

        for i in range(len(self.positive_day_regroup)):
            positive_x_group = self.positive_day_regroup[i]
            positive_y_group = self.positive_change_percent_regroup[i]
            plt.plot(positive_x_group, positive_y_group, marker='+', color='red')

        for i in range(len(self.negative_day_regroup)):
            negative_x_group = self.negative_day_regroup[i]
            negative_y_group = self.negative_change_percent_regroup[i]
            plt.plot(negative_x_group, negative_y_group, marker='x', color='green')

        plt.title(period)
        plt.xlabel('nearest ' + str(self.ndays) + " days")
        plt.ylabel("change_percent_sorted")

        if show:
            plt.show()
        else:
            plot_filename = "nearest " + str(self.ndays) + " days " + "change_percent_sorted.pdf"
            dst_plot_path = os.path.join(self.stock_folder_path, plot_filename)
            plt.savefig(dst_plot_path)
        plt.close()

    def show_nearest_ndays_updown(self, choice, show=True):
        nearest_ndays_list = self.stock_daily_data_ndays
        start_date = nearest_ndays_list[0].date
        end_date = nearest_ndays_list[-1].date
        period = self.stock_number + " " + start_date + " ~ " + end_date

        positions = np.arange(1, self.ndays + 1)
        list = []
        choose_kind = ""
        for daily_data in nearest_ndays_list:
            if choice == "rise":
                list.append(daily_data.rise_percent)
                choose_kind = "rise_percent"
            elif choice == "fall":
                list.append(daily_data.fall_percent)
                choose_kind = "fall_percent"
            elif choice == "vibrate":
                list.append(daily_data.vibrate_percent)
                choose_kind = "vibrate_percent"
            elif choice == "change":
                list.append(daily_data.change_percent)
                choose_kind = "change_percent"
            else:
                print("Error: wrong parameter. You can choose 'rise', 'fall', 'vibrate', 'change' these 4! quit...")
        if not list:
            return

        plt.scatter(positions, list)
        plt.title(period)
        plt.xlabel('nearest ' + str(self.ndays) + " days")
        plt.ylabel(choose_kind)

        if show:
            plt.show()
        else:
            plot_filename = "nearest " + str(self.ndays) + " days " + str(choose_kind) + ".pdf"
            dst_plot_path = os.path.join(self.stock_folder_path, plot_filename)
            plt.savefig(dst_plot_path)
        plt.close()

    def show_nearest_ndays_rise_fall(self, show=True):
        nearest_ndays_list = self.stock_daily_data_ndays
        start_date = nearest_ndays_list[0].date
        end_date = nearest_ndays_list[-1].date
        period = self.stock_number + " " + start_date + " ~ " + end_date

        positions = np.arange(1, self.ndays + 1)
        rise_list = self.daily_rise_percent_ndays
        fall_list = self.daily_fall_percent_ndays
        close_list = self.daily_change_percent_ndays

        # do the line
        for i in range(len(positions)):
            x_list = []
            y_list = []

            x_list.append(positions[i])
            x_list.append(positions[i])

            y_list.append(fall_list[i])
            y_list.append(rise_list[i])

            plt.plot(x_list, y_list, color='0.5')

        y_zero_list = [0] * len(positions)
        plt.plot(positions, y_zero_list, color='0.3')

        # do the pointer
        plt.scatter(positions, rise_list, marker="+", c="red")
        plt.scatter(positions, fall_list, marker="x", c="green")
        plt.scatter(positions, close_list, marker="o", c="blue")

        plt.title(period)
        plt.xlabel('nearest ' + str(self.ndays) + " days")
        plt.ylabel("ndays rise fall")

        if show:
            plt.show()
        else:
            plot_filename = "nearest " + str(self.ndays) + " days " + "rise fall" + ".pdf"
            dst_plot_path = os.path.join(self.stock_folder_path, plot_filename)
            plt.savefig(dst_plot_path)
        plt.close()

    def show_nearest_ndays_continues(self, choice, show=True):
        nearest_ndays_list = self.stock_daily_data_ndays
        start_date = nearest_ndays_list[0].date
        end_date = nearest_ndays_list[-1].date
        period = self.stock_number + " " + start_date + " ~ " + end_date

        list = []
        choose_kind = ""
        if choice == "0":
            choose_kind = "positive_continue_days"
            list = self.positive_continue_days
        elif choice == "1":
            choose_kind = "positive_continue_change_percent"
            list = self.positive_continue_change_percent
        elif choice == "2":
            choose_kind = "negative_continue_days"
            list = self.negative_continue_days
        elif choice == "3":
            choose_kind = "negative_continue_change_percent"
            list = self.negative_continue_change_percent
        else:
            print(
                "Error: wrong parameter. You can choose 'rise', 'fall', 'vibrate', 'change' these 4! quit...")
        if not list:
            return

        positions = np.arange(1, len(list) + 1)

        plt.scatter(positions, list)
        plt.title(period)
        plt.xlabel('nearest ' + str(self.ndays) + " days")
        plt.ylabel(choose_kind)

        if show:
            plt.show()
        else:
            plot_filename = "nearest " + str(self.ndays) + " days " + str(choose_kind) + ".pdf"
            dst_plot_path = os.path.join(self.stock_folder_path, plot_filename)
            plt.savefig(dst_plot_path)
        plt.close()


    def show_nearest_ndays_volume(self, show=True):
        nearest_ndays_list = self.stock_daily_data_ndays
        start_date = nearest_ndays_list[0].date
        end_date = nearest_ndays_list[-1].date
        period = self.stock_number + " " + start_date + " ~ " + end_date

        volumes = []
        for daily_data in nearest_ndays_list:
            volumes.append(daily_data.volume)

        # do the plot.
        fig, ax = plt.subplots()
        positions = np.arange(1, self.ndays + 1)
        ax.bar(positions, volumes, 0.5)
        plt.title(period)
        plt.xlabel('nearest ' + str(self.ndays) + " days")
        plt.ylabel('volume')
        if show:
            plt.show()
        else:
            volume_plot_filename = "nearest " + str(self.ndays) + " days " + "volume.pdf"
            volume_plot_path = os.path.join(self.stock_folder_path, volume_plot_filename)
            plt.savefig(volume_plot_path)
        plt.close()

    def do_cleaning(self):
        first_layer_folderpaths = File(self.stock_folder_path).get_folderpath_in_dir()
        for first_layer_folderpath in first_layer_folderpaths:
            shutil.rmtree(first_layer_folderpath)
        # after delete all the folders in this dir, we then can clean the files not needed.
        filepaths = File(self.stock_folder_path).get_filepath_in_dir()
        for filepath in filepaths:
            if filepath != self.stock_csv_path:
                os.remove(filepath)

    def write_stock_bref(self):
        bref_filepath = os.path.join(self.stock_folder_path, self.stock_number + ".txt")
        with open(bref_filepath, "w") as filehandle:
            filehandle.write("ndays: %d\n" % self.ndays)
            filehandle.write("start_date: %s\n" % self.stock_daily_data_ndays[0].date)
            filehandle.write("end_date: %s\n" % self.stock_daily_data_ndays[-1].date)
            filehandle.write("growth_in_ndays: %f\n" % self.growth_in_ndays)
            filehandle.write("vibrate_percent_accum_ndays: %f\n" % self.vibrate_percent_accum_ndays)
            filehandle.write("rise_days_ratio_in_ndays: %f\n" % self.rise_ratio_in_ndays)
            filehandle.write("daily_rise_percent_ndays: " + str(self.daily_rise_percent_ndays) + "\n")
            filehandle.write("daily_rise_percent_ndays_mean: %f\n" % self.daily_rise_percent_ndays_mean)
            filehandle.write("daily_rise_percent_ndays_cov: %f\n" % self.daily_rise_percent_ndays_cov)
            filehandle.write("daily_fall_percent_ndays: " + str(self.daily_fall_percent_ndays) + "\n")
            filehandle.write("daily_fall_percent_ndays_mean: %f\n" % self.daily_fall_percent_ndays_mean)
            filehandle.write("daily_fall_percent_ndays_cov: %f\n" % self.daily_fall_percent_ndays_cov)
            filehandle.write("daily_vibrate_percent_ndays: " + str(self.daily_vibrate_percent_ndays) + "\n")
            filehandle.write("daily_vibrate_percent_ndays_mean: %f\n" % self.daily_vibrate_percent_ndays_mean)
            filehandle.write("daily_vibrate_percent_ndays_cov: %f\n" % self.daily_vibrate_percent_ndays_cov)
            filehandle.write("daily_change_percent_ndays: " + str(self.daily_change_percent_ndays) + "\n")
            filehandle.write("daily_change_percent_ndays_mean: %f\n" % self.daily_change_percent_ndays_mean)
            filehandle.write("daily_change_percent_ndays_cov: %f\n" % self.daily_change_percent_ndays_cov)
            filehandle.write("positive_continue_days_cov: %f\n" % self.positive_continue_days_cov)
            filehandle.write("positive_continue_change_percent_cov: %f\n" % self.positive_continue_change_percent_cov)
            filehandle.write("negative_continue_days_cov: %f\n" % self.negative_continue_days_cov)
            filehandle.write("negative_continue_change_percent_cov: %f\n" % self.negative_continue_change_percent_cov)
            filehandle.write("positive_day_regroup: " + str(self.positive_day_regroup) + "\n")
            filehandle.write("positive_change_percent_regroup: " + str(self.positive_change_percent_regroup) + "\n")
            filehandle.write("negative_day_regroup: " + str(self.negative_day_regroup) + "\n")
            filehandle.write("negative_change_percent_regroup: " + str(self.negative_change_percent_regroup) + "\n")
            filehandle.write("positive_continue_days: " + str(self.positive_continue_days) + "\n")
            filehandle.write("positive_continue_change_percent: " + str(self.positive_continue_change_percent) + "\n")
            filehandle.write("negative_continue_days: " + str(self.negative_continue_days) + "\n")
            filehandle.write("negative_continue_change_percent: " + str(self.negative_continue_change_percent) + "\n")

    def write_the_data(self):
        self.do_cleaning()
        self.show_nearest_ndays_volume(show=False)
        # for i in range(4):
        #     self.show_nearest_ndays_continues(str(i), show=False)
        # for choice in ["rise", "fall", "vibrate", "change"]:  # ["rise", "fall", "vibrate", "change"]
        #     self.show_nearest_ndays_updown(choice, show=False)
        # self.show_nearest_ndays_updown("vibrate", show=False)
        self.show_nearest_ndays_rise_fall(show=False)
        self.show_nearest_ndays_change_sorted(show=False)
        self.write_stock_bref()