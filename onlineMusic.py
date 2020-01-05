# # -*- coding: UTF-8 -*-

# try:
#     from Tkinter import *
#     import ttk
#     from Tkinter import tkMessageBox as messagebox
# except ImportError as e:
#     from tkinter import *
#     from tkinter import ttk
#     from tkinter import messagebox
# import urllib 
# import json 
# import mp3play 
# import time 
  
# musicList = [] 
  
# #定义点击按钮响应的函数 
# def music(): 
#     #print "按钮点击" 
#     #先判断用户是否在编辑框输入了内容 
#     if E.get() == '': 
#         #发出警告，需要先import tkMessageBox 
#         messagebox.showinfo("提示：","请先输入内容！") 
#         #使用return，当满足前面的条件时，不在往下执行 
#         return
#     #使用网易api，发送请求，需要import urllib 
#     #报错，需要将汉字编码程ascii，才能添加到链接中 
#     name = E.get().encode('utf-8') 
#     name = urllib.quote(name) 
#     html = urllib.urlopen('http://s.music.163.com/search/get/?type=1&s=%s&limit=9'%name).read() 
#     #返回json格式数据,可用正则匹配需要数据，也可使用json.loads() 
#     print(html)
#     #将返回文件转化为json格式，提取所需要的数据，需要import json 
#     a = json.loads(html) 
#     #print a 
#     print(a[u'result'][u'songs'][0][u'album'][u'name'])
#     #将所有结果显示在列表中 
#     #print len(a[u'result'][u'songs'][0]) 
#     for i in range(len(a[u'result'][u'songs'][0])): 
#         #注意insert参数 
#         LB.insert(i,a[u'result'][u'songs'][i][u'album'][u'name']+"("+a[u'result'][u'songs'][i][u'artists'][0][u'name']+")") 
#         #先获取到歌曲url列表 
#         musicList.append(a[u'result'][u'songs'][i][u'audio']) 

# #定义双击列表响应函数 
# def play(event): 
#     #获取点击后返回的结果curselection() 
#     #print LB.curselection()[0] 
#     urlnum = LB.curselection()[0] 
#     #不用流媒体播放，先下载下来再播放 
#     # urllib.urlretrieve(musicList[urlnum],'1.mp3') 
#     # #播放歌曲，调用import mp3play 
#     # time.sleep(50) 
#     clip = mp3play.load('1.mp3') 
#     clip.play() 
#     #设置播放时间import time 
#     time.sleep(min(300, clip.seconds())) 
#     #死机了，无法响应，因为线程的问题！！！！！！ 
#     #一个线程同一时间只能做一件事情，放歌时需再开一个线程 
  
  
# #创建父窗口对象， 
# top = Tk() 
# #可以设置窗口的属性,如：标题，大小 
# top.title("在线音乐播放器——张强") 
# top.geometry('500x300+800+300') 
# #创建编辑框，放到父窗口top上,用pack显示 
# E = Entry(top) 
# E.pack() 
# #创建按钮,定义按钮触发的函数command 
# B = Button(top,text="搜 索",command = music) 
# B.pack() 
# #定义列表的响应函数 
# LB = Listbox(top,width = '50',listvariable = StringVar()) 
# #绑定触发事件的方式-双击左键，和响应函数 
# LB.bind('<Double-Button-1>',play) 
# LB.pack()#要放到最后 
# #定义标签 
# label = Label(top,text = "欢迎使用！",fg = 'red') 
# label.pack() 
# #循环向windows发送消息，用于显示窗口 
# top.mainloop() 

import pygame
import mp3play
import time
pygame.init()
#clip = mp3play.load(‘能不能.mp3‘)
clip = mp3play.load("http://upupyoyoyo.net/COFFdD0xMzY5NzM1OTU1Jmk9MTIxLjE1LjEzMC4xNTMmdT1Tb25ncy92Mi9mYWludFFDLzVjL2E3LzZiN2QyZjEwNzEzZTM5ZGI5ZDZiOGE2ODc4YmRhNzVjLm1wMyZtPTdkOThlNmM2ZTVkNTAwMzAzMmEwMGY3NzJhYWRkNmY0JnY9ZG93biZuPcqyw7S2vL/J0tQmcz27xs/+w/cmcD1z.mp3")
clip.play()
time.sleep(min(30, clip.seconds()))
clip.stop()