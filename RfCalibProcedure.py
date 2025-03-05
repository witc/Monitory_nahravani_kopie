import time 
import numpy as np
import pandas as pd
import threading
from PyJlinkClass   import Mcu
import tkinter as tk
from tkinter import *       
from tkinter import ttk
import MyGuiConsole as prt
from PySpektrakClass import SpektrakClass


# Global Variables
glRfPowerAttempt=0
glRfFreqAttempt=0
glRfTestFreq=869525000
glRfcanCalib = False
glPulseCanCalib = False
glAttenOffset=4 #4dB //zraty na vedeni
glUtlumak = 0  #predradny utlumak

def initAndStartCalibRf(globalData):
   global glRfPowerAttempt
   global glRfFreqAttempt
   global glRfTestFreq
     
   glRfPowerAttempt = 0
   glRfFreqAttempt = 0
   glRfTestFreq=869525000

   globalData.analyzer.clearTraces()
   startRfCalib()
   
def measureRFProc(globalData, freq_in):
    global glRfPowerAttempt
    global glRfFreqAttempt
    global glRfTestFreq
    
    globalData.analyzer.clearTraces()
    
    if globalData.STM32.stopCW(globalData) == False:
       prt.myPrint(globalData,"Opakuj mereni",tag='error')
       #ukonci mereni
       return "False"

    if globalData.STM32.setFreq(glRfTestFreq,globalData) == False:
       prt.myPrint(globalData,"Opakuj mereni",tag='error')
       #ukonci mereni
       return "False"

    if globalData.STM32.startCW(globalData) == False:
       prt.myPrint(globalData,"Opakuj mereni",tag='error')
       #ukonci mereni
       return "False"
       
    time.sleep(0.6)
    if globalData.STM32.stopCW(globalData) == False:
       prt.myPrint(globalData,"Opakuj mereni",tag='error')
       #ukonci mereni
       return "False"

    freq, power = globalData.analyzer.getRfResult()
    power+=glAttenOffset+glUtlumak
    prt.myPrint(globalData,'Frequency: {:.0f} '.format(freq))
    prt.myPrint(globalData, 'Power: {:.2f} '.format(power))

    globalData.sqTXPower = power
    
    if (power)>=(globalData.minTxPower):
      if (freq) >= freq_in-1000  and (freq) <= freq_in+1000:
        # measure is done - OK
        globalData.STM32.saveRfTxOK(globalData)
        prt.myPrint(globalData,"Rf TX - OK",tag = 'ok')
       
        return "OK"

      glRfFreqAttempt+=1
      if  glRfFreqAttempt > 8:
          prt.myPrint(globalData,"Spatna frekvence RF {:.0f}".format(freq),'error')
          prt.myPrint(globalData,"Opakuj mereni",tag='error')
          
          #ukonci mereni
          return "FalseTX"

      newFreq=869525000-(freq)
      newFreq=glRfTestFreq+newFreq
      glRfTestFreq=newFreq

    else:
      glRfPowerAttempt+=1
      if glRfPowerAttempt > 4:
        #LowPower - NOK
        prt.myPrint(globalData,"Nizky vykon RF {:.4f}".format(power),tag='error')
        prt.myPrint(globalData,"Opakuj mereni",tag='error')
      
        #ukonci mereni
        return "FalseTX"


def startRfCalib():
   global glRfcanCalib
   glRfcanCalib = True


def stopRfCalib():
   global glRfcanCalib
   glRfcanCalib = False

def RfCalibEnabled():
  global glRfcanCalib
  return glRfcanCalib
