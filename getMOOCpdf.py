"""
    Author: Adam
    Email : 511533552@qq.com
    Blog  : www.adamyt.com
"""
import requests, re, time, os, urllib.request, math
 
headers = {'Host': 'www.icourse163.org',
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
'Accept-Encoding': 'gzip, deflate',
'Content-Type': 'text/plain',
'Connection': 'keep-alive'}
 
dataSearch = {'callCount':'1',
'scriptSessionId':'${scriptSessionId}190',
'c0-scriptName':'MocSearchBean',
'c0-methodName':'searchMocCourse',
'c0-id':'0',
'c0-e1':'string:python',
'c0-e2':'number:1',
'c0-e3':'boolean:true',
'c0-e4':'null:null',
'c0-e5':'number:0',
'c0-e6':'number:30',
'c0-e7':'number:20',
'c0-param0':'Object_Object:{keyword:reference:c0-e1,pageIndex:reference:c0-e2,highlight:reference:c0-e3,\
categoryId:reference:c0-e4,orderBy:reference:c0-e5,stats:reference:c0-e6,pageSize:reference:c0-e7}',
'batchId':'1490456943066'}
 
dataGetMocTermDto = {'callCount':'1',
'scriptSessionId':'${scriptSessionId}190',
'c0-scriptName':'CourseBean',
'c0-methodName':'getMocTermDto',
'c0-id':'0',
'c0-param0':'number:1001962001',                        #tid 课程学期Id
'c0-param1':'number:1',
'c0-param2':'boolean:true',
'batchId':'1490456943066'}
 
dataGetLessonUnitLearnVo = {'callCount':'1',
'scriptSessionId':'${scriptSessionId}190',
'c0-scriptName':'CourseBean',
'c0-methodName':'getLessonUnitLearnVo',
'c0-id':'0',
'c0-param0':'number:805080',                            #contentId
'c0-param1':'number:3',                                 #type=3代表文档  type=1代表视频
'c0-param2':'number:0',
'c0-param3':'number:1002834377',                        #id
'batchId':'1490456943066'}                        
 
pagesInfo = {'pageIndex': 0, 'totalPages': 0, 'totalCount': 0}      #页数信息
coursesList = []                                                    #储存课程列表
 
def getResponse(url, data):
    try:
        res = requests.post(url, headers = headers, data = data)
        res.raise_for_status()
        return res.text
    except:
        print('[-]ERROR: post error')
 
 
def batchId():                                                      #批处理时间
    return round(time.time()*1000)
 
 
def turnToPage(keyword, page):                                      #翻页
    global pagesInfo
    if(page == 'n' and pagesInfo['totalPages'] > pagesInfo['pageIndex']):
        search(keyword, pagesInfo['pageIndex']+1)
    elif(page == 'u' and pagesInfo['pageIndex'] > 1):
        search(keyword, pagesInfo['pageIndex']-1)
    elif(type(page) == int and page > 0 and page <= pagesInfo['totalPages']):
        search(keyword, page)
    else:
        print('无法翻页')
 
 
def calcTime(unixStart, unixEnd):                                   #计算当前周
    unixStart = int(unixStart) /1000
    unixEnd = int(unixEnd) / 1000
    unixNow = round(time.time())
    if(unixNow > unixEnd):
        return '已经结束'
    elif(unixNow < unixStart):
        return '尚未开始'
    else:
        return '至第{}周'.format(math.ceil((unixNow-unixStart) / (3600*24*7)))
 
def zh_en(string, col = 0):                                         #严格输出col个宽度
    if col == 0:
        return string
    string = str(string)
    length = len(string)
    lenChinese = 0
    lenEnglish = 0
    for i in range (length):
        if string[i] >= u'\u4e00' and string[i] <= u'\u9fa5':       #中文
            lenChinese += 1
        elif string[i] >= u'\uff00' and string[i] <= u'\uffef':     #全角标点
            lenChinese += 1
        elif string[i] >= u'\u3000' and string[i] <= u'\u303f':     #CJK标点
            lenChinese += 1
        elif string[i] >= u'\u2013' and string[i] <= u'\u2026':     #神奇的破折号等
            lenChinese += 1
        else:
            lenEnglish += 1
    realLen = lenChinese*2 + lenEnglish
    diff = col - realLen
    for i in range(diff):
        string += ' '
    string = string[0:col]
    return string + '\t'
     
def printList(coursesList, pageInfo):
    print('\n' + zh_en('序号', 2) + zh_en('课程', 30) + zh_en('进度', 8) + zh_en('学校', 32) + zh_en('教师', 20))
    for i in range(len(coursesList)):
        course = coursesList[i][0]
        schedule = calcTime(coursesList[i][5], coursesList[i][3])
        school = coursesList[i][2]
        teachers = coursesList[i][1]
        print(zh_en(i, 2) + zh_en(course, 30) + zh_en(schedule, 8) + zh_en(school, 32) + zh_en(teachers, 20))
    print('\n\t共{}条记录\t当前第{}页\t共{}页\n'.format(pageInfo[1], pageInfo[0], pageInfo[2]))
    print('\t下一页 - n\t上一页 - u\t跳至第n页 - pn\t\t选择序号n - n')
 
def printList_old(coursesList, pageInfo):                           #老办法，效果太差
    table = '{:2}\t{:32}\t{:15}\t{:32}\t{:.20s}'                    #中英文混合排版问题有点难搞...
    print('\n' + table.format('序号', '课程', '进度', '学校', '教师'))
    for i in range(len(coursesList)):
        print(table.format(i, coursesList[i][0], calcTime(coursesList[i][5], coursesList[i][3]), coursesList[i][2], coursesList[i][1]))
    print('\n\t共{}条记录\t当前第{}页\t共{}页\n'.format(pageInfo[1], pageInfo[0], pageInfo[2]))
    print('\t下一页 - n\t上一页 - u\t跳至第n页 - pn\t\t选择序号n - n')
 
 
def selectCourse(number, tid = 0):
    try:
        courseName = tid if tid != 0 else coursesList[number][0]
        tid = tid if tid != 0 else coursesList[number][4]
        pdfList = getMocTermDto(tid)
        confirm = input('《{}》当前共有{}份pdf文档，确认全部下载？(Y/N)\n'.format(courseName, len(pdfList)))
        if re.match(r'[Yy]', confirm):
            while(True):
                path = input('输入保存路径：\t(ctrl-c结束)\n')
                try:
                    if not os.path.isdir(path):
                        os.mkdir(path)
                    break
                except:
                    print('[-]ERROR:非法路径')
                    pass
            downloadPdf(pdfList, path)
    except:
        print('[-]ERROR: select error\n')
 
 
def parseInfo(resText):                                             #解析搜索返回信息
    #re_courseInfo = r'cid=(\d*);.*highlightName="(.*?)";.*highlightTeacherNames="(.*?)";.*highlightUniversity="(.*?)";'
    re_getInfo = r'.*highlightName="(.*?)";.*highlightTeacherNames="(.*?)";.*highlightUniversity="(.*?)";[\s\S]+?endTime=(\d*);[\s\S]+?\.id=(\d*);[\s\S]+?startTime=(\d*);'
    re_getPageInfo = r'pageIndex=(\d*);.*totleCount=(\d*);.*totlePageCount=(\d*);'  #你没有看错 不是我单词拼错了orz
    try:
        content = resText.encode('utf-8').decode('unicode_escape')
        content = re.sub(r'(\{##)|(##\})', '', content)
        coursesList = re.findall(re_getInfo, content)
        pageInfo = re.findall(re_getPageInfo, content[-500:])[0]
        if coursesList == [] or pageInfo == []:
            raise
        global pagesInfo
        pagesInfo['pageIndex'] = int(pageInfo[0])
        pagesInfo['totalCount'] = int(pageInfo[1])
        pagesInfo['totalPages'] = int(pageInfo[2])
        return coursesList, pageInfo
    except:
        if(int(pageInfo[1]) == 0):
            print('\n未搜索到任何记录\n')
        else:
            print('[-]ERROR: parse error\n')
 
 
def parseMocTermDto(resText):                                       #解析课程返回信息
    re_getList = r'anchorQuestions=.*contentId=(\d*);.*contentType=3;.*id=(\d*);.*name="(.*)";'
    try:
        content = resText.encode('utf-8').decode('unicode_escape')
        pdfList = re.findall(re_getList, content)
        if pdfList == []:
            raise
        return pdfList
    except:
        print(content[:500])
        print('[-]ERROR: pdfList is empty')
 
 
def parseLessonUnitLearnVo(resText):                                #解析课件返回信息
    re_getPdf = r'http://nos.netease.com/.*?\.pdf'
    try:
        #content = resText.encode('utf-8').decode('unicode_escape')
        pdfUrl = re.search(re_getPdf, resText).group(0)
        if pdfUrl == None:
            raise
        return pdfUrl
    except:
        print('[-]ERROR: pdfUrl is None')
 
 
def search(keyword, pageIndex = 1, pageSize = 20, status = 30):     #搜索MOOC网的课程
    global coursesList, pagesInfo
    searchUrl = 'http://www.icourse163.org/dwr/call/plaincall/MocSearchBean.searchMocCourse.dwr'
    urlKeyword = urllib.request.quote(keyword)
    dataSearch['c0-e1'] = 'string:{}'.format(urlKeyword)
    dataSearch['c0-e2'] = 'number:{}'.format(pageIndex)
    dataSearch['c0-e6'] = 'number:{}'.format(status)                #0: 已结束; 10: 正在进行; 20: 即将开始; 30: 所有课程
    dataSearch['c0-e7'] = 'number:{}'.format(pageSize)
    dataSearch['batchId'] = batchId()
    try:
        resText = getResponse(searchUrl, dataSearch)
        (coursesList, pageInfo) = parseInfo(resText)
        printList(coursesList, pageInfo)
    except:
        if not pagesInfo['totalCount'] == 0:
            print('[-]ERROR: search error')
 
 
def getMocTermDto(tid):                                             # post to getMocTermDto.dwr
    getMocTermDtoUrl = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getMocTermDto.dwr'
    dataGetMocTermDto['c0-param0'] = 'number:{}'.format(tid)
    dataGetMocTermDto['batchId'] = batchId()
    try:
        resText = getResponse(getMocTermDtoUrl, dataGetMocTermDto)
        pdfList = parseMocTermDto(resText)
        return pdfList
    except:
        print('[-]ERROR: getMocTermDto has failed')
        pass
 
 
def downloadPdf(pdfList, path):                                     # post to getLessonUnitLearnVo.dwr
    getLessonUnitLearnVoUrl = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr'
    count = 1
    errorCount = 0
    for item in pdfList:
        pdfName = item[2]
        contentId = item[0]
        Id = item[1]
        pdfName = re.sub(r'[/\\"<>:\*\|\?]', '', pdfName)           #文件名非法字符
        if os.path.exists('{}/{}.pdf'.format(path, pdfName)):
            print('{}\t已存在， 跳过 ...\n'.format(pdfName))
            continue
        dataGetLessonUnitLearnVo['c0-param0'] = 'number:{}'.format(contentId)
        dataGetLessonUnitLearnVo['c0-param3'] = 'number:{}'.format(Id)
        dataGetLessonUnitLearnVo['batchId'] = batchId()
        print('[+]正在下载第{}份 - {} ...\n'.format(count, pdfName))
        try:
            resText = getResponse(getLessonUnitLearnVoUrl, dataGetLessonUnitLearnVo)
            pdfUrl = parseLessonUnitLearnVo(resText)
            pdf = requests.get(pdfUrl)
            with open('{}/{}.pdf'.format(path, pdfName), 'wb') as file:
                file.write(pdf.content)
        except Exception as e:
            print('[-]ERROR: {} download error\n'.format(pdfName))
            print(e)
            errorCount += 1
            continue
        count += 1
    print('下载完成\t共下载{}份\t{}份下载失败\n'.format(count - 1, errorCount))
    return
 
 
def main():
    keyword = input('输入查询课程(or tid)：')
    if re.match(r'\d{10}', keyword):
        selectCourse(0, keyword)
    else:
        search(keyword)
    while(True):
        operate = input('\n接下来的操作:\t( quit退出 ,想重新搜索请quit后输入main() )\n')
        if re.match(r'^\d+$', operate):
            selectCourse(int(operate))
        elif re.match(r'^p\d+$', operate, re.I):
            turnToPage(keyword, int(operate[1:]))
        elif re.match(r'^[un]$', operate):
            turnToPage(keyword, operate)
        elif re.match(r'^quit$', operate):
            break
        else:
            try:
                eval(operate)
            except:
                print('无效操作')
    return
 
 
if __name__ == '__main__':
    main()
