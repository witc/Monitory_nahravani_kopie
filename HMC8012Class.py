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

# Multimeter Class
class HMC8012Class:

    def connectHMC8012(self, ipAdr):
        try:
            rm = pyvisa.ResourceManager()
            self.hmc8012 = rm.open_resource("TCPIP::" +ipAdr+ "::INSTR")# :192.168.1.185:
            #self.hmc8012 = rm.open_resource("TCPIP::192.168.1.185::5025::SOCKET")
            self.hmc8012.timeout = 2000
            #self.hmc8012.read_termination = "\n"
            #self.hmc8012.write_termination = "\n"

        except Exception as ex:
            #prt.myPrint(globalData,"Error initializing the instrument session:",tag="error")
            print("HMC8012 not found!")
            print('Error initializing HMC8012:' + str(ex.args[0]))
            
            return False

        print("HMC8012 found: " +self.hmc8012.query('*IDN?'))     

        self.initHMC8012()
        self.setCurrentAutoRange()

        return True

    def initHMC8012(self):
        self.hmc8012.write("*CLS") # Clear status
        #self.hmc8012.write("*RST") # Reset the instrument, clear the Error queue

    def queryOpc(self):
        while True:
            ret = self.hmc8012.query('*OPC?')
            if int(ret) == 1:
                break

    def setCurrentAutoRange(self):
        self.hmc8012.write("CONFigure:CURRent AUTO")
        self.hmc8012.write("*wai")
        self.hmc8012.write("MEAS:CURR:DC? AUTO")
        self.hmc8012.write("*wai")
       
        self.queryOpc()
        #self.hmc8012.query('*IDN?'))   

    def setCurrentMaxRange(self):
        self.hmc8012.write("CONFigure:CURRent 2 A")
        self.hmc8012.write("*wai")
        self.hmc8012.write("MEAS:CURR:DC? 2 A")
        self.hmc8012.write("*wai")
       
        self.queryOpc()

    def startDCIMeas(self):
        self.setCurrentAutoRange()

    def getAvg(self):
        ret = self.hmc8012.query("CALCulate:AVERage:AVERage?")

        return float(ret)
        
      
   