import time
import serial
import numpy as np
import cv2
from decoder import Decoder

class Radar:
    def __init__(self, configPort, dataPort):
        self.configSerial =  serial.Serial(port=configPort,
                            baudrate=115200,
                            timeout=1)
        self.dataSerial = serial.Serial(port=dataPort,
                            baudrate=921600,
                            timeout=1)
        
        self.dataChunks = []
        self.buffer = bytearray()

        self.storedData = []
        self.active = True
    
    def send_cmd_file(self, cmdFile):
        with open(cmdFile, "r") as file:
            for line in file:
                if not line.strip():
                    continue
                
                self.send_cmd(line)

    def send_cmd(self, cmd: str):
        cmd = cmd.strip().encode("utf-8") + b"\n"
        print(cmd)

        self.configSerial.write(cmd)
        testTime = time.perf_counter()

        while True:
            if self.configSerial.readline().strip() == b"Done":
                print("Done")
                break

            if time.perf_counter() > testTime + 0.2:
                self.configSerial.write(cmd)
                testTime = time.perf_counter()

    def start(self):
        self.send_cmd("sensorStart")
        print("RADAR STARTED")

    def stop(self):
        self.send_cmd("sensorStop")
        print("RADAR STOPPED")

    def find_msg_start(self, data):
        magicWord = [2, 1, 4, 3, 6, 5, 8, 7]
        if len(data) < len(magicWord):
            return -1
        else:
            for i in range(len(data) -len(magicWord) + 1):
                if data[i:i+len(magicWord)] == magicWord:
                    return i
            return -1

    def read_data(self):
        data = self.dataSerial.read(4096)
        count = 0
        magicWord = bytes([2,1,4,3,6,5,8,7])
        for i in range(len(data) - len(magicWord) + 1):
            if data[i:i+len(magicWord)] == magicWord:
                count+=1
        
        chunks = data.split(magicWord)

        if len(chunks[0]):
            self.buffer.extend(chunks[0])
            self.dataChunks.append(self.buffer)

        for chunk in chunks[1:-1]:
            self.dataChunks.append(chunk)
        
        self.buffer = bytearray(chunks[-1])

    def run(self):
        self.start()

        self.storedData = []
        self.active = True

        decoder = Decoder()
        while self.active:
            self.read_data()
            for chunk in self.dataChunks:
                tlvDict = {}
                chunkData = [ int(np.frombuffer(chunk[0:4], dtype=np.uint32)[0]),    #Version
                              int(np.frombuffer(chunk[4:8], dtype=np.uint32)[0]),    #Total Packet Length
                              int(np.frombuffer(chunk[8:12], dtype=np.uint32)[0]),   #Platform
                              int(np.frombuffer(chunk[12:16], dtype=np.uint32)[0]),  #Frame Number
                              int(np.frombuffer(chunk[16:20], dtype=np.uint32)[0]),  #Time in CPU Cycles
                              int(np.frombuffer(chunk[20:24], dtype=np.uint32)[0]),  #Number of Detected Objects
                              int(np.frombuffer(chunk[24:28], dtype=np.uint32)[0])]  #Number of TLVs
                if chunkData[-1] == 0:
                    pass
                else:
                    pos = 28
                    for i in range(chunkData[-1]):
                        tlvType = np.frombuffer(chunk[pos:pos+4], dtype=np.uint32)[0]
                        tlvLength = np.frombuffer(chunk[pos+4:pos+8], dtype=np.uint32)[0]
                        tlvValue = chunk[pos+8:pos+8+tlvLength]

                        pos = pos + 8 + tlvLength

                        tlvValue = decoder.tlv_decode(tlvType,tlvValue)

                        tlvDict[int(tlvType)] = tlvValue
                
                for i in range(1,7):
                    if i in tlvDict:
                        chunkData.append(tlvDict[i])
                    else:
                        chunkData.append(None)
                self.storedData.append(chunkData)
            self.dataChunks = []
        self.stop()
                


def serial_init(port, baudrate):
    serialPort = serial.Serial(port=port,
                               baudrate=baudrate,
                               timeout=1)
    return serialPort



def main():

    radar = Radar(configPort="COM5", dataPort="COM4")
    radar.send_cmd_file(cmdFile="commands.txt")
    radar.run()

if __name__ == "__main__":
    main()