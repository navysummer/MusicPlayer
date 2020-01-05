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

class MUsicPlayer(object):
    """docstring for MUsicPlayer"""
    def __init__(self):
        super(MUsicPlayer, self).__init__()
        self.MainWindow()

    def MainWindow(self):
        self.root = Tk()
        self.playListFrame = Frame(self.root, height=200, width=300)
        self.playFrame = Frame(self.root, height=200, width=300)
        self.playListFrame.pack(side=LEFT,fill=BOTH)
        self.playFrame.pack(side=RIGHT,fill=BOTH)
        self.playlistTitleLabel = Label(self.root,text='播放列表')
        self.playList = Listbox(self.playListFrame)
        self.playList.pack()
        self.playList.bind('<Button-1>', self.play)
        self.root.mainloop()

    def play(self):
        pass
    


def main():
    MUsicPlayer()

if __name__ == '__main__':
    main()
        