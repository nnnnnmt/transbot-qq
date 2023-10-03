import win32gui
import win32con
import win32clipboard as clipboard
import time
import schedule
from PIL import Image
from io import BytesIO
from datetime import datetime
import string
import random
import requests
import mysql.connector
from flask import Flask,request
import re

def getText():
    clipboard.OpenClipboard()
    d = clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
    clipboard.CloseClipboard()
    return d

def Send_Image(name,path):
    img = Image.open(path)
    output = BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    # 打开剪贴板
    clipboard.OpenClipboard()
    # 清空剪贴板
    clipboard.EmptyClipboard()
    clipboard.SetClipboardData(win32con.CF_DIB, data)  #将图片放入剪贴板
    # 获取qq窗口句柄
    handle = win32gui.FindWindow(None, name)
    if handle == 0:
        print("未找到窗口")
    #关闭剪切板
    clipboard.CloseClipboard()
    # 把剪切板内容粘贴到qq窗口
    win32gui.SendMessage(handle, win32con.WM_PASTE, 0, 0)
    # 按下后松开回车键，发送消息
    win32gui.SendMessage(handle, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    win32gui.SendMessage(handle, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
    time.sleep(1)

def Send(name, msg):
    # 打开剪贴板
    clipboard.OpenClipboard()
    # 清空剪贴板
    clipboard.EmptyClipboard()
    # 设置剪贴板内容
    clipboard.SetClipboardData(win32con.CF_UNICODETEXT,msg)
    # 获取剪贴板内容
    #date = clipboard.GetClipboardData()
    # 关闭剪贴板
    clipboard.CloseClipboard()
    #print("***"+getText())
    # 获取qq窗口句柄
    handle = win32gui.FindWindow(None, name)
    if handle == 0:
        print('未找到窗口！')
    # 显示窗口
    #win32gui.ShowWindow(handle, win32con.SW_SHOW)
    # 把剪切板内容粘贴到qq窗口
    win32gui.SendMessage(handle, win32con.WM_PASTE, 0, 0)
    # 按下后松开回车键，发送消息
    win32gui.SendMessage(handle, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    win32gui.SendMessage(handle, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
    time.sleep(1)

def extract_cq_strings(input_string):
    cq_strings = []  # 存储含有 [CQ:*****] 的子字符串
    non_cq_string = ""  # 存储不含 [CQ:*****] 的部分
    # 使用正则表达式匹配所有形如 [CQ:*****] 的子字符串
    pattern = r'\[CQ:(.*?)\]'
    matches = re.finditer(pattern, input_string)
    # 遍历匹配结果
    start_index = 0
    for match in matches:
        # 获取匹配到的子字符串的起始位置和结束位置
        match_start = match.start()
        match_end = match.end()

        # 将不含 [CQ:*****] 的部分添加到 non_cq_string
        non_cq_string += input_string[start_index:match_start]

        # 将含有 [CQ:*****] 的子字符串添加到 cq_strings
        cq_strings.append(match.group(1))

        # 更新下一次搜索的起始位置
        start_index = match_end

    # 添加最后一个 [CQ:*****] 后面的部分到 non_cq_string
    non_cq_string += input_string[start_index:]
    
    url_pattern = r'\[CQ:[^\]]*url=([^]]*)\]'
    urlmatches = re.findall(url_pattern, input_string)

    return cq_strings, non_cq_string,urlmatches

def format_time(timestamp):
    # 将十位时间转换为整数
    # 使用datetime将时间戳转换为datetime对象
    dt_object = datetime.fromtimestamp(timestamp)

    years=dt_object.year
    months=dt_object.month
    days=dt_object.day
    hours = dt_object.hour
    minutes = dt_object.minute
    seconds = dt_object.second
    # 将结果格式化为字符串
    time_format = f"{years}-{months}-{days}-{hours}-{minutes}-{seconds}"
    return time_format,days

def get_nickname(user_id):
    nicknames_dict = {}
    with open('assigned_nicknames.txt', 'r', encoding='utf-8') as assigned_nicknames_file:
        for line in assigned_nicknames_file:
            parts = line.strip().split()
            if (str(user_id)==parts[0]):
                return parts[1]

    return "用户编号未找到昵称" 

def picturedownload(url,index_picture,QQ_id,timestr,usernickname):
    response = requests.get(url)
    if response.status_code == 200:
        file_path="picture/"+timestr+"-"+str(index_picture)+"-"+str(QQ_id)+"-"+usernickname+".jpg"
    # 打开一个本地文件用于写入图片数据，可以使用'wb'模式以二进制方式写入
        with open(file_path, 'wb') as file:
            # 将响应内容写入本地文件
            file.write(response.content)
            msg=usernickname+"："
            print('图片下载完成。')
            insert_wordpicturelog(0,timestr,QQ_id,usernickname,file_path)
            Send(qunname,msg)
            Send_Image(qunname,file_path)
    else:
        print('无法下载图片。HTTP响应代码:', response.status_code)

def refresh_nickname(refresh_user_id=None):
    # 从用户编号文件中读取用户编号
    with open('user_ids.txt', 'r', encoding='utf-8') as user_ids_file:
        user_ids = user_ids_file.readlines()

    # 从昵称文件中读取可用的昵称
    with open('nicknames.txt', 'r', encoding='utf-8') as nicknames_file:
        nicknames = nicknames_file.readlines()

    # 去除末尾的换行符并随机打乱昵称列表
    nicknames = [nickname.strip() for nickname in nicknames]
    random.shuffle(nicknames)

    timestr,days=format_time(time.time())
    # 创建一个文件来存储用户编号和分配的昵称
    if (refresh_user_id==None):
        with open('assigned_nicknames.txt', 'w', encoding='utf-8') as result_file:
            for user_id in user_ids:
                user_id = user_id.strip()
                if not nicknames:
                    break  # 所有昵称都已分配完毕
                nickname = nicknames.pop()
                result_file.write(f"{user_id} {nickname}\n")
                insert_qqidandnickname(timestr,user_id,nickname)
                
        print("昵称分配完成，并已写入 assigned_nicknames.txt 文件中")
    else:
        #print("***"+refresh_user_id)
        with open('assigned_nicknames.txt', 'r', encoding='utf-8') as open_file:
            lines=open_file.readlines()
        nicknameused=[]
        for line in lines:
            line=line.rstrip('\n')
            usernick=line.split()
            nicknameused+=[usernick[1]]

        for i in range(len(lines)):
            usernicks=lines[i].split()
            if (usernicks[0]!=str(refresh_user_id)):
                pass
            else:
                oldnickname=usernicks[1]
                nickkname=nicknames.pop()
                while (nickkname in nicknameused):
                    nickkname=nicknames.pop()
                lines[i]=usernicks[0]+' '+nickkname+'\n'
        #print("****"+oldnickname)
        with open('assigned_nicknames.txt', 'w', encoding='utf-8') as result_file:
            insert_nicknamechangelog(timestr,refresh_user_id,oldnickname,nickkname)
            insert_qqidandnickname(timestr,refresh_user_id,nickkname)
            result_file.writelines(lines)

        print("昵称已更新完成，并已写入 assigned_nicknames.txt 文件中")

class Blacklist:
    def __init__(self):
        self.blacklist = {}  # 用字典来存储黑名单用户及其过期时间

    def add_to_blacklist(self, user_id, hours):
        expiration_time = time.time() + hours*3600
        self.blacklist[user_id] = expiration_time
        print(f"用户 {user_id} 已被添加到黑名单，将在 {hours} 小时后自动移除")

    def remove_from_blacklist(self, user_id):
        if user_id in self.blacklist:
            del self.blacklist[user_id]
            print(f"用户 {user_id} 已从黑名单中移除")
        else:
            print(f"用户 {user_id} 不在黑名单中")

    def check_blacklist(self):
        current_time = time.time()
        expired_users = [user_id for user_id, expiration_time in self.blacklist.items() if current_time >= expiration_time]
        
        for user_id in expired_users:
            del self.blacklist[user_id]
            print(f"用户 {user_id} 已自动从黑名单中移除")
            
    def view_blacklist(self):
        if not self.blacklist:
            print("当前黑名单为空")
        else:
            print("当前黑名单中的用户:")
            for user_id, expiration_time in self.blacklist.items():
                print(f"用户 {user_id}，过期时间: {time.ctime(expiration_time)}")

    def is_user_in_blacklist(self, user_id):
        return user_id in self.blacklist

def blacklistoperation(message,opeqqid,timestr):
    word_list = message.split()
    with open('assigned_nicknames.txt', 'r', encoding='utf-8') as assigned_nicknames_file:
        for line in assigned_nicknames_file:
            parts = line.strip().split()
            if (str(word_list[2])==parts[1]):
                real_number=parts[0]
    #print(word_list)
    if (word_list[1]=="set"):
    #    print("blacklistoperation")
        insert_blacklistlog(timestr,opeqqid,real_number,word_list[2],"set",word_list[3])
        Send(qunname,"用户"+word_list[2]+"被管理员禁言"+str(word_list[3])+"小时")
        blacklist.add_to_blacklist(real_number,int(word_list[3]))
    elif (word_list[1]=="reset"):
    #    print("blacklistoperation")
        insert_blacklistlog(timestr,opeqqid,real_number,word_list[2],"reset")
        Send(qunname,"用户"+word_list[2]+"被管理员解除禁言")
        blacklist.remove_from_blacklist(real_number)

def ifauthorized(QQ_id):
    file_path="authorizedadmin.txt"
    with open(file_path, 'r') as file:
        lines=file.readlines()
        stripped_lines = [line.strip() for line in lines]
        if (str(QQ_id) in stripped_lines):
            return True
        else:
            return False

def insert_qqidandnickname(timestr,qqid,nickname):
    #print(timestr,qqid,nickname)
    insert_query = "INSERT INTO qqidandnickname VALUES (%s,%s,%s)"
    data_to_insert = (timestr,str(qqid),nickname)
    cursor.execute(insert_query, data_to_insert)
    conn.commit()

def insert_nicknamechangelog(timestr,qqid,oldnickname,newnickname):
    insert_query = "INSERT INTO nicknamechangelog VALUES (%s,%s,%s,%s)"
    data_to_insert=(timestr,str(qqid),oldnickname,newnickname)
    cursor.execute(insert_query, data_to_insert)
    conn.commit()

def insert_wordpicturelog(type,timestr,qqid,nickname,msg):
    if (type==0):
        insert_query = "INSERT INTO picturelog VALUES (%s,%s,%s,%s)"
    if (type==1):
        insert_query = "INSERT INTO messagelog VALUES (%s,%s,%s,%s)"
    data_to_insert=(timestr,str(qqid),nickname,msg)
    cursor.execute(insert_query, data_to_insert)
    conn.commit()   

def insert_blacklistlog(timestr,opeqqid,recqqid,nickname,opetype,hour="-1"):
    insert_query = "INSERT INTO blacklistlog VALUES (%s,%s,%s,%s,%s,%s)"
    data_to_insert=(timestr,opeqqid,recqqid,nickname,opetype,hour)
    cursor.execute(insert_query, data_to_insert)
    conn.commit()      

index_word=0
index_picture=0
blacklist = Blacklist()
scheduler=schedule.Scheduler()
scheduler.every()
current_day=0
conn = mysql.connector.connect(
    host="******",
    user="******",
    password="******",
    database="******"
)
qunname="****QQ群名称****"
cursor = conn.cursor()
app=Flask(__name__)
@app.route('/',methods=["POST"])

def QQBot():
    global index_word,index_picture,blacklist,current_day
    p='0'
    #print(request.get_json())
    if request.get_json().get('message_type')=='private':
        QQ_id=request.get_json().get('sender').get('user_id')
        ttime=request.get_json().get('time')
        timestr,current_day0=format_time(ttime)
        if (current_day0 != current_day):
            refresh_nickname()
            current_day=current_day0

        nickname=request.get_json().get('sender').get('nickname')
        message=request.get_json().get('message')
        usernickname=get_nickname(QQ_id)

        blacklist.check_blacklist()
        
        cq_strings, non_cq_string,urlmatches=extract_cq_strings(message)

        if (cq_strings==[] or len(non_cq_string)>0):
            if (ifauthorized(QQ_id) and ("@blacklist" in non_cq_string)):
                blacklistoperation(non_cq_string,QQ_id,timestr)
            elif (("@changename" in non_cq_string) and (blacklist.is_user_in_blacklist(str(QQ_id))==False)):
                word_list = non_cq_string.split()
                #print(word_list)
                if (str(QQ_id)==word_list[1]):
                    refresh_nickname(word_list[1])

            elif (blacklist.is_user_in_blacklist(str(QQ_id))==False):
                #纯文字情况 或文字、表情/文字、图片表情夹杂情况  只处理文字段信息
                #print("***收到消息，准备文字发送\n")
                #print("***"+non_cq_string)
                file_path="word/"+timestr+"-"+str(index_word)+"-"+str(QQ_id)+"-"+usernickname+".txt"
                insert_wordpicturelog(1,timestr,QQ_id,usernickname,non_cq_string)
                non_cq_string=usernickname+"：\n"+non_cq_string
                Send(qunname,non_cq_string)
            else:
                pass
        else:
            #发送图片的情况
            if (blacklist.is_user_in_blacklist(str(QQ_id))==False):
                print(urlmatches)
                #print("***收到消息，准备图片发送\n")
                for urll in urlmatches:
                    picturedownload(urll,index_picture,QQ_id,timestr,usernickname)
                    index_picture=index_picture+1
    return p


if __name__=="__main__":
    app.run(debug=True,host="127.0.0.1",port='5701')

