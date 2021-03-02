import time
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import struct
import pyvisa 
from pyvisa import constants
import MyGuiConsole as prt

class RthScopeClass:

    def connectScope(self, IpAdr):
        try:
            rm = pyvisa.ResourceManager()
            self.scope = rm.open_resource('TCPIP::'+IpAdr+'::INSTR')
            self.scope.timeout = 2000

        except Exception as ex:                
            return False
    
        print("Oscilloscope found: " +self.scope.query('*IDN?'))     
        self.initScope()
        return True

    def initScope(self):
        self.scope.write('*CLS',)
        self.scope.write("*RST") # Reset the instrument, clear the Error queue
        self.setChanState(1,"OFF")

        self.setHorizontScale(0.00001)
        self.setHorizontPosition(0.000001)
        self.setHorizontScale(0.00005)

        #self.setVerticalOffset(1,2000)
        self.setVerticalScale(1,2000)  #1000
        self.setProbe(1,"V1000To1") 
        self.setChanPos(1,-3)
        self.setChanState(1,"ON")
        
        """ Set trigger """
        self.setTrigMode("SING")
        self.setTrigSource("C1")
        self.setTrigType("EDGE")
        self.setTrigLevel(1,500)  #500
        
        self.setMeasEnable(1,"ON")
        self.setMeasSource(1,"C1")
        self.setMeasType(1,"MAX")

        #self.acquireMode("AVERage")
        self.acquireUpdate('FULL')
        self.initMeas()
        
        #self.scope.write_str("CHAN1:RANGe 15000" )
        #self.scope.write_str("CHAN1:PROB V1000To1" ) 

    """
    @param: chan: 1-4
            state: ON/OFF
    """    
    def setChanState(self,chan,state)   :
        self.scope.write("CHAN"+str(chan)+":STAT "+str(state))
        self.scope.write("CHAN"+str(chan)+":BAND B2HK")
    """  
    @ param:    chan: 1-4
                scale. max 100 V/div
    """
    def setVerticalScale(self,chan,scale):
        self.scope.write("CHAN"+str(chan)+":SCAL "+str(scale))   

    """  
    @ param:    chan: 1-4
                offset: 
    """
    def setVerticalOffset(self,chan,offset):
        self.scope.write("CHAN"+str(chan)+":OFFset "+str(offset))

    """
    @ param: chan: 1-4
             pos: -4 - +4
    """
    def setChanPos(self,chan, pos):
        self.scope.write("CHAN"+str(chan)+":POSition "+str(pos))

    """  
    @ param:    chan: 1-4
                type:RTIM,... 
    """
    def setMeasureType(self,chan,type):
        self.scope.write("MEAS"+str(chan)+":TYPE "+str(type))

    #self.scope.write_str("TRIGger:SOURce C1" )
        #self.scope.write_str("TRIGger:EDGE:SLOPe POSitive" )
        #self.scope.write_str("TRIGger:LEVel1:VALue 500" )

    """  
    @ param: source: C1-4
    """
    def setTrigSource(self, source):
        self.scope.write("TRIG:SOUR "+str(source))

    """  
    @ param: mode: AUTO, NORM, SING
    """
    def setTrigMode(self, mode):
        self.scope.write("TRIG:MODE "+(mode))
    
    """
    @ param: type: EDGE
    """
    def setTrigType(self, type):
        self.scope.write("TRIG:TYPE "+(type))
    
    """
    @ param: chan: 1-4, VAL: -10 - +10
    """
    def setTrigLevel(self,chan,val):
        self.scope.write("TRIG:LEVel"+str(chan)+":VAL "+str(val))

    """
    @param: time: max 500
    """
    def setHorizontScale(self,time):
        self.scope.write("TIM:SCAL "+str(time))
        
    """
    @param: pos
    """
    def setHorizontPosition(self,pos):
        self.scope.write("TIM:HOR:POS "+str(pos))

    def setProbe(self,chan, probeSet):
        self.scope.write("CHAN"+str(chan)+":PROB "+probeSet)

    """ ON/OFF"""
    def setMeasEnable(self,chan, state):
        self.scope.write("MEAS"+str(chan)+":ENAB "+state)

    """ C1... C2"""
    def setMeasSource(self,chan,source):
        self.scope.write("MEAS"+str(chan)+":SOUR "+source)

    """ MAX, PKPK"""
    def setMeasType(self,chan,type):
        self.scope.write("MEAS"+str(chan)+":TYPE "+type) 

    def getMeasResult(self,chan):
        dummy=self.scope.query("MEAS"+str(chan)+":RESult:ACT?")
        if dummy == "0":
            return 0
        
        return dummy

    def clearScreen(self):
        #self.setChanState(1,"OFF")
        time.sleep(0.3)
        #self.scope.write('*OPC?')
        #self.setChanState(1,"ON")
        #self.scope.write('*OPC?')
    
    def checkTrigState(self, chan):
        ret = self.scope.query('TRIG:STAT:CHAN'+str(chan)+'?')
        return ret

    def queryOpc(self):
        while True:
            ret = self.scope.query('*OPC?')
            if int(ret) == 1:
                break
    
    def isOpcDone(self):
        ret = self.scope.query('*OPC?')
        return ret

    """ SAMPle | PDETect | HRESolution | AVERage | ENVelope"""
    def acquireMode(self, mode):
        self.scope.write("ACQuire:MODE "+(mode))

    """ INTermediate | FULL """
    def acquireUpdate(self, mode):
        self.scope.write('ACQuire:WAVeformupd '+(mode))

    def startAcquisition(self):
        self.scope.write('RUN')
    
    def stopAcquisition(self):
        self.scope.write('STOP')

    def poolForSingleDone(self,globalData):
        try:
            while True:
                if int(self.isOpcDone()) == 1:
                    break
        except:
            print('Timeout on Trigger')   
            prt.myPrint(globalData,'Timeout on Trigger',tag = 'error')
            return False     
        
        return True

    #def isMeasDone(self):

    def initMeas(self):
        #self.setTrigMode('AUTO')
        #time.sleep(0.1)
        self.setHorizontScale(0.00002)
        self.queryOpc()
        self.setTrigMode('NORM')
        self.queryOpc()
        self.setHorizontScale(0.00005)
        self.queryOpc()
        self.startAcquisition()
        self.queryOpc()
        #self.stopAcquisition()
        #self.startAcquisition()

    def reconnect(self):
        rm = pyvisa.ResourceManager()
        self.scope = rm.open_resource('TCPIP::192.168.1.139::INSTR')
        self.scope.timeout = 10000
    
    