import time
import math
import numpy as np
import time
import struct
import pyvisa

class SpektrakClass:

    def connectSpektrak(self,IpAdr,freq):
        
        try:
            rm = pyvisa.ResourceManager()
            self.analyzer = rm.open_resource('TCPIP::'+IpAdr+'::INSTR')
            self.analyzer.timeout = 2000

        except Exception as ex:
            #prt.myPrint(globalData,"Error initializing the instrument session:",tag="error")
            print("Spectrum analyzer did not find!")
            print('Error initializing the instrument session:\n' + ex.args[0])
            
            return False

        #prt.myPrint(globalData,'Oscilloscope found: '+self.scope.query('*IDN?'),tag = 'ok')
        print("Spectrum analyzer found: " +self.analyzer.query('*IDN?'))  
        self.initSpektrak(freq)

    def initSpektrak(self,freq):
        self.analyzer.write("*CLS") # Clear status
        #self.analyzer.write("*RST") # Reset the instrument, clear the Error queue
        #self.queryOpc()
        self.analyzer.write("INIT:CONT OFF") # Switch OFF the continuous sweepd
        self.queryOpc()
        #Basic Setting
        #self.analyzer.write('FREQ:CENT 869525000Hz')
        self.analyzer.write(f'FREQ:CENT {freq}Hz')
        self.queryOpc()
        self.analyzer.write('FREQ:SPAN 100KHz')
        self.queryOpc()
        self.analyzer.write("INIT:CONT ON") # Switch OFF the continuous sweepd
        self.queryOpc()
        #Activate signal tracking to keep the center frequency on the signal peak:
        #specAnalyzer.write("CALC:MARK:FUNC:STR ON")
        #specAnalyzer.write("CALC:MARK:FUNC:STR:BAND 1kHz")
        #specAnalyzer.write("CALC:MARK:FUNC:STR:THR 5dBm")
        #specAnalyzer.write("CALC:MARK:FUNC:STR:TRAC 1")
        #After each sweep the maximum on trace 1 is searched within a range of 1 MHz
        #around the center frequency. It must have a minimum power of 18dBm.

        self.analyzer.write("BAND:AUTO OFF")
        #self.queryOpc()
        self.analyzer.write("BAND 1KHz")
        #self.queryOpc()
        self.analyzer.write("BAND:VID:AUTO OFF")
        #self.queryOpc()
        self.analyzer.write("BAND:VID 100kHz")
        #self.queryOpc()
        #/Decouples the VBW from the RBW and decreases it to smooth the trace.

        #--------------Configuring the Sweep--------------------------
        self.analyzer.write("SENS:SWE:TIME:AUTO OFF")
        #self.queryOpc()
        self.analyzer.write("SENS:SWE:TIME 20ms")
        #self.queryOpc()
        #--------------Configuring Attenuation------------------------
        #specAnalyzer.write("INP:ATT 10dB")
        #Sets the mechanical attenuation to 10 dB and couples the reference level
        #to the attenuation instead of vice versa.

        #--------------Configuring the Amplitude and Scaling----------
        self.analyzer.write("DISP:TRAC1:Y:RLEV 30dBm")
        #self.queryOpc()

        #--------------Configuring the Trace--------------------------
        self.analyzer.write("DISP:TRAC1 ON")
        #self.queryOpc()
        self.analyzer.write("DISP:TRAC2:MODE WRIT")
        #self.queryOpc()
        self.analyzer.write("DISP:TRAC2 ON")
        #self.queryOpc()
        self.analyzer.write("DISP:TRAC2:MODE MAXH")
        #self.queryOpc()
        self.analyzer.write("SENS:DET2 POS")
        #self.queryOpc()


    def getRfResult(self):
        self.analyzer.write("CALC2:MARK1:TRAC 2")
        self.analyzer.write('CALC2:MARK1:MAX')
        #self.queryOpc()
        #self.analyzer.write_with_opc('CALC1:MARK1:MAX')  # Set the marker to the maximum point of the entire trace, wait for it to be set
        markerFreq =self.analyzer.query("CALC2:MARK1:X?")
        self.queryOpc()
        markerPower=self.analyzer.query("CALC2:MARK1:Y?")

        return float(markerFreq), float(markerPower)

    def clearTraces(self):
        self.analyzer.write("DISP:TRAC1 ON")
        self.analyzer.write("DISP:TRAC2:MODE WRIT")
        self.analyzer.write("DISP:TRAC2 ON")
        self.analyzer.write("DISP:TRAC2:MODE MAXH")
        self.analyzer.write("SENS:DET2 POS")
        self.queryOpc()

    def queryOpc(self):
        while True:
            ret = self.analyzer.query('*OPC?')
            if int(ret) == 1:
                break