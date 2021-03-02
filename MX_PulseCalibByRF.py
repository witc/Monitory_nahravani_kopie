
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import tkinter as tk
from tkinter import *       
from tkinter import ttk
from tkinter import messagebox
import threading 
import time
from RthScopeClass import RthScopeClass
import serial
from serial.tools import list_ports
from tabulate import tabulate
import xlwt
from xlwt import Workbook
from xlrd import open_workbook
from xlutils.copy import copy
from datetime import date
from datetime import datetime
import MyGuiConsole as prt
import winsound
from ESP32ZatezClass import ESP32Zatez
import PulseCalibProcedure as pclb
from USB_RF_Link import USBSerialLink
import array 
from struct import unpack
import binascii
from easysettings import EasySettings

frequency = 2500  # Set Frequency To 2500 Hertz
duration = 100  # Set Duration To 1000 ms == 1 second

MAX_TIME_WAIT_FOR_MX = 120

class GlobDataStruct:
    pass    

globalData=GlobDataStruct()
globalData.MAC_HEADER = 0b10100000
globalData.DEV_EUI = 0xffffffffffffffff
globalData.USB_STATIC_MAC	= 0xAAAAAAAABBBBBBBB
globalData.ZERO_PADING = 0x00000000000000
CMD = 0x5
COEF_A = 0x1122
COEF_B = 0x2211
RFU = 0x99

glScopeConnected = False
glAnalyzerConnected = False
glStopLookingForMX = False
glUartConnected = False

# Create label widget
root= Tk()
root.title("Kalibrace merni pulzu")
root.geometry("960x840")

#------create Plot object on GUI----------
fig = plt.figure()
ax = fig.add_subplot(111)

# plot
canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.get_tk_widget().place(x = 20,y=20, width = 920,height = 400)
canvas.draw()

ax.set_title('Impulsy')
ax.set_xlabel('ADC [mV]')
ax.set_ylabel('Scope [V]')
ax.grid()
ax.set_xlim(0,3000)
ax.set_ylim(0,12000)
lines = ax.plot([],[])[0]
line = ax.plot()

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()

#widgets
# Nastaveni konsole
console = Text(root,height=5, width=93)
console.place(x=10,y=680)
console.tag_config('normal', background="white", foreground="black")
console.tag_config('warning', background="yellow", foreground="black")
console.tag_config('error', background="yellow", foreground="red")
console.tag_config('ok', background="white", foreground="green")

# ProgressBar kalibrace
Label(root, text="Kalibrace impulsu: ",fg="Black", font=("Verdana", 12)).place(x = 300, y = 490)  
rLabel=Label(root, text='R: --',fg='Black', font=("Verdana", 14))#.place(x = 650, y = 490)  
rLabel.place(x = 650, y = 490) 
pulseProgress = ttk.Progressbar(root,orient = HORIZONTAL, length = 100, mode = 'determinate')

# fill globalData
globalData.root = root
globalData.rLabel=rLabel
globalData.console=console
globalData.rfFreq = 869525000
globalData.RfPowerAttempts = 0
globalData.RfCanMeas = False
globalData.monitorVers = "Fencee - Cesko"
PulseThreadRun = False
RfThreadRun = False
ZatezThreadRun = False

USE_SCOPE = True
USE_ZATEZ = True
USE_USB_RF_LINK = True

mxCalibConfig = EasySettings('MxCalibraceConf.conf')
IpScope = mxCalibConfig.get('IpScope') 
IpZatez = mxCalibConfig.get('IpZatez')

if IpScope == '':
  mxCalibConfig.set("IpScope","192.168.1.204")
  mxCalibConfig.save()
  IpScope = mxCalibConfig.get('IpScope') 

if IpZatez == '':
  mxCalibConfig.set("IpZatez","192.168.1.22")
  mxCalibConfig.save()
  IpZatez = mxCalibConfig.get('IpZatez')   


#######################################################################################
#                       F U N K C E                                                   #          
#######################################################################################
def keyboardForExit():
  value = input("Enter - ukonci aplikaci ")
  exit()

def clickCloseApp():
  if messagebox.askokcancel("Quit", "Opravdu zavrit aplikaci?"):
      #root.destroy()
      os._exit
      exit()

def clickStopPulseCalib():
  global PulseThreadRun
  global RfThreadRun
  PulseThreadRun = False

  b1["text"] = "Start kalibrace"
  b1["state"] = "normal"

def getRandNum():
  np.random.normal()

def clickStartPulseCalib():
  global glStopLookingForMX
  glStopLookingForMX = False

  b1["text"] = "S T O P"
  prt.myPrint(globalData,"Hledam monitor...")
  globalData.USBLink.URSBRFLinkFlushBuff()
  threading.Timer(0.01,runSerialLink).start()
  b1.configure(command=clickStopLookingForMX)

def clickStopLookingForMX():
  global glStopLookingForMX
  global PulseThreadRun
  glStopLookingForMX = True
  b1["text"] = "Start kalibrace"
  prt.myPrint(globalData,"Konec kalibrace...")
  b1.configure(command=clickStartPulseCalib)
  PulseThreadRun = False #OK?!
  pclb.stopCalib() #OK?!
  globalData.USBLink.URSBRFLinkFlushBuff()
 

def runSerialLink():
  global PulseThreadRun
  global glSstopLookingForMX
  runSerialLink.counterTimeout+=1

  cmdLookFor = 0x4
  globalData.actualRndSesKey = np.random.bytes(4)
  serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'little'), globalData.DEV_EUI.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
    globalData.ZERO_PADING.to_bytes(7,byteorder = 'little'), globalData.actualRndSesKey, cmdLookFor.to_bytes(1,byteorder='little'),COEF_A.to_bytes(2,byteorder='little'),
    COEF_B.to_bytes(2,byteorder='little'),RFU.to_bytes(1,byteorder='little')]

  print(binascii.hexlify(globalData.actualRndSesKey))
  globalData.USBLink.txUSBRFLink(serialPacket)
  MX_EUI, RndSessionKey, Cmd,PulsemV = globalData.USBLink.rxUSBRFLink(0.4)

  if RndSessionKey == int.from_bytes(globalData.actualRndSesKey, byteorder='little') and Cmd == 1:
    prt.myPrint(globalData,"Monitor nalezen...",tag = 'ok')
    prt.myPrint(globalData,"Session Key: {}".format(RndSessionKey))
    
    if globalData.EspZatez.setLoadTrig(6000,globalData) == "Trig timeout":
      globalData.EspZatez.setLoadNoTrig(6000,globalData) 
      
    # ulozeni hodnot
    globalData.actualMxEui = MX_EUI
    globalData.actualRndSesKey = RndSessionKey
    PulseThreadRun = True
    runSerialLink.counterTimeout=0
  
  elif (glStopLookingForMX == False) and (runSerialLink.counterTimeout < MAX_TIME_WAIT_FOR_MX):
    # hledej monitor znovu
    threading.Timer(0.01,runSerialLink).start()

  else:
    #serialLinkTimer.cancel()
    if runSerialLink.counterTimeout >= MAX_TIME_WAIT_FOR_MX:
      prt.myPrint(globalData,'Zadny monitor nepripojen - restartuj mereni', tag = 'warning' )
      b1.configure(command=clickStartPulseCalib)
      b1["text"] = "Start kalibrace"
      prt.myPrint(globalData,"Konec kalibrace...")
      
    runSerialLink.counterTimeout=0

def runPulseCalib():
  global PulseThreadRun

  while True:
    time.sleep(0.1)
    while PulseThreadRun == True:
        prt.myPrint(globalData,'Zacinam kalibrovat - Cekam na impuls',tag='ok')
        pclb.initAndStartCalibPulse(globalData)

        ax.clear()
        ax.set_title('Impulsy')
        ax.set_xlabel('ADC [mV]')
        ax.set_ylabel('Scope [V]')    
        ax.grid()

        globalData.rLabel.config(fg="black",text='R: --')
        pulseProgress['value'] = 0
        root.update_idletasks() 

        while PulseThreadRun == True: 
          if pclb.canIMeas() == True: 
            temp =pclb.calibPulseProc(pulseProgress,globalData)

            if temp=="calib_ok":
              prt.myPrint(globalData,'Kalibrace uspesna',tag='ok')
              PulseThreadRun = False 
              pclb.stopCalib() 
              clickStopLookingForMX()
              break

            elif temp=="chyba":
                prt.myPrint(globalData,'Kalibace se nezdarila!',tag='error')
                PulseThreadRun = False 
                pclb.stopCalib() 
                clickStopLookingForMX()
                break                

def testTools():
  scopeConnected = False
  zatezConnected = False
  UsbLinkConnected = False

  if USE_ZATEZ == True:
    EspLoad = ESP32Zatez()
    globalData.EspZatez = EspLoad
    retZatez = EspLoad.connect(IpZatez)
    if retZatez == False:
      prt.myPrint(globalData,'ESP load not found ',tag='error') 
      prt.myPrint(globalData,'with IP Adress :' + IpZatez,tag = 'error' )
      zatezConnected = False
    else:
      prt.myPrint(globalData,'ESP load found ',tag='ok') 
      prt.myPrint(globalData,'with IP Adress :' + IpZatez,tag = 'ok' )
      zatezConnected = True

    del EspLoad

  if USE_SCOPE == True:
    scope = RthScopeClass()
    globalData.scope = scope
    retScope = scope.connectScope(IpScope)

    if retScope == False:
      prt.myPrint(globalData,'RTH scope not found!',tag='error')
      prt.myPrint(globalData,'with IP Adress:' + IpScope,tag = 'ok' )
      scopeConnected = False

    else:
      scopeConnected = True
      prt.myPrint(globalData,'RTH scope OK !',tag='ok')
      prt.myPrint(globalData,'with IP Adress:' + IpScope,tag = 'ok' )
      print('RTH scope OK !')

    del scope

  if USE_USB_RF_LINK == True:
    try:
      USBLink = USBSerialLink()
      if USBLink.openUSBRfLink(2) != 'False':
        globalData.USBLink = USBLink
        UsbLinkConnected = True
        prt.myPrint(globalData,'UART USB Link OK!',tag='ok')
      else :
        prt.myPrint(globalData,'UART USB Link was not found!',tag='warning')
        UsbLinkConnected = False
    
    except :
      prt.myPrint(globalData,'UART USB Link connected',tag='ok')
      UsbLinkConnected = True
      pass
    
    del USBLink

  if UsbLinkConnected == True and scopeConnected == True and zatezConnected == True:
      b1['state'] = "normal"

  else:
      b1['state'] = "disable"

   

root.protocol("WM_DELETE_WINDOW", clickCloseApp)

pulseProgress.pack(pady=5)
pulseProgress.place(x = 500, y = 495)
prt.myPrint(globalData,"App is running...",tag="ok")

# Init classes
glPulseCanCalib = False

def animate(args):
    
    if pclb.isAnyToClearandPlot() == True:
        x,y=pclb.readDataToPlot_erase()
        ax.clear()
        ax.set_title('Impulsy')
        ax.set_xlabel('ADC [mV]')
        ax.set_ylabel('Scope [V]')    
        ax.scatter(x,y)
        #lines.set_ydata(y)
        #lines.set_xdata(x)
        ax.grid()
        #return lines

    if pclb.isAnyToPlot() == True:
        x,y = pclb.readDataToPlot_Noerase()
        #line.set_ydata(y)
        #line.set_xdata(x)
        ax.plot(x,y,color='cyan')

b1 = Button(root, text='Start kalibrace',padx=30, pady=20, height = 1, width = 8, command=lambda:clickStartPulseCalib())
b1.place(x = 420, y = 520)
b1["state"] = "disable"

pulseCalibThread = threading.Thread(target=runPulseCalib, daemon = False)
pulseCalibThread.start()

#####################################################
# T I M E R S
#####################################################
serialLinkTimer = threading.Timer(0.01,runSerialLink)

runSerialLink.counterTimeout = 0
#plotting = Stripchart(root)
ani = animation.FuncAnimation(fig, animate,interval = 100, blit = False)
root.after(100,testTools())
#b1["state"] = "normal"
root.mainloop()

