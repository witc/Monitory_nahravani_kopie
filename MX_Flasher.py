import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import pandas as pd
import os
import ctypes
import sys
import time
import platform
import struct
from PySpektrakClass import SpektrakClass
import tkinter as tk
from tkinter import *       
from tkinter import ttk
from tkinter import messagebox
from RthScopeClass import RthScopeClass
from HMC8012Class import HMC8012Class
import threading 
import RfCalibProcedure as rfclb
import MyGuiConsole as prt
from PyJlinkClass   import Mcu
import bincopy
from MyMenuBar import myMenuBar
from easysettings import EasySettings
from USB_RF_Link import USBSerialLink
from serial.tools import list_ports
import serial
from HMC8012Class import HMC8012Class
import sqlite3 as sl
import requests
import git 
import glob
import shutil
import signal


USE_HMC8012 = True
USE_FPL1003 = True
USE_USB_RF_LINK = True

mxFlasherConfig = EasySettings('MxFlasherConfig.conf')
SNJlink = mxFlasherConfig.get('snJlink') 
IpAnalyzer = mxFlasherConfig.get('IpAnalyzer') 
IpAmpMeter = mxFlasherConfig.get('IpAmpMeter')
minTxPower = mxFlasherConfig.get('minTxPower[dBm]')

if SNJlink == '':
  mxFlasherConfig.set("snJlink",260102277)
  mxFlasherConfig.save()
  SNJlink = mxFlasherConfig.get('snJlink') 

if IpAnalyzer == '':
  mxFlasherConfig.set("IpAnalyzer","192.168.0.100")
  mxFlasherConfig.save()
  IpAnalyzer = mxFlasherConfig.get('IpAnalyzer') 

if IpAmpMeter == '':
  mxFlasherConfig.set("IpAmpMeter","192.168.0.102") 
  mxFlasherConfig.save()
  IpAmpMeter = mxFlasherConfig.get('IpAmpMeter') 

if minTxPower == '':
  mxFlasherConfig.set("minTxPower[dBm]",18.2) 
  mxFlasherConfig.save()
  minTxPower = mxFlasherConfig.get('minTxPower[dBm]') 


print("Seriove cislo JLink: ", SNJlink)
print("Ip adresa pro spektralni analyzator FPL1003: ", IpAnalyzer)
print("Ip adresa pro multimetr HMC8012: ", IpAmpMeter)

class GlobDataStruct:
    pass    

globalData=GlobDataStruct()
glToolsConnected = False
glSerialLinkConnected = False
glAnalyzerConnected = True
globalData.minTxPower = minTxPower
monitorVersion = [
  "!!Vyber verzi!!",
  "Fencee - Cesko",
  "Voss - Nemecko",
]

# Create label widget
root= Tk()
root.title("Monitor MX - nahravani + test RF TX")
root.geometry("800x500")
#menu = myMenuBar(root)

#------create Plot object on GUI----------
#widgets
console = Text(root,height=8, width=75)
console.place(x=23,y=320)
console.tag_config('normal', background="white", foreground="black")

console.tag_config('warning', background="yellow", foreground="black")
console.tag_config('error', background="yellow", foreground="red")
console.tag_config('ok', background="white", foreground="green")

emptyText = ' -- '
ltext1=tk.StringVar()
ltext2=tk.StringVar()
ltext3=tk.StringVar()
ltext4=tk.StringVar()
ltext6=tk.StringVar()
ltext8=tk.StringVar()
ltext9=tk.StringVar()

ltext1.set(emptyText)
ltext2.set(emptyText)
ltext3.set(emptyText)
ltext4.set(emptyText)
ltext6.set(emptyText)
ltext8.set(emptyText)
ltext9.set(emptyText)

#Label(root, text="NAHRAVANI a test RF: ",fg="Black", font=("Verdana", 12)).place(x = 350, y = 60)  
Label(root, text="1: Program ",fg="Black", font=("Verdana", 12)).place(x =520, y = 60)  
lret1 =Label(root, textvariable=ltext1,fg="Black", font=("Verdana", 12))
lret1.place(x = 700, y = 60)  

Label(root, text="2: MAC adresa",fg="Black", font=("Verdana", 12)).place(x = 520, y = 100)  
lret2 = Label(root, textvariable=ltext2,fg="Black", font=("Verdana", 12))
lret2.place(x = 700, y = 100)

Label(root, text="3: Test TX",fg="Black", font=("Verdana", 12)).place(x = 520, y = 140)  
lret3 = Label(root, textvariable=ltext3,fg="Black", font=("Verdana", 12))
lret3.place(x = 700, y = 140)

Label(root, text="4: Test Rx",fg="Black", font=("Verdana", 12)).place(x = 520, y = 180)  
lret4 =Label(root, textvariable=ltext4,fg="Black", font=("Verdana", 12))
lret4.place(x = 700, y = 180)

Label(root, text="5: Spotreba",fg="Black", font=("Verdana", 12)).place(x = 520, y = 220)  
lret6 =Label(root, textvariable=ltext6,fg="Black", font=("Verdana", 12))
lret6.place(x = 700, y = 220)

Label(root, text="6: Test R",fg="Black", font=("Verdana", 12)).place(x = 520, y = 260)  
lret9 =Label(root, textvariable=ltext9,fg="Black", font=("Verdana", 12))
lret9.place(x = 700, y = 260)


Label(root, text="Verze vyrobku: ",fg="Black", font=("Verdana", 12)).place(x = 25, y = 38)  

Label(root, text="Vysledek: ",fg="Black", font=("Verdana", 18)).place(x = 100, y = 220)  
lret8 =Label(root, textvariable=ltext8,fg="Black", font=("Verdana", 18))
lret8.place(x = 300, y = 220)

#lret7 =Label(root, textvariable=ltext6,fg="Black", font=("Verdana", 12))

#enter PCB code
#Label(root, text="Cislo PCB: ",fg="Black", font=("Verdana", 12)).place(x = 50, y = 60)  
#lret5 =Label(root, textvariable=ltext4,fg="Black", font=("Verdana", 12))
#lret5.place(x = 250, y = 130)
#entry1 = tk.Entry(root, text="").place(x=50, y = 90)


#e1.
#e1.grid(row=0, column=1)

# fill globalData
globalData.root = root
globalData.console=console
globalData.RfPowerAttempts = 0
globalData.monitorVers = "!!Vyber verzi!!"
globalData.J_Link_SN = SNJlink
RfThreadRun = False
globalData.MAC_HEADER = 0b10100000
globalData.DEV_EUI = 0xffffffffffffffff
globalData.USB_STATIC_MAC	= 0xAAAAAAAABBBBBBBB
globalData.ZERO_PADING = 0x00000000000000
CMD_RfSwitch = 0x6
RFU = 0x99
RFSwitchMX_Analyzer = 2
RFSwitchMX_Generator = 1
ButtonThreadRun = False

def keyboardForExit():
  value = input("Enter - ukonci aplikaci ")
  exit()

#Clone Repo - priprava na stahovani aktualniho FW z repa do vyroby
# directory = "C:\\VyrobaMonitory\\Binarky\\mx10_assemblyline" 
# try:
#    #shutil.rmtree(directory)
#    os.system("rmdir /s /q "+directory )
# except OSError as e:
#     print("Error:  %s" % (e.strerror))

# git.Git('C:\\VyrobaMonitory\\Binarky').clone("http://192.168.1.202/root/mx10_assemblyline.git")

try:
  with open('C:/VyrobaMonitory/Binarky/mx10_assemblyline/FENCEE_Monitor.map') as f:     
    file=f.read()
    if 'GlFactoryTest' in file:      
        keyword = "GlFactoryTest"
        before_keyword, keyword, after_keyword = file.partition(keyword)
        adr=after_keyword.replace("\n","")
        startAdr=adr.find('0x')
        Finaladr=adr[startAdr:startAdr+10]
        print("Hledana adresa je: {0}".format(Finaladr))       

    else:
      prt.myPrint(globalData,"Chyba v nacitani MAP File", tag = 'error' )
      keyboardForExit()
except:
   prt.myPrint(globalData,"Chyba v nacitani MAP File", tag = 'error' )
   keyboardForExit() 

addrFtStruct=int(Finaladr,0)
STM32=Mcu(addrFtStruct)
globalData.STM32 = STM32
globalData.STM32.setMcu(globalData)
      
def clickCloseApp():
  if messagebox.askokcancel("Quit", "Opravdu zavrit aplikaci?"):
    mxFlasherConfig.set("snJlink",globalData.J_Link_SN)
    mxFlasherConfig.save()

    #os.kill(os.getpid(),signal.SIGKILL)
    os._exit(1)
    #root.destroy()
    #os._exit
    #sys.exit()

def comboclick(event):
   global globalData
   globalData.monitorVers =  monitorCombo.get()
   threading.Timer(0.5,lookForPCB).cancel()

def setRfSwitch(switch):
    serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'big'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
      globalData.ZERO_PADING.to_bytes(7,byteorder = 'big'), bytearray(4), CMD_RfSwitch.to_bytes(1,byteorder='big'),switch.to_bytes(2,byteorder='big'),
      switch.to_bytes(2,byteorder='big'),RFU.to_bytes(1,byteorder='big')]
    
    globalData.USBLink.txUSBRFLink(serialPacket)

def  ledStartMeas():
    global globalData
    globalData.USBLink.LEDOff("red",globalData)
    time.sleep(0.1)
    globalData.USBLink.LEDOff("green",globalData)
    time.sleep(0.1)
    globalData.USBLink.LEDBlinking("red",globalData)
    time.sleep(0.1)


def ledEndOfMeas(succes):
    global globalData
    global ButtonThreadRun
    globalData.USBLink.LEDOff("red",globalData)
    globalData.USBLink.LEDOff("green",globalData)

    if succes == True:
      globalData.USBLink.LEDOn("green",globalData)

    else:
      globalData.USBLink.LEDOn("red",globalData) 

    globalData.USBLink.URSBRFLinkFlushBuff()
    ButtonThreadRun=True

def clickUploadCode():
    global globalData
    global RfThreadRun
    global ltext1, ltext2,ltext3,ltext4,ltext9
    global entry1
    global ButtonThreadRun

    tempVer = 2
    if globalData.monitorVers == "!!Vyber verzi!!":
       prt.myPrint(globalData,"Vyber verzi programu - Ceska/Nemecka !!", tag = 'error' )
       ledEndOfMeas(False)
       return 
      
    if globalData.monitorVers == "Fencee - Cesko":
        tempVer = 1

    ButtonThreadRun = False

    #if not entry1.get():
    ltext1.set(emptyText)
    ltext2.set(emptyText)
    ltext3.set(emptyText)
    ltext4.set(emptyText)
    ltext6.set(emptyText)
    ltext8.set(emptyText)
    ltext9.set(emptyText)

    lret1.config(fg="black")
    lret2.config(fg="black")
    lret3.config(fg="black")
    lret4.config(fg="black")
    lret6.config(fg="black")
    lret8.config(fg="black")
                    
    root.update()
   
    b1["state"] = "disable"
    ledStartMeas()
    globalData.sqTXPower = globalData.sqRXRssi  = globalData.sqConsumption =0

    if testTools(False) == False:
      ledEndOfMeas(False)
      return
    
    globalData.USBLink.switchSWDOn(globalData)
    time.sleep(0.3)
    b1["state"] = "disable"
    b1["text"] = "Nahravam"
    if globalData.STM32.connectToMcu(globalData) == False:
        b1["state"] = "normal"
        b1["text"] = "N A H R A T"
        ltext8.set('Chyba')
        lret8.config(fg="red")
        ledEndOfMeas(False)
        return 
    
    try:
      f = open('C:/VyrobaMonitory/Binarky/mx10_assemblyline/FENCEE_Monitor.binary', 'rb')
      t= f.read()
      f.close()
    except:
      prt.myPrint(globalData,"Chyba v nacitani binary souboru", tag = 'error' )
      b1["state"] = "normal"
      b1["text"] = "N A H R A T"
      ledEndOfMeas(False)
      return 

    if globalData.STM32.downloadFile(globalData,t) == False:
        b1["state"] = "normal"
        b1["text"] = "N A H R A T"
        ltext1.set('CHYBA')
        lret1.config(fg="red")
        ltext8.set('Chyba')
        lret8.config(fg="red")
        ledEndOfMeas(False)
        return 
    lret1.config(fg="green")
    ltext1.set('OK')
  
    #time.sleep(0.2)
    #globalData.STM32.setMxOnEeprom(globalData)
    #time.sleep(0.2)

    tx_Eui = time.time()
    globalData.sqMAC=int(tx_Eui)
    if globalData.STM32.setTX_EUI(int(tx_Eui),globalData) == False:
      b1["state"] = "normal"
      b1["text"] = "N A H R A T"
      ltext2.set('CHYBA')
      lret2.config(fg="red")
      ltext8.set('Chyba')
      lret8.config(fg="red")
      ledEndOfMeas(False)
      return 

    #b2["state"] = "disable"
    
    time.sleep(0.2)
    globalData.STM32.resetMcu()
    time.sleep(0.2)

    globalData.sqVersion = tempVer
    if globalData.STM32.setNameVerson(tempVer,globalData) == False:
      b1["state"] = "normal"
      b1["text"] = "N A H R A T"
      ltext2.set('CHYBA')
      lret2.config(fg="red")
      ltext8.set('Chyba')
      lret8.config(fg="red")
      ledEndOfMeas(False)
      return 

    ltext2.set('OK')
    lret2.config(fg="green")

    #globalData.STM32.resetMcu()
    #time.sleep(0.5)
    #if globalData.STM32.turnMxOn(globalData) == False:
    #   b1["state"] = "normal"
    #   b1["text"] = "N A H R A T"
    #   return

    b1["text"] = "Kalibruji Rf"
    
    # nastaveni RF switch
    setRfSwitch(RFSwitchMX_Analyzer)
    if USE_HMC8012 == True:
      globalData.HMC8012.setCurrentMaxRange()

    rfclb.initAndStartCalibRf(globalData)
    globalData.RfPowerAttempts=0
    RfThreadRun = True
    return 

def runRfCalib():
  # databaze historie
  con = sl.connect('C:/VyrobaMonitory/Zaznam/MX_History.db')
  try:
    cursor = con.cursor()
    cursor.execute("CREATE TABLE MXdata ( MAC Text, TXPower_dBm INTEGER, RXRssi_dBm INTEGER, Consumption_uA INTEGER, Version Text)")
    con.commit()
  except Exception as ex:
    print(ex)
    pass

  global RfThreadRun
  rssiOK = False
  pulseWayOK = False
  while True:
    time.sleep(0.1)
    while RfThreadRun == True:
        if rfclb.RfCalibEnabled() == True:
          temp = rfclb.measureRFProc(globalData)
          if temp == "OK":  # Teset TX OK
            ltext3.set('OK')
            lret3.config(fg="green")

            #pokracuj v testovani RSSI
            rfclb.stopRfCalib()
            globalData.USBLink.setRfSwitch(RFSwitchMX_Generator,globalData)
            #setRfSwitch(RFSwitchMX_Generator)
            #cekej dokud nebude potvrzen prijem se spravnym rssi
            for i in range(15): # MAX 2 sec
              time.sleep(0.2)
              if globalData.STM32.isRssiMeasDone(globalData) == True:
                rssiOK = True
                prt.myPrint(globalData,"Rssi je: " +str(globalData.STM32.readRssiVal(globalData)))
                break

              prt.myPrint(globalData,"Rssi je: " +str(globalData.STM32.readRssiVal(globalData)))

            if rssiOK == True:
              rssiOK = False
              prt.myPrint(globalData,'rssi Test OK', tag = 'ok' )
              globalData.STM32.shutDownMx(globalData)
              time.sleep(0.5)

              ltext4.set('OK')
              lret4.config(fg="green")
              
              # cteni pinu AUX6:
              tempCnt = 0
              while True:
                tempCnt +=1
                globalData.USBLink.readPinAux6(globalData)              
                command,hodnota,nic2,nic3 = globalData.USBLink.rxUSBRFLink(0)
                if command == 0x30  and nic2==nic3=="AUX6":
                  if hodnota == 1:
                    # test OK
                    pulseWayOK = True
                    break
                  
                if  tempCnt > 4:
                  #chyba
                  break
                
              if pulseWayOK == True:
                if USE_HMC8012 == True:
                  #mereni spotreby
                  globalData.USBLink.switchSWDOff(globalData)
                  #time.sleep(0.5)
                  globalData.HMC8012.setCurrentAutoRange()
                  #globalData.HMC8012.startDCIMeas()
                  time.sleep(2)
                  dcI =  globalData.HMC8012.getAvg()
                  dcI = abs(dcI)
                  globalData.sqConsumption = dcI
                  if dcI < 0.000045:
                    prt.myPrint(globalData,'Mereni spotreby - OK - PROUD: ' + str(dcI)+' A', tag ='ok')
                  
                    # ulozeni do databaze
                    if globalData.sqVersion == 1:
                      textVers = "Fencee"
                    else:
                      textVers = "VOSS"

                    #tempDate = datetime.datetime.fromtimestamp
                    cursor.execute('INSERT INTO MXdata VALUES(?,?,?,?,?)',(str(hex(globalData.sqMAC)), globalData.sqTXPower, globalData.sqRXRssi, globalData.sqConsumption, textVers))
                    con.commit()

                    measOk = True
                
                  else:
                    prt.myPrint(globalData,'Prilis velky odber proudu! PROUD: ' + str(dcI)+' A', tag = 'error')
                    ltext6.set('CHYBA')
                    lret6.config(fg="red")
            
                  globalData.HMC8012.setCurrentMaxRange()
                  globalData.USBLink.switchSWDOn(globalData)
                  
                  time.sleep(0.1)
                  #resetovanim se M zapne
                  globalData.STM32.resetMcu()
                  time.sleep(0.2)
                  globalData.STM32.resetMcu()

                  b1["text"] = "N A H R A T"
                  b1["state"] = "normal"
                  RfThreadRun = False

                  if measOk == True:
                    ltext6.set('OK')
                    lret6.config(fg="green")
                    ltext8.set('OK')
                    lret8.config(fg="green")
                    measOk=False
                    ledEndOfMeas(True)
                  else:
                    ltext8.set('Chyba')
                    lret8.config(fg="red")
                    ledEndOfMeas(False)

                else:
                  globalData.STM32.resetMcu()
                  # ulozeni do databaze
                  if globalData.sqVersion == 1:
                    textVers = "Fencee"
                  else:
                    textVers = "VOSS"

                  ledEndOfMeas(True)
                  ltext8.set('OK')
                  lret8.config(fg="green")
                  #tempDate = datetime.datetime.fromtimestamp
                  cursor.execute('INSERT INTO MXdata VALUES(?,?,?,?,?)',(str(hex(globalData.sqMAC)), globalData.sqTXPower, globalData.sqRXRssi, globalData.sqConsumption, textVers))
                  con.commit()
              
              else: #vstupni R - Fail
                prt.myPrint(globalData,'Chyba vstupni R ', tag = 'error' )  
                ltext9.set('CHYBA')
                lret9.config(fg="red")
                ltext8.set('Chyba')
                lret8.config(fg="red")
                b1["text"] = "N A H R A T"
                b1["state"] = "normal"
                # b2["state"] = "normal"
                RfThreadRun = False

                ledEndOfMeas(False)

            else: #RSSI fail
              prt.myPrint(globalData,'Chybny RSSI Test ', tag = 'error' )
              ltext4.set('CHYBA')
              lret4.config(fg="red")
              ltext8.set('Chyba')
              lret8.config(fg="red")
              ledEndOfMeas(False)
            # ukonci mereni
           
            b1["text"] = "N A H R A T"
            b1["state"] = "normal"
           # b2["state"] = "normal"
            RfThreadRun = False
            break

          elif temp == 'FalseTX':
            ltext3.set('CHYBA')
            lret3.config(fg="red")
            ltext8.set('Chyba')
            lret8.config(fg="red")
            b1["text"] = "N A H R A T"
            b1["state"] = "normal"
           # b2["state"] = "normal"
            RfThreadRun = False
            ledEndOfMeas(False)
            
          elif temp == 'False':
            RfThreadRun = False
            ltext3.set('CHYBA')
            lret3.config(fg="red")
            ltext8.set('Chyba')
            lret8.config(fg="red")
            b1["text"] = "N A H R A T"
            b1["state"] = "normal"
            ledEndOfMeas(False)
  
def runScanButton():
  global ButtonThreadRun
  global globalData

  while True:

    while ButtonThreadRun == True:
      ret,nic1,nic2,nic3 = globalData.USBLink.rxUSBRFLink(0)

      if ret == 0x29  and nic1==nic2==nic3=="button":
        #tlacitko stisknuto
        ButtonThreadRun = False
        clickUploadCode()

def lookForPCB():

  if globalData.STM32.readMcuVoltage() > 3000:
    prt.myPrint(globalData,'PCB pripojeno', tag = 'ok' )
    clickUploadCode()

  else: 
    prt.myPrint(globalData,'PCB neni pripojeno', tag = 'error' ) 
    threading.Timer(0.5,lookForPCB).start()
  #timPCB.start()

def testMeasTools():
  threading.Thread(target=testTools(True), daemon = True).start()

def testTools(firstTest):
    global glAnalyzerConnected 
    global glSerialLinkConnected
    global glToolsConnected 
    global ButtonThreadRun
    HMC8012Connected = False

    #zkouska spojeni spektralni analyzator
    if USE_FPL1003 == True:
      analyzer=SpektrakClass()
      globalData.analyzer = analyzer
      retAlyzer = analyzer.connectSpektrak(IpAnalyzer)
      if retAlyzer == False:
        prt.myPrint(globalData,'Spectral analyzer did not find',tag='error') 
        prt.myPrint(globalData,'with IP Adress:' + IpAnalyzer,tag = 'error' )
        glAnalyzerConnected = False
      
      else:
        prt.myPrint(globalData,'Spectral analyzer found',tag='ok') 
        prt.myPrint(globalData,'with IP Adress:' + IpAnalyzer,tag = 'ok' )
        glAnalyzerConnected = True

      del analyzer
    else:
      glAnalyzerConnected = True

    if USE_HMC8012 == True:
      #multimetr HMC8012 
      HMC8012=HMC8012Class()
      globalData.HMC8012 = HMC8012
      retHMC8012 = globalData.HMC8012.connectHMC8012(IpAmpMeter)
      if retHMC8012 == False:
        prt.myPrint(globalData,'Multimetr HMC8012 did not find',tag='error') 
        prt.myPrint(globalData,'with IP Adress:' + IpAmpMeter,tag = 'error' )
      else:
        prt.myPrint(globalData,'Multimetr HMC8012 found',tag='ok') 
        prt.myPrint(globalData,'with IP Adress:' + IpAmpMeter,tag = 'ok' )
        HMC8012Connected = True

      del HMC8012
    else:
      HMC8012Connected = True

    if USE_USB_RF_LINK == True:
        # USB serial LoRa link
        try:
          USBLink = USBSerialLink()
          if USBLink.openUSBRfLink() != "False":
            globalData.USBLink = USBLink
            prt.myPrint(globalData,'UART USB Link connected',tag='ok')
            glSerialLinkConnected = True
          
          else :
            prt.myPrint(globalData,'UART USB Link was not found',tag='error')
            glSerialLinkConnected = False
        except :
          prt.myPrint(globalData,'UART USB Link connected',tag='ok')
          pass

        del USBLink

    else:
       glSerialLinkConnected = True

    if glSerialLinkConnected == True and glAnalyzerConnected == True and HMC8012Connected == True:
      if firstTest == True:
        b1["state"] = "normal"
        ButtonThreadRun = True 
        ledEndOfMeas(False)  #zhasnuti LED

      return True
    else:
      b1["state"] = "disable"
      ButtonThreadRun = False
      return False


globalData.testTools = testTools

root.protocol("WM_DELETE_WINDOW", clickCloseApp)
prt.myPrint(globalData,"App is running...",tag="ok")

b1 = Button(root, text='N A H R A T ',padx=25, pady=15,height = 1, width = 7, command=lambda:clickUploadCode())
b1.place(x = 75, y = 130)
b1["state"] = "disable"

#b2 = Button(root, text='Test pristroju',padx=20, pady=10,height = 1, width = 7, command=lambda:testTools())
#b2.place(x = 100, y = 5)
#b2["state"] = "normal"

monitorCombo = ttk.Combobox(root, value = monitorVersion)
monitorCombo.current(0)
monitorCombo.bind("<<ComboboxSelected>>",comboclick)
monitorCombo.place(x = 180, y = 40)

#menu.addNewItem(globalData)

timPCB = threading.Timer(0.5,lookForPCB)
#timPCB.start()
testTools(True)
rfCalibThread = threading.Thread(target=runRfCalib, daemon = True)
rfCalibThread.start()
scanButtonThread = threading.Thread(target=runScanButton, daemon = False)
scanButtonThread.start()

root.mainloop()

