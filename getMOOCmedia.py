"""
    author: Adam
    email : adam.yangt@gmail.com
    blog  : www.adamyt.com
"""
# 有下载不动的现象 暂不知怎么回事 推测可能与开了Fiddler有关
# 有课件或视频同名的情况 待修改
import requests
import re
import time
import os
import urllib.request
import math


class MOOCException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


# 其实下面三个都还有个参数叫httpSessionId， 但没用
# 用于搜索接口的POST数据
dataSearch = {'callCount': '1',
              'scriptSessionId': '${scriptSessionId}190',
              'c0-scriptName': 'MocSearchBean',
              'c0-methodName': 'searchMocCourse',
              'c0-id': '0',
              'c0-e1': 'string:python',
              'c0-e2': 'number:1',
              'c0-e3': 'boolean:true',
              'c0-e4': 'null:null',
              'c0-e5': 'number:0',
              'c0-e6': 'number:30',
              'c0-e7': 'number:20',
              # 下面这个参数温馨地为我们提供了解释
              'c0-param0': 'Object_Object:{keyword:reference:c0-e1,pageIndex:reference:c0-e2,'
                           'highlight:reference:c0-e3,categoryId:reference:c0-e4,'
                           'orderBy:reference:c0-e5,stats:reference:c0-e6,pageSize:reference:c0-e7}',
              'batchId': '1490456943066'}

# 获取课程所有文件列表的POST数据
dataMocTermDto = {'callCount': '1',
                  'scriptSessionId': '${scriptSessionId}190',
                  'c0-scriptName': 'CourseBean',
                  'c0-methodName': 'getMocTermDto',
                  'c0-id': '0',
                  'c0-param0': 'number:1001962001',  # tid 课程学期Id
                  'c0-param1': 'number:1',
                  'c0-param2': 'boolean:true',
                  'batchId': '1490456943066'}

# 获取文档和视频的POST数据
dataLessonUnitLearnVo = {'callCount': '1',
                         'scriptSessionId': '${scriptSessionId}190',
                         'c0-scriptName': 'CourseBean',
                         'c0-methodName': 'getLessonUnitLearnVo',
                         'c0-id': '0',
                         'c0-param0': 'number:805080',  # contentId
                         'c0-param1': 'number:3',  # type=3代表文档  type=1代表视频
                         'c0-param2': 'number:0',
                         'c0-param3': 'number:1002834377',  # 文件id
                         'batchId': '1490456943066'}

# 记录搜索返回的课程列表信息
pagesInfo = {'page_index': 0, 'totalPages': 0, 'totalCount': 0}
coursesList = []


# 产生批处理时间 其实这参数并没有被检查 但还是意思一下
def batch_id():
    return round(time.time() * 1000)


# POST请求
def post_response(url, data):
    try:
        res = requests.post(url, data=data)
        res.raise_for_status()
        return res.text
    except requests.HTTPError as ex:
        print('[-]ERROR: %s' % str(ex))
        raise
        

# 分块下载文件
def get_file_by_chunk(url, file_path, chunk_size=1024*512):
    try:
        res = requests.get(url, stream=True)
        res.raise_for_status()
        if 'Content-Length' not in res.headers:
            raise requests.HTTPError('No Content Length')
        content_size = int(res.headers['Content-Length'])
        size_mb = content_size / 1024 / 1024
        download_size = 0
        with open(file_path, 'wb') as file:
            for chunk in res.iter_content(chunk_size=chunk_size):
                progress = download_size / content_size
                prompt_bar = '[{:50}] {:.1f}%\tSize: {:.2f}MB'.format('=' * int(progress * 50), progress * 100, size_mb)
                print(prompt_bar, end='\r')
                file.write(chunk)
                download_size += chunk_size
            print('[{:50}] 100% Done!\tSize: {:.2f}MB'.format('=' * 50, size_mb))
    except requests.HTTPError as ex:
        print('[-]ERROR: %s' % ex)
    except KeyboardInterrupt:
        os.remove(file_path)
        raise


# 下载字幕文件  Transfer-Encoding:chunked
def get_file_from_chunked(url, file_path):
    try:
        res = requests.get(url)
        res.raise_for_status()
        with open(file_path, 'wb') as file:
                file.write(res.content)
    except requests.HTTPError as ex:
        print('[-]ERROR: %s' % ex)
    except KeyboardInterrupt:
        os.remove(file_path)
        raise


# 从课件返回信息寻找下载链接
def get_lesson_pdf_url(res_text):
    re_pdf = r'http://nos.netease.com/.*?\.pdf'
    try:
        # content = res_text.encode('utf-8').decode('unicode_escape')
        pdf_url = re.search(re_pdf, res_text)
        if pdf_url is None:
            raise MOOCException('pdf_url is None')
        return pdf_url.group(0)
    except MOOCException as ex:
        print('[-]ERROR: %s' % str(ex))


# 从课件返回信息寻找视频下载链接及字幕链接
def get_lesson_video_url(res_text, quality):
    video_format = ['flvHdUrl', 'flvSdUrl', 'flvShdUrl', 'mp4HdUrl', 'mp4SdUrl', 'mp4ShdUrl']
    re_video = r'{}="(.+?)";'.format(video_format[int(quality)])
    re_srt = r's\d+\.name="([\w\\]+?)";s\d+\.url="(.+?)";'
    try:
        # content = res_text.encode('utf-8').decode('unicode_escape')
        video_url = re.search(re_video, res_text)
        srt_url = re.findall(re_srt, res_text)
        if video_url is None:
            raise MOOCException('video_url is None')
        return video_url.group(1), srt_url
    except MOOCException as ex:
        print('[-]ERROR: %s' % str(ex))


# 解析课程返回的媒体信息流的文件
def parse_lesson_file(res_text, video=False):
    content_type = 1 if video else 3
    re_file_list = r'anchorQuestions=.*contentId=(\d*);.*contentType={};.*id=(\d*);.*name="(.*)";'.format(content_type)
    try:
        content = res_text.encode('utf-8').decode('unicode_escape')
        file_list = re.findall(re_file_list, content)
        if not file_list:
            raise MOOCException('file_list is empty')
        return file_list
    except MOOCException as ex:
        print('[-]ERROR: %s' % str(ex))
        raise


# 获取课程的媒体信息流
def get_lesson_file(tid, video=False):  # post to getMocTermDto.dwr
    # 现在换成了 CourseBean.getLastLearnedMocTermDto.dwr
    get_moc_term_dto_url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getMocTermDto.dwr'
    dataMocTermDto['c0-param0'] = 'number:{}'.format(tid)
    dataMocTermDto['batchId'] = batch_id()
    try:
        res_text = post_response(get_moc_term_dto_url, dataMocTermDto)
        file_list = parse_lesson_file(res_text, video=video)
        return file_list
    except requests.HTTPError:
        print('[-]ERROR: getMocTermDto has failed')
        raise
    except MOOCException:
        raise
    

# 下载课件或视频
def download_file(file_list, path, video=False):  # post to getLessonUnitLearnVo.dwr
    get_lesson_unit_learn_vo_url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr'
    video_quality = ['高清', '标清', '超清', '高清', '标清', '超清']
    count = 1
    if video:
        quality = input('请选择格式\nFLV高清 (0)\nFLV标清 (1)\nFLV超清 (2)\nMP4高清 (3)\nMP4标清 (4)\nMP4超清 (5)\n')
        quality = int(quality)
        if quality < 0 or quality > 5:
            raise MOOCException('[-] ERROR: 选择错误')
    for item in file_list:
        content_id = item[0]
        file_id = item[1]
        file_name = re.sub(r'[/\\*|<>:?"]', '', item[2])  # Windows文件名非法字符
        dataLessonUnitLearnVo['c0-param0'] = 'number:{}'.format(content_id)
        dataLessonUnitLearnVo['c0-param1'] = 'number:{}'.format(1 if video else 3)
        dataLessonUnitLearnVo['c0-param3'] = 'number:{}'.format(file_id)
        dataLessonUnitLearnVo['batchId'] = batch_id()
        print('\n[+]正在下载第{}份 - {} ...\n'.format(count, file_name))
        try:
            if video:
                suffix = 'flv' if quality < 3 else 'mp4'
                video_name = '{}({}).{}'.format(file_name, video_quality[quality], suffix)
                complete_path = '{}/{}'.format(path, video_name)
                res_text = post_response(get_lesson_unit_learn_vo_url, dataLessonUnitLearnVo)
                video_url, srt_url = get_lesson_video_url(res_text, quality)
                if os.path.exists(complete_path):
                    print('\t{}\t已存在  ...'.format(video_name))
                else:
                    get_file_by_chunk(video_url, complete_path, chunk_size=1024 * 1024)
                    count = count + 1
                for srt in srt_url:
                    srt_name = file_name + '({}).srt'.format(srt[0].encode('utf-8').decode('unicode_escape'))
                    complete_path = '{}/{}'.format(path, srt_name)
                    if os.path.exists(complete_path):
                        print('\t{}\t已存在  ...'.format(srt_name))
                        continue
                    get_file_from_chunked(srt[1], complete_path)  # 不算在文件数内
            else:
                complete_path = '{}/{}.pdf'.format(path, file_name)
                if os.path.exists(complete_path):
                    print('\t{}.pdf\t已存在 ...'.format(file_name))
                    continue
                res_text = post_response(get_lesson_unit_learn_vo_url, dataLessonUnitLearnVo)
                pdf_url = get_lesson_pdf_url(res_text)
                get_file_by_chunk(pdf_url, complete_path, chunk_size=1024*128)
                count = count + 1
        except requests.HTTPError:
            print('[-]ERROR: {} download error'.format(file_name))
        except KeyboardInterrupt:
            print('[*] 你中断了此次下载')
            break
    print('\n下载完成\t此次共下载{}份\n'.format(count - 1))


# 解析搜索返回信息
def parse_info(res_text):
    global pagesInfo
    re_info = '.*highlightName="(.*?)";.*highlightTeacherNames="(.*?)";.*highlightUniversity="(.*?)";' \
              '[\s\S]+?endTime=(\d*);[\s\S]+?\.id=(\d*);[\s\S]+?startTime=(\d*);'
    re_page_info = r'pageIndex=(\d*);.*totleCount=(\d*);.*totlePageCount=(\d*);'  # 你没有看错 不是我单词拼错了orz
    try:
        content = res_text.encode('utf-8').decode('unicode_escape')
        content = re.sub(r'({##)|(##\})', '', content)      # 高亮的关键词会被井号括起来 应该可以通过c0-e3参数控制
        courses_list = re.findall(re_info, content)
        page_info = re.findall(re_page_info, content[-500:])
        if not courses_list or page_info is None:
            raise MOOCException('未搜索到任何记录')
        page_info = page_info[0]
        pagesInfo['page_index'] = int(page_info[0])
        pagesInfo['totalCount'] = int(page_info[1])
        pagesInfo['totalPages'] = int(page_info[2])
        return courses_list, list(page_info)
    except MOOCException or IndexError as ex:
        print('[-]ERROR: %s' % str(ex))
        raise


# 搜索页跳转
def turn_to_page(keyword, page):
    global pagesInfo
    if page == 'n' and pagesInfo['totalPages'] > pagesInfo['page_index']:
        search(keyword, pagesInfo['page_index'] + 1)
    elif page == 'u' and pagesInfo['page_index'] > 1:
        search(keyword, pagesInfo['page_index'] - 1)
    elif type(page) is int and 0 < page <= pagesInfo['totalPages']:
        search(keyword, page)
    else:
        print('无法翻页')


# 计算当前课程状态
def calc_time(unix_start, unix_end):
    unix_start = int(unix_start) / 1000
    unix_end = int(unix_end) / 1000
    unix_now = round(time.time())
    if unix_now > unix_end:
        return '已经结束'
    elif unix_now < unix_start:
        return '尚未开始'
    else:
        return '至第{}周'.format(math.ceil((unix_now - unix_start) / (3600 * 24 * 7)))


# 严格输出col个宽度
def zh_en(string, col=0):
    if col == 0:
        return string
    string = str(string)
    length = len(string)
    len_chinese = 0
    len_english = 0
    for i in range(length):
        if u'\u9fa5' >= string[i] >= u'\u4e00':  # 中文
            len_chinese += 1
        elif u'\uffef' >= string[i] >= u'\uff00':  # 全角标点
            len_chinese += 1
        elif u'\u303f' >= string[i] >= u'\u3000':  # CJK标点
            len_chinese += 1
        elif u'\u2026' >= string[i] >= u'\u2013':  # 神奇的破折号等
            len_chinese += 1
        else:
            len_english += 1
    real_len = len_chinese * 2 + len_english
    diff = col - real_len
    for i in range(diff):
        string += ' '
    string = string[0:col]
    return string + '\t'


# 显示搜索到的课程表
def print_list(page_info):
    print('\n' + zh_en('序号', 2) + zh_en('课程', 30) + zh_en('进度', 8) + zh_en('学校', 32) + zh_en('教师', 20))
    for i in range(len(coursesList)):
        course = coursesList[i][0]
        schedule = calc_time(coursesList[i][5], coursesList[i][3])
        school = coursesList[i][2]
        teachers = coursesList[i][1]
        print(zh_en(i, 2) + zh_en(course, 30) + zh_en(schedule, 8) + zh_en(school, 32) + zh_en(teachers, 20))
    print('\n\t共{}条记录\t当前第{}页\t共{}页\n'.format(page_info[1], page_info[0], page_info[2]))
    print('\t下一页 - n\t上一页 - u\t跳至第n页 - pn\t\t选择序号n - n')


# def print_list_old(page_info):  # 老办法，效果太差
#     table = '{:2}\t{:32}\t{:15}\t{:32}\t{:.20s}'  # 中英文混合排版问题有点难搞...
#     print('\n' + table.format('序号', '课程', '进度', '学校', '教师'))
#     for i in range(len(coursesList)):
#         print(table.format(i, coursesList[i][0], calc_time(coursesList[i][5], coursesList[i][3]), coursesList[i][2],
#                            coursesList[i][1]))
#     print('\n\t共{}条记录\t当前第{}页\t共{}页\n'.format(page_info[1], page_info[0], page_info[2]))
#     print('\t下一页 - n\t上一页 - u\t跳至第n页 - pn\t\t选择序号n - n')


# 选定课程
def select_course(number, tid=0):
    try:
        course_name = tid if tid != 0 else coursesList[number][0]
        tid = tid if tid != 0 else coursesList[number][4]
        video = input('下载视频(v)还是课件(p)？ ')
        video = True if re.match(r'[Vv]', video) else False
        file_list = get_lesson_file(tid, video=video)
        file_type = '段视频' if video else '份课件'
        confirm = input('《{}》当前共{}{}，确认下载？(Y/N)\n'.format(course_name, len(file_list), file_type))
        if re.match(r'[Yy]', confirm):
            while True:
                path = input('输入保存路径：(默认当前目录-{})\n'.format(os.getcwd()))
                try:
                    if not path:
                        break
                    if not os.path.isdir(path):
                        os.mkdir(path)
                    break
                except NotImplementedError:
                    print('[-]ERROR:非法路径')
            download_file(file_list, path, video=video)
    except requests.HTTPError:
        print('[-]ERROR: select error\n')
        raise
    except MOOCException as ex:
        print(str(ex))
        # print('[*]WARNING: 该课程无课件文档\n')


# 搜索MOOC网的课程
def search(keyword, page_index=1, page_size=20, status=30):
    global coursesList, pagesInfo
    search_url = 'http://www.icourse163.org/dwr/call/plaincall/MocSearchBean.searchMocCourse.dwr'
    url_keyword = urllib.request.quote(keyword)
    dataSearch['c0-e1'] = 'string:{}'.format(url_keyword)
    dataSearch['c0-e2'] = 'number:{}'.format(page_index)
    dataSearch['c0-e6'] = 'number:{}'.format(status)  # 0-已结束; 10-正在进行; 20-即将开始; 30-所有课程
    dataSearch['c0-e7'] = 'number:{}'.format(page_size)
    dataSearch['batchId'] = batch_id()
    try:
        res_text = post_response(search_url, dataSearch)
        (coursesList, page_info) = parse_info(res_text)
        print_list(page_info)
    except requests.HTTPError or MOOCException as ex:
        print('[-]ERROR: %s' % str(ex))
        raise


def main():
    keyword = input('输入学期ID(tid)，或者输入关键字搜索课程：')
    if re.match(r'\d{10}', keyword):
        select_course(0, int(keyword))
        return
    search(keyword)
    while True:
        operate = input('\n接下来的操作:\t( quit退出 )\n')
        if re.match(r'^\d+$', operate):
            select_course(int(operate))
        elif re.match(r'^p\d+$', operate, re.I):
            turn_to_page(keyword, int(operate[1:]))
        elif re.match(r'^[un]$', operate):
            turn_to_page(keyword, operate)
        elif re.match(r'^quit$', operate):
            break
        else:
            try:
                print(eval(operate))
            except NameError:
                print('无效操作')


if __name__ == '__main__':
    main()
