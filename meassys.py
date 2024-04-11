'''
XKM measurement system .. central definition for sensors and the measurement system 
(PRODAT BKM Wireless, PRODATM BKM Cable, PRODAT RKM Wireless, PRODAT, ADAM SensorXKM Types  

Created on 27.09.2023

@author: PRODAT

@TODO:
saving measurement system configuration, should we add an additional 0 when automatically saving (max. 99 systems), means sorted
'''
import enum
import collections
import configparser
import os
import re
import pytest
import threading
import time
import numpy
import functools
import sys
import struct
import queue

from dataclasses import dataclass

#from core import flexmsg #@everyone -> comment if this makes problems

import dbg
import appdef
import appcfg
import measzeromon
import meas_sensor as sensor
#import flexmsg_status_msg_sensor as msg_sensor_status


#except:
#    print("ERROR (TODO): cmdset import -> module dependencies", sys.stderr)      
#debugging support
DBG_OUT = False
 
DEF_SYSTYPE_DEFAULT = appdef.DEF_SYSTEMTYPES.XKM #system type identifier -> default measurement system to use
DEF_INITYPE_SYS = "syscfg" #identifier token for system configuration files (*.ini) in the file system
DEF_SYSINDEX_DEFAULT = 0
#INIFILE DEFINITIONS FOR MEASUREMENT SYSTEM CFG
DEFINI_FILEBASE = DEF_INITYPE_SYS
DEFINI_FILEENDING = ".ini"
DEFINI_FILENAME = DEFINI_FILEBASE+DEFINI_FILEENDING #base filename -> will be extended with system index specifier
DEFINI_TEMPLATE = "syskonst_template_v20.ini" #see templates work in progress
DEFINI_SEC_VER = 'version'
DEFINI_SEC_SYS = 'system'
DEFINI_SEC_SYSPARASTR = '' #appdef.DEF_PYOBJ_ID #parameter identifier for obj and ini file

def load_systems_from_directory(p_dir):
    '''
    function loads measurement system configurations from a specified directory and returns this configurations as a list
    '''
    p_dir = os.path.abspath(p_dir)
    if DBG_OUT: print("msys:load from dir:", p_dir)
    syslist = []
    for afile in os.listdir(p_dir):
        print(afile, DEFINI_FILEBASE, DEFINI_FILEENDING)
        if (DEFINI_FILEBASE in afile) and (DEFINI_FILEENDING in afile):
            p = os.path.join(p_dir, afile)
            sys = MeasurementSystemXKM()
            syslist.append(sys)
    return syslist

class DataFieldsSystem():
    '''
    Datafields Functionality (easier to see, and to process)
    '''
    def __init__(self):
        #system idenfication information
        self.df_systype_f = "SYS-TYP"
        self.df_systype_v = "NOTSET" #measurement system type -> default is XKM
        self.df_nameapp_f = "SYS-NAME"
        self.df_nameapp_v = "NOTSET"
        self.df_namecust_f = "SYS-CUST" 
        self.df_namecust_v = "NOTSET CUSTOMER NAME" #measurement system customer name
        self.df_idpro_f = "ID-PRODAT"
        self.df_idpro_v = "999999" #PRODAT measurement system ID string
        self.df_idcust_f = "ID-CUST"
        self.df_idcust_v = "ABCDEF" #system id of measurement system customer 
        self.df_datebuild_f = "DATE-BUILD"
        self.df_datebuild_v = "31.12.1990" #build date of the measurement system
        self.df_datecali_f = "DATE-SYSCALI"
        self.df_datecali_v = "01.01.1990"
        self.df_lang_f = 'SYS-LANG:'
        self.df_lang_v = 'en' #system language specifier #@TODO: need definitions

        # generate a df dict for easier (and faster) lookup by users in the future (this could be generated)
        # maps -> _v -> _f
        self.DATAFIELDS = {}
        #for item in sorted(dir(self),reverse=True):
        #    #values shall rule the dictionary. exceptions are handled by programmer -> must define always both
        #    if appdef.DEF_PYOBJ_ID in item and appdef.DEF_PYOBJ_FIELD in item:
        #        self.DATAFIELDS[getattr(self,item)] = getattr(self,item.replace(appdef.DEF_PYOBJ_FIELD,appdef.DEF_PYOBJ_VAL))

class MeasurementSystemXKM(DataFieldsSystem):
    '''
    measurement system abstraction -> our abstraction for sensors, measurement channels, measurement system actions and so on.
    --> we support different measurement system abstractions 
    '''    
    CFG_RX_TOREAD = 120 #bytes to read from serial port per iteration
    CFG_TX_REPEAT = 1 #number of repeats when sending messages (just go with 1) -> should be configurable
    CFG_TX_SEQ = 0 #if an other value, we will get a serial ack [can use this behaviour to check basestation serial rx/tx]
    
    def __init__(self, sensors=[], comdevs=[], gateways=[],
                 sysindex=DEF_SYSINDEX_DEFAULT, systemtype=DEF_SYSTYPE_DEFAULT, dir_zeromon=None):
        ''' 
        
            Measurement System Abstraction which supports:
                - comdevs .. communication devices -> these are polled via collector threads use a list
                - sensors .. sensors we maintain -> data from comdevs is distributed into the sensors use  a list 
                - gateways .. a gateway abstraction
            
            @TODO: do we really need gateways -> do we support gateways in addition to comdevs, are there multiple muliple gateways possible?
            
            --> we receive an ordererd list of sensor objects for the initialiatzion
            p_dir_zeromon = zeromonitor directory
        '''
        super().__init__() #initialize parent class -> DATAFIELDS Functionality
        
        #holds system index in a list
        self.sysindex = sysindex # overall measurement system index, when maintaining configuration of multiple system / -1 = not set        
        
        #set some of the df fields automatically
        self.df_systype_v = systemtype      
        self.df_nameapp_v = "SYS" + str(sysindex+1)
        
        #system inicfgp (ini config parser object)
        self.inicfgp = None
        
        #gatewaylist
        self.gateways = gateways
        #sensorlist
        self.sensors_lock = threading.Lock()
        self.sensors = sensors
        
        #note: Most Dictionary Operations Are Atomic Many common operations on a dict are atomic, meaning that they are thread-safe.
        self.sensors_addr = {}      #lookup: sensorindex by list -> we use binary string (as received) for building lookup table
        self.sensors_unknown = {}   #holds unknown sensors (sensors unknown to the system)
        
        #create our list with output sensor channels (=processed data)
        self.chans_out = [] #all output sensor channels
        self.chans_in = []  #all input sensor channels
        
        #process information based on the 
        for i,sen in enumerate(self.sensors):
            try:
                self.sensors_addr[struct.pack("!BB", sen.addr_group, sen.addr_node)] = i
            except struct.error:
                print("ERROR: no adress specified for sensor - set is", sen.addr_group, sen.addr_node)
                self.sensors_addr[struct.pack("!BB", sen.addr_group, 0)] = i
            
            for chan in sen.chans_out:
                self.chans_out.append(chan)
            for chan in sen.chans_in:
                self.chans_in.append(chan)
            
            #associate this measurement system with the sensor after initialization
            sen.measys = self
            
        #THREADING (TASK) SUPPORT   
        self.threads_list = [] #list with all active collector threads (@note: collectors must support a type)
        self.threads_active = False #global thread activity control

        self.threads_txq = []  #list of transmit queues all active collectors use to, sent messages (from global cmd abstraction)
        self.threads_txq_lock = threading.Lock() #is this really needed?
        
        #communication device objects we are operating on
        self.comdevs = comdevs #remember -> can be None (!)
        
        #supporting information (ini file)
        self.ver_ini = 0 #ini file version number -> is incremented with each write
                        
        #zeroing monitor implementation -> remember/log zeroed measurement data        
        if dir_zeromon != None:
            self.zeromon = measzeromon.MeasurementZeroMonitor(p_dir=dir_zeromon)
            self.zeromon.open()
        else:
            self.zeromon = None
        
        #supported commandset and communication protocols with their needed data structures
        #not available in case of a bad import
        self.cmdset_sensor_force = None
        self.cmdset_sensor_pressure = None
        
    def threads_start(self):
        '''
        starting collector threads of measurement system
        '''
        print("meassys: starting %i threads" % len(self.comdevs))
        self.threads_list = []
        self.threads_txq = []
        self.threads_active = True
        
        for i,dev in enumerate(self.comdevs):
            name = "TH-COL[%i] TYPE: STD" % i
            txq = queue.Queue()
            self.threads_txq.append( txq )
            
            
            
        for th in self.threads_list:
            th.start()
        
    def threads_stop(self):
        '''
        stopping collector threads of measurement system
        '''
        print("meassys: stopping %i threads" % len(self.comdevs))
        
        self.threads_active = False
        for th in self.threads_list:
            th.join(0.5)
        self.threads_list = []  
    
    
    def process(self):
        '''
        regular processing of the measurement system. does all regular work. this can be called by a GUI on a regular basis!
        
        THREAD SAFE: yes
        '''
        #if DBG_OUT: print("sys:processing")
        
        #updating sensor status information (timeout detection)
        self.sensors_lock.acquire()
        for sen in self.sensors:
            sen.process()
        self.sensors_lock.release()
    
    def sensor_by_packetaddr(self, packet):
        '''
        returns sensor index from raw addr in a packet
        
        packet .. is the raw binary xbee packet | we extract the senet addresss
        
        THREAD SAFE: yes (dictionary access is atomic -> read in python documentation)
        '''
        addr_raw = packet[11:13] #@TODO: make central definition
        try:
            index = self.sensors_addr[addr_raw]
            return index
        except KeyError:
            self.sensors_unknown[addr_raw] = packet
            return None
            
    def process_gateways(self):
        '''
        thread safe processing of gateways (if needed)
        '''
        
    def update_sensor_from_status_msg(self, packet):
        '''
        we are updating sensor information from a received status message (raw packet)
        '''
        if DBG_OUT: print("update_sensor_from_status_msg")
        self.update_sensor_by_addr(packet)

    def update_sensor_from_cmd_msg(self, packet):
        '''
        we are updating sensor information from a received status message (raw packet)
        '''
        if DBG_OUT: print("update_sensor_from_cmd_msg")
        self.update_sensor_by_addr(packet)

    def update_sensor_from_datacol_msg(self, packet):
        if DBG_OUT: print("update_sensor_from_datacol_msg")
        self.update_sensor_by_addr(packet)
      
    def update_sensor_data(self, addr_node, state=None, rx=None, tx=None, vals=None):
        ''' 
        thread safe update of typical sensor information
        
        state .. the remote hardware state the sensor is in
        '''
        try:
            self.sensors_lock.acquire()
            sen = self.sensors_addr[addr_node]
            if rx!=None: sen.rxq.push(rx)
            if tx!=None: sen.txq.push(tx)
            return True
        except Exception as e:
            print(f"ERROR: meassys:update_sensor_byaddr: sensor with addr_node={addr_node} is unknown") #@TODO: add to logging
            return None #in case 
        finally:
            self.sensors_lock.release()
    
    def mdata_current_from_channel(self):
        ''' returns all current (output) measurement channel data (if this mode is used, simplified processing). do we have a list
            alternative?
            
            THREADING: is threadsafe
        '''
        try:
            self.sensors_lock.acquire()
            #speed can be improved
            data = []
            for s in self.sensors:
                for c in s.chans_out:
                    data.append(c.val)
            return(data)
        finally:
            self.sensors_lock.release()
    
    def measure_data(self):
        ''' returns the current calibrated meassurement data of the measurement system '''
        pass
    
    def measure_data_raw(self):
        ''' returns the current raw (uncalibrated) measurement data for each channel of the measurement system '''
        pass
    
    def measure_data_update(self, sensorid):
        ''' update  '''
        pass 
    
    def do_zero(self, for_chansel=None):
        ''' do the zero calibration for the specified sensor with id, if none do zeroing for all sensors'''
        
        if for_chansel==None: 
            pass
        
        #implement zero monitor behaviour (must write data, after doing the zeroing
        if self.zeromon != None:
            self.zeromon.write([0],[0],["TO-IMPLEMENT!!!"])

    def do_calibrate(self, sensorid, calitype=None):
        '''
        do the calibration routine for the specified sensor (sensorid) and the the specified calibration type (calitype = None -> default calibration 
        routine is choosen) 
        '''
        pass
    
    def do_remote_state_control(self):
        '''
        bring all devices into the expected remote state (i.e., IDLE, MEASURE) 
        --> Is called on a regular basis. Devices which are in the wrong mode, go into the required mode (i.e., IDLE, MEASURE) and so on
        '''
        raise Exception("must be implemented")
        
        
    def list_sensors(self):
        '''
        returns a list with all sensors of the measurement system
        '''
        return self.sensors
    
    def list_devices(self):
        '''
        returns a list with all devices (gateways and sensors) of the measurement system
        '''
        return self.sensors + self.gateways
    
    def list_gateways(self):
        '''
        returns a list with all gateways of te measurement system
        '''
        return self.gateways
    
    def list_comdevs(self):
        '''
        returns a list with all communication devices
        '''
        return self.comdevs
    
    def check(self):
        '''
        do an internal system data check, raise exceptions in case of errors, convert parameters if required
        '''
        self.sysindex = int(self.sysindex)
        self.ver_ini = int(self.ver_ini)

    def check_basestation(self, all=True):
        '''
        will check if there is a valid base station, will retrieve base station information
        '''
        
    ######################################## 
    # ini file settings and configurations #
    ########################################    
    def ini_cfgp(self):
        ''' generates a configuration parser object 
            --> see syskonst_template_v20.ini
        '''
        inisecsys = ""
        for para in dir(self):
            if DEFINI_SEC_SYSPARASTR in str(para) in para:
                ininame = appdef.ini_varname_to_key(para) #in the inifile we don't want df_ and _v             
                #print("ininame", ininame)
                val = getattr(self,para)
                if type(val) == type(enum.Enum):
                    inisecsys += f"{ininame} = {val.value}\n"
                else:
                    inisecsys += f"{ininame} = {val}\n"
                #special case of enum 
        inisecsen = ""        
        for j,sen in enumerate(self.sensors):
            i = j+1 #let's start counting with 1
#@TODO: this is BAAAAD -> better doing this directly in the sensor abstraction, and just provide an output string
            inisecsen +=f'''[SENSOR{i}]
idsen = {sen.df_idpro_f}
name = {sen.df_nameapp_f}
sentype = {sen.devtype}
sengroup = {sen.sengroup}
addr_node = {sen.addr_node}
idsencust = {sen.df_idcust_f}
chans_out = {len(sen.chans_out)}
chans_in = {len(sen.chans_in)}
'''
        inistr =  f'''[general]
initype = 20
initemplate = syskonst_template_v20.ini
#measurement system configuration
[{DEFINI_SEC_SYS}]
{inisecsys}
#sensor configuration section
{inisecsen}
#ini version configuratoin
[{DEFINI_SEC_VER}]
ver_ini = {self.ver_ini}
ver_ctrl = 0
'''        
        inicfgp = configparser.ConfigParser()
        inicfgp.read_string(inistr)
        self.inicfgp = inicfgp
        return inicfgp
    
   
    def ini_check(self, path, exception=True, fix_errors=False):
        '''
        check measurement system ini file -> is everything as expected or do we have errors?
        
        exception .. True/False either raise 
        '''
    def __str__(self):
        return f'''SYS:{self.df_idpro_v}|{self.df_nameapp_v}[T={self.df_systype_v}, IND={self.sysindex}] / SENS={len(self.sensors)} IN={len(self.chans_in)} OUT={len(self.chans_out)}'''

TEST_SYS = MeasurementSystemXKM(sensors = sensor.TEST_DEVLIST2) #a Testsystem
TEST_SYS2 = MeasurementSystemXKM(sensors = sensor.TEST_DEVLIST3_FORCE_SENSORS) #a Testsystem


def test_zeroing():
    val_init = 1.0
    sensors = []
    md_in  = numpy.zeros(shape=[7, 0]) #input data  -> raw input  channel data
    md_out = numpy.zeros(shape=[7, 0]) #output data -> raw output channel data
    
    for i in range(1,7):
        #we have sensors first -> it is more practi
        sen = sensor.SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, addr_node=i, calib=appdef.DEF_CALIBRATION.TEST_1_FAKT)
        sensors.append( sen ) #we need a handle
        [md_in, md_out] = sen.md_init(md_in, md_out) #remember we are handing the data over
        sen.md_clear(clearval = val_init)
    
    #register the same array for all sensors (!)
    for i,s in enumerate(sensors):
        s.md_register(ary_in=md_in, ary_out=md_out)    
    for i,x in enumerate(numpy.nditer(md_out)):
        if i>=0 and i<len(sensors):
            assert x == val_init
    for i,x in enumerate(numpy.nditer(md_in)):
        if i>=0 and i<len(sensors):
            assert x == val_init
    print("INITIAL ARRAY STATE:")
    print(md_in)
    print(md_out)
    for i,s in enumerate(sensors):
        s.zero_set() #set the zero val
        assert md_in[0,i] != 0.0 #zeroed, and recalculated
    print("Tested zero_set() - it will update the currently shown output value")
    print(md_out)
    
    #now the interesting part, if we show 0 and we zero again?
    for i,s in enumerate(sensors):
        s.zero_set() #set the zero val
        assert md_out[0,i] == 0.0  #after we zet zero, the current value is always zero
    for i,s in enumerate(sensors):
        s.zero_set() #set the zero val
        assert md_out[0,i] == 0.0  #after we zet zero, the current value is always zero
    for i,s in enumerate(sensors):
        s.zero_set() #set the zero val
        assert md_out[0,i] == 0.0  #after we zet zero, the current value is always zero
    print("we are adding data now")
    val1 = 10.0
    valcalc = (10.0+10.0) #see specified calibration routine
    for i,s in enumerate(sensors):
        valzero = s.zero_get()
        valcalc = 180.0
        s.md_update([val1]*100)
        #assert md_out[0,i] == valcalc
    for i,s in enumerate(sensors):
        valzero = s.zero_get()
        valcalc = 180.0
        s.md_update([val1]*20)
        s.md_update([val1]*20)
        s.md_update([val1]*20)
        for k in range(0,10): s.zero_set() #means we zero again, and first line shows zeros, we can do this inefinitly
        assert md_out[0,i] == 0.0
        s.md_update([val1*5]*20)
        assert md_out[0,i] == 800.0
    print(md_out)
    print(md_in)



    
if __name__ == '__main__':
    import os
    print("running: meassys - demonstrating the usage")
    TESTCFG_DIR = "../tests/msys/" #working directory to save/store data during testing
    if not os.path.exists(TESTCFG_DIR): os.makedirs(TESTCFG_DIR)
    DBG_OUT = True
    test_zeroing()  
    #following tests are using a plotter
    #test_matplotlib_liveview()
    #test_tool_dataview()
    print("done")