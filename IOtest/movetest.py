# adapted from https://github.com/yurmor/mclpiezo/blob/master/mcl_piezo_lib.py
# 
from ctypes import cdll, c_int, c_uint, c_double
import atexit
from time import sleep
import time
import numpy as np

class Madstage():
    def __init__(self):
        # provide valid path to MicroDrive.dll. MicroDrive.h and MicroDrive.lib should also be in the same folder
        path_to_dll = './MicroDrive.dll'
        self.madlib = cdll.LoadLibrary(path_to_dll)
        self.handler = self.mcl_start()
        atexit.register(self.mcl_close)
    def mcl_start(self):
        """
        Requests control of a single Mad City Labs Microstage.
        Return Value:
            Returns a valid handle or returns 0 to indicate failure.
        """
        mcl_init_handle = self.madlib['MCL_InitHandle']
        
        mcl_init_handle.restype = c_int
        handler = mcl_init_handle()
        if(handler==0):
            print("MCL init error")
            return -1
        return  handler
        print("Success!")

    def mcl_close(self):
        """
        Releases control of all MCL stages controlled by this instance of the DLL.
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

    def mcl_move(self,axis,velocity,distance):
        """
        Move axis
        """     
        mcl_movecmd = self.madlib['MCL_MDMove']
        mcl_movecmd.restype = c_int
        return mcl_movecmd(c_uint(axis), c_double(velocity), c_double(distance), c_int(self.handler))



if __name__ == "__main__":
    
    # intialize
    stage = Madstage()
#   print(stage.mcl_serial()) # get serial number

    axis = 0
    velocity = 1 # mm/s
    distance = (1/1000)*50 # um values, converted to mm
    stage.mcl_move(axis,velocity,distance)