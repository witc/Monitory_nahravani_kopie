import time 
import numpy as np
import pandas as pd
import threading
from sklearn.linear_model import LinearRegression
from sklearn import linear_model
import sklearn.utils._cython_blas
import sklearn.neighbors.typedefs
import sklearn.neighbors.quad_tree
import sklearn.tree
import sklearn.tree._utils
from PyJlinkClass   import Mcu
import tkinter as tk
from tkinter import *       
from tkinter import ttk
import MyGuiConsole as prt
#from PySpektrakClass import SpektrakClass
from RthScopeClass import RthScopeClass
from USB_RF_Link import USBSerialLink
import xlwt
import xlrd
from xlwt import Workbook
from xlutils.copy import copy
from xlrd import open_workbook
from datetime import date
from datetime import datetime

glPulsedictOfLoads = [6000,1000,680,500,400]    # z 6000 nehybat - bereme jako vychozi hodnotu
glNoOfMeasPerLoad = 3
glScopeMeasData = []
glZatezCountDivider = 0
glCalibCountDivider = 0
glUgenerator = 0

glPulseCountLoads = 0
calibDoneCoef = []  
globY = []
globX = []
globFinalY = []
globNewDataToPlot = False 
globFinalDataPlot = False
glMcuConnected = False
glPulseCanCalib = False
glZatezCanCalib = False

table = { 'ADC':  [],
          'Scope': [],
        }
glPulseCalibDf = pd.DataFrame(data = table)
USBLink = 1

dictUsbCmds = {
    0: "USB_CMD_NONE",
    1: "USB_CMD_HERE_I_AM",
    2: "USB_CMD_SENDING_ADC_MV",
    3: "USB_CMD_RESERVED"
}


def calibPulseProc(pulseProgress,globalData):
    global glPulseCanCalib
    global glPulseCalibDf
    global glPulseCountLoads
    global calibDoneCoef
    global glPulsedictOfLoads
    global globY
    global globX
    global globNewDataToPlot
    global glUgenerator
    global glCalibCountDivider

    restartMeas = False
    #cekej na prijem novych dat
    MX_EUI, RndSessionKey, Cmd,PulsemV = globalData.USBLink.rxUSBRFLink(0)

    if (MX_EUI == globalData.actualMxEui) and (RndSessionKey == globalData.actualRndSesKey):
        #dictUsbCmds.get(Cmd,"USB_CMD_NONE")
        if dictUsbCmds.get(Cmd,"USB_CMD_NONE") == "USB_CMD_SENDING_ADC_MV":

            prt.myPrint(globalData,"Monitor ADC voltage: {}".format(PulsemV))
            time.sleep(0.2)
            if  globalData.scope.poolForSingleDone(globalData):
                time.sleep(0.2)
                result = int(float(globalData.scope.getMeasResult(1)))
                time.sleep(0.2)
                prt.myPrint(globalData,"Scope Voltage: {}".format(result))
                glScopeMeasData.append(result)
                globalData.scope.initMeas()
                    
                glPulseCalibDf.loc[len(glPulseCalibDf)] = [PulsemV,int(float(result))] 
                globX.append(PulsemV)
                globY.append(result)

                # ++count loads 
                glCalibCountDivider+=1
                if glCalibCountDivider%glNoOfMeasPerLoad == 0:
                    # zmen zatez
                    glPulseCountLoads +=1 
                    pulseProgress['value'] = (100/(len(glPulsedictOfLoads)))*(glPulseCountLoads)
                    globalData.root.update_idletasks() 

                    if (glPulseCountLoads) == (len(glPulsedictOfLoads)):
                        glCalibCountDivider = 0
                        prt.myPrint(globalData,"Zapis koeficientu do Monitoru "+str(glUgenerator),tag='ok')
                        # Measuring is done
                        calibDoneCoef = fitMeasData(glPulseCalibDf,globalData)
                        retResult = calibDoneCoef[2]
                        globalData.EspZatez.setLoadTrig(6000,globalData) 
                        if retResult == False:
                            return "chyba"
                        # zapis coeficientu do MCU
                        cmdSaveCoef = 5
                        rfu = 0
                        coeaf_a = int(calibDoneCoef[0]*1000)
                        coeaf_b = int(calibDoneCoef[1])

                        if coeaf_a > 65535:
                           prt.myPrint(globalData,"Coef A prilis velky", tag = 'error')
                           return "chyba"
                        
                        if coeaf_b > 65535:
                            prt.myPrint(globalData,"Coef B prilis velky", tag = 'error')
                            return "chyba"

                        serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'little'), globalData.actualMxEui.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
                            globalData.ZERO_PADING.to_bytes(7,byteorder = 'little'), globalData.actualRndSesKey.to_bytes(4,byteorder ='little'), cmdSaveCoef.to_bytes(1,byteorder='little'),
                            coeaf_a.to_bytes(2,byteorder='little',signed = True),
                            coeaf_b.to_bytes(2,byteorder='little',signed = True),rfu.to_bytes(1,byteorder='little')]

                        globalData.EspZatez.setLoadTrig(6000,globalData) 

                        for i in range(4):
                            globalData.USBLink.txUSBRFLink(serialPacket)
                            time.sleep(0.3)
                            
                                                
                        return "calib_ok"    # uspesny konec kalibrace

                    globalData.EspZatez.setLoadTrig(glPulsedictOfLoads[glPulseCountLoads],globalData) 
                    globalData.USBLink.URSBRFLinkFlushBuff()                   
               
                globNewDataToPlot = True
                
            else:
                restartMeas = True
                prt.myPrint(globalData,"Restarting Scope...")
                globalData.scope.initScope()

            if restartMeas == True:
                stopCalib()
                initAndStartCalibPulse(globalData)

    return True

def initAndStartCalibPulse(globalData):
    global glPulseCountLoads
    global calibDoneCoef
    global glPulseCalibDf
    global glUgenerator

    stopCalib()

    glPulseCountLoads=0
      
    globX.clear()
    globY.clear()
    globFinalY.clear()
    
    calibDoneCoef = 0
    glPulseCountLoads = 0
    #zresetuj zatez
    globalData.EspZatez.setLoadNoTrig(glPulsedictOfLoads[glPulseCountLoads],globalData)
    
    #cistka tabulky
    glPulseCalibDf=glPulseCalibDf.drop(glPulseCalibDf.index[glPulseCalibDf.index>=0]) 
        
    time.sleep(0.05)
    globalData.USBLink.URSBRFLinkFlushBuff()
    startCalib()


def fitMeasData(measData,globalData):
    global globFinalDataPlot
    global globFinalY
    retResult = False

    X=measData.iloc[:,0].values.reshape(-1, 1)
    Y=measData.iloc[:,1].values.reshape(-1, 1)

    #TODO nahradit https://devarea.com/linear-regression-with-numpy/#.X70nJmhKggw
    lm = linear_model.LinearRegression(fit_intercept = True)
    model=lm.fit(X, Y)
    globFinalY.clear()
    globFinalY=lm.predict(X)
    globFinalY=globFinalY.tolist()
    globFinalDataPlot = True
    
    score=lm.score(X,Y)
    
    intercept=model.intercept_
    coef=model.coef_
    prt.myPrint(globalData,"coef: {}".format(coef))
    prt.myPrint(globalData,"intercept_: {}".format(intercept))

    if 100*score >= 99.95:
        color='green'
        styl="ok"
        retResult = True
    else:
        color='red'
        styl='error'

    prt.myPrint(globalData,"Score: {:.6f} %".format(score*100),tag=styl)
    globalData.rLabel.config(fg=color,text = 'R: {:.3f} %'.format(score*100))
    
    return coef,intercept, retResult
 
def isAnyToClearandPlot():
    global globNewDataToPlot
    willPlot = globNewDataToPlot
    globNewDataToPlot = False
    return willPlot

def isAnyToPlot():
    global globFinalDataPlot
    willPlot = globFinalDataPlot
    globFinalDataPlot= False
    return willPlot

def readDataToPlot_erase():
    global globX
    global globY

    return globX,globY

def readDataToPlot_Noerase():
    global globFinalY
    global globX
    
    return globX,globFinalY

def canIMeas():
    global glPulseCanCalib
    return glPulseCanCalib

def stopCalib():
    global glPulseCanCalib
    glPulseCanCalib = False

def startCalib():
    global glPulseCanCalib
    glPulseCanCalib = True

def startCalibZatez():
    global glZatezCanCalib
    glZatezCanCalib = True

def stopCalibZatez():
    global glZatezCanCalib
    glZatezCanCalib = True

def canICalibZatez():
    global glZatezCanCalib
    return glZatezCanCalib

def initCalib():
    pass

def saveGlobalData(globData):
    global globalData
    globalData = globData

def readGLobalData():
    global globalData
    return globalData