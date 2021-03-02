import winsound
import numpy as np
import binascii
import serial
from serial.tools import list_ports


class USBSerialLink:

    def openUSBRfLink(self, serNumber = 1):
        comlist = list(list_ports.comports())
        PossbileComs=[]
        count=0
        for element in comlist:
            if 'Silicon Labs' in element.manufacturer:
                if serNumber == 2:
                    if '0002' in element.serial_number:
                        # save possible ports
                        PossbileComs.append(element.device)
                elif serNumber == 3:
                        PossbileComs.append(element.device)
                else:
                    # save possible ports
                    PossbileComs.append(element.device)

                count+=1          
               
        if count == 0:
            print("No Com ports!: " + str(PossbileComs))
            return "False"
        else:           
            self.ser = serial.Serial(PossbileComs[0])
            serial.Serial()
            try:
                self.ser
            except NameError:
                return "True"
            else:
                self.ser.close()  # close serial port    

            self.ser=serial.Serial(PossbileComs[0],9600,timeout=0.5)
            print(str(self.ser)+ " is Open")
            print("USART Baud: " + "9600")

            return "Open"

    def URSBRFLinkFlushBuff(self):
        self.ser.reset_input_buffer()#flushInput()

    def rxUSBRFLink(self,timeout): 
        #self.ser(write_timeout=timeout)
        #self.ser.write_timeout(timeout)

        y_raw=[]
        #self.ser.flushInput()
        syncWord = []
        count = 0
        while True:
            snc = self.ser.read(1)
            if snc:
                count+=1
                syncWord.append(ord(snc))

                if (count>=5):
                    if syncWord[count-5] == 0xaa and syncWord[count-4] == 0xbb and syncWord[count-3] == 0xcc and syncWord[count-2] == 0xdd and syncWord[count-1] == 10:
                        break
            #else:
            #    return "timeout",0,0,0              
            #nize zakomentvane ok pro MX_Flasher
            elif count != 0:
                return "timeout",0,0,0
                           
        
        #self.ser.read_until(bytearray(b'\xaa\xbb\xcc\xdd\n'))

        rxCmd =self.ser.read(1)
        if len(rxCmd) == 0:
            print("uart Timeout")
            return "timeout",0,0,0

        rxCmd = int.from_bytes(rxCmd,byteorder='little') 
        #precti velikost nasledujicoho bufferu
        bufferSize=self.ser.read(1)
        bufferSize=int.from_bytes(bufferSize,byteorder='little')
               
        #print("Buffer size is: {}".format(bufferSize))
        #cti po bytech
        for i in range(bufferSize):
            znak = self.ser.read(1)
            if znak:
                y_raw.append(ord(znak))
            else: return 0,0,0,0
         
        #self.ser.flushInput()

        #kontrola CRC
        CRC=self.crc16(bytearray(y_raw),0,bufferSize-2)
        Rxcrc1=int.from_bytes(y_raw[bufferSize-2:bufferSize],byteorder='little')
        
        if CRC==Rxcrc1:      
            if rxCmd ==  1:    
                MX_EUI = int.from_bytes(y_raw[:8],byteorder='little')
                RndSessionKey=int.from_bytes(y_raw[8:12],byteorder='little')
                Cmd=int.from_bytes(y_raw[12:13],byteorder='little')
                PulseADCmV=int.from_bytes(y_raw[13:15],byteorder='little')

                #po precteni spalte
                del y_raw[:]

                return MX_EUI, RndSessionKey, Cmd, PulseADCmV
            
            elif rxCmd == 2:
                #po precteni spalte
                del y_raw[:]
                return 0x29, "button", "button", "button"
            
            else:
                del y_raw[:]
                return 0, 0, 0, 0
        else:
            #po precteni spalte
            del y_raw[:]
            
            print("Wrong CRC")
            self.ser.flushInput()
            return 0, 0, 0, 0

    def LEDBlinking(self,color,globalData):
        Cmd = 9
        if color == "green":
            clr = 1

        elif color == "red":
            clr = 2
        RFU=0
        serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'big'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
            globalData.ZERO_PADING.to_bytes(7,byteorder = 'big'), bytearray(4), Cmd.to_bytes(1,byteorder='big'),clr.to_bytes(2,byteorder='big'),clr.to_bytes(2,byteorder='big'),RFU.to_bytes(1,byteorder='big')]
        
        self.txUSBRFLink(serialPacket)

    def LEDOn(self,color,globalData):
        Cmd = 10
        if color == "green":
            clr = 1

        elif color == "red":
            clr = 2
        RFU=0
        serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'big'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
            globalData.ZERO_PADING.to_bytes(7,byteorder = 'big'), bytearray(4), Cmd.to_bytes(1,byteorder='big'),clr.to_bytes(2,byteorder='big'),clr.to_bytes(2,byteorder='big'),RFU.to_bytes(1,byteorder='big')]
        
        self.txUSBRFLink(serialPacket)        

    def LEDOff(self,color,globalData):
            Cmd = 11
            if color == "green":
                clr = 1

            elif color == "red":
                clr = 2
            RFU=0
            serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'big'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
                globalData.ZERO_PADING.to_bytes(7,byteorder = 'big'), bytearray(4), Cmd.to_bytes(1,byteorder='big'),clr.to_bytes(2,byteorder='big'),clr.to_bytes(2,byteorder='big'),RFU.to_bytes(1,byteorder='big')]
            
            self.txUSBRFLink(serialPacket)       

    def switchSWDOff(self,globalData):
        CmdSWD = 8
        SWDstate = 1
        RFU=0
        serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'big'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
            globalData.ZERO_PADING.to_bytes(7,byteorder = 'big'), bytearray(4), CmdSWD.to_bytes(1,byteorder='big'),SWDstate.to_bytes(2,byteorder='big'),SWDstate.to_bytes(2,byteorder='big'),RFU.to_bytes(1,byteorder='big')]
        
        self.txUSBRFLink(serialPacket)

    def switchSWDOn(self,globalData):
        CmdSWD = 8
        SWDstate = 2
        RFU=0
        serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'big'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
            globalData.ZERO_PADING.to_bytes(7,byteorder = 'big'), bytearray(4), CmdSWD.to_bytes(1,byteorder='big'),SWDstate.to_bytes(2,byteorder='big'),SWDstate.to_bytes(2,byteorder='big'),RFU.to_bytes(1,byteorder='big')]
        
        self.txUSBRFLink(serialPacket)

    def setRfSwitch(self,switch,globalData):
        CMD_RfSwitch = 6
        switch
        RFU=0
        serialPacket=[globalData.MAC_HEADER.to_bytes(1,byteorder = 'big'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'), globalData.USB_STATIC_MAC.to_bytes(8,byteorder = 'little'),
        globalData.ZERO_PADING.to_bytes(7,byteorder = 'big'), bytearray(4), CMD_RfSwitch.to_bytes(1,byteorder='big'),switch.to_bytes(2,byteorder='big'),
        switch.to_bytes(2,byteorder='big'),RFU.to_bytes(1,byteorder='big')]
        
        self.txUSBRFLink(serialPacket)


    def txUSBRFLink(self, data):
        bytePacket = bytearray()
        for i in data:
            bytePacket+=i
            
        crc=self.crc16(bytePacket,0,len(bytePacket))
        bytePacket+=crc.to_bytes(2,'little')
        #print(binascii.hexlify(bytePacket))

        self.ser.write(bytePacket)#bytePacket
    
    def crc16(self, data : bytearray, offset , length):
        if data is None or offset < 0 or offset > len(data)- 1 and offset+length > len(data):
            return 0
        crc = 0xFFFF
        for i in range(0, length):
            crc ^= data[offset + i] #<< 8
            for j in range(0,8):
                if (crc & 0x1) > 0:
                    crc =(crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return crc & 0xFFFF

