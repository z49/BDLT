#!/usr/bin/env python3
import curses as crs
from curses import wrapper
import time
import npyscreen
import serial
import sys
import platform
import glob

import os
import traceback
import atexit

class cmenu(object):
	options = []
	pos = 0

	def __init__(self,options,title='Menu'):
		self.screen = crs.initscr()
		crs.start_color()
		crs.init_pair(1,crs.COLOR_RED,crs.COLOR_WHITE)
		crs.curs_set(0)
		self.screen.keypad(1)

		self.h = crs.color_pair(1)
		self.n = crs.A_NORMAL

		self.options = options
		self.title = title
		#atexit.register(self.cleanup)

	def cleanup(self):
		crs.doupdate()
		crs.reset_shell_mode()

	def upKey(self):
		if(self.pos == (len(self.options)-1)):
			self.pos = 0
		else:
			self.pos += 1

	def downKey(self):
		if (self.pos <= 0):
			self.pos = len(self.options)-1
		else:
			self.pos -= 1

	def display(self):
		screen = self.screen

		while True:
			screen.clear()
			screen.addstr(2,2,self.title,crs.A_STANDOUT|crs.A_BOLD)
			screen.addstr(4,2, "Select a serial port to connect to:",crs.A_BOLD)

			ckey = None
			fkey = None

			while ckey != ord('\n'):
				for n in range(0,len(self.options)):
					optn = self.options[n]
					if n!=self.pos:
						screen.addstr(5+n,4,str(n+1) + '\t' + self.options[n],self.n)
					else:
						screen.addstr(5+n,4,str(n+1) + '\t' + self.options[n],self.h)
				screen.refresh()
				ckey = screen.getch()
				if ckey == crs.KEY_UP:
					self.upKey()
				if ckey == crs.KEY_DOWN:
					self.downKey()
			ckey = 0
			#self.cleanup()
			if(self.pos>=0 and self.pos < len(self.options)):
				return self.options[self.pos]
			else:
				crs.flash()


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

def main(scr):
	# configure the serial connections (the parameters differs on the device you are connecting to)
	available = enum_serial_ports()
	if(len(available)==0):
		print('No serial ports available')
	menu = cmenu(enum_serial_ports())
	ser = serial.Serial(
	    port=menu.display(),
	    baudrate=9600,
	    parity=serial.PARITY_ODD,
	    stopbits=serial.STOPBITS_TWO,
	    bytesize=serial.EIGHTBITS,
	    timeout=0
	)
	#This only to make sure the port is open, the above declaration should open it
	if not ser.isOpen():
		ser.open()

	L = []

	q=-1
	scr.timeout(0)
	scr.clear()
	dim = scr.getmaxyx()
	#scr.addstr(dim[0]-1,dim[1]-len(str(dim))-1,str(dim))
	scr.keypad(1)
	scr.box()
	scr.noutrefresh()

	cli = crs.newwin(dim[0],int((dim[1]+1)/2)-1,0,0)
	clidim = cli.getmaxyx()
	cli.box()
	cli.noutrefresh()

	clin = cli.derwin(clidim[0]-2,clidim[1]-2,1,1)

	win = crs.newwin(int(dim[0]),int((dim[1]+1)/2),0,int((dim[1])/2))
	windim = win.getmaxyx()
	win.border(0)

	content = win.derwin(windim[0]-2,windim[1]-2,1,1)
	#content.idlok(1)
	content.setscrreg(0,content.getmaxyx()[0]-1)
	content.scrollok(1)
	y = content.getmaxyx()[0]-1
	pos = 1
	content.move(y,1)
	win.noutrefresh()

	data = ''

	while(q != ord('q')):
		crs.doupdate()

		data = ser.readline().decode()
		for ch in data:
			if ch == '\n':
				content.scroll()
				pos = 1
				data = data.replace('\n','')
				data = data.replace('\r','')
				continue
			content.addch(pos,y,ch)
			win.touchwin()
			win.noutrefresh()
			content.noutrefresh()
			pos += 1
			if pos >= content.getmaxyx()[1]-1:
				pos = 1
		data = ''

		#crs.napms(5)
		q = scr.getch()
		if(q == crs.KEY_RESIZE):
			dim = scr.getmaxyx()
			scr.clear()
			scr.box()
			scr.noutrefresh()
			win.resize(int(dim[0]),int((dim[1]+1)/2))
			win.mvwin(0,int((dim[1])/2))
			windim = win.getmaxyx()
			win.clear()
			win.box()
			win.noutrefresh()
		elif(q==crs.KEY_UP):
			if y > 0:
				y -= 1
				win.move(y,x)
		elif(q==crs.KEY_RIGHT):
			if x < windim[1]-1:
				x += 1
				win.move(y,x)
		elif(q==crs.KEY_DOWN):
			if y < windim[0]-1:
				y += 1
				win.move(y,x)
		elif(q==crs.KEY_LEFT):
			if x > 0:
				x -= 1
				win.move(y,x)
		elif(q!=-1):
			win.addch(chr(q))
		



if __name__ == "__main__":
	wrapper(main)