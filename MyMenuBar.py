import tkinter as tk
from tkinter import *       
from tkinter import ttk


class myMenuBar():

    def __init__(self, master = None):
        self.master = master

    def addNewItem(self,globalData):
        myMenu = Menu(self.master)
        self.master.config(menu = myMenu)

        settings = Menu(myMenu)
        settings.add_command(label = 'Nastaveni J-Link ID', command = lambda:self.setJlinkId(globalData))
        settings.add_command(label = 'Kontrola pristroju', command = lambda:globalData.testTools())
        myMenu.add_cascade(label = 'Nastaveni', menu = settings)
        
    def setJlinkId(self,globalData):
        self.top = Toplevel()
        self.top.title('Setting Serial number of J link')
        self.center_window(self.top,500,200)
        
        # popisek
        Label(self.top, text="Serial Number of J-Link: ",fg="Black", font=("Verdana", 10)).place(x = 10, y = 20)  
        # okno pro cislo
        self.SN = tk.StringVar()
        numberSN = ttk.Entry(self.top, width = 10, textvariable = self.SN)
        numberSN.grid(column = 0, row = 1)
        numberSN.bind("<KeyRelease>",self.callbackJlinkSnChange)
        numberSN.place(x = 300, y = 20)
        numberSN.insert(END, str(globalData.J_Link_SN))

        self.btnOk = Button(self.top,text = 'Save', command = lambda:self.saveJlinkId(globalData))
        self.btnOk.place(x=100, y =50)

    def saveJlinkId(self,globalData):
        temp = self.SN.get()
        if temp.isnumeric() == True:
            globalData.J_Link_SN = int(temp)
            self.top.destroy()
        #else:

    def callbackJlinkSnChange(self, globalData):
        temp = self.SN.get()
        if temp.isnumeric() == True :
            self.btnOk["state"] = "normal"
        else: 
            self.btnOk["state"] = "disable"

    def center_window(self,window,width=300, height=200):
        # get screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # calculate position x and y coordinates
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        window.geometry('%dx%d+%d+%d' % (width, height, x, y))