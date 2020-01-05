from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
import re
import psutil as ps
import os
import pathlib as pa
# from tkinter import messagebox
from pygame import mixer
# import eyed3
# import time
from tinytag import TinyTag as ti
from threading import Timer
from random import randint


##music list choose
class mlf(Toplevel):
    def __init__(self, parent, stems, lb_test, musiclist, playlist):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        self.title('Files you find')
        self.parent = parent
        self.grab_set()
        self.lb_test = lb_test
        self.fr = ttk.Labelframe(self, text='Choose desks to scan')
        self.fr.pack(side=TOP, fill=BOTH, expand=YES)
        self.stems = stems
        self.select_stem = []
        self.musiclsit = musiclist
        self.playlist = playlist
        self.lb = Listbox(self.fr, font=('微软雅黑', 10, 'bold'), selectmode='extended')
        self.lb.pack(side=LEFT, fill=BOTH, expand=YES)
        for stem in stems:
            self.lb.insert(END, pa.Path(stem).stem)
        scroll = ttk.Scrollbar(self.fr, command=self.lb.yview)
        scroll.pack(side=RIGHT, fill=BOTH)
        self.lb.configure(yscrollcommand=scroll.set)
        self.select_all = ttk.Button(self, text='Select all', command=self.select_allf)
        self.select_all.pack(side=LEFT, fill=Y, expand=YES)
        self.ok = ttk.Button(self, text='Ok', command=self.okf)
        self.ok.pack(side=LEFT, fill=Y, expand=YES)
        self.quit_all = ttk.Button(self, text='Quit all', command=self.quit_allf)
        self.quit_all.pack(side=RIGHT, fill=Y, expand=YES)

    def select_allf(self):
        self.lb.selection_set(0, END)

    def okf(self):
        print(self.lb.curselection())
        for x in self.lb.curselection():
            if x not in self.select_stem:
                self.select_stem.append(self.stems[x])
        print(self.select_stem)
        for x in self.select_stem:  # should create a txt to save musiclist !!
            if x not in self.musiclsit:
                self.musiclsit.append(x)
                self.lb_test.insert(END, pa.Path(x).stem)
                self.playlist.append(x)
        self.destroy()

    def quit_allf(self):
        self.lb.selection_clear(0, END)


# Custom Dialog
class sfs(Toplevel):
    def __init__(self, parent, lb, sf, musiclist, save, playlist):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        self.title('Choose desks and Scan files')
        self.parent = parent
        self.grab_set()
        self.lb_test = lb
        self.musiclist = musiclist
        self.playlist = playlist
        self.sf = sf
        self.save = save
        fr = ttk.Labelframe(self, text='Choose desks to scan')
        fr.pack()
        d = ps.disk_partitions()
        # limit files size
        self.test = FALSE
        self.maxs = IntVar()
        self.mins = IntVar()
        self.maxs.set(50)
        self.mins.set(1)
        self.ax = []
        self.bool = BooleanVar()
        self.bool.set(FALSE)

        for xx in d:
            if not xx[3] == 'cdrom':
                print(xx[0])
                self.ax.append(xx[0])
        i = 0
        self.desks = []
        for desk in self.ax:
            strVar = StringVar()
            self.desks.append(strVar)
            cb = ttk.Checkbutton(self, text=desk, variable=strVar, onvalue=str(i), offvalue='none',
                                 command=self.choose);
            i += 1
            cb.pack(anchor=W)
        self.ok = ttk.Button(self, text='Ok', command=self.okf);
        self.ok.pack(side=LEFT, fill=Y, expand=YES)
        self.cancel = ttk.Button(self, text='Return', command=self.cancelf)
        self.cancel.pack(side=LEFT, fill=Y, expand=YES)
        self.sizel = ttk.Button(self, text='Limit the file size', command=self.sizelf)
        self.sizel.pack(side=RIGHT, fill=Y, expand=YES)

    def choose(self):
        st = [e.get() for e in self.desks]
        print(st)

    def okf(self):
        st = [e.get() for e in self.desks]
        # print(st)
        sc = []
        for xx in range(len(st)):
            if str(xx) in st:
                sc.append(self.ax[xx])
        print(sc)

        stems = []
        # for format in ('.mp3','.flac'):\for x in p.glob('**/*'):
        for fx in sc:
            px = pa.Path(fx)
            for x in px.glob('**/*'):
                if ti.is_supported(str(x.name)):
                    # print(x)
                    if (os.path.getsize(x)) > self.mins.get() * 1024 * 1024 and (
                    os.path.getsize(x)) < self.maxs.get() * 1024 * 1024:
                        stems.append(x)
        test = mlf(self, stems, self.lb_test, self.musiclist, self.playlist)

    def cancelf(self):
        self.parent.focus_set()
        self.destroy()
        print('sss')
        self.bool.set(TRUE)
        self.test = TRUE
        self.sf['style'] = 'SM.TLabel'
        self.save()

    def sizelf(self):
        maxs = simpledialog.askinteger('Minimum szie', 'the minimum size of files (\M)', initialvalue=1, )
        mins = simpledialog.askinteger('Maximum szie', 'the maximum size of files (\M)', initialvalue=50)
        if maxs:
            self.mins.set(maxs)
        if mins:
            self.maxs.set(mins)

        print(self.maxs.get())
        print(self.mins.get())


class App():
    def __init__(self, master):
        self.master = master
        self.initt()

    def initt(self):
        titlefont = ('simkai', 15, 'bold')
        self.musiclist = []
        self.playlist = []#播放列表
        self.lines = []
        self.pbl = []
        self.pl = []  # playlist  歌单列表
        self.like=[]#like 歌单第一个
        self.filepathlist=[]  #file path list
        self.play_if = BooleanVar()
        self.play_if.set(FALSE)
        self.is_all = BooleanVar()
        self.is_all.set(TRUE)
        self.playinglist = StringVar()

        self.filename = 'save_music.txt'
        mixer.init()
        self.playing = StringVar()
        self.endsave=[]#save_end_

        try:
            with open(self.filename, 'r+', True, 'UTF-8') as ff:
                self.lines = ff.readlines()
        except:
            f = open(self.filename, 'w+', True, 'UTF-8')
            f.write('musiclist--> \n')
            f.write('playlist--> \n')
            f.write('Like (protected playlist)\n')
            f.write('end--> \n')
            f.write("mode 3\n")
        with open(self.filename, 'r+', True, 'UTF-8') as ff:
            self.lines = ff.readlines()
            if self.lines[1] == 'playlist--> \n':
                print('musiclist is empty')
            else:
                print('tt')
                for line in self.lines[1:self.lines.index(('playlist--> \n'))]:
                    if not line == '\n':
                        self.musiclist.append(line[0:-1])
            if self.lines.index('playlist--> \n') == self.lines.index('end--> \n') - 1:
                print('playlist is empty')
            else:
                for line in self.lines[self.lines.index('playlist--> \n') + 1:self.lines.index('end--> \n')]:
                    if not line == '\n':
                        self.pbl.append(line[0:-1])
                for line in self.lines[self.lines.index('end--> \n')+1: ]:
                    self.endsave.append(line)
                #print(self.pbl)
            #print(self.lines)
        for pb in self.pbl:
            if not ti.is_supported(pb):
                self.pl.append(pb)
        if len(self.musiclist)!=0:
            self.playing.set(self.musiclist[0])
        for x in self.pbl[1:]:
            if pa.Path(x).is_file():
                self.like.append(x)
                #print(x)
            else:
                break
        #print(self.like)
        style = ttk.Style()
        style.configure("BW.TLabel", foreground="blue", background="white", font=titlefont, anchor=W)
        style.configure("CL.TLabel", foreground="blue", background='gray', font=titlefont, anchor=W)
        style.configure("SM.TLabel", foreground="blue", background='white', font=('微软雅黑', 10, 'bold'), anchor=W)
        style.configure("SMCL.TLabel", foreground="blue", background='gray', font=('微软雅黑', 10, 'bold'), anchor=W)
        fmlt = ttk.Frame(self.master, height=1000, width=800)
        fmlt.pack(side=TOP, fill=BOTH, expand=YES, padx=10, pady=10, anchor=NW)
        fml = ttk.Frame(fmlt, height=100, width=100)
        fml.pack(side=LEFT, fill=NONE, expand=NO, padx=10, pady=10, anchor=NW)
        fmb = ttk.Frame(self.master, width=800)
        fmb.pack(side=BOTTOM, fill=X, expand=NO, anchor=S, padx=10, pady=10)
        fmr = ttk.Frame(fmlt, width=500)
        fmr.pack(side=RIGHT, fill=BOTH, expand=YES, anchor=W, padx=5, pady=5)

        fm1 = ttk.Labelframe(fml, text='Playlist setting')
        fm1.pack(side=TOP, fill=NONE, expand=YES, anchor=NW)
        fm1.bind('<Leave>', self.leave_lefttop)
        self.ap = ttk.Button(fm1, text='Add playlist', style='BW.TLabel', command=self.add_pl)
        self.ap.pack(side=TOP, fill=X, expand=YES)
        self.am = ttk.Button(fm1, text='All added mousic', style='BW.TLabel', command=self.all_music)
        self.am.pack(side=TOP, fill=X, expand=YES)
        self.fm2 = ttk.Labelframe(fml, text='Playlist list')
        self.fm2.pack(side=TOP, fill=BOTH, expand=YES, anchor=N, pady=10)
        self.fm3 = ttk.Labelframe(fmr, text='Music list')
        self.fm3.pack(side=BOTTOM, fill=BOTH, expand=YES)
        self.lb = Listbox(self.fm3, selectmode='browse', font=titlefont, foreground="green", background="white")#four mode
        self.lb.pack(side=LEFT, fill=BOTH, expand=YES)
        self.lb.bind('<Button-3>', self.pop)
        self.lb.bind('<Motion>', self.lb_focus)
        self.pb = Listbox(self.fm2, selectmode='browse', font=titlefont)
        self.pb.pack(side=LEFT, fill=BOTH, expand=YES)
        self.pb.bind('<Button-1>', self.artist_play)
        self.pb.bind('<Button-3>', self.pbpop)
        self.pb.bind('<Motion>', self.pb_focus)
        self.pb.bind('<Control-1>',self.ctrlpb)
        self.pb.bind('<ButtonRelease-3>',self.pbrel)
        self.ctrl=BooleanVar()
        self.ctrl.set(FALSE)
        self.popmenu = Menu(self.lb, tearoff=0)
        self.popmenu.add_cascade(label='play', command=self.play_it)
        self.popmenu.add_cascade(label='pause or play', command=self.pause)
        self.m = Menu(self.popmenu, tearoff=0)
        self.popmenu.add_cascade(label='add to playlist', menu=self.m)
        self.popmenu.add_cascade(label='delate', command=self.del_music)

        self.pbmenu = Menu(self.pb, tearoff=0)
        self.pbmenu.add_cascade(label='delate', command=self.del_list)
        self.pbmenu.add_cascade(label='rename', command=self.rename)
        self.pbmenu.add_cascade(label='add', command=self.add_pl)

        fm2 = ttk.Frame(fml)
        fm2.pack(side=BOTTOM, fill=BOTH, expand=YES, anchor=N, pady=10)
        ttk.Button(fm2, text='delate playlist', style='SM.TLabel', command=self.del_list).pack(side=LEFT, expand=NO,
                                                                                               padx=5,
                                                                                               anchor=SW)  # ddddeeettt
        ttk.Button(fm2, text='rename', style='SM.TLabel', command=self.rename).pack(side=LEFT, expand=NO,
                                                                                    padx=5, anchor=SW)
        self.sort=ttk.Button(fm2, text='sort by artist', style='SM.TLabel', command=self.artist)
        self.sort.pack(side=LEFT, expand=NO,padx=5, anchor=SW)
        self.artistnow = BooleanVar()
        self.artistnow.set(FALSE)
        scrollp = ttk.Scrollbar(self.fm2, command=self.pb.yview)
        scrollp.pack(side=RIGHT, fill=Y)
        self.pb.configure(yscrollcommand=scrollp.set)
        for x in self.pl:  # should create a txt to save musiclist !!
            self.pb.insert(END, x)
            self.m.add_command(label=x, command=self.testt(self.add_topl, x=x))
        # ttk.Button(fm2, text='All added mousic', style='BW.TLabel').pack(side=BOTTOM, fill=X, expand=YES)
        fm4 = ttk.Frame(fmr);
        fm4.pack(side=TOP, fill=NONE, expand=NO, anchor=W)
        self.sf = ttk.Button(fm4, text='Scan files', style='SM.TLabel', command=self.sff)
        self.sf.pack(side=LEFT, expand=YES, padx=5, anchor=W)
        self.af = ttk.Button(fm4, text='Add file path', style='SM.TLabel',command=self.aff)
        self.af.pack(side=LEFT, expand=YES, padx=5, anchor=W)
        self.ms = ttk.Button(fm4, text='Browse', style='SM.TLabel',command=self.modechange)
        self.ms.pack(side=LEFT, expand=YES, padx=5, anchor=W)
        self.strVar = StringVar()

        self.cb = ttk.Button(fm4, text=self.endsave[0][0:-1] , style='SM.TLabel', command=self.change_module)
        self.cb.pack(side=LEFT, expand=YES, fill=BOTH, padx=5, anchor=W)
        # Combobox(fm4,textvariable=self.strVar,values=['play in order','random play','loop play in list','loop play single song']), four play model to select
        if len(self.endsave)>1:
            for x in self.endsave[1:]:
                if 'mode' not in x and x!='\n':
                    self.playlist.append(x[0:-1])
                    self.lb.insert(END, pa.Path(x).stem)
                    #print(x)
        else:
            for x in self.musiclist:  # should create a txt to save musiclist !!
                self.lb.insert(END, pa.Path(x).stem)
                self.playlist.append(x)


        scroll = ttk.Scrollbar(self.fm3, command=self.lb.yview)
        scroll.pack(side=LEFT, fill=Y)
        self.lb.configure(yscrollcommand=scroll.set)
        self.lb.bind('<Double-1>', self.choose_play)
        self.cv = Canvas(fmb, background='white', height=40)
        self.cv.pack(fill=BOTH, expand=NO)
        self.cv.bind('<Button-1>', self.click)
        self.cv.bind('<ButtonRelease-1>', self.release)
        self.cv.create_line(97.5 - 5, 22.5 - 10, 97.5 - 5, 22.5 + 10, fill='red', width=4, tag='g1')  # playing
        self.cv.create_line(97.5 + 5, 22.5 - 10, 97.5 + 5, 22.5 + 10, fill='red', width=4, tag='g1')
        self.play_name = self.cv.create_text(220, 5, text=' ', font='simkai', fill='blue', anchor=W, justify=LEFT,
                                             tag='g3')  # play_name
        self.spand = self.cv.create_rectangle(260, 35, 260, 40, fill='green', tag='g3')
        self.cv.tag_lower('g3')

        self.cv.create_line(220, 5 + 2, 220, 35, arrow=FIRST, width=2, fill='red', tag='m2', arrowshap=(5, 10, 5))
        self.cv.create_line(220, 5, 250 - 2, 5, arrow=LAST, width=2, fill='red', tag='m2', arrowshap=(5, 10, 5))
        self.cv.create_line(250, 5, 250, 35 - 2, arrow=LAST, width=2, fill='red', tag='m2', arrowshap=(5, 10, 5))
        self.cv.create_line(250, 35, 220 + 2, 35, arrow=LAST, width=2, fill='red', tag='m2', arrowshap=(5, 10, 5))

        self.cv.create_line(220, 5, 220, 35, arrow=FIRST, width=2, fill='violet', tag='m3', arrowshap=(5, 10, 5))
        self.cv.create_line(220, 5, 250, 5, arrow=None, width=2, fill='violet', tag='m3', arrowshap=(5, 10, 5))
        self.cv.create_line(250, 5, 250, 35, arrow=None, width=2, fill='violet', tag='m3', arrowshap=(5, 10, 5))
        self.cv.create_line(250, 35, 220, 35, arrow=None, width=2, fill='violet', tag='m3', arrowshap=(5, 10, 5))
        self.cv.create_oval(235 - 10, 20 - 10, 235 + 10, 20 + 10, fill='yellow', outline='green', tag='m3')
        self.name=self.cv.create_text(235, 20, text=' ', width=2, fill='blue', tag='m3')

        self.cv.create_line(235 - 5, 20 + 5, 220, 35, arrow=LAST, width=2, fill='violet', tag='m4',
                            arrowshap=(5, 10, 5))
        self.cv.create_line(235 - 5, 20 - 5, 220, 5, arrow=LAST, width=2, fill='violet', tag='m4', arrowshap=(5, 10, 5))
        self.cv.create_line(235 + 5, 20 + 5, 250, 35, arrow=LAST, width=2, fill='violet', tag='m4',
                            arrowshap=(5, 10, 5))
        self.cv.create_line(235 + 5, 20 - 5, 250, 5, arrow=LAST, width=2, fill='violet', tag='m4', arrowshap=(5, 10, 5))

        self.cv.create_rectangle(0, 1, 200 - 5, 42, fill='yellow', width=0)
        self.cv.create_rectangle(200, 1, 260, 42, fill='white', width=0)
        self.cv.create_line(225, 5, 225, 35, arrow=LAST, width=2, fill='red', tag='m1', arrowshap=(5, 10, 5))
        self.cv.create_line(235, 5, 235, 35, arrow=LAST, width=2, fill='red', tag='m1', arrowshap=(5, 10, 5))
        self.cv.create_line(245, 5, 245, 35, arrow=LAST, width=2, fill='red', tag='m1', arrowshap=(5, 10, 5))

        self.cv.create_oval(20, 5, 60 - 5, 40, fill='pink', outline='green')
        self.cv.create_oval(80, 5, 120 - 5, 40, fill='pink', outline='green')
        self.cv.create_oval(140, 5, 180 - 5, 40, fill='pink', outline='green')
        self.cv.create_polygon(22.5, 22.5, 45, 22.5 - 7.5 * 3 ** 0.5, 45, 22.5 + 7.5 * 3 ** 0.5, fill='red')
        self.cv.create_polygon(172.5 - 60, 22.5, 150 - 60, 22.5 - 7.5 * 3 ** 0.5, 150 - 60, 22.5 + 7.5 * 3 ** 0.5,
                               fill='red', tag='g2')  # stop playing
        self.cv.create_polygon(172.5, 22.5, 150, 22.5 - 7.5 * 3 ** 0.5, 150, 22.5 + 7.5 * 3 ** 0.5,
                               fill='red')  # 190-22.5
        self.cv.create_rectangle(500,0,600,10,fill='orange')
        self.cv.create_text(470,6,text='Volume',fill='blue')
        self.vol=self.cv.create_rectangle(500,0,600,10,fill='green')
        self.to_like = self.cv.create_polygon(190, 30, 210, 30, 200, 0, fill='gray')
        self.to_like=self.cv.create_polygon(190,15,210,15,200,30,fill='gray')
        # 定时器需要
        self.pause = BooleanVar()
        self.pause.set(FALSE)
        self.press_3=BooleanVar()
        self.press_3.set(FALSE)#youjian
        self.save()
        self.func()  # check playing_if
        self.speed = 1
        self.long = DoubleVar()
        self.long.set(260.)
        self.control_play = BooleanVar()
        self.control_play.set(FALSE)
        self.change_module();self.change_module();self.change_module();self.change_module();self.change_module();
    def func(self):#实时更新
        if self.play_if.get() and mixer.music.get_busy():
            test = ti.get(self.playing.get())
            self.speed = 24 / float(test.duration)
            self.long.set(self.long.get() + self.speed)
            #self.name['text']=self.playing.get()
            self.cv.itemconfigure(self.name,text=self.playing.get())
            # print(str(self.long.get()))
            self.cv.coords(self.spand, 260, 33, float(self.long.get()), 42)
        elif self.play_if.get() and not mixer.music.get_busy() and not len(self.playlist) == 0:
            self.to_next()
            #print('to_next')
        elif not self.play_if.get() and not mixer.music.get_busy() and not len(self.playlist) == 0:
            self.playing.set(self.playlist[0])
            # print('start')
            # self.t.cancel()
        if len(self.playlist) == 0 and not mixer.music.get_busy():
            self.play_if.set(FALSE)
            self.cv.tag_raise('g2')
            self.cv.tag_lower('g1')
        if self.playing.get() in self.like:
            self.cv.itemconfigure(self.to_like,fill='red')
        else:
            self.cv.itemconfigure(self.to_like,fill='gray')
        t = Timer(0.1, self.func)
        t.setDaemon(TRUE)
        t.start()

    def to_next(self):
        if self.cb['text'] == 'mode 1':
            if self.playing.get() not in self.playlist:
                self.playing.set(self.playlist[0])
            elif self.playlist.index(self.playing.get()) == len(self.playlist) - 1:
                if not mixer.music.get_busy():
                    mixer.music.stop()
                    self.play_if.set(FALSE)  # notplaying
                    print('busy')
                    self.cv.tag_raise('g2')
                    self.cv.tag_lower('g1')
                else:
                    self.playing.set(self.playlist[0])
                    self.play_music(self.playing.get())
            elif self.play_if.get():
                self.playing.set(self.playlist[self.playlist.index(self.playing.get()) + 1])
                self.play_music(self.playing.get())
            else:
                self.play_music(self.playing.get())
               # print('??')
        elif self.cb['text'] == 'mode 2':
            if self.playlist.index(self.playing.get()) == len(self.playlist) - 1:
                self.playing.set(self.playlist[0])
                self.play_music(self.playing.get())
            else:
                self.playing.set(self.playlist[self.playlist.index(self.playing.get()) + 1])
                self.play_music(self.playing.get())
        elif self.cb['text'] == 'mode 3':
            if self.play_if.get() and not mixer.music.get_busy():
                self.play_music(self.playing.get())
            elif self.playlist.index(self.playing.get()) == len(self.playlist):
                self.playing.set(self.playlist[0])
                self.play_music(self.playing.get())
            else:
                self.playing.set(self.playlist[self.playlist.index(self.playing.get()) + 1])
                self.play_music(self.playing.get())
        elif self.cb['text'] == 'mode 4':
            self.playing.set(self.playlist[randint(0, len(self.playlist)) - 1])
            self.play_music(self.playing.get())
          #  print(self.playing.get())
       # print('ss')

    def to_before(self):
        if self.cb['text'] == 'mode 1':
            self.playing.set(self.playlist[self.playlist.index(self.playing.get()) - 1])
            self.play_music(self.playing.get())
        elif self.cb['text'] == 'mode 2':
            self.playing.set(self.playlist[self.playlist.index(self.playing.get()) - 1])
            self.play_music(self.playing.get())
        elif self.cb['text'] == 'mode 3':
            self.playing.set(self.playlist[self.playlist.index(self.playing.get()) - 1])
            self.play_music(self.playing.get())
        elif self.cb['text'] == 'mode 4':
            self.playing.set(self.playlist[randint(0, len(self.playlist)) - 1])
            self.play_music(self.playing.get())
        print('ss')

    def to_play(self):
        if self.cb['text'] == 'mode 4':
            self.playing.set(self.playlist[randint(0, len(self.playlist)) - 1])
            self.play_music(self.playing.get())
        else:
            self.play_music(self.playing.get())
        print('ss')

    def add_pl(self):
        if not self.artistnow.get():
            self.ap['style'] = 'CL.TLabel'
            self.am['style'] = 'BW.TLabel'
            print('no')
            name = simpledialog.askstring('Create a playlist', 'input the name of playlist:',
                                          initialvalue='New playlist')
            print(name)
            if name:
                i = 0
                strr = ''
                while name in self.pl:
                    for xx in range(len(name)):
                        if re.match(r'\d', name[len(name) - 1 - xx]):
                            strr += name[len(name) - 1 - xx]
                            name = name[0:len(name) - 1 - xx]
                    i += 1
                    name = name + str(i)
                self.pb.insert(END, name)
                self.m.add_command(label=name)
                self.pl.append(name)
                self.pbl.append(name)
                print(name)
            self.save()

    def all_music(self):
        self.am['style'] = 'CL.TLabel'
        self.ap['style'] = 'BW.TLabel'
        self.is_all.set(TRUE)
        if self.artistnow.get():
            self.artistnow.set(FALSE)
        self.pb.delete(0, END)
        for x in self.pl:  # should create a txt to save musiclist !!
            self.pb.insert(END, pa.Path(x).stem)
        self.lb.delete(0, END)
        self.playlist=[]
        for x in self.musiclist:  # should create a txt to save musiclist !!
            self.lb.insert(END, pa.Path(x).stem)
            self.playlist.append(x)

    def sff(self):
        self.sf['style'] = 'SMCL.TLabel'
        self.af['style'] = 'SM.TLabel'
        self.ms['style'] = 'SM.TLabel'
        test = sfs(self.master, self.lb, self.sf, self.musiclist, self.save, self.playlist)
    def aff(self):
        filepath=filedialog.askdirectory(title='choose file path',initialdir='F:/')
        stems = []
        # for format in ('.mp3','.flac'):\for x in p.glob('**/*'):
        for x in pa.Path(filepath).glob('**/*'):
            if ti.is_supported(str(x.name)):
                if (os.path.getsize(x)) > 1 * 1024 * 1024 and (
                        os.path.getsize(x)) < 50 * 1024 * 1024:
                    stems.append(x)

        test = mlf(self.master, stems, self.lb, self.musiclist, self.playlist)
    def save(self):
        self.endsave=['mode 3']
        self.endsave.extend(self.playlist)
        #print(self.endsave)
        self.lines = ['musiclist--> \n'] + self.musiclist + ['playlist--> \n'] + self.pbl + ['end--> \n']+self.endsave
        # print('save_test')
        # print(self.lines)
        with open(self.filename, 'w', True, 'UTF-8') as ff:
            for x in self.lines:
                if not '\n' in x.__str__():
                    ff.write(x.__str__() + '\n')
                    #print(x.__str__() + '\n')
                elif x !='\n':
                    ff.write(x.__str__())

    def choose_play(self, event):
        print(u"播放音乐1")
       # track = mixer.music.load(str(self.playlist[self.lb.curselection()[0]]))
        # print(track)
        self.play_music(self.playlist[self.lb.curselection()[0]])
        self.play_if.set(TRUE)

    #  'play in order', 'random play', 'loop play in list', 'loop play single song'
    def play_music(self, file):
        print(file)
        mixer.init()
        try:
            track = mixer.music.load(str(file))
        except:
            self.lb.delete(self.playlist.index((file)))
            self.musiclist.remove(file)
            track = mixer.music.load(str(self.playlist[(self.playlist.index(file)+1)%len(self.playlist)]))
            print(str(self.playlist[(self.playlist.index(file)+1)%len(self.playlist)]))
            self.playlist.remove(file)

        self.playing.set(str(file))
        self.play_if.set(TRUE)
        self.long.set(260.)
        mixer.music.play()
        self.lb.selection_clear(0, END)
        self.lb.selection_set(self.playlist.index(file))
        self.lb.see(self.playlist.index(file))
        test = ti.get(file)
        self.cv.tag_raise('g1')
        self.cv.tag_lower('g2')
        self.cv.delete('g3')
        self.play_name = self.cv.create_text(260, 20, text=pa.Path(file).name, font='simkai', fill='green',
                                             anchor=W, justify=LEFT, tag='g3')
        self.cv.create_text(510, 35, text=str(int(test.duration)) + ' s', font=('simkai', 10, 'bold'), fill='green',
                            anchor=W, justify=LEFT, tag='g3')
        self.cv.create_rectangle(260, 33, 500, 42, fill='blue', width=0, tag='g3')
        self.spand = self.cv.create_rectangle(260, 35, 260, 40, fill='yellow', tag='g3')

        self.cv.tag_raise('g3')

    def change_module(self):
        if self.cb['text'] == 'mode 1':
            self.cb['text'] = 'mode 2'
            self.cv.tag_raise('m2')
            self.cv.tag_lower('m1')
        elif self.cb['text'] == 'mode 2':
            self.cb['text'] = 'mode 3'
            self.cv.tag_raise('m3')
            self.cv.tag_lower('m2')
        elif self.cb['text'] == 'mode 3':
            self.cb['text'] = 'mode 4'
            self.cv.tag_raise('m4')
            self.cv.tag_lower('m3')
        elif self.cb['text'] == 'mode 4':
            self.cb['text'] = 'mode 1'
            self.cv.tag_raise('m1')
            self.cv.tag_lower('m4')

    def click(self, event):
        if event.x > 80 and event.x < 115 and mixer.music.get_busy() and not len(self.playlist) == 0:
            if self.pause.get():
                print('??')
                self.pause.set(FALSE)
                mixer.music.unpause()
                self.play_if.set(TRUE)
                self.cv.tag_raise('g1')
                self.cv.tag_lower('g2')
            else:
                mixer.music.pause()
                self.play_if.set(FALSE)
                print('busy')
                self.cv.tag_raise('g2')
                self.cv.tag_lower('g1')
                self.pause.set(TRUE)
        if event.x > 80 and event.x < 115 and not mixer.music.get_busy() and not len(self.playlist) == 0:
            print('stt')
            self.to_play()
        elif event.x > 140 and event.x < 175 and not len(self.playlist) == 0:
            self.to_next()
        elif event.x > 20 and event.x < 55 and not len(self.playlist) == 0:
            self.to_before()
        elif event.x > 260 and event.x < 500 and event.y > 30 and self.play_if.get():
            self.control_play.set(TRUE)
        elif event.x > 220 and event.x < 250:
            self.change_module()
        elif event.x>500 and event.x<600 and event.y<11:
            mixer.music.set_volume((event.x-500)/100)
            self.cv.coords(self.vol,500,0,event.x,10)
        elif event.x>190 and event.x<210 and event.y>15 and event.y<30:

            if self.playing.get() not in self.like:
                self.like.append(self.playing.get())
                self.pbl.insert(1,self.playing.get())
                self.cv.itemconfigure(self.to_like, fill='red')
            else:
                self.like.remove(self.playing.get())
                self.pbl.remove(self.playing.get())
                self.cv.itemconfigure(self.to_like, fill='gray')
    def release(self, event):
        print('release')
        if event.x > 260 and event.x < 500 and event.y > 30 and self.control_play.get() and mixer.music.get_busy():
            test = ti.get(self.playing.get())
            self.long.set(event.x)
            mixer.music.rewind()
            mixer.music.play(start=(event.x - 260.) / 240. * float(test.duration))
            print('??')
            self.pause.set(FALSE)
            # mixer.music.unpause()
            self.play_if.set(TRUE)
            self.cv.tag_raise('g1')
            self.cv.tag_lower('g2')
        elif event.x>500 and event.x<600 and event.y<11:
            mixer.music.set_volume((event.x-500)/100)
            self.cv.coords(self.vol,500,0,event.x,10)
            print(mixer.music.get_volume())
        # pygame.mixer.music.pause() #暂停
        # pygame.mixer.music.unpause()#取消暂停

    def del_list(self):
        if not len(self.pb.curselection()) == 0 and (not self.pb.curselection()[0] == 0) and not self.artistnow.get():
            #print(str(self.pb.curselection()))
            self.m.delete(self.pb.curselection()[0]), (self.pb.curselection()[0])

            print(self.pl)
            for xxx in self.pb.curselection():
                i = 0
                for xx in self.pbl[self.pbl.index(self.pl[xxx]):]:
                    if ti.is_supported(xx) or i == 0:
                        self.pbl.remove(xx)
                        i= 1
                    else:
                        break
                self.pl.pop(xxx)
                self.pb.delete(xxx)
            self.save()
        elif not len(self.pb.curselection()) == 0 and self.sort['text']=='sort by filepath':
            ss=self.pb.curselection()
            sel,pl,plist=[],[],[]
            for x in ss:
                print(len(self.filepathlist))
                sel.append(self.filepathlist[x])
            self.pb.delete(0,END)
            self.lb.delete(0,END)
            for xxx in sel:
                self.filepathlist.remove(xxx)
            print(self.filepathlist)
            for xx in self.musiclist:
                    if pa.Path(xx).parent in self.filepathlist:
                        pl.append(xx)
                        print(xx)
                        if xx in self.playlist:
                            self.lb.insert(END,pa.Path(xx).stem)
                            plist.append(xx)
            self.musiclist=pl.copy()
            self.playlist=plist.copy()
           # print(self.musiclist)
            for x in self.filepathlist:
                self.pb.insert(END,x)
        for x in self.pbl[1:]:
            if pa.Path(x).is_file():
                self.like.append(x)
            else:
                break
        self.save()
    def rename(self):
        if not len(self.pb.curselection()) == 0 and (not self.pb.curselection()[0] == 0) and not self.artistnow.get():
            num = int(str(self.pb.curselection())[1:-2])
            test = simpledialog.askstring('Rename the playlist', 'input a name:',
                                          initialvalue=str(self.pl[int(str(self.pb.curselection())[1:-2])]))
            if test:
                print(num)
                self.pb.delete(num)
                self.pb.insert(num, test)
                self.m.delete(num, num)
                self.m.insert_command(num, label=test, command=self.testt(self.add_topl, x=test))
                self.pbl[self.pbl.index(self.pl[num])] = test
                self.pl[num] = test

    def artist(self):
        if self.artistnow.get() and self.sort['text']=='sort by filepath':
            self.pb['selectmode']='browse'
            self.ctrl.set(FALSE)
            print('sss')
            self.press_3.set(FALSE)
            self.sort['text']='sort by artist'
            self.artistnow.set(FALSE)
            self.pb.delete(0, END)
            for x in self.pl:  # should create a txt to save musiclist !!
                self.pb.insert(END, pa.Path(x).stem)
        elif self.artistnow.get() and self.sort['text']=='sort by artist':
            self.sort['text']='sort by filepath'
            self.pb.delete(0, END)
            self.filepathlist=[]
            for x in self.musiclist:
                if pa.Path(x).parent not in self.filepathlist:
                    self.filepathlist.append(pa.Path(x).parent)
            self.all_path=[pa.Path(x).parent for x in self.musiclist]
            print(self.all_path)
            print(self.filepathlist)
            ind=[self.all_path.count(x) for x in self.filepathlist]
            inds=ind.copy()
            self.pathcopy=self.filepathlist.copy()
            inds.sort(reverse=TRUE)
            nosame=[]
            #print(ind)
            for x in inds:
                if x not in nosame:
                    nosame.append(x)
            i=0
            for x in nosame:
                ax=ind.index(x)
                for a in range(inds.count(x)):
                    self.filepathlist[i]=self.pathcopy[ind.index(x,ax)]
                    if not a ==inds.count(x)-1:
                        ax=ind.index(x,ax+1)
                    i+=1
            for x in self.filepathlist:
                self.pb.insert(END, str(x)+ '  (' + str(inds[self.filepathlist.index(x)]) + ')')

        else :
            self.artistnow.set(TRUE)
            self.pb.delete(0, END)
            self.artistlist, allartistlist = [], []
            for x in self.musiclist:
                #print(x)
                try:
                    tag = ti.get(x)
                    allartistlist.append(tag.artist)
                    if tag.artist not in self.artistlist:
                        self.artistlist.append(tag.artist)
                except:
                    if x in self.playlist:
                        self.lb.delete(self.playlist.index((x)))
                        self.playlist.remove(x)
                    self.musiclist.remove(x)
                    #print(x)
                    self.save()
            ind = [allartistlist.count(xx) for xx in self.artistlist]
            inds = ind.copy()  # 这里有点绕，利用指标辅助帮助艺术家根据歌曲数目排序，不简单
            inds.sort(reverse=True)
            artistlistsort = self.artistlist.copy()
            for x in artistlistsort:
                self.artistlist[artistlistsort.index(x)] = '0'
            for art in artistlistsort:
                i = inds.index(ind[artistlistsort.index(art)])
                while True:
                    if self.artistlist[i] == '0':
                        self.artistlist[i] = art
                        break
                    else:
                        i += 1
            for x in self.artistlist:  # should create a txt to save musiclist !!
                # print(x)
                if not x:
                    self.pb.insert(END, 'Unkonw' + ' (' + str(inds[self.artistlist.index(x)]) + ') ')
                else:
                    self.pb.insert(END, x + '  (' + str(inds[self.artistlist.index(x)]) + ')')

    def artist_play(self, event):  # 事件响应一定要记得加event!!!!!
        if self.artistnow.get() and not str(self.pb.curselection()) == '()' and self.sort['text']=='sort by artist':
            # print(str(self.pb.curselection()))
            x = self.pb.curselection()[0]
            self.lb.delete(0, END)
            self.playlist.clear()
            # print(self.artistlist[x])
            for xx in self.musiclist:
                try:
                    tag = ti.get(xx)
                    if tag.artist:
                        # print(tag.artist)
                        if tag.artist == self.artistlist[x]:
                            self.lb.insert(END, pa.Path(xx).stem)
                            self.playlist.append(xx)
                    elif not self.artistlist[x]:
                        self.lb.insert(END, pa.Path(xx).stem)
                        self.playlist.append(xx)
                except:
                    self.lb.delete(self.playlist.index((xx)))
                    self.musiclist.remove(xx)
                    self.playlist.remove(xx)
                    #print(xx)
                    self.save()
        elif self.artistnow.get() and not str(self.pb.curselection()) == '()' and self.sort['text']=='sort by filepath':
            x = self.pb.curselection()[0]
            self.is_all.set(TRUE)
            self.lb.delete(0, END)
            self.playlist.clear()
            for xx in self.musiclist:
                if pa.Path(xx).parent==self.filepathlist[x]:
                    self.lb.insert(END, pa.Path(xx).stem)
                    self.playlist.append(xx)


        elif not str(self.pb.curselection()) == '()':
            x = self.pb.curselection()[0]
            self.lb.delete(0, END)
            self.playlist.clear()
            self.playlist = []
            self.is_all.set(FALSE)
            self.playinglist.set(self.pl[x])
            for xx in self.pbl[self.pbl.index(self.pl[x]) + 1:]:
                if ti.is_supported(pa.Path(xx).name):
                    self.lb.insert(END, pa.Path(xx).stem)
                    self.playlist.append(xx)
                else:
                    break

    def pop(self, event):
        self.popmenu.post(event.x_root, event.y_root)

    def pbpop(self, event):
        self.pbmenu.post(event.x_root, event.y_root)
        self.press_3.set(TRUE)
    def pbrel(self,event):
        self.press_3.set(FALSE)
        print('xxxx')
    def play_it(self):
        print(self.lb.curselection())
        if str(self.lb.curselection()) == '()':
            print('ddd')
            self.to_play()
        else:
            self.play_music(self.playlist[self.lb.curselection()[0]])
            self.play_if.set(TRUE)

    def pause(self):
        if self.pause.get():
            print('??')
            self.pause.set(FALSE)
            mixer.music.unpause()
            self.play_if.set(TRUE)
            self.cv.tag_raise('g1')
            self.cv.tag_lower('g2')
        else:
            mixer.music.pause()
            self.play_if.set(FALSE)
            print('busy')
            self.cv.tag_raise('g2')
            self.cv.tag_lower('g1')
            self.pause.set(TRUE)

    def add_topl(self, x):
        # print(str(self.lb.curselection())[1:-2])
        # print(self.lb.curselection()[0])
        #print(self.playlist)
        if not str(self.lb.curselection()) == '()':
            for ax in self.lb.curselection():
                # print(self.pbl.index(x))
                if x == self.pl[-1] and self.playlist[ax] not in self.pbl[int(self.pbl.index(x)):]:
                    self.pbl.insert(int(self.pbl.index(x)) + 1, self.playlist[ax])
                    #print(self.pbl)
                    self.save()
                elif x == self.pl[-1]:
                    pass
                elif self.playlist[ax] not in self.pbl[int(self.pbl.index(x)):int(self.pbl.index(self.pl[self.pl.index(x) + 1]))]:
                    self.pbl.insert(int(self.pbl.index(x)) + 1, self.playlist[ax])
                    #print(self.pbl)
                    self.save()
        for x in self.pbl[1:]:
            if pa.Path(x).is_absolute():
                self.like.append(x)
            else:
                break



    def testt(self, fun, **kwds):
        # print('xx')
        return lambda fun=fun, kwds=kwds: fun(**kwds)

    def leave_lefttop(self, event):
        self.am['style'] = 'BW.TLabel'
        self.ap['style'] = 'BW.TLabel'

    def del_music(self):
        print('de l')
        if not len(self.lb.curselection()) == 0 and self.is_all.get():
            self.musiclist.remove(self.playlist[self.lb.curselection()[0]])
            self.playlist.pop(self.lb.curselection()[0])
            self.lb.delete(self.lb.curselection()[0])
            print('del')
        elif not len(self.lb.curselection()) == 0:
            print(self.playinglist.get())
            for ax in self.lb.curselection():
                if ax<len(self.playlist):
                    print(len(self.playlist))
                    print(ax)
                    m = self.playlist.pop(ax)
                    print(m)
                    self.lb.delete(ax)
                    x = self.pbl.index(self.playinglist.get())
                    print(x)
                    if x == len(self.pl) - 1:
                        if m in self.pbl[x:]:
                            print(self.pbl.pop(self.pbl.index(m, x)))
                    else:
                        y = self.pbl.index(self.pl[self.pl.index(self.playinglist.get()) + 1])
                        print(self.pbl.pop(self.pbl.index(m, x, y)))



    def lb_focus(self, event):
        if self.ms['text']=='Browse' or self.ms['text']=='Single':
            self.lb.selection_clear(0,END)
            self.lb.selection_set(self.lb.nearest(event.y))
    def pb_focus(self, event):
        if not self.press_3.get():
            if not self.ctrl.get():
                self.pb.selection_clear(0, END)
            self.pb.selection_set(self.pb.nearest(event.y))
            #print(self.pb.curselection())


    def modechange(self):
        if self.ms['text']=='Browse':
            self.ms['text']='Single'
            self.lb['selectmode']='single'
        elif self.ms['text']=='Single':
            self.ms['text']='Multiple'
            self.lb['selectmode'] = 'multiple'
        elif self.ms['text']=='Multiple':
            self.ms['text']='Extended'
            self.lb['selectmode'] = 'extended'
        elif self.ms['text']=='Extended':
            self.ms['text']='Browse'
            self.lb['selectmode'] = 'browse'
    def ctrlpb(self,event):
        if self.ctrl.get() and self.sort['text']=='sort by filepath':
            self.ctrl.set(FALSE)
        elif self.sort['text']=='sort by filepath' :
            self.ctrl.set(TRUE)
            #print('ttt')
        print(self.ctrl.get())
root = Tk()
root.title('Music')
test = App(root)
if not root.mainloop():
    mixer.music.stop()
    test.save()
    # root.quit()

