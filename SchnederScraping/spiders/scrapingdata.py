from __future__ import division, absolute_import, unicode_literals
from scrapy import Spider
from selenium import webdriver
from time import sleep
import os
import csv
import time
from more_itertools import unique_everseen


class PepcoSpider(Spider):
    name = "pepco"
    start_urls = [
        'https://secure.pepco.com/Pages/Login.aspx'
    ]
    passed_vals = []

    def __init__(self, download_directory=None, *args, **kwargs):
        super(PepcoSpider, self).__init__(*args, **kwargs)

        with open('Pepco Credentials All.csv', 'rb') as csvfile:
            reader = csv.reader(csvfile)
            self.password_list = []
            self.username_list = []
            self.accountOwnerID_credential_list = []
            self.clientID_list = []
            for row_index, row in enumerate(reader):
                if row_index != 0:
                    self.accountOwnerID_credential_list.append(row[0])
                    self.username_list.append(row[1])
                    self.password_list.append(row[2])
                    self.clientID_list.append(row[3])

        self.user_index = 0
        self.download_directory = download_directory if download_directory else 'C:/Users/webguru/Downloads/pepco/'

        if not os.path.exists(self.download_directory):
            os.makedirs(self.download_directory)

        cwd = os.getcwd().replace("\\", "//").replace('spiders', '')
        opt = webdriver.ChromeOptions()
        opt.add_argument("--start-maximized")
        # opt.add_argument('--headless')
        self.driver = webdriver.Chrome(executable_path='{}/chromedriver.exe'.format(cwd), chrome_options=opt)

        with open('{}/scrapy.log'.format(cwd), 'r') as f:
            self.logs = [i.strip() for i in f.readlines()]
            f.close()

    def login(self, user_index=None):
        while True:
            try:

                user_email = self.driver.find_element_by_xpath(
                    '//div[contains(@class, "exc-form-group-double")]//input[contains(@id, "Username")]')
                user_name = self.username_list[user_index]
                password = self.password_list[user_index]
                user_email.send_keys(user_name)
                user_password = self.driver.find_element_by_xpath(
                    '//div[contains(@class, "exc-form-group-double")]//input[contains(@id,"Password")]'
                )
                user_password.send_keys(password)
                btn_login = self.driver.find_element_by_xpath(
                    '//button[contains(@processing-button, "Signing In...")]'
                )
                btn_login.click()
                break
            except:
                time.sleep(10)
                continue

    def parse(self, response):

        all_users_option = True
        user_index = 0

        while all_users_option:

            if user_index == 0:
                self.driver.get(response.url)
            if self.driver.current_url != 'https://secure.pepco.com/Pages/Login.aspx':
                self.driver.get('https://secure.pepco.com/Pages/Login.aspx')
            self.login(user_index)
            time.sleep(3)

            accountOwnerID = self.accountOwnerID_credential_list[user_index]
            clientID = self.clientID_list[user_index]
            account_file_name = 'account_number REV.csv'
            input = open(account_file_name, 'rb')
            with input as csvfile:
                reader = csv.reader(csvfile)
                account_number_list_csv = []
                for row_index, row in enumerate(reader):
                    if row_index != 0 and row[0] == accountOwnerID:
                        account_number_list_csv.append(row[1])
            input.close()

            all_pages_option = True
            account_numbers = []
            while all_pages_option:

                if self.driver.current_url != 'https://secure.pepco.com/Pages/ChangeAccount.aspx':
                    self.driver.get('https://secure.pepco.com/Pages/ChangeAccount.aspx')
                time.sleep(10)
                account_rows = self.driver.find_elements_by_xpath('//table[@id="changeAccountDT1"]//tbody//tr')
                if account_rows:
                    for row in account_rows:
                        if 'Inactive' not in row.text.split(' '):
                            account_number = row.text.split(' ')[1]
                            account_numbers.append(account_number)
                        else:
                            pass
                else:
                    pass

                time.sleep(3)

                try:
                    self.driver.find_elements_by_xpath('//li[@class="paginate_button next"]')[
                        0].click()
                except:
                    all_pages_option = False

            print('===========All account numbers of all pages has been collected================')

            for account_number in account_numbers:
                if account_number not in account_number_list_csv:
                    output = open(account_file_name, 'a')
                    with output as csv_write:
                        fieldnames = ['ClientID', 'AccountOwnerID', 'AccountNumber', 'LastDownloadBillDate',
                                      'BillCycleDays']
                        writer = csv.DictWriter(csv_write, fieldnames=fieldnames)
                        line = {'ClientID': clientID, 'AccountOwnerID': accountOwnerID, 'AccountNumber': account_number,
                                'LastDownloadBillDate': '1/6/2019', 'BillCycleDays': '28'}
                        writer.writerow(line)
                    output.close()
                else:
                    continue

            with open(account_file_name, 'r') as f, open('updated.csv', 'w') as out_file:
                out_file.writelines(unique_everseen(f))

            input = open('updated.csv', 'rb')
            output = open('output.csv', 'wb')
            writer = csv.writer(output)
            for row in csv.reader(input):
                if row:
                    writer.writerow(row)
            input.close()
            output.close()

            os.remove('updated.csv')
            os.remove('account_number REV.csv')
            os.rename('output.csv', account_file_name)

            signout_button = self.driver.find_elements_by_xpath(
                    '//button[@class="btn btn-accent exc-sign-in-btn" and contains(text(), "Sign Out")]')
            if signout_button:
                    signout_button[0].click()

            user_index = user_index + 1
            if user_index > len(self.accountOwnerID_credential_list) - 1:
                all_users_option = False

        print('===========All account numbers of all users have been rechecked================')
        self.driver.close()

    def date_to_string(self, d):
        d = d.split('/')
        return ''.join([i.zfill(2) for i in d])
