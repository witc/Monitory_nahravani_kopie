import pyvisa

class HMC_8043Class:

    def __init__(self):
        try:
            rm = pyvisa.ResourceManager()
            self.powerSup = rm.open_resource('TCPIP::192.168.1.137::INSTR')
        except Exception as ex:
            print('Error initializing the instrument session:\n' + ex.args[0])
            exit()
    
        print("Device found: " +self.powerSup.query('*IDN?'))
    
        self.powerSup.write("*CLS")
        self.powerSup.write("*RST")
        print(" - - - - Reset OK - - - - ")
    
    def setChannel(self, chan):
        self.powerSup.write("INST OUT"+str(chan))

    def setVoltage(self, chan, voltage):
        self.setChannel(chan)
        self.powerSup.write("VOLT "+str(voltage))

    def setCurrentmA(self, chan, current):
        self.setChannel(chan)
        self.powerSup.write("CURR "+str(current)+"mA")
    
    def setChanState(self, chan, state):
        self.setChannel(chan)
        self.powerSup.write("OUTP "+(state))
