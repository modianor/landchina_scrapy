import base64
import logging
import os
import pickle
import uuid

import cv2
import requests
import scrapy
import xlrd
import xlwt
from bs4 import BeautifulSoup
from scrapy import Request
from sklearn.svm import SVC
from xlutils.copy import copy

from landchina_scrapy.items import LandchinaScrapyItem
from landchina_scrapy.settings import VALUE_TITLE


class LandchinaSpider(scrapy.Spider):
    name = 'landchina'
    allowed_domains = ['www.landchina.com']
    start_urls = ['https://www.landchina.com/default.aspx?tabid=263']

    def str_to_hex(self, s):
        return ''.join([hex(ord(c)).replace('0x', '') for c in s])

    def __init__(self, start=None, end=None, regin=None, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.START_DATE = str(start)
        self.END_DATE = str(end)
        self.REGION = str(regin)
        self.book_name_xls = 'data/excel/{}~{}.xls'.format(self.START_DATE, self.END_DATE)
        self.sheet_name_xls = 'xls格式测试表'
        self.url = 'https://www.landchina.com/default.aspx?tabid=263'
        self.session = requests.session()

    def detection(self, src):
        with open('data/svm/model.dat', 'rb') as f:
            svc: SVC = pickle.loads(f.read())
            text = ''
            for i in range(5):
                x = src[:, i * 20:i * 20 + 20, :].reshape(1, 27 * 20 * 3)
                y_ = svc.predict(x)
                text += str(int(y_[0]))
        return text

    def get_img(self, src):
        data = src.split(',')[1]
        image_data = base64.b64decode(data)
        file_path = 'data/img/{}.bmp'.format(uuid.uuid1())
        with open(file_path, 'wb') as f:
            f.write(image_data)
        img = cv2.imread(file_path)
        text = self.detection(img)
        os.remove(file_path)
        self.log('验证码：{}'.format(text), level=logging.INFO)
        # cv2.namedWindow('src', cv2.WINDOW_NORMAL)
        # cv2.imshow('src', img)
        # cv2.waitKey(0)
        return text

    def write_excel_xls(self, path, sheet_name, value):
        index = len(value)  # 获取需要写入数据的行数
        workbook = xlwt.Workbook()  # 新建一个工作簿
        sheet = workbook.add_sheet(sheet_name)  # 在工作簿中新建一个表格
        for i in range(0, index):
            for j in range(0, len(value[i])):
                sheet.write(i, j, value[i][j])  # 像表格中写入数据（对应的行和列）
        workbook.save(path)  # 保存工作簿
        self.log("xls格式表格写入数据成功！", level=logging.INFO)

    def write_excel_xls_append(self, path, data):
        value = [[data['合同签订日期'],
                  data['供地方式'],
                  data['项目位置'],
                  data['行政区'],
                  data['面积(公顷)'],
                  data['土地用途'],
                  data['行业分类'],
                  data['电子监管号'],
                  data['土地级别'],
                  data['土地来源'],
                  data['批准单位'],
                  data['约定开工时间'],
                  data['约定竣工时间'],
                  data['实际开工时间'],
                  data['实际竣工时间'],
                  data['成交价格(万元)'],
                  data['约定交地时间'],
                  data['项目名称'],
                  data['土地使用年限'],
                  data['土地使用权人'],  # 最后六个属性不一样
                  data['分期数'],
                  data['约定支付日期'],
                  data['约定支付金额(万元)'],
                  data['下限'],
                  data['上限']
                  ], ]
        index = len(value)  # 获取需要写入数据的行数
        workbook = xlrd.open_workbook(path)  # 打开工作簿
        sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
        worksheet = workbook.sheet_by_name(sheets[0])  # 获取工作簿中所有表格中的的第一个表格
        rows_old = worksheet.nrows  # 获取表格中已存在的数据的行数
        new_workbook = copy(workbook)  # 将xlrd对象拷贝转化为xlwt对象
        new_worksheet = new_workbook.get_sheet(0)  # 获取转化后工作簿中的第一个表格
        for i in range(0, index):
            for j in range(0, len(value[i])):
                new_worksheet.write(i + rows_old, j, value[i][j])  # 追加写入数据，注意是从i+rows_old行开始写入
        new_workbook.save(path)  # 保存工作簿
        self.log("第{}条数据【追加】写入数据成功！".format(rows_old), level=logging.INFO)

    def parse_page_data(self, soup, start='', end='', page_num=1):
        try:
            __VIEWSTATE = soup.find('input', {'id': '__VIEWSTATE'}).attrs['value']
            __EVENTVALIDATION = soup.find('input', {'id': '__EVENTVALIDATION'}).attrs['value']
            TAB_QuerySubmitConditionData = soup.find('input', {'id': 'TAB_QueryConditionItem270'}).attrs['value']
            TAB_QuerySort1 = soup.find('input', {'id': 'TAB_QuerySort1'}).attrs['value']

            data = None
            if start != '':
                data = {
                    '__VIEWSTATE': __VIEWSTATE,
                    '__EVENTVALIDATION': __EVENTVALIDATION,
                    'hidComName': 'default',
                    'TAB_QueryConditionItem': TAB_QuerySubmitConditionData,
                    'TAB_QuerySortItemList': '282:False',
                    'TAB_QuerySubmitConditionData': '{}:{}~{}'.format(TAB_QuerySubmitConditionData, start, end),
                    'TAB_QuerySubmitOrderData': '282:False',
                    'TAB_RowButtonActionControl': '',
                    'TAB_QuerySubmitPagerData': str(page_num),
                    'TAB_QuerySubmitSortData': ''
                }
            else:
                data = {
                    '__VIEWSTATE': __VIEWSTATE,
                    '__EVENTVALIDATION': __EVENTVALIDATION,
                    'hidComName': 'default',
                    'TAB_QuerySortItemList': '282:False',
                    'TAB_QuerySubmitConditionData': '',
                    'TAB_QuerySubmitOrderData': '',
                    'TAB_RowButtonActionControl': '',
                    'TAB_QuerySubmitPagerData': str(1),
                    'TAB_QuerySubmitSortData': ''
                }
        except AttributeError:
            return {
                '__VIEWSTATE': '',
                '__EVENTVALIDATION': '',
                'hidComName': 'default',
                'TAB_QuerySortItemList': '282:False',
                'TAB_QuerySubmitConditionData': '',
                'TAB_QuerySubmitOrderData': '',
                'TAB_RowButtonActionControl': '',
                'TAB_QuerySubmitPagerData': str(1),
                'TAB_QuerySubmitSortData': ''
            }

        return data

    def start_requests(self):
        self.data = dict()
        self.curr_page = 1
        self.cookie = dict()
        self.write_excel_xls(self.book_name_xls, self.sheet_name_xls, VALUE_TITLE)
        self.headers = {
            'Host': 'www.landchina.com',
            'Proxy-Connection': 'keep-alive',
            # 'Content-Length': '3122',
            'Cache-Control': 'max-age=0',
            'Origin': 'https://www.landchina.com',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.landchina.com/default.aspx?tabid=263',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

        while True:
            self.log('正在尝试识别验证码登录....', level=logging.INFO)
            response = self.session.get(url=self.url)
            soup = BeautifulSoup(response.text, 'lxml')
            Img = soup.select('.verifyimg')[0]
            text = self.get_img(Img.attrs['src'])
            self.session.cookies['srcurl'] = self.str_to_hex(self.url)
            ver_url = '{}&security_verify_img={}'.format(self.url, self.str_to_hex(text))
            response = self.session.get(url=ver_url)

            if 'security_session_high_verify' in self.session.cookies.keys():
                break
            self.log('验证码识别错误....', level=logging.ERROR)
        self.log('验证码登录成功....', level=logging.INFO)

        response = self.session.get(url=self.url)
        soup = BeautifulSoup(response.text, 'lxml')

        self.data = self.parse_page_data(soup, self.START_DATE, self.END_DATE)
        response = self.session.post(url=self.url, data=self.data)
        soup = BeautifulSoup(response.text, 'lxml')
        page_num_str = soup.select(
            '#mainModuleContainer_485_1113_1539_tdExtendProContainer > table > tbody > tr:nth-child(1) > td > table > tbody > tr:nth-child(2) > td > div > table > tbody > tr > td:nth-child(1)')[
            0].text
        self.log('{} ~ {} {}'.format(self.START_DATE, self.END_DATE, page_num_str), level=logging.INFO)
        self.page_num = int(page_num_str.split('\xa0')[0][1:-1])

        self.data = self.parse_page_data(soup, self.START_DATE, self.END_DATE, 1)

        for k in self.session.cookies.keys():
            self.cookie[k] = self.session.cookies[k]

        yield scrapy.FormRequest(
            url=self.url,
            headers=self.headers,
            cookies=self.cookie,
            formdata=self.data,
            callback=self.parse_page)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'lxml')

        try:
            tb_head = soup.select('#mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1 > tbody')[0].contents
            data = dict()
            data['行政区'] = tb_head[2].contents[1].text
            data['电子监管号'] = tb_head[2].contents[3].text

            data['项目名称'] = tb_head[3].contents[1].text

            data['项目位置'] = tb_head[4].contents[1].text

            areaSV = tb_head[5].contents[1].text
            areaS2V = tb_head[5].contents[3].text
            if areaSV == areaS2V:
                areaS2 = "现有建设用地"
            elif (areaS2V == 0):
                areaS2 = "新增建设用地"
            else:
                areaS2 = "新增建设用地(来自存量库)"

            data['面积(公顷)'] = areaSV

            data['土地来源'] = areaS2

            data['土地用途'] = tb_head[6].contents[1].text
            data['供地方式'] = tb_head[6].contents[3].text

            data['土地使用年限'] = tb_head[7].contents[1].text
            data['行业分类'] = tb_head[7].contents[3].text

            data['土地级别'] = tb_head[8].contents[1].text
            data['成交价格(万元)'] = tb_head[8].contents[3].text

            data['土地使用权人'] = tb_head[10].contents[1].text

            data['约定交地时间'] = tb_head[12].contents[3].find('span').text

            data['约定开工时间'] = tb_head[13].contents[1].text
            data['约定竣工时间'] = tb_head[13].contents[3].text

            data['实际开工时间'] = tb_head[14].contents[1].text
            data['实际竣工时间'] = tb_head[14].contents[3].text.strip()

            data['批准单位'] = tb_head[15].contents[1].text
            data['合同签订日期'] = tb_head[15].contents[3].text.strip()

            data['分期数'] = ''
            data['约定支付日期'] = ''
            data['约定支付金额(万元)'] = ''
            data['下限'] = ''
            data['上限'] = ''
            # print(data)
            self.write_excel_xls_append(self.book_name_xls, data)
        except IndexError:
            print(response.text)

    def parse_page(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        trs = soup.find(name='table', attrs={'id': 'TAB_contentTable'})
        trs = trs.find_all('tr')
        for tr in trs[1:]:
            item = LandchinaScrapyItem()
            target_url = 'https://www.landchina.com/' + tr.select('.queryCellBordy')[1].find('a').attrs['href']
            yield Request(url=target_url, cookies=self.cookie, headers=self.headers, meta={'item': item},
                          callback=self.parse_item,
                          dont_filter=True)

        for i in range(self.curr_page, self.page_num + 1, 1):
            self.data = self.parse_page_data(soup, self.START_DATE, self.END_DATE, page_num=i)
            yield scrapy.FormRequest(
                url=self.url,
                cookies=self.cookie,
                headers=self.headers,
                formdata=self.data,
                callback=self.parse_page)
