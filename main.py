# adapted from https://github.com/yurmor/mclpiezo/blob/master/mcl_piezo_lib.py
# GUI control of MadCityLabs Microstage
# N Laohakunakorn, University of Edinburgh, 2021

from ctypes import cdll, c_int, c_uint, c_double
import atexit
from time import sleep
import time
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import traceback, sys


# MCL functions

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
        print("Success!")
        return  handler


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


# GUI
class WorkerSignals(QObject):
    '''defines signals from running worker thread
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class Worker(QRunnable):
    '''worker thread
    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        # Add the callback to our kwargs
        self.kwargs['results'] = self.signals.result

    @pyqtSlot()
    def run(self):
        '''initialise runner function with passed args, kwargs
        '''
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class MainWindow(QMainWindow):

    def __init__(self, stage, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)


        self.setWindowTitle("MCL Microstage Controller")
        self.setFixedSize(300,300)

        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)

        buttons = {'-X': (1, 0),
                   '+Y': (0, 1),
                   '-Y': (2, 1),
                   '+X': (1, 2)
                  }

        self._createButtons(buttons)
        self._createInputField()
        self._createVfield()
        self._createDfield()

        self.show()
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.resetButtonsState()

    # Auxilary functions


    def _createInputField(self):
        self.horizonLayout = QHBoxLayout()
        self.label = QLabel("Input:")
        self.label.setFixedWidth(120)
        self.k = QLineEdit()
#        self.k.setText(self.A)
        self.horizonLayout.addWidget(self.label)
        self.horizonLayout.addWidget(self.k)
        self.generalLayout.addLayout(self.horizonLayout)

    def _createVfield(self):
        self.horizonLayout = QHBoxLayout()
        self.label = QLabel("Velocity (mm/s):")
        self.label.setFixedWidth(120)
        self.V = QLineEdit()
        self.V.setText('1')
        self.horizonLayout.addWidget(self.label)
        self.horizonLayout.addWidget(self.V)
        self.generalLayout.addLayout(self.horizonLayout)

    def _createDfield(self):
        self.horizonLayout = QHBoxLayout()
        self.label = QLabel("Distance (um):")
        self.label.setFixedWidth(120)
        self.D = QLineEdit()
        self.D.setText('50')
        self.horizonLayout.addWidget(self.label)
        self.horizonLayout.addWidget(self.D)
        self.generalLayout.addLayout(self.horizonLayout)


    def _createButtons(self,buttons):
        self.buttons = {}
        buttonsLayout = QGridLayout()

        for btnText, pos in buttons.items():
            self.buttons[btnText] = QPushButton(btnText)
            self.buttons[btnText].setFixedSize(60,60)
            self.buttons[btnText].setCheckable(True)
            self.buttons[btnText].clicked.connect(self.getButtonsState) # when button clicked, get state
            buttonsLayout.addWidget(self.buttons[btnText], pos[0], pos[1])
        self.generalLayout.addLayout(buttonsLayout)

    # slots

    def getButtonsState(self):
        # read state of buttons and trigger actions
        state = []
        for btnText, pos in self.buttons.items():
            state.append(int(self.buttons[btnText].isChecked()))
        binstring = ''.join(['1' if x else '0' for x in state])
        self.k.setText(binstring)

        # Write command
        INPUT = binstring 
        self.move(INPUT)
        self.resetButtonsState() # reset all buttons
        
    def resetButtonsState(self):
        for btnText, pos in self.buttons.items():
                self.buttons[btnText].setChecked(False)

    def move(self,INPUT):
#       -X = 1000 -> +M1
#       +X = 0001 -> -M1
#       -Y = 0010 -> +M2
#       +Y = 0100 -> -M2

        if INPUT == '1000':
            axis = 1
            distance = float(self.D.text())*(1/1000) # convert to mm
        elif INPUT == '0001':
            axis = 1
            distance = -float(self.D.text())*(1/1000) # convert to mm
        elif INPUT == '0100':
            axis = 2
            distance = -float(self.D.text())*(1/1000) # convert to mm
        elif INPUT == '0010':
            axis = 2
            distance = float(self.D.text())*(1/1000) # convert to mm
        velocity = float(self.V.text())       
        stage.mcl_move(axis,velocity,distance)
        print('Move', axis, velocity, distance)


def handle_exit():
#   carry out exit functions here
    print('Exiting')

def main(stage):

#   Exit items here
    atexit.register(handle_exit)

    # here is the app running
    app = QApplication(sys.argv)

    window = MainWindow(stage)
    window.show()

    sys.exit(app.exec_())


if __name__=='__main__':

    #   Startup items here
    print('Starting MCL Microstage')
    # intialize
    stage = Madstage()
    print(stage.mcl_serial()) # get serial number

    main(stage)
