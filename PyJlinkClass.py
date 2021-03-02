import os
import ctypes
import fnmatch
import sys
import time
import platform
import struct
from ctypes import *
from tkinter import *       #importuje vse
import MyGuiConsole as prt

readU32=ctypes.c_uint32()
readI32=ctypes.c_int32()
readU16=ctypes.c_uint16()
readU8=ctypes.c_uint8()
readI8=ctypes.c_int8()
readI16=ctypes.c_int16()
writeU32=ctypes.c_uint32()
writeU16=ctypes.c_uint16()
writeU8=ctypes.c_uint8()
null_ptr = POINTER(c_int)()

class tFactoryTest(Structure):
    _fields_ = [('NewRxPendingMsg', ctypes.c_bool),
                ('FactoryCmd', ctypes.c_uint8),
                ('SetFreq', ctypes.c_uint32),
                ('ShiftFreq', ctypes.c_uint32),
                ('SetPower', ctypes.c_uint8),
                ('PulseIsUpdated', ctypes.c_bool),
                ('PulseInmV', ctypes.c_uint16),
                ('Calib_Coef_A', ctypes.c_uint32),
                ('Calib_Coef_B', ctypes.c_uint32)]

# From now on the target is identified and we can start working with it.
class POINT(Structure):
    _fields_ = [('Vtarget', ctypes.c_uint16),
                ('tck', ctypes.c_uint8),
                ('tdi', ctypes.c_uint8),
                ('tdo', ctypes.c_uint8),
                ('tms', ctypes.c_uint8),
                ('tres',ctypes.c_uint8),
                ('trst',ctypes.c_uint8)]

class Mcu:

    def __init__(self,startAddr):
        self.startStructAddr=startAddr
        self.addrCMD=startAddr+1
        self.addrSetFreq=startAddr+2
        self.addrPulseIsUPdated=startAddr+11
        self.addrPulseInmV=startAddr+12
        self.addrPulseCount=startAddr+14
        self.addrCoefA=startAddr+15
        self.addrIntercept=startAddr+19
        self.addrPulseInkV=startAddr+23
        self.addrcanStartTest=self.addrPulseInkV+2
        self.addrPendingMsg=self.startStructAddr
        self.addrRssiFlag =startAddr+26
        self.addrRssiValue = startAddr+27
        
        # Load DLL
        ActiveOS = platform.system()
        PyArch   = (struct.calcsize("P") * 8)   # Determine if 32 or 64 bit python is running
        sDLLPath = (os.path.dirname(__file__))  # Look for DLL relative to this script's directory
        if ActiveOS == 'Windows':
            if (PyArch == 32):
                sDLLPath += "/JLinkARM.dll"
            else:
                sDLLPath += "/JLink_x64.dll"
        #sDLLPath ='c:\\Users\\jan.ropek\\Documents\\aaVNT_2016\\Vyvoj_projekty\\Ohradniky\\MonitorMX\\01_PyCalibMonitorApp\\pyfactorytestapp_mx10/JLinkARM.dll'

        self.dll = ctypes.cdll.LoadLibrary(sDLLPath)
        self.dll.JLINKARM_Open.restype = ctypes.c_char_p           # Reset function return from int to char pointer for Python compiler
        # Get serial number if USB selected or IP address if Ethernet selected as host interface
        serialNo=801025475
       # self.dll.JLINKARM_EMU_SelectByUSBSN(ctypes.c_uint32(serialNo))        

    def setMcu(self,globalData):
        ## Create commandstring for J-Link
        temp= 'Device = STM32L071CB'
        acCmd = temp.encode('utf-8')                            # Convert to utf for c interpreter
        self.dll.JLINKARM_ExecCommand(ctypes.c_char_p(acCmd), 0, 0)

        swd=1
        self.dll.JLINKARM_TIF_Select(int(swd))
        speedSwd=   4000
        self.dll.JLINKARM_SetSpeed(int(speedSwd))

    def connectToMcu(self,globalData):
        self.setMcu(globalData)
        
        #if self.checkIfDevConnected() == False:
        #    prt.myPrint(globalData,"Connect failed. Error:",tag="error")                 # Print errorcode if aviable
        #    return False

        try:
            # Connect to target CPU
            r = self.dll.JLINKARM_Connect()

        except Exception as ex:
            prt.myPrint(globalData,"Connect to MCU failed. Error:",tag="error")                 # Print errorcode if aviable
            return False

        if (r < 0):
            prt.myPrint(globalData,"Connect to MCU failed. Error:",tag="error")                 # Print errorcode if aviable
            return False
        else:
            prt.myPrint(globalData,"Connected to MCU successfully.",tag="ok")
            return True

    def checkIfDevConnected(self):
        if self.dll.JLINKARM_GetId() == (-1):
            return False

        return True


    def readMcuVoltage(self):
        pStat=POINT()
        self.dll.JLINKARM_GetHWStatus(pointer(pStat))
        return pStat.Vtarget

    def resetMcu(self):
        self.dll.JLINKARM_ResetNoHalt()
        time.sleep(0.2)
        
    def startCW(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addr=ctypes.c_uint32(self.addrCMD)
        cmd=1 #run CW
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    pass #print("Run CW cmd write: OK")
                else:
                    prt.myPrint(globalData,"Chyba zapis startCW",tag="error")
        self.updateCmd()
        self.mcuRun()

    def stopCW(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addr=ctypes.c_uint32(self.addrCMD)
        cmd=2
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    pass #print("Run CW cmd write: OK")
                                        
        self.updateCmd()
        self.mcuRun()
        
    def saveRfTxOK(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addr=ctypes.c_uint32(self.addrCMD)
        cmd=6
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    pass #print("Run CW cmd write: OK")
                                        
        self.updateCmd()
        self.mcuRun()

    def shutDownMx(self,globalData):
        #if self.waitForBusy(globalData) == False:
        #    if self.busyFalse(globalData) == False:
        #        return False
        if self.mcuHalt() == False:
            return False
        addr=ctypes.c_uint32(self.addrCMD)
        cmd=12
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    time.sleep(0.1)
                    pass #print("Run CW cmd write: OK")
                                        
        self.updateCmd()
        self.mcuRun()
        time.sleep(0.1)

    def turnMxOn(self,globalData):
        #if self.waitForBusy(globalData) == False:
        #    if self.busyFalse(globalData) == False:
        #        return False
        #self.mcuHalt()
        addr=ctypes.c_uint32(self.addrCMD)
        cmd=13
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    pass #print("Run CW cmd write: OK")
                                        
        self.updateCmd()
        self.mcuRun()

    def setMxOnEeprom(self,globalData):
        if self.mcuHalt() == False:
            return False
        addr = ctypes.c_uint32(0x8080000)
        vers = 4
        if self.dll.JLINKARM_WriteU32(addr,ctypes.c_uint32(vers)) == 0:
            if self.dll.JLINKARM_ReadMemU32((addr),ctypes.c_uint32(1),ctypes.byref(readU32),null_ptr) >= 0:
                if (readU32.value) == vers:
                    #prt.myPrint(globalData,"MxTyp - Verze Fencee/Voss zapsana",tag="ok")#
                    pass
                else: 
                    prt.myPrint(globalData,"Chyba zapis zapnuti MX",tag="error")
        self.mcuRun()

    def setFreq(self,freq,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        frekvence=int(freq)
        if self.mcuHalt() == False:
            return False

        addr=ctypes.c_uint32(self.addrCMD)
        cmd=7 #set freq
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    pass # print("Run CW cmd write: OK")
                
                else:
                    prt.myPrint(globalData,"Chyba zapis CMD Set freq",tag="error")    

        addr=ctypes.c_uint32(self.addrSetFreq)
        
        if self.dll.JLINKARM_WriteU32(addr,ctypes.c_uint32(frekvence)) == 0:
            if self.dll.JLINKARM_ReadMemU32((addr),ctypes.c_uint32(1),ctypes.byref(readU32),null_ptr) >= 0:
                if (readU32.value) == frekvence:
                    pass #print("Run CW cmd write: OK")
                else:
                    prt.myPrint(globalData,"Chyba zapis frekvence",tag="error")     

        self.updateCmd()
        self.mcuRun()
        
    def prepareMeasure(self):
        if self.mcuHalt() == False:
            return False
        addr=ctypes.c_uint32(self.addrCMD)
        cmd=8 #enable pulse trigger
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    pass # OK
                else:
                    #prt.myPrint(globalData,"Chyba zapis Prepare pulse measure",tag="error")
                    pass

        self.updateCmd()
        self.mcuRun()
        time.sleep(0.1)
       
    def isPulseMeasDone(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addrPulseFlag=ctypes.c_uint32(self.addrPulseIsUPdated)
        dummy= self.dll.JLINKARM_ReadMemU8((addrPulseFlag),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr)
        self.mcuRun()
        
        if dummy >= 0:
            if (readU8.value) == True:
                return True

        return False

    def isRssiMeasDone(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addrRssiFlag=ctypes.c_uint32(self.addrRssiFlag)
        dummy= self.dll.JLINKARM_ReadMemU8((addrRssiFlag),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr)
        self.mcuRun()
        
        if dummy >= 0:
            if (readU8.value) == True:
                return True

        return False

    def readRssiVal(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addrRssiValue=ctypes.c_uint32(self.addrRssiValue)
        dummyVal= self.dll.JLINKARM_ReadMemU8((addrRssiValue),ctypes.c_uint32(1),ctypes.byref(readI8),null_ptr)
        self.mcuRun()
        
        if dummyVal >= 0:
            globalData.sqRXRssi = readI8.value
            return readI8.value

        return 0

    def readPulsemV(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addrPulsemV=ctypes.c_uint32(self.addrPulseInmV)
        read=ctypes.c_uint16()
        dummy= self.dll.JLINKARM_ReadMemU16((addrPulsemV),ctypes.c_uint32(2),ctypes.byref(read),null_ptr)
        self.mcuRun()
        time.sleep(0.1)
        if dummy >= 0:
            return (read.value)

    def readPulsekV(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addrPulsekV=ctypes.c_uint32(self.addrPulseInkV)
        read=ctypes.c_uint8()
        dummy= self.dll.JLINKARM_ReadMemU8((addrPulsekV),ctypes.c_uint32(1),ctypes.byref(read),null_ptr)
        self.mcuRun()
        time.sleep(0.1)
        if dummy >= 0:
            return (read.value)

    def readPulseCount(self,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addrPulseCount=ctypes.c_uint32(self.addrPulseCount)
        read=ctypes.c_uint8()
        dummy= self.dll.JLINKARM_ReadMemU8((addrPulseCount),ctypes.c_uint32(1),ctypes.byref(read),null_ptr)
        self.mcuRun()
        time.sleep(0.1)
        if dummy >= 0:
            return (read.value)

        return 0    

    def writePulseCount(self, count):
        if self.mcuHalt() == False:
            return False
        addrPulseCount=ctypes.c_uint32(self.addrPulseCount)
        if self.dll.JLINKARM_WriteU8(addrPulseCount,ctypes.c_uint8(count)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addrPulseCount),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == count:
                    pass # OK
                else:
                    #prt.myPrint(globalData,"Chyba zapis count set",tag="error")
                    pass

        self.updateCmd()
        self.mcuRun()
        #time.sleep(0.1)
       
    def writeCoeficients(self,coefA, intercept,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addr=ctypes.c_uint32(self.addrCMD)
        cmd=9 #write coef CMD
        if self.dll.JLINKARM_WriteU8(addr,ctypes.c_uint8(cmd)) == 0:
            if self.dll.JLINKARM_ReadMemU8((addr),ctypes.c_uint32(1),ctypes.byref(readU8),null_ptr) >= 0:
                if (readU8.value) == cmd:
                    pass # print("Run CW cmd write: OK")
                else:
                    prt.myPrint(globalData,"Chyba zapis Coeficientu",tag="error")

        #coeficienty
        tempCoef = int(coefA)
        tempIntercept = int(intercept)
        addr = ctypes.c_uint32(self.addrCoefA)
        if self.dll.JLINKARM_WriteU32(addr,ctypes.c_int32(tempCoef)) == 0:
             if self.dll.JLINKARM_ReadMemU32((addr),ctypes.c_uint32(1),ctypes.byref(readI32),null_ptr) >= 0:
                if (readI32.value) == tempCoef:
                    pass
                else: 
                    prt.myPrint(globalData,"Chyba zapis CoefA",tag="error")
        addr = ctypes.c_uint32(self.addrIntercept)
        if self.dll.JLINKARM_WriteU32(addr,ctypes.c_int32(tempIntercept)) == 0:
             if self.dll.JLINKARM_ReadMemU32((addr),ctypes.c_uint32(1),ctypes.byref(readI32),null_ptr) >= 0:
                if (readI32.value) == tempIntercept:
                    pass
                else: 
                    prt.myPrint(globalData,"Chyba zapis Intercept",tag="error")

        self.updateCmd()
        self.mcuRun()
        #time.sleep(0.01)

    
    def isHalted(self):
        temp=self.dll.JLINKARM_IsHalted()
        if temp == (1):
            return True
        elif  temp == 0:
            return False
        
        else:
            #self.connectToMcu(globalData)
            return False
        
    def mcuHalt(self):
        busyHalt=0
        self.dll.JLINKARM_Halt()
        while self.isHalted() != True:
            time.sleep(0.01)
            self.dll.JLINKARM_Halt()
            if busyHalt >= 20:
                return False
            busyHalt+=1

        return True
        #time.sleep(0.1)

    def mcuRun(self):
        if self.isHalted() == True:
            self.dll.JLINKARM_Go() #rozbehnuti po halte
            
        time.sleep(0.1)
        

    def updateCmd(self):
        time.sleep(0.02)
        write=ctypes.c_bool(1)   # set new pending message
        addrNewData=ctypes.c_uint32(self.startStructAddr)
        if self.dll.JLINKARM_WriteU8(addrNewData,write) == 0:
            #print("Cmd updated")
            pass

        self.invokeIRQ()

    def invokeIRQ(self):
        write=0x1
        addrSWIER=ctypes.c_uint32(0x40010410)   # vyvolani preruseni
        if self.dll.JLINKARM_WriteU32(addrSWIER,ctypes.c_uint32(write)) == 0:
            pass #print("IRQ generated")

        time.sleep(0.02)

    def isMcuBusy(self):
        if self.mcuHalt() == False:
            return "HaltError"
        addrPending=ctypes.c_uint32(self.addrPendingMsg)
        read=ctypes.c_bool()
        dummy= self.dll.JLINKARM_ReadMemU8((addrPending),ctypes.c_uint32(1),ctypes.byref(read),null_ptr)
        self.mcuRun()
        time.sleep(0.1)
        if dummy >= 0:
            return (read.value)

    def waitForBusy(self,globalData):
        busyCont=0
        while self.isMcuBusy() == True:
            prt.myPrint(globalData,"wait for MCU")
            time.sleep(0.1)
            if busyCont >= 10:
                prt.myPrint(globalData,"MCU is busy - restart APP",tag="warning")
                return False

            busyCont+=1

        return True

    def waitForReset(self):
        if self.mcuHalt() == False:
            return "HaltError"
        addrResetDone=ctypes.c_uint32(self.addrcanStartTest)
        read=ctypes.c_bool()
        dummy= self.dll.JLINKARM_ReadMemU8((addrResetDone),ctypes.c_uint32(1),ctypes.byref(read),null_ptr)
        self.mcuRun()
        time.sleep(0.1)
        if dummy >= 0:
            return (read.value)
    
    def setTX_EUI(self,txEui,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False

        if self.mcuHalt() == False:
            return False
        addr = ctypes.c_uint32(0x08080008)
        if self.dll.JLINKARM_WriteU32(addr,ctypes.c_uint32(txEui)) == 0:
             if self.dll.JLINKARM_ReadMemU32((addr),ctypes.c_uint32(1),ctypes.byref(readU32),null_ptr) >= 0:
                if (readU32.value) == txEui:
                    prt.myPrint(globalData,"MAC Adresa {0} zapsana".format(txEui),tag="ok")
                    pass
                else: 
                    prt.myPrint(globalData,"Chyba zapis MAC Adresy",tag="error")
        
        self.mcuRun()

    def setNameVerson(self,vers,globalData):
        if self.waitForBusy(globalData) == False:
            if self.busyFalse(globalData) == False:
                return False
        if self.mcuHalt() == False:
            return False
        addr = ctypes.c_uint32(0x8080048)
        if self.dll.JLINKARM_WriteU32(addr,ctypes.c_uint32(vers)) == 0:
            if self.dll.JLINKARM_ReadMemU32((addr),ctypes.c_uint32(1),ctypes.byref(readU32),null_ptr) >= 0:
                if (readU32.value) == vers:
                    prt.myPrint(globalData,"Typ - Verze Fencee/Voss zapsana",tag="ok")
                    pass
                else: 
                    prt.myPrint(globalData,"Chyba zapis: verze Fencee/Voss",tag="error")
        
        self.mcuRun()

    def checkIfProgrammed(self):
        if self.mcuHalt() == False:
            return False
        addr=ctypes.c_uint32(0x8080060)
        read=ctypes.c_uint32()
        #self.dll.JLINKARM_BeginDownload(0)  
        dummy= self.dll.JLINKARM_ReadMemU32((addr),ctypes.c_uint32(1),ctypes.byref(read),null_ptr)
        #self.dll.JLINKARM_EndDownload()  
        self.mcuRun()
        if dummy >= 0:
            if read.value == 0x29631:
                return True

        return False
        

    def downloadFile(self,globalData, file):
        #self.resetMcu()

        self.dll.JLINKARM_Reset()
        ret = ctypes.c_int(0)
        self.dll.JLINKARM_BeginDownload(0)  
        ret = self.dll.JLINK_EraseChip()
        self.dll.JLINKARM_EndDownload()       
       
        if ret < 0:
            prt.myPrint(globalData,"Nepovedlo se smazat MCU",tag = "error")  
            return False
        self.dll.JLINKARM_WriteMem.argtypes = [ctypes.c_uint32,ctypes.c_uint32, ctypes.c_void_p]
        
        
        addr=ctypes.c_uint32(0)#0/*0x08000000*/
        count=ctypes.c_uint32(file.__len__())
        if self.mcuHalt() == False:
            return False   
        self.dll.JLINKARM_BeginDownload(0)                               
        ret= self.dll.JLINKARM_WriteMem(addr,count,file)     
        self.dll.JLINKARM_EndDownload()       
        if ret < 0:
            prt.myPrint(globalData,"Nepovedlo se nahrat Bin file",tag = "error")
            return False
        
        else:
            prt.myPrint(globalData,"Monitor uspesne nahran",tag = "ok")

        self.resetMcu()
        time.sleep(.2)
        self.connectToMcu(globalData)
        self.resetMcu()
        self.mcuRun()

        return True
        
    def busyFalse(self,globalData):
        self.invokeIRQ()
        return self.waitForBusy(globalData)