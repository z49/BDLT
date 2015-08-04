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
import platform
import glob

def enum_serial_ports():
    system_name = platform.system()
    if(system_name == "Windows"):
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append(i)
                s.close()
            except serial.SerialException:
                pass
        return available
    elif(system_name == "Darwin"):
        return glob.glob('/dev/tty.usb*')
    else:
        return glob.glob('/dev/ttyUSB*')

#This allows inline changing loaded config by filling
#in the input prompt with editable lines
def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()

#This class exists to store the device config read in through the serial port
#It is stored in an ordered dictionary
class Config:
    CONFIGSIZE = 44
    #fmt = 'Hh8h11sxbb5s5s'
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

print('Select serial port:')
options = enum_serial_ports()
for n in range(len(options)):
    print(str(n+1) + '  : ' + str(options[n]))
n = int(input('>> '))
ser = serial.Serial(
    port=options[n-1],
    baudrate=9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS
)

#This only to make sure the port is open, the above declaration should open it
if not ser.isOpen():
	ser.open()

print('Enter your commands below.')
helpstr = """Commands:
help\t (h): This
config\t(cf): Enters Config mode, nothing happens before this
read\t(rd): Read config from device
change\t(ch): Inline change loaded config
write\t(wt): Write loaded config back to device
commit\t (c): Commit changes to device, resetting it
listen\t(ls): Print out all data from device
empty\t (e): If serial buffers are full, run this to empty
exit\t (x): exits
Anything else will be sent straight to the device
"""
print(helpstr)
ser.timeout = 5
while 1 :
    inp = input(">> ")

    if inp == 'exit' or inp == 'x':
        ser.close()
        exit()

    elif inp == 'help' or inp == 'h':
        print(helpstr)
        continue

    elif inp == 'config' or inp == 'cf':
        ser.write('config\r'.encode())
        i = 10
        while ser.inWaiting() == 0 and i > 0:
            i = i - 1
            time.sleep(.1)

    elif inp == 'commit' or inp == 'c':
        ser.write('commit'.encode())
        i = 10
        while ser.inWaiting() == 0 and i > 0:
            i = i - 1
            time.sleep(.1)

    elif 'listen' in inp or inp == 'ls':
        print('Listening: ')
        while 1:
            data = ser.readline()
            print(data.decode('ascii'),end='')

#change read config, dont run before reading!
    elif inp == 'change' or inp == 'ch':
        newinp = rlinput('edit config:\n',str(ldcfg))
        for line in newinp.splitlines():
            ldcfg.cfg[line[:line.find('\t')]] = ast.literal_eval(line[line.index(':')+2:])

#Write config back to device, dont run before reading!
    elif inp == 'write' or inp == 'wt':
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
    elif inp == 'read' or inp == 'rd':
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

    elif inp == 'empty' or inp == 'e':
        while ser.inWaiting() > 0:
            while ser.inWaiting() > 0:
                byt = ser.read(1)
            time.sleep(.2)

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
#This waiting on the device occurs for every command
#which is why it is on the level of the while(1)
    out = ''
    i = 100
    while ser.inWaiting() > 0 and i > 0:
        while ser.inWaiting() > 0 and i > 0:
            byt = ser.read(1)
            out += byt.decode('ascii')
            i -= 1
        time.sleep(.2)

    if out != '':
        print(out,end='')
        if not out.endswith('\n'):
            print('')