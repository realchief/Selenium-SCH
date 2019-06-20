from __future__ import division, absolute_import, unicode_literals
from scrapy import Spider
from selenium import webdriver
from time import sleep
import os
import csv
import time
from more_itertools import unique_everseen
import scrapy
import urllib
import requests


class SiteProductItem(scrapy.Item):
    ASIN = scrapy.Field()
    Model_Number = scrapy.Field()
    Qty = scrapy.Field()


class SCHSpider(Spider):
    name = "scrapingdata"
    allowed_domains = ['myseus.schneider-electric.com', 'ims.wsecure.schneider-electric.com']
    DOMAIN_URL = 'https://www.myseus.schneider-electric.com'
    START_URL = 'https://secureidentity.schneider-electric.com/identity/idp/login?app=0sp1H000000CabV&goto' \
                'New=cHpPCYDETfPPyuJAxBqH&idpDisable=TRUE'

    def __init__(self, **kwargs):

        self.input_file = 'Schneider_SquareD.csv'

        with open(self.input_file, 'r+') as csvfile:
            reader = csv.reader(csvfile)
            self.sku_list = []
            for row_index, row in enumerate(reader):
                if row_index != 0:
                    self.sku_list.append(row[0])

        cwd = os.getcwd().replace("\\", "//").replace('spiders', '')
        opt = webdriver.ChromeOptions()
        opt.add_argument("--start-maximized")
        opt.add_argument('--headless')
        self.driver = webdriver.Chrome(executable_path='{}/chromedriver.exe'.format(cwd), chrome_options=opt)

        self.headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
                          "70.0.3538.102 Safari/537.36"
        }

        self.USERNAME = 'lenore@totalelectricny.com'
        self.PASSWORD = 'Zilch12@5614'

    def start_requests(self):

        start_url = self.START_URL
        yield scrapy.Request(url=start_url, callback=self.login)

    def login(self, response):
        while True:
            try:
                user_name = self.USERNAME
                password = self.PASSWORD

                user_email = self.driver.find_element_by_xpath(
                    '//div[contains(@class, "inner-addon right-addon")]//input[contains(@id, "inputEmail")]')
                user_email.send_keys(user_name)
                user_password = self.driver.find_element_by_xpath(
                    '//div[contains(@class, "inner-addon right-addon")]//input[contains(@id,"inputPassword3")]'
                )
                user_password.send_keys(password)
                btn_login = self.driver.find_element_by_xpath(
                    '//button[contains(@class, "btn btn-default btn-block active-btn")]'
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
