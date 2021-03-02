import numpy as np
import pandas as pd
import os
import socket
import MyGuiConsole as prt

class ESP32Zatez:
    def connect(self,ipAdr):
        try:
            self.ip = ipAdr#"192.168.137.22"
            self.port = 5025
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.ip, self.port))
            self.client.settimeout(2000.0)
            self.setHome()
            return True

        except Exception as ex:
            #print('Could not connec to ESP32 (zatez):\n')
            return False

        #print("ESP32 connected") 

    def disconnect(self):
        pass
        # try:
        #     socket.socket.shutdown(socket.SHUT_RDWR)
        #     return True
        # except Exception as ex:
        #     #print('Could not connec to ESP32 (zatez):\n')
        #     return False

    def setHome(self):
        #msg="home"
        #msg+="\n"
        #self.client.send(msg.encode("utf-8"))
        pass

    def setLoadTrig(self, load,globalData):
        self.connect(self.ip)

        msg = "TRIG:"
        msg+=str(load)
        msg+="\n"
        self.client.send(msg.encode("utf-8"))

        response = self.client.recv(4096)
        print("Load set to: {}".format(response.decode("utf-8")))
        length = len(response)
        res = response[0:(length-2)]
        prt.myPrint(globalData,"Load set to: {}".format(res.decode("utf-8"))) #
        
        self.disconnect()
        return response.decode("utf-8")

    def setLoadNoTrig(self, load,globalData):
        self.connect(self.ip)
        msg=str(load)
        msg+="\n"
        self.client.send(msg.encode("utf-8"))

        response = self.client.recv(4096)
        print("Load set to: {}".format(response.decode("utf-8")))
        length = len(response)
        res = response[0:(length-2)]
        prt.myPrint(globalData,"Load set to: {}".format(res.decode("utf-8"))) #

        self.disconnect()
        return response.decode("utf-8")