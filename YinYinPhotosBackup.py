import gzip
import re
import os
import sys
import time
import threading
import http.cookiejar
import urllib.request
import urllib.parse

url = 'http://www.renren.com/PLogin.do'

header = {
    'Connection': 'Keep-Alive',
    'Accept': 'text/html, application/xhtml+xml, */*',
    'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.renren.com',
    'AllowAutoRedirect': 'false',
    'DNT': '1'
}

postDict = {
        'email': None,
        'password': None,
        'autoLogin': 'true',
        "origURL": "http://www.renren.com/home",
        "domain": "renren.com",
        "key_id": "1",
        "captcha_type": "web_login"
}

  
def ungzip(data):
    try:        #尝试解压
        data = gzip.decompress(data)
    except:
        pass
    return data
  
  
def buildOpener(head):
    # 创建Opener自动处理Cookies
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(pro)
    header = []
    for key, value in head.items():
        elem = (key, value)
        header.append(elem)
    opener.addheaders = header
    urllib.request.install_opener(opener)
    

def photosCalculator(albumId):
    global ownerId, numberOfPhoto
    albumLink = 'http://photo.renren.com/photo/'+ownerId+'/album-'+albumId+'/v7'
    albumPage=ungzip(urllib.request.urlopen(albumLink).read()).decode()
    photoLinkRe = re.compile('"url":"(.*?)"}')
    numInOneAlbum = len(re.findall(photoLinkRe, albumPage))
    numberOfPhoto = numberOfPhoto+numInOneAlbum


    
def getPhotos(albumName, albumId):  #获取图片的函数
    global ownerId, lockObj, currentCount
    downloadDir = albumName+os.sep
    albumLink = 'http://photo.renren.com/photo/'+ownerId+'/album-'+albumId+'/v7'
    albumPage=ungzip(urllib.request.urlopen(albumLink).read()).decode()
    photoLinkRe = re.compile('"url":"(.*?)"}')
    photoLinkList = re.findall(photoLinkRe, albumPage)
    for i,j in enumerate(photoLinkList):
        j=j.replace('\\','')
        urllib.request.urlretrieve(j, downloadDir+'%d.jpg' % i)
        if lockObj.acquire(1):
            currentCount +=1
            lockObj.release()
  

##################################################################
#创建opener自动处理cookie
buildOpener(header)
  
#初次登陆 获取对应用户的ID
while True:
    try:
        postDict['email'] = input("请输入您的人人网账号： ").strip()
        postDict['password'] = input("请输入您的账号密码： ").strip()
        postData = urllib.parse.urlencode(postDict).encode()
        req = urllib.request.Request(url, postData)
        htmlObj=urllib.request.urlopen(req)
    except:
        print("登陆账号或密码不正确！请重新输入！")
    else:
        print('正在登陆人人网服务器获取相册及相片信息，请稍等...\n')
        break
ownerId=htmlObj.geturl()[22:]



#用户相册的主页URL
albumsLink='http://photo.renren.com/photo/'+ownerId+'/albumlist/v7#'

#确保获取的相册名正确无误
tag=True
while tag:
    tag=False
    
    req1=urllib.request.Request(albumsLink)
    htmlObj1=urllib.request.urlopen(req1)
    data = htmlObj1.read()
    albumsPage = ungzip(data).decode() #获取相册首页代码

    #正则 获取相册名
    albumsNameRe = re.compile('"albumName":"(.*?)","albumId"') #重复元字符后加？表示：匹配的非贪婪模式 
    albumsList = re.findall(albumsNameRe,albumsPage)
    
    #如果相册名字中包含 \\ 则跳出此循环，然后重新请求一次
    for i in albumsList:
        if i.count('\\')>0:
            tag=True
            break                      


#正则 获取相册ID
albumsIdRe = re.compile(r'"albumId":"(.*?)","ownerId"')
albumsId = re.findall(albumsIdRe,albumsPage)


#此乃计算相册数和相片数代码
numberOfPhoto = 0  #初始相片总数
tList=[]
for i in albumsId:
    tt=threading.Thread(target=photosCalculator, args=(i,))
    tList.append(tt)
    tt.start()   
for i in tList:
    i.join()
    
print('您有%d个相册' % len(albumsList))
print('您有%d张相片' % numberOfPhoto)
print('是否开始备份？（请输入"yes" 或 "no"）')
if 'no'==input():
    print("感谢您的使用，程序将在3秒后自动退出。")
    time.sleep(3)
    sys.exit()
else:
    print('\n')
    pass


#创建相册文件夹
os.mkdir('myRenRenPhoto')
os.chdir('myRenRenPhoto')
for i in albumsList:
    os.mkdir(i)


#多线程 图片备份代码
print('图片备份中，请稍等...')
currentCount = 0
lockObj = threading.Lock()
time.clock()
threadsList=[]
for i,j in zip(albumsList,albumsId):
    t=threading.Thread(target=getPhotos, args=(i,j))
    threadsList.append(t)
    t.start()


#循环提示当前备份了多少张相片
while(currentCount!=numberOfPhoto):
    time.sleep(3)
    print("您备份了 %d/%d 张相片！" % (currentCount,numberOfPhoto))

print('\n')
print('备份完毕！')
print('您总共花了%.1f秒时间备份了%d张照片!' % (time.clock(),numberOfPhoto))

input("\n请按任意键退出程序。")



    
    







