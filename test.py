#!/usr/bin/python

import time
import serial
import sys
import binascii as b
import struct

class BinaryReaderEOFException(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return 'Not enough bytes to satisfy read request'

def read_data(data):
    fmt = 'H h 8h 11s x b b 5s 5s'
    size = struct.calcsize(fmt)
    #if size > len(data):
    #    raise BinaryReaderEOFException
    return struct.unpack(fmt,data)

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
    elif inp == 'change':
        print('Changing struct...')
        data[11] = 1
        data[0] = 2
        print(data)
    elif inp == 'write':
        ser.write('wt\r'.encode('ascii'));
        ser.write(struct.pack('H h 8h 11s x b b 5s 5s',*data))
        data2 = list(read_data(ser.read(44)))
        if data2 == data:
            print('correct')
            ser.write(bytes([255]))
        else:
            print('nope')
            print(data2)
            ser.write(bytes([0]))
        print(ser.readline().decode(),end='')
    else:
        # send the character to the device
        # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
        inp += '\r\n'
        ser.write(inp.encode('ascii'))
        out = ''
        byts = b.hexlify(bytes([]))
        # let's wait one second before reading output (let's give device time to answer)
        #time.sleep(1)
        binbytes = 0
        i = 10
        while ser.inWaiting() == 0 and i > 0:
            i = i - 1
            time.sleep(.1)
        while ser.inWaiting() > 0:
            #print('out: ',end='')
            #print(out.encode())
            #print('bin: ',end='')
            #print(binbytes)
            byt = ser.read(1)
            if out == 'read\n#!bin\n':
                binbytes = 44
                out = 'binary:'
            try:
                if binbytes > 0:
                    binbytes = binbytes - 1
                    byts += b.hexlify(byt)
                else:
                    out += byt.decode('ascii')
            except:
                print('ER')
                #print(binbytes)
                #print(byt)
                #print(byts)

        if out != '':
            print(out,end='')
        if byts != b.hexlify(bytes([])):
            data = read_data(b.unhexlify(byts))
            data = list(data)
            print(data)
