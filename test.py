#!/usr/bin/env python3

import time
import serial
import sys

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

while 1 :
    # get keyboard input
#    input = raw_input(">> ")
        # Python 3 users
    inp = input(">> ")
    if inp == 'exit':
        ser.close()
        exit()
    else:
        # send the character to the device
        # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
        inp += '\r\n'
        ser.write(inp.encode('ascii'))
        out = ''
        # let's wait one second before reading output (let's give device time to answer)
        #time.sleep(1)
        ser.timeout = 1
        while ser.inWaiting() > 0:
            out += ser.readline().decode('ascii')

        if out != '':
            print(out)
