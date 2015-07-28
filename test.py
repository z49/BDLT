#!/usr/bin/env python3

import time
import serial
import sys
import struct
import collections as cs
import binascii as b
import copy
import readline
import ast

def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()

class Config:
    CONFIGSIZE = 44
    fmt = 'Hh8h11sxbb5s5s'
    st = struct.Struct('Hh8h11sxbb5s5s')
    #keys = ['ints','pulse','A','G','B','L','M','S','V','na','file','mode','channel','txaddr','rxaddr']
    keys = ['flags','pulse','accel','gyro','baro','light','magneto','sync','voltage','/na','file','mode','channel','txaddr','rxaddr']

    def __init__(self,data):
        values = Config.st.unpack(data)
        self.cfg = cs.OrderedDict(zip(Config.keys,values))

    def __str__(self):
        pdict = copy.deepcopy(self.cfg)
        #pdict['txaddr'] = b.hexlify(pdict['txaddr'])
        #pdict['rxaddr'] = b.hexlify(pdict['rxaddr'])
        #pdict['flags'] = bin(pdict['flags'])[2:].zfill(8)
        #pdict['mode'] = bin(pdict['mode'])[2:].zfill(8)
        string = ''
        for k,v in pdict.items():
            string += k + '\t: ' + str(v) + '\n'
        return string

    def repack(self):
        return Config.st.pack(*self.cfg.values())



# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='/dev/ttyUSB'+sys.argv[1],
    baudrate=9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS
)

if not ser.isOpen():
	ser.open()

print('Enter your commands below.\r\nInsert "exit" to leave the application.')

ser.timeout = 5
while 1 :
    # get keyboard input
#    input = raw_input(">> ")
        # Python 3 users
    inp = input(">> ")

    if inp == 'x':
        ser.close()
        exit()

#change read config
    elif inp == 'change':
        newinp = rlinput('edit config:\n',str(ldcfg))
        for line in newinp.splitlines():
            ldcfg.cfg[line[:line.find('\t')]] = ast.literal_eval(line[line.index(':')+2:])

#Write config back to device
    elif inp == 'write':
        data = ldcfg.repack()
        ser.write('wt\r'.encode('ascii'))
        ser.write(data)
        data2 = ser.read(Config.CONFIGSIZE)
        if data2 == data:
            print('correct')
            ser.write(bytes([255]))
        else:
            print('nope')
            print(data2)
            ser.write(bytes([0]))
        print(ser.readline().decode(),end='')

#Read config from device
    elif inp == 'read':
        ser.write('rd\r'.encode('ascii'))
        out = ''
        i = 10
        while ser.inWaiting() == 0 and i > 0:
            i = i - 1
            time.sleep(.1)
        while(out != 'read\n#!bin\n'):
            out += ser.read(1).decode('ascii')
        byts = ser.read(Config.CONFIGSIZE)
        while(ser.inWaiting()):
            ser.read(1)
        ldcfg = Config(byts)
        print(ldcfg)

#Send command straight to device.  Will later be deprecated, 
#as all will be handled by client
    else:
        inp += '\r'
        ser.write(inp.encode('ascii'))
        out = ''
        # let's wait one second before reading output (let's give device time to answer)
        #time.sleep(1)
        i = 10
        while ser.inWaiting() == 0 and i > 0:
            i = i - 1
            time.sleep(.1)
        while ser.inWaiting() > 0:
            while ser.inWaiting() > 0:
                byt = ser.read(1)
                out += byt.decode('ascii')
            time.sleep(.1)
        if out != '':
            print(out,end='')
