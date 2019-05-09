import os
import time
import tushare
import sys
sys.path.append(os.path.abspath(".."))
from Tools.File import File


def get_stock_number_from_cvs_file(cvs_file_path):
    stock_numbers = []
    if not os.path.exists(cvs_file_path):
        return stock_numbers
    else:
        stock_lines = open(cvs_file_path, "r", encoding="utf-8").readlines()
        stock_lines.pop(0)  # delete the header
        for stock_line in stock_lines:
            stock_number = stock_line.split(",", 2)[1]
            stock_numbers.append(stock_number)
        return stock_numbers


class StockDataBaseManager:
    def __init__(self):
        pass

    def init_database(self, databasedir, start_date, end_date):
        dir_checker = File(databasedir)
        if not dir_checker.exists():
            dir_checker.mkdirs()

        today_all_stocks_path = os.path.join(databasedir, "all_stocks.csv")
        today_all_stocks = tushare.get_today_all()
        today_all_stocks.to_csv(today_all_stocks_path)

        stock_number_list = []
        lines = open(today_all_stocks_path, "r", encoding="utf-8").readlines()
        for line in lines:
            stock_number_list.append(line.split(",")[1])
        del stock_number_list[0]  # the csv first line is not stock data, so del it
        os.remove(today_all_stocks_path)

        for stock_number in stock_number_list:
            stock_dir = os.path.join(databasedir, stock_number)
            stock_csv_path = os.path.join(stock_dir, stock_number + ".csv")
            File(stock_dir).mkdirs()
            stock_history = tushare.get_k_data(stock_number, start_date, end_date)
            stock_history.to_csv(stock_csv_path)
        print("database init successfully!")

    def update_database(self, databasedir, stock_numbers=[]):
        all_stock_folder_paths = File(databasedir).get_folderpath_in_dir()
        stock_folder_paths = []
        if len(stock_numbers) != 0:
            for stock_number in stock_numbers:
                stock_folder_path = os.path.join(databasedir, stock_number)
                if stock_folder_path not in all_stock_folder_paths:
                    print("Stock: %s not in the database: %s, please be noticed." % (stock_number, databasedir))
                else:
                    stock_folder_paths.append(stock_folder_path)
        else:
            stock_folder_paths = all_stock_folder_paths
        total_num = len(stock_folder_paths)

        if total_num == 0:
            print("Error: update_database failed, 0 stock's been updated")
            return
        else:
            print("updating database, %s stocks will be updated" % total_num)

        current_updated_num = 0
        for stock_folder_path in stock_folder_paths:
            stock_number = File(stock_folder_path).get_foldername_by_path()
            stock_csv_path = os.path.join(stock_folder_path, stock_number + ".csv")
            if not os.path.exists(stock_csv_path):
                print("Warnning: %s does not exist!" % stock_csv_path)
                print("update csv file failed.")
                continue
            else:
                current_updated_num = current_updated_num + 1
                stock_csv_last_line= open(stock_csv_path, "r", encoding="utf-8").readlines()[-1]
                # check csv file validation
                if len(stock_csv_last_line.split(",")) < 8:
                    print("Error stock %s csv file invalid！" % stock_number)
                    continue
                stock_csv_index = int(stock_csv_last_line.split(",")[0])
                stock_csv_date = stock_csv_last_line.split(",")[1]
                update_stock_csv_path = os.path.join(stock_folder_path, stock_number + "_update.csv")
                start_date = stock_csv_date
                end_date = time.strftime("%Y-%m-%d", time.localtime())
                stock_history = tushare.get_k_data(stock_number, start_date, end_date)
                stock_history.to_csv(update_stock_csv_path)
                update_stock_lines = open(update_stock_csv_path, "r", encoding="utf-8").readlines()
                date_matched = False
                need_update_lines = []
                need_update_index = stock_csv_index
                for update_stock_line in update_stock_lines:
                    update_stock_line_split = update_stock_line.split(",", 2)
                    if stock_csv_date == update_stock_line_split[1]:
                        date_matched = True
                        continue
                    if date_matched:
                        need_update_index = need_update_index + 1
                        update_stock_line_split[0] = str(need_update_index)
                        connnect_line = update_stock_line_split[0] + "," + update_stock_line_split[1] + "," + update_stock_line_split[2]
                        need_update_lines.append(connnect_line)
                with open(stock_csv_path, "a+", encoding="utf-8") as stock_csv_handle:
                    for need_update_line in need_update_lines:
                        stock_csv_handle.write(need_update_line)
                os.remove(update_stock_csv_path)

                num = int(0.1 * total_num )
                if num == 0:
                    num = 1

                if current_updated_num % num == 0:
                    print("%d updated, %d to go!" % (current_updated_num, total_num - current_updated_num))

        print("update database finished!")

    def check_date_update_database(self, databasedir, yesterday, stocks_csv_file_path=""):
        ref_csv_file_path = ""
        stock_numbers = []
        if stocks_csv_file_path != "":
            stock_numbers = get_stock_number_from_cvs_file(stocks_csv_file_path)
            if len(stock_numbers) == 0:
                return False
            else:
                ref_stock_number = stock_numbers[0]
                ref_csv_file_path = os.path.join(databasedir, ref_stock_number, ref_stock_number + ".csv")
        else:
            folder_paths = File(databasedir).get_folderpath_in_dir()
            ref_folder_path = folder_paths[0]
            ref_stock_number = File(ref_folder_path).get_foldername_by_path()
            ref_csv_file_path = os.path.join(ref_folder_path, ref_stock_number + ".csv")
        if not os.path.exists(ref_csv_file_path):
            print("Error: %s does not exist" % ref_csv_file_path)
            return False
        stock_csv_last_line = open(ref_csv_file_path, "r", encoding="utf-8").readlines()[-1]
        stock_csv_date = stock_csv_last_line.split(",")[1]
        if yesterday == stock_csv_date:
            print("csv file is all ready updated to yesterday: %s" % yesterday)
        else:
            self.update_database(databasedir, stock_numbers)
        return True


if __name__ == "__main__":
    database_dir = r"C:\Data\Stock\StockDataBase"
    # start_date = "2019-01-01"
    # end_date = "2019-04-25"
    m = StockDataBaseManager()
    # m.init_database(database_dir, start_date, end_date)
    m.update_database(r"C:\Data\Stock\StockDataBase")