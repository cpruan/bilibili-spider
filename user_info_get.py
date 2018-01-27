import xlrd, xlwt, time
from splinter import Browser
from selenium import webdriver
from bs4 import BeautifulSoup as BS

def main():

    def user_info_get(user_id):   #重要的函数，对列表中“某一”视频的所有评论进行提取。输入暴走视频av号(字符串格式！)，采集评论区的粉丝id，返回一个excel文件
        url = "https://space.bilibili.com/" + user_id
        browser.visit(url)
        time.sleep(2)    #休眠时间。作用一、可能是js信息加载需要等待时间，太快获取html导致信息获取不完全！！作用二、避免被封ip，目前测试sleep 2s经过3 hour没被封
        page = browser.html
        page_soup = BS(page, 'html.parser')

        with open('test2.txt', 'w', encoding='utf-8') as file:
            file.write(page)
        user_name = page_soup.select('span[id="h-name"]')[0].text
        if 'male' in page_soup.select('span[id="h-gender"]')[0].get('class'):
            gender = 'male'
        elif 'female' in page_soup.select('span[id="h-gender"]')[0].get('class'):
            gender = 'female'
        else:
            gender = ''
        level = page_soup.select('a[class~="h-level"]')[0].get("lvl")
        big_member = True if page_soup.select('a[class~="annual-v"]') else False
        location = page_soup.select('div[class="item geo"]')[0].get("title")
        birthday = page_soup.select('div[class="item birthday"] > span[class="text"]')[0].text.strip('\n').strip()
        registration_date = page_soup.select('div[class="item regtime"]')[0].text.strip('\n').strip()[4:]
        sign = page_soup.select('div[class="h-sign"]')[0].get("title")

        user_info = [user_id, user_name, gender, level, big_member, location, birthday, registration_date, sign]
        return user_info


    def user_info(file_name, start, end=None):
        file_path_part = r'C:\Users\Administrator\PycharmProjects\untitled' + '\\'
        file_path = file_path_part + file_name
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)
        info_book = xlwt.Workbook()
        info_sheet = info_book.add_sheet('user_info')

        start_col = int(start)
        end_col = sheet.ncols if end == '' else int(end)

        info_max = 0
        for info_index in range(start_col, end_col):   #计算总共需要采集的数据量
            info_max += len([label for label in sheet.col_values(info_index) if label])

        row_counter = 1
        col_counter = 0
        info_count = 0    #用来统计程序中断前采集了多少信息
        error = []    #错误日志
        info_title = ['user_id', 'user_name', 'gender', 'level', 'big_member', 'location', 'birthday', 'registration_date', 'sign']
        for n, tag in enumerate(info_title):
            info_sheet.write(0, col_counter*len(info_title)+n, tag)    #写入初始抬头title

        try:
            time_start = time.asctime(time.localtime(time.time()))
            print('\n程序开始运行：{}'.format(time_start))

            for col_index in range(start_col, end_col):    #列循环
                col_raise = col_index    #col_raise参数用于记录出现异常的列
                col_index_current = col_index+1
                col_index_max = sheet.ncols
                rate_col = round(col_index_current / col_index_max * 100)
                print('\n解析第{}列...'.format(col_index+1))
                print('\r{}{}运行中...进行到{:^3}%，{:^3}列/{:^3}列'.format(chr(9608) * rate_col, ' '*(105-rate_col), rate_col, col_index_current, col_index_max))

                col_values_nonnull = [label for label in sheet.col_values(col_index) if label]
                for row_index in range(1, len(col_values_nonnull)):     #行循环
                    row_raise = row_index
                    try:
                        info_data = user_info_get(sheet.cell(row_index, col_index).value)   #关键行,采集数据
                        for index, property in enumerate(info_data):
                            info_sheet.write(row_counter, col_counter+index, property)
                        row_counter += 1    #换列标记，超过一定数量即换列

                        info_count += 1    #标记已经成功解析的信息数量，以下为状态显示，改善用户体验
                        row_index_current = row_index+1
                        row_index_max = len(col_values_nonnull)
                        rate_row = round(row_index_current / row_index_max * 100)
                        print('\r解析{:^3}%，{:^5}个/{:^5}个'.format(rate_row, row_index_current, row_index_max), end='')
                    except:
                        error.append('出错在：{:^3}列{:^5}行数据，{}，累积{}个'.format(col_raise, row_raise, time.asctime(time.localtime(time.time())), len(error)))
                        print('出错！在{:^3}列{:^5}行数据，{}，累积{}个'.format(col_raise, row_raise, time.asctime(time.localtime(time.time())), len(error)))
                        if len(error) > 100:    #如果错误过多（估计被封ip），则退出
                            error.append('\n终止在{}列，已采集{:^5}个数据，错误率：{:^3}%，采集率{:^3}%'.format(col_index, info_count, round(len(error)/info_count * 100, 2), round(info_count/info_max * 100, 2)))
                            print('\n终止在{}列，已采集{:^5}个数据，错误率：{:^3}%，采集率{:^3}%'.format(col_index, info_count, round((len(error)-1)/info_count * 100, 2), round(info_count/info_max * 100, 2)))
                            raise

                    if row_counter > 10000:  #存储xls的换行操作
                        row_counter = 1
                        col_counter += len(info_title)
                        for n, tag in enumerate(info_title):
                            info_sheet.write(0, col_counter+n, tag)   #写入每列抬头
                #     if info_count > 5:
                #         break
                # if info_count > 5:
                #     break
            error.append('\n解析完成！已采集{:^5}个数据，错误率：{:^3}%，采集率{:^3}%'.format(info_count, round(len(error)/info_count * 100, 2), round(info_count/info_max * 100, 2)))
            print('\n解析完成！已采集{:^5}个数据，错误率：{:^3}%，采集率{:^3}%'.format(info_count, round((len(error)-1)/info_count * 100, 2), round(info_count/info_max * 100, 2)))

        except:
            print("\n因其他错误退出！")

        finally:
            time_end = time.asctime(time.localtime(time.time()))
            print('\n程序结束：{}'.format(time_end))
            with open('Error_log_{} to {}.txt'.format(start_col, end_col-1), 'w', encoding='utf-8') as error_file:   #保存错误日志
                for log in error:
                    error_file.write('{}\n'.format(log))
                error_file.close()

            workbook.release_resources()
            info_book.save(file_path_part + 'user_info_{} to {}.xls'.format(start_col, end_col-1))   #最关键的，存储已解析的信息


    print(
    '''
    *****欢迎使用B站采集系统*****
    ''')
    start = input('Start_col: ')
    end = input('End_col: ')
    tem_name = input('Filename: ')
    filename = 'clean_data.xls' if tem_name == '' else tem_name
    tem_headless = input('Headless:')
    head_less = False if tem_headless == 'False' else True
    print('请稍候...')

    prefs={
    'profile.default_content_setting_values':
        {
            'images': 2,
            'javascript':1
        }
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs',prefs)
    headers = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    #url = "https://www.bilibili.com/video/av18453664"
    browser = Browser('chrome', headless=head_less, user_agent=headers, options=chrome_options)   #默认开启无GUI浏览模式，一开始就运行Browser，避免反复运行关闭

    user_info(filename, start, end)
    browser.quit()
    input()

main()
