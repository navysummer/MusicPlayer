try:
    from Tkinter import *
    import ttk
    from Tkinter import tkMessageBox as messagebox
except ImportError as e:
    from tkinter import *
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import filedialog
    from tkinter import simpledialog
finally:
    import os
    import pygame

class MUsicPlayer(object):
    """docstring for MUsicPlayer"""
    def __init__(self):
        super(MUsicPlayer, self).__init__()
        self.musicList=[]
        self.musicFormat = ['cda','wav','mid','mp3','m4a','ogg','flac','amr']
        self.flag = False
        self.MainWindow()

    def MainWindow(self):
        self.root = Tk()
        self.sourceAddFrame = Frame(self.root)
        self.sourceAddFrame.pack()
        self.addLocalSource = ttk.Combobox(self.sourceAddFrame,state='readonly')
        self.addLocalSource['values'] = ['请选择本地源','本地音乐文件','本地文件夹']
        self.addLocalSource.current(0)
        self.addLocalSource.bind('<<ComboboxSelected>>',self.getLocalMusic)
        self.addNetworkSource = Button(self.sourceAddFrame,text='添加网络音乐',command=self.getNetworkMusic)
        self.addLocalSource.pack(side=LEFT,fill=BOTH)
        self.addNetworkSource.pack(side=RIGHT,fill=BOTH)

        self.playListFrame = Frame(self.root, height=200, width=300)
        self.playFrame = Frame(self.root, height=200, width=300)
        
        self.playlistTitleLabel = Label(self.playListFrame,text='播放列表')
        self.playList = Listbox(self.playListFrame)
        self.playListFrame.pack(side=LEFT,fill=BOTH)
        self.playFrame.pack(side=RIGHT,fill=BOTH)
        self.playlistTitleLabel.pack()
        self.playList.pack()
        for l in self.musicList:
            self.playList.insert(END,i['song'])
        self.playList.bind('<Double-Button-1>', self.play)

        self.setFrame = Frame(self.root)
        # self.playsetFrame = Frame(self.setFrame, height=200, width=300)
        self.playBtn = Button(self.setFrame,text='播放',command=self.change)
        # self.volumeFrame = Frame(self.setFrame, height=200, width=300)
        self.setFrame.pack()
        self.playBtn.pack()
        # self.volumeFrame.pack(side=LEFT,fill=BOTH)
        self.root.mainloop()

    def getNetworkMusic(self):
        self.master = Tk()
        self.keyword = Entry(self.master)
        self.searchBtn = Button(self.master,text='搜索',command=self.searchSong)
        self.keyword.pack(side=LEFT,fill=BOTH)
        self.searchBtn.pack(side=RIGHT,fill=BOTH)
        self.master.mainloop()

    def searchSong(self):
        self.keyword.pack_forget()
        self.searchBtn.pack_forget()


    def getLocalMusic(self,event):
        if self.addLocalSource.current() == 1:
            localMusicList = filedialog.askopenfilenames()
            for i in localMusicList:
                songFormat = i.split('/')[-1].split('.')[-1]
                songName = i.split('/')[-1].split('.')[:-1]
                if songFormat.lower() in self.musicFormat:
                    self.musicList.append({'song':songName,'path':i,'format':songFormat,'status':0})
                    self.playList.insert(END,songName)
        elif self.addLocalSource.current() == 2:
            path = filedialog.askdirectory()
            # print(path)
            files = os.listdir( path )
            for f in files:
                songFormat = f.split('/')[-1].split('.')[-1]
                songName = f.split('/')[-1].split('.')[:-1]
                if songFormat.lower() in self.musicFormat:
                    songPath = path + '/' + f
                    self.musicList.append({'song':songName,'path':songPath,'format':songFormat,'status':0})
                    self.playList.insert(END,songName)
    def play(self,even):
        pygame.mixer.init()
        if self.playList.curselection():
            i = int(self.playList.curselection()[0])
            song = self.musicList[i]
            filename = song['path']
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play(loops=0, start=0)
            pygame.mixer.music.set_volume(0.5)

    def change(self,even):
        if self.flag:
            self.play(even)
        else:
            pygame.mixer.music.stop()
        self.flag = not self.flag
    


def main():
    MUsicPlayer()

if __name__ == '__main__':
    main()
        