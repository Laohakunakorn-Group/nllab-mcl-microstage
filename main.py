# adapted from https://github.com/yurmor/mclpiezo/blob/master/mcl_piezo_lib.py
# 
# from ctypes import cdll, c_int, c_uint, c_double
import atexit
from time import sleep
import time
import numpy as np

class Madpiezo():
	def __init__(self):
		# provide valid path to Madlib.dll. Madlib.h and Madlib.lib should also be in the same folder
		path_to_dll = './MicroDrive.dll'
		self.madlib = cdll.LoadLibrary(path_to_dll)
		self.handler = self.mcl_start()
		atexit.register(self.mcl_close)
	def mcl_start(self):
		"""
		Requests control of a single Mad City Labs Nano-Drive.
		Return Value:
			Returns a valid handle or returns 0 to indicate failure.
		"""
		mcl_init_handle = self.madlib['MCL_InitHandle']
		
		mcl_init_handle.restype = c_int
		handler = mcl_init_handle()
		if(handler==0):
			print("MCL init error")
			return -1
		return 	handler
		print("Success!")

	def mcl_close(self):
		"""
		Releases control of all Nano-Drives controlled by this instance of the DLL.
		"""
		mcl_release_all = self.madlib['MCL_ReleaseAllHandles']
		mcl_release_all()

	def mcl_serial(self):
		"""
		Get serial number
		"""
		mcl_serial_no = self.madlib['MCL_GetSerialNumber']
		mcl_serial_no.restype = c_int
		return  mcl_serial_no(c_int(self.handler))

if __name__ == "__main__":
	
	#simple scanning example
	
	# intialize the piezo
	piezo = Madpiezo()
	print(piezo.mcl_serial())