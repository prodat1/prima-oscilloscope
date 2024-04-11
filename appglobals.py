'''
GLOBAL VARIABLE DEFINITIONS
'''
import threading
import enum
from kivy.app import App

import appcfg as cfg
import appcfg_gui as guicfg
import appdef as appdef

from enum import auto

#############################
#global variable definition # -> we want everything in a single memory object (not a module declaration)
#############################
CFG_AUTOLOADAPP = True #determine default kivy style

class MSGTYPE(enum.Enum):
    ERROR = -1
    WARNING = 0
    INFO = 1
    
class MSGACTION(enum.Enum):
    USERINFO = 1
    APPISRUNNING = 100

class Globals():
    def __init__(self, autoappload=CFG_AUTOLOADAPP):
        #general variables for configuration
        ####################################
        self.CFG = cfg.CFG #central application configuration - used in app and all modules if required
        self.GUI = guicfg.get_cfg(guicfg.DEF_STD) #gui application configuration
        self.GUI_KVSTR_GLOB = guicfg.get_kvstr(guicfg.DEF_STD) #@TODO: is this needed for everyone?
        #self.USER = appdef.User() #current user 
        self.DB = None
        self.USER_LOGGER = None 
        self.SYSTEM_LOGGER = None
        self.VEHICLE = None # vehicle the user operates on , None if not set 
        self.MEASUREMENT = None #current measurement the user is doing, None if not set (means no measurement yet)
        
        # Global working variables -> lowercase
        #######################################
        self.system = None #measurement system handle (the measurement system currently active)
        self.sensors = None #sensor list handle (part of the measurement system)
        self.channels = None #measurement channel handle (part of the measurement system)

        # Global working variables for threading
        ########################################
        self.th_active = False #active in case of running threads, all threads listen to this flag
        self.th_threads = [] #handles to all threads [0 .. control&aggregator, 1..N = collector threads]
        

        #system user messages (important with reaction
        self.msgs = []

        # device lists
        self.device_list = []
        self.device_index_list = []
        self.sensor_list = []
        self.basestation_list = []
        self.comport_list = []

        if autoappload: self = self.app_load()

    def msgs_len(self):
        ''' returns the number of saved messages '''
        try:
            self.lock_msgs.acquire()
            return len(self.msgs)
        finally:
            self.lock_msgs.release()   
    
    def msgs_write(self, type, action, msg):
        ''' simple global messaging system, write msgs '''
        try:
            self.lock_msgs.acquire()
            self.msgs.append( (type, action, msg) )
        except:
            raise
        finally:
            self.lock_msgs.release()

    def msgs_read(self, clear=True):
        ''' simple global messaging system, read last msgs '''
        try:
            self.lock_msgs.acquire()
            if clear: return(self.msgs.pop(0)) #returns the oldest message
            else: raise AssertionError("to implement - are multiple readers, really needed?")
        except:
            raise
        finally:
            self.lock_msgs.release()
            
    def app_load(self):
        ''' load global data object from app'''
        app = App.get_running_app() #handled by kivy
        try:
            if app.GLOB == None:
                return None
            else:
                self = app.GLOB
                return self
        except:
            return None
    
    def read(self):
        ''' reading global object parameters -> provide an instance'''
        return self
    
    def write(self):
        raise AssertionError("needs implementation")
    
    def mdata(self, mdata=None):
        ''' update measurement data, thread safe style '''
        if mdata != None:
            self.lock_mdata.acquire()
            self.mdata = mdata
            self.lock_mdata.release()
        return mdata
    
    #@TODO: other data structure
    #def vehicle(self, vehicledata=None):

#provide a single data object to handle globals in modules (if needed)
GLOB = Globals()

def read(): 
    #read global configuration object
    return GLOB

def write(globvar):
    #write/set global configuration object
    global GLOB
    GLOB = globvar

