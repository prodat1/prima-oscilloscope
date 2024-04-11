'''
PRODAT XKM sensor abstractions (sensor definitions)
    - organize measurement data
    - store sensor information and sensor state

'''
import time
import enum
import collections
import numpy
import struct
import sys
import statistics #for processing of mean (numpy alternative)

from dataclasses import dataclass
#from core.protocols import datacollection


import dbg
import meas_channel as channel
import appdef

   
DBG_OUT = False
DBG_VERBOSE = False #print more information

CFG_PRINTRX = True #if enabled, sensor will print all RX messages on commandline

'''
we are supporting two datamodes to handle measurment data
    SINGLEVALUES -> data is hold in the channels (we have input and output channels). A channel holds a single value.
    DATAARRAY -> measurement data is organized in a big numpy measurement array.
'''
class DATAMODES:
    SINGLEVALUES =  0 #if enabled update as single value stored in measurement channels (simple processing)
    DATAARRAY = 1 #if enabled process data in large data arrays
CFG_DATAMODE = DATAMODES.SINGLEVALUES

class DEF_TIMEOUTS():
    SENSOR_XKM = 30.0 #in s, XKM sensor timeout for BKM and RKM sensor
    
#@TODO: Enum needed?
class DEF_STATES(enum.Enum):
    '''
    SENSOR STATE DEFINITION
    '''
    ERROR_TIMEOUT = -10 #sensor in timeout, means we lost track, have not heard anything
    ERROR = -1 #general error of unknown reason
    
    INIT = 0 #initialization after system start, no additional information
    INACTIVE = 1 #sensor is in inactive state, means not used and data is not updated
    
    IDLE = 2 #idle mode
    MEASURE = 3 #measure mode @TODO: there can be different measurement modes how general do we want to make everything?
    CHARGE = 4 #charging mode
    CALIB = 5 #calibration mode

class SensorXKM():
    ''' 
        PRODAT XKM general (default) sensor definition - handles types PRODAT RKM und BKM 
        @see: core.channel.py
    '''
    DEF_QRX_MAX = 10 #max. number of messages
    def __init__(self, 
        #most important configuration
        sentype, #sensor type specifier
        sengroup = None, #sensor selection group specifier (to have them in groups) --> @TODO: needed?
        
        meassys = None, #measurement system handle -> if we want to access the parents functionality
        
        # sensor information, needed to work with the sensor
        mdata : bool = False, # with = True or without measurement data support (create data arrays)
        
        addr_node = None,  #network: node addr
        addr_group = None, #network: group addr
        calib = None, #calibration information (preferably a module) @TODO
        status = -1, #@TODO Nico & Robert -> introduced this?
        #df_chanpro = None, 
        mvals_init = None, #initialization values for measurement channels (out), if None not used
        
        #organizational parameters -> we need something we can parse -> "df", for datafield
        df_nameapp : str = "application nick name i.e. F1 / PMULT1 / PMULT4", #the name in the application
        df_nameapp_cust : str = "application nick name from customer for example: Sensor 1, S1", 
        df_type : str ="sensor type name & id: RKM-M-G2",
        df_idpro : str = "prodat serial number: 123456.01",
        df_idcust : str = "",#customer serial number: K-9854",
        df_pos : str = "position during measurement R1.1 hinten/link",
        df_comment : str = "an optional user comment",
        df_datecali : str = "calibration date: 20230101", 
        df_chanpro: list = ['g','g'], #PRODAT channel name
        df_chancust : list = ['customer measurement channel ID1', 'customer measurement channel ID2'],  
        
        #config parameters (change only if really needed)
        cfg_qlen = DEF_QRX_MAX,
        cfg_rx_onlyunique = True
        ):
        '''
        mdata .. a numpy measurement data array we operate for. it holds current data with historie ("a channel snapshot")
        sentype .. sensor type specifier -> must be part of DEF_SENTYPES, sensor type (see DEF_SENTYPES), must be one of this types        
        addr_node .. sensor node address in the measurement system (default is None), user handles the type, i.e. string or int
        addr_group .. sensor node group address
        calib .. calibration method/functionality used (default is None), if default standard calibration is used
        cfg_rx_onlyunique .. only accept unique messages for reception (means discard duplicates)
        '''
        # important working variables
        if not isinstance(sentype, appdef.DEF_SENSORTYPES): raise TypeError("Require type appdef.DEF_SENSORTYPES")
        self.devtype = sentype   #identifies the XKM sensor type -> see: appdef.DEF_SENSORTYPES
        self.sengroup = sengroup #a selection group identifier
        self.measys = meassys
        # datafields "df_XXXX" -> this is information for organizational purposes (i.e, sensor type name, IDs and so on)
        # df_XXXX_f .. fieldname (used in GUI) -> field name used to show information
        # df_XXXX_v .. value (the actual value)
        self.df_nameapp_f = "SEN"       #application name -> fieldname to use in the app (SEN)
        self.df_nameapp_v = df_nameapp  #application name -> the actual value to use in the app
        self.df_nameapp_cust_f = ""
        self.df_nameapp_cust_v = df_nameapp_cust
        self.df_type_f = "TYP"
        self.df_type_v = df_type        #sensor type
        self.df_idpro_f = "ID-PRODAT"
        self.df_idpro_v = df_idpro
        self.df_idcust_f = "ID-CUSTOMER"
        self.df_idcust_v = df_idcust
        self.df_pos_f = "POS (TODO: needed here?)"   #@TODO: is this needed in sensor
        self.df_pos_v = df_pos
        self.df_comment_f = "COMMENT"
        self.df_comment_v = df_comment
        self.df_datecali_f = "CALI-DATE"
        self.df_datecali_v = df_datecali
        self.df_chancust_f = "CHAN (CUST)"
        self.df_chancust_v = df_chancust  #measurement channel names, assigned by PRODAT
        self.df_chanpro_f = "CHAN (PRO)"
        self.df_chanpro_v = df_chanpro    #measurement channel names, assigned by Customer
        
        # generate a df dict for easier (and faster) lookup by users in the future (this could be generated)
        # maps -> _v -> _f
        self.DATAFIELDS = {}
        #for item in sorted(dir(self),reverse=True):
            #values shall rule the dictionary. exceptions are handled by programmer -> must define always both
            #if appdef.DEF_PYOBJ_ID in item and appdef.DEF_PYOBJ_FIELD in item:
             #   self.DATAFIELDS[getattr(self,item)] = getattr(self,item.replace(appdef.DEF_PYOBJ_FIELD,appdef.DEF_PYOBJ_VAL))
        
        #communication support: SENET node addr and group addr
        self.addr_node = addr_node     #sensor node address
        self.addr_group = addr_group   #sensor group address
        
        #measurement data
        self.mvals_init = mvals_init # inititalization values
        self.mdata = mdata # this is obsolet?
        self._marry_in = None  #@handle, set later on -> we operate on big measurement data array // always have independent data structures
        self._marry_out = None #@handle, set later on -> we operate on big measurement data array // always have independent data structures
        
        #zeroing data -> is an numpy array to much overhead?
        self.zero_in  = [] #holds the current zero values (raw values)
        self.zero_out = []  #hold the current, raw (uncalibrated measurement values for each channel)

        #behaviour configuration
        self.cfg_rx_onlyunique = bool(cfg_rx_onlyunique)

        #should we provide a "last message queue for each sensor"
        # -> this is needed for duplicate detection on a per sensor basis
        # -> this is (might be helpful), we use it also as support tool for debugging & Co.
        self.qrx = collections.deque( maxlen=int(cfg_qlen) )
        self.txq = collections.deque( maxlen=int(cfg_qlen) )
        
        #additional internal working variables
        self.status = status
        self.state = DEF_STATES.INIT #local sensor state -> should always match remote state, or second field needed?
        self.state_remote = DEF_STATES.INIT #remove sensor state (the device is in) -> @TODO: we need to take care that remote state equals local state
        
        self.time_lastrx = time.time() #last time we received a message from the sensor
        self.time_start = time.time() #current sensor system time
        self.time = time.time() #the current sensor time
        
        #calibration routine, if None do not use any calibration
        self.calib = calib
        self.calib_const = None #None, calibration constant table -> used for the specified calibration routine 
        
        #additional sensortype specific initialization
        self.__init_sentype__()
    
    def __init_sentype__(self):
        #do the type dependent initiali
        #configure and initialize measurement channels
        
        self.chans_in_index = []
        self.chans_out_index = []
        
        if appdef.DEF_SENSORTYPES.PRO_BKM_W_1CH0 == self.devtype or appdef.DEF_SENSORTYPES.PRO_BKM_W_1CH1 == self.devtype: 
            self.addr_group = 1
            self.chans_in =  [channel.Channel(sensorhandle=self)] #one input channel.Channel -> one output channel.Channel
            self.chans_out = [channel.Channel(sensorhandle=self)]
        elif appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM == self.devtype:
            self.addr_group = 1
            self.chans_in  = [channel.Channel(sensorhandle=self), channel.Channel(sensorhandle=self)] #two input channel.Channel -> one output channel.Channel
            self.chans_out = [channel.Channel(sensorhandle=self)]
        elif appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_DUAL == self.devtype:
            self.addr_group = 1
            self.chans_in  = [channel.Channel(sensorhandle=self), channel.Channel(sensorhandle=self)] #two input channel.Channel -> one output channel.Channel
            self.chans_out = [channel.Channel(sensorhandle=self)]            
        elif appdef.DEF_SENSORTYPES.PRO_PINT_W_CH1 == self.devtype:
            self.chans_in  = [channel.Channel(sensorhandle=self) ] #initialize with two channel.Channels by default
            self.addr_group = 4
            self.chans_out = [channel.Channel(sensorhandle=self)] #initialize with two channel.Channels by default
        elif appdef.DEF_SENSORTYPES.PRO_PINT_W_CH4 == self.devtype:
            self.addr_group = 4
            self.chans_in = []
            self.chans_out = []
            for i in range (0,4): #@TODO: this can be improved -> central definition?
                self.chans_in.append(  channel.Channel(sensorhandle=self) ) #initialize with two channel.Channels by default
                self.chans_out.append( channel.Channel(sensorhandle=self) )
        elif appdef.DEF_SENSORTYPES.PRO_PINT_W_CH8 == self.devtype:
            self.addr_group = 4
            self.chans_in = []
            self.chans_out = []
            for i in range (0,8): #@TODO: this can be improved -> central definition?
                self.chans_in.append( channel.Channel(sensorhandle=self) ) #initialize with two channel.Channels by default
                self.chans_out.append( channel.Channel(sensorhandle=self) ) #initialize with two channel.Channels by default
        elif appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH:
            self.addr_group = 1
            self.chans_in =  [channel.Channel(sensorhandle=self), channel.Channel(sensorhandle=self)]
            self.chans_out = [channel.Channel(sensorhandle=self)]            
        else:
            raise AssertionError("not yet implemented")
        
    def process(self, packet=None, rx_data=True,  rx_queue=True, rx_check=True ):
        '''
        regular sensor processing loop, call it regulary to update maintained sensor information i.e.,
        - status
        - measurement data
        - commandset protocol
        
        packet .. raw binary packet senet sensor network packet.
        rx_data .. the received packets holds data we process and update this data
        rx_queue .. enable to use a reception queue, to detect and prevent duplicate packets (in case data reaching us from multiple collectors)
        rx_check .. [True/False], if enabled check incoming messages for example valid address, checksum and so on
        
        @note: this can be also done by an user above.
        ATTENTION: NOT THREAD SAFE (USER HANDLES THREADING AND LOCK MECHANISM)
        '''
        self.time = time.time()

        mstat = ""
               
     
        #@TODO, is this working - will it also work with binary data for received messages?
        if self.cfg_rx_onlyunique:
            if packet not in self.qrx: #otherwise it will mean a complete du
                self.qrx.append(packet) #"when new items are added, a corresponding number of items are discarded from the opposite end"
            
        if self.state != DEF_STATES.INIT: #in all states except the init state check for sensor timeout condition
            if (self.time - self.time_lastrx) > DEF_TIMEOUTS.SENSOR_XKM: self.state = DEF_STATES.ERROR_TIMEOUT
        
        if DBG_OUT: print("sensor: updated values", self)
        
    def zero_set(self, zeroval_in=None, zeroval_out=None):
        '''
        sets the zero value for both input and output channel. It means, we will have to update
        the last shown output value. We will have to recalculate the calibration.
         
        do the zero routine -> set and save the zero value for each sensor measurement channel
        we do it for the raw measurement values and for the calibrated measurement values 
        
        returns: zero values for (output, input)
        '''
        if zeroval_in==None:
            self.zero_in[0,:] = self._marry_in[0, self.chans_in_index]  #this is easy, we simply save the values
        else:
            self.zero_in[0,:] = zeroval_in
        
        if zeroval_out==None: 
            self.zero_out[0,:] = self.calc_calibrate()
        else:
            self.zero_out[0,:] = zeroval_out
        
        #recalculate the first shown value
        self._marry_out[0,self.chans_out_index] = self.calc_zero()
        
        return (self.zero_out,self.zero_in)
    
    def zero_get(self):
        '''
        returns zero values for (output, input)
        '''
        return (self.zero_out,self.zero_in)
    
    def calc_zero(self):
        '''
        calculate zerod output value a single time for the current values (top most entries)
        please note: zeroing calculation is done for output value only.
        '''
        return self.calc_calibrate() - self.zero_out[0,:]
        
    def calc_pre(self):
        '''
        processing: do calculations BEFORE CALIBRATION (pre calculation)
        @TODO later
        '''
        if DBG_OUT: print("calc_pre()")
    
    def calc_post(self):
        '''
        processing: additional calculations after calibration and zeroing
        @TODO: later
        '''
        if DBG_OUT: print("calc_post()")
    
    def calc_calibrate(self):
        '''
        processing: do calculations -> calculate outputs in dependence of inputs 
        @note: we don't know what data changed -> so we don't how much we need to update

        #we are taking input channel state and process the output channel state
        #we assume we will only have to process the first line

        '''        
        if DBG_OUT: print("calc_calib()")
        match self.calib:
            case appdef.DEF_CALIBRATION.TEST_1_FAKT:
                #print("DBG!!! CALI VIA DEF_CALIBRATION.TEST_1_FAKT")
                #a test on a per channel basis we summation and afterwards adding
                #we have to roll, and afterwards we will have to calibrate the newest
                ret = numpy.sum(self._marry_in[0, self.chans_in_index]*10.0, axis=0)
                return ret
            case appdef.DEF_CALIBRATION.TEST_2_SUM:
                #print("DBG!!! CALI VIA DEF_CALIBRATION.TEST_2_SUM")
                ret = numpy.sum(self._marry_in[0, self.chans_in_index], axis=0)
                return ret
            case None:
                ret = numpy.sum(self._marry_in[0, self.chans_in_index], axis=0)
                return ret
            
    def rx_last(self):
        '''
        returns the last saved packet from the RX queue (if used), None if there is nothing in the queue
        '''
        if len(self.qrx) == None: return None
        return self.qrx[-1]
    
    def rx_strout(self):
        '''
        will show the content of the reception queue as a string
        '''
        strout = ""
        for i in reversed(range(0,10)):
            rxstr = self.qrx[i] #we only want reverse iteration
            strout += "SENSOR-RX[%02i]: %s\n" % (i,str(rxstr))
        return strout
    
    def tx_last(self, leave_in_queue=True):
        '''
        returns last saved packet from the TX queue (if used), None if there is nothing in the queue
        '''
        if len(self.qtx) == None: return None
        return self.qtx[-1]
    
    #####################################################################
    # measurement data (md_) handling -> we work on a big numpy array   #
    #    -> initialization means, adding a new array column & arry copy #
    #####################################################################
    def md_register(self, ary_in=None, ary_out=None):
        '''
        register measurement object handle (numpy array) for the sensor abstraction to operate on,
        do this for:
            * input channel data (raw data)
            * output channel data (measured and processed data)
        '''
        if ary_in is None: raise TypeError("we need a numpy array structure")
        if ary_out is None: raise TypeError("we need a numpy array structure")         
        
        self._marry_in = ary_in
        self._marry_out = ary_out
         
    def md_info(self):
        '''
        return information about the sensor and where it stores its information in the big measurement array
            - return a dictionary with information
            input .. input data selection for array
            output .. output data selection for array
        '''
        return {
            "input":self.chans_in_index,
            "output":self.chans_out_index,
            "ary-obj-in":self._marry_in,
            "ary-obj-out": self._marry_out
        }
        
    def md_init(self, ary_in, ary_out, axis_datagrow=0, axis_changrow=1):
        '''
        ary .. numpy array to operate on, with this sensor abstraction (it must have enough space for all sensor channels)
        sel_out .. table selection (array dimenstion) for output data
        sel_in .. table selection (array dimension) for input data
        axis .. the axis to operate on (the direction to extend the array in)
        @attention: currently not threadsafe (but numpy might be??) -> user must handle everything
        
        returns: expanded input array, expanded output array, zero array
        '''
        if DBG_OUT: print("sensor: mdata initialization")
        if self._marry_in != None: raise AssertionError("to implement, not allow for array to grow indefinitly")
        if self._marry_out != None: raise AssertionError("to implement, not allow for array to grow indefinitly")
        
        self._marry_in = ary_in #create a handle for the measurement data object (array)
        self._marry_out = ary_out #create a handle for the measurement data object (array)
        
        #we will grow the array automatically for our input and output channels
        #@TODO: we assume always the same max. size for the input and for the output array
        ylen = numpy.size(self._marry_in, axis_datagrow)
        ylenb = numpy.size(self._marry_out, axis_datagrow)
        if ylen != ylenb: raise TypeError("we currently support only arrays with the same length for input and output data")
        initdata = numpy.zeros( shape=[ylen,1] )
        
        self.zero_in  = numpy.zeros( shape=[1, len(self.chans_in)] )
        self.zero_out = numpy.zeros( shape=[1, len(self.chans_out)] )
        
        if dbg.DBG_MEASYS_MDATAINIT_WITH_NODEADDR:
            print("DBG: DBG_MEASYS_MDATAINIT_WITH_NODEADDR ACTIVE -> different array init values")
            for i,val in enumerate(initdata):
                initdata[i] = float(self.addr_node*10.0)
        
        #we need to enter data for each array
        self.chans_in_index = []
        for i,chan in enumerate(self.chans_in):
            self._marry_in = numpy.append(self._marry_in, initdata, axis=axis_changrow)
            index = numpy.ma.size(self._marry_in, axis=axis_changrow)
            self.chans_in_index.append(index-1)
            if DBG_OUT: print("CHAN:%i with selection index %i" % (i, self.chans_in_index[i]) )

        #we need to enter data for each array
        self.chans_out_index = []
        for i,chan in enumerate(self.chans_out):
            self._marry_out = numpy.append(self._marry_out, initdata, axis=axis_changrow)
            index = numpy.ma.size(self._marry_out, axis=axis_changrow)
            self.chans_out_index.append(index-1)
            if DBG_OUT: print("CHAN:%i with selection index %i" % (i, self.chans_out_index[i]) )
                
        return (self._marry_in, self._marry_out) #we return upated sensor information
        
    def md_clear(self, clearval=0.0, clear_in=True, clear_out=True):
        '''
        sensor -> sensor clears its sections of the measurement data array
        '''
        if clear_out:
            for cindex in self.chans_out_index: #want a better way -> store it in channel information 
                if DBG_OUT: print(f"clear: spalte: {cindex} ")
                self._marry_out[:,cindex] = float(clearval)
        if clear_in:
            for cindex in self.chans_in_index: #want a better way -> store it in channel information 
                if DBG_OUT: print(f"clear: spalte: {cindex} ")
                self._marry_in[:,cindex] = float(clearval)
    
    
    def md_update_block(self, vals, do_calib=True, do_calc=True):
        '''
        we will update a number of measurement input values (a block)
        '''
                      
    def md_update(self, vals, do_calib=True, do_calc=True):
        '''
            update measurement values -> new data is added to measurement input channel data. 
             - we are using a sliding window by default, old data is removed
             - oldest data moves to the end
             - INDEX 0 .. NEWEST DATA
             - 
             - INDEX N .. OLDEST DATA
            
            @param do_calib .. execute calibration routines to update output data from input data (means calibration)
            @param do_calc .. execute additional calculations, any processing functionality if required
        '''
        if DBG_OUT: print("md_update: mary_in: " + str(vals))
        
        #problem is -> we can not create a copy of the original array, we can only roll a copied section from memory
        #slowest possible update approach (copy over by value)
        aslice = self._marry_in[:,  self.chans_in_index]
        rolled = numpy.roll(aslice, shift=1, axis=0) #select axis for rolling (=shifting)
        rolled[0,:] = vals[0:len(self.chans_in_index)] #will it update a whole line
        self._marry_in[: , self.chans_in_index] = rolled
        #additional processing
        if do_calc == True: 
            self.calc_pre()
        
        #calibration routine
        #print(self._marry_out)
        if do_calib == True: 
            ret = self.calc_calibrate()
            aslice = self._marry_out[:, self.chans_out_index]
            rolled = numpy.roll(aslice,shift=1,axis=0) #select axis for rolling (=shifting)
            rolled[0,:] = ret
            self._marry_out[:, self.chans_out_index] = rolled            
        
        #zeroing is always done
        self._marry_out[0 , self.chans_out_index] = self.calc_zero()
        
        if do_calc == True:
            self.calc_post()
        
        
    def md_current(self, num=None):
        '''
        returns the current (newest) measurement values from the data array 
        -> output measurement channel data is returned
        (returns the measurement data)
        
        @param slice .. the number of values to return i.e., 0:4
        returns: a slice of the array (output numpy array, input numpy array)
        '''
        retin = None
        retout = None
        
        if self._marry_out is not None:
            if num is None:
                retout = self._marry_out[0, self.chans_out_index]
            else:
                retout = self._marry_out[0:num, self.chans_out_index]
        if self._marry_in is not None:
            if num is None:
                retin = self._marry_in[0, self.chans_in_index]
            else:
                retin = self._marry_in[0:num, self.chans_in_index]
        
        #return (self._marry_out[0:num, self.chans_out_index], self._marry_in[0:num, self.chans_in_index]) #return the newest value
        return (retout, retin)

    def md_current_in(self, num=None):
        '''
        returns the current (newest) input values (the raw uncalibrated input data) 
        '''
        if num is None:
            return self._marry_in[0, self.chans_in_index] #return the newest value
        else:
            return self._marry_in[0:num, self.chans_in_index]
    
    def md_current_out(self, num=None):
        '''
        returns the current (newest) output values (the raw calibrated output data)
        '''
        if num is None:
            return self._marry_out[0, self.chans_out_index] #return the newest value
        else:
            return self._marry_out[0:num, self.chans_out_index]
        
    def md_in(self):
        '''
        returns all input measurement channel data (this object takes care of)
        '''
        return self._marry_in[:, self.chans_in_index] #return the newest value
    
    def md_out(self):
        '''
        returns all output measurement channels data (this object takes care of)
        '''
        return self._marry_out[:, self.chans_out_index] #return the newest value
        
    def channels(self):
        '''
        return measurement channel information for output and input channels
        
        return (self.chans_out, self.chans_in)
        '''
        return (self.chans_out, self.chans_in)
    
    ###########################################################################
    # special functionality for hardware control -> we could make this easier #
    ###########################################################################
    # @TODO: do we want to simply i.e., pass commandset(s) to the sensor, just pass TX messages or use the action list below?
    def do_tx_hardware_reset(self, *args):
        if DBG_OUT: print("sensor action: reset")
        if self.measys is None: print("ERROR: measurement system is not registered", sys.stderr)
        else: self.measys.hw_do_reset(addr_node=self.addr_node, addr_group=self.addr_group)
    
    def do_tx_mode_idle(self, *args):
        if DBG_OUT: print("sensor action: mode idle")
        if self.measys is None: print("ERROR: measurement system is not registered", sys.stderr)
        else: self.measys.hw_do_mode_idle(addr_node=self.addr_node, addr_group=self.addr_group)
    
    def do_tx_lightnpick(self, *args):
        if DBG_OUT: print("sensor action: picknlight")
        if self.measys is None: print("ERROR: measurement system is not registered", sys.stderr)
        else: self.measys.hw_do_lightnpick(addr_node=self.addr_node, addr_group=self.addr_group)
    
    def do_tx_mode_measure(self, *args):    
        if DBG_OUT: print("sensor action: mode measure")
        if self.measys is None: print("ERROR: measurement system is not registered", sys.stderr)
        else: self.measys.hw_do_mode_measure(addr_node=self.addr_node, addr_group=self.addr_group)
    
    def do_tx_mode_sleep(self, *args):
        if DBG_OUT: print("sensor action: mode measure")
        if self.measys is None: print("ERROR: measurement system is not registered", sys.stderr)
        else: self.measys.hw_do_mode_sleep(addr_node=self.addr_node, addr_group=self.addr_group)

    def do_tx_status(self, *args):
        if DBG_OUT: print("sensor action: mode measure")
        if self.measys is None: print("ERROR: measurement system is not registered", sys.stderr)
        else: self.measys.hw_do_status(addr_node=self.addr_node, addr_group=self.addr_group)
    
    def get_actions_hardware(self):
        '''
        returns a list of user hardware actions, the sensor supports in the measurement system. 
        Returned is as dictionary with GUI name and function handle. There is no
        need for function parameter support -> use different methods for this purpose.
        
        These action list can be used by GUI widgets in the software.
        '''
        return {
            "Light&Pick": self.do_tx_lightnpick,
            "Reset": self.do_tx_hardware_reset,
            "Idle": self.do_tx_mode_idle,
            "Measure": self.do_tx_mode_measure,
            "Sleep": self.do_tx_mode_sleep,
            "Status": self.do_tx_status
        }
    
    def get_information(self):
        '''
        returns important information to show in the GUI. Returns a dictionary with field and value
        '''
        if self.measys is None: measys = "X"
        else: measys = f"{self.measys.df_nameapp_v} [{self.measys.sysindex}]"
        mydict = {"System": measys, 
                  "NWK-ADDR": f"A={self.addr_node} | G={self.addr_group}", 
                  "CH-OUT" : self.str_channeldata_out(),
                  "CH-IN" : self.str_channeldata_in(),
                  } | self.DATAFIELDS 
        return mydict
    
    # printing support
    def str_addr(self):
        '''
        returns an address information string (for displaying purposes)
        '''
        return "A=%02i G=%02i" % (self.addr_node, self.addr_group)

    def str_channeldata_in(self):
        ''' input channel data as string (if set)'''
        chandata_in = "IN: "
        for i,c in enumerate(self.chans_in):
            chandata_in += "[%i]=%3.2f " % (i, c.val) 
        return chandata_in
    
    def str_channeldata_out(self):
        ''' output channel data as string (if set)'''
        chandata_out = "OUT: "
        for i,c in enumerate(self.chans_out):
            chandata_out += "[%i]=%3.2f " % (i, c.val) 
        return chandata_out
    
    def str_channeldata(self):
        ''' input and output channel data (if set) '''
        return self.str_channeldata_in() + self.str_channeldata_out()
    
    def __str__(self):
        ''' provide short output about the sensor and important data in it '''
        rxlen = len(self.qrx)==0
        
        if rxlen: rxstr = "X"
        else:  rxstr = str(self.qrx[-1])
        if self.time_lastrx == None: timestr = "X"
        else: timestr = "%4.2f" % (time.time() - self.time_lastrx )
        
        val_in, val_out = self.md_current()
        
        #process current channel data
        chandata_in = "IN: "
        for i,c in enumerate(self.chans_in):
            chandata_in += "[%i]=%3.2f " % (i, c.val) 
        chandata_out = "OUT: "
        for i,c in enumerate(self.chans_out):
            chandata_out += "[%i]=%3.2f " % (i, c.val) 
        
        if DBG_VERBOSE:
            datafields = "DF:"
            for k in self.DATAFIELDS.keys():
                datafields += "\n\tDF:" + str(k) + " -> " + str(self.DATAFIELDS[k])
        else: datafields = "DF: (not shown)"
        return f'''SEN: T={self.devtype.name} A={self.addr_node} G={self.addr_group} S:{self.state} | L-RX: {rxstr} T-RX:{timestr} 
DAT: {self.str_channeldata()} | DATA-ARY : {val_in} OUT={val_out}'''

#SUPPORT FOR TESTING
#@TODO -> TYPE_BKM must use definitions above
TYPE_BKM = appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM
TEST_DEVLIST__SENSOR_FORCE = [
    #@NOTE: df_chanpro and mvals_init is defined via the sensor type | information can be updated later
    SensorXKM(TYPE_BKM, df_idpro="123456.01", df_chanpro=["g"], mvals_init=[2.01],  df_nameapp="F1",   df_chancust=["F Rad 1"], status=[1],
           df_datecali="20230101", addr_node=1),
    #df_chanpro=['kN'], mvals_init=[1.00],
    SensorXKM(TYPE_BKM, df_idpro="123456.02", df_chanpro=['g'], mvals_init=[2.01],  df_nameapp="F2", df_chancust=["F Rad 2"], status=[1],
           df_datecali="20230101", addr_node=2),
    SensorXKM(TYPE_BKM, df_idpro='123456.03', df_chanpro=['g'], mvals_init=[3.02],  df_nameapp="F3", df_chancust=["F Rad 3"], status=[1],
           df_datecali="20230101", addr_node=3),
    SensorXKM(TYPE_BKM, df_idpro='123456.04', df_chanpro=['g'], mvals_init=[10.04], df_nameapp="F4", df_chancust=["F Rad 4"], status=[1],
           df_datecali="20230101", addr_node=4),
    SensorXKM(TYPE_BKM, df_idpro='123456.05', df_chanpro=['g'], mvals_init=[17.06], df_nameapp="F5", status=[2],
           df_datecali="20230101", addr_node=5),
    SensorXKM(TYPE_BKM, df_idpro='123456.06', df_chanpro=['g'], mvals_init=[24.08], df_nameapp="F6", status=[2],
           df_datecali="20230101", addr_node=6),
    SensorXKM(TYPE_BKM, df_idpro='123456.07', df_chanpro=['g'], mvals_init=[31.1],  df_nameapp="F7", status=[2],
           df_datecali="20230101", addr_node=7),
    SensorXKM(TYPE_BKM, df_idpro='123456.08', df_chanpro=['g'], mvals_init=[38.12], df_nameapp="F8", status=[2],
           df_datecali="20230101", addr_node=8),
    SensorXKM(TYPE_BKM, df_idpro='123456.09', df_chanpro=['g'], mvals_init=[45.14], df_nameapp="F9", status=[3],
           df_datecali="20230101", addr_node=9),
    SensorXKM(TYPE_BKM, df_idpro='123456.10', df_chanpro=['g'], mvals_init=[52.16], df_nameapp="F10", status=[3],
           df_datecali="20230101", addr_node=10),
    SensorXKM(TYPE_BKM, df_idpro='123456.11', df_chanpro=['g'], mvals_init=[59.18], df_nameapp="F11", status=[3],
           df_datecali="20230101", addr_node=11)
]

TYPE_PSING = appdef.DEF_SENSORTYPES.PRO_PINT_W_CH1
TEST_DEVLIST_PRESSURE_SENSORS_SINGLE = [
    SensorXKM(TYPE_PSING, df_idpro='234567.01', df_chanpro=['g'], mvals_init=[1.28], df_nameapp=  "PS1", status=[1],
           df_datecali="20230101", addr_node=1),
    SensorXKM(TYPE_PSING, df_idpro='234567.02', df_chanpro=['g'], mvals_init=[12.8],  df_nameapp= "PS2", status=[1],
           df_datecali="20230101", addr_node=1),
    SensorXKM(TYPE_PSING, df_idpro='234567.03', df_chanpro=['g'], mvals_init=[24.32], df_nameapp= "PS3", status=[1],
           df_datecali="20230101", addr_node=1),
    SensorXKM(TYPE_PSING, df_idpro='234567.04', df_chanpro=['g'], mvals_init=[1.28],  df_nameapp= "PS4", status=[1],
           df_datecali="20230101", addr_node=1),
    SensorXKM(TYPE_PSING, df_idpro='234567.05', df_chanpro=['g'], mvals_init=[12.8],  df_nameapp= "PS5", status=[1],
           df_datecali="20230101", addr_node=1),
    SensorXKM(TYPE_PSING, df_idpro='234567.06', df_chanpro=['g'], mvals_init=[24.32], df_nameapp= "PS6", status=[1],
           df_datecali="20230101", addr_node=1),
    SensorXKM(TYPE_PSING, df_idpro='234567.07', df_chanpro=['g'], mvals_init=[35.84], df_nameapp= "PS7", status=[1],
           df_datecali="20230101", addr_node=1)
    ]

TYPE_PMULT4 = appdef.DEF_SENSORTYPES.PRO_PINT_W_CH4
TYPE_PMULT6 = appdef.DEF_SENSORTYPES.PRO_PINT_W_CH6
TEST_DEVLIST_PRESSURE_SENSORS_MULTI = [
    SensorXKM(TYPE_PMULT4, df_idpro="345678.05", mvals_init=[4.03, 5.04, 6.05, 7.06],
           df_chanpro=["MP1(CH1)", "MP1(CH2)", "MP1(CH3)", "MP1(CH4)"],
           df_chancust=["Sensor 1", "Sensor 2", "Sensor 3", "Sensor 4"], status=[0, 1, 2, 3], df_datecali="20230101",
           addr_node=1),
    SensorXKM(TYPE_PMULT6, df_idpro="345678.06",
           mvals_init=[8.07, 9.08, 10.09, 11.10, 12.11, 13.12],
           df_chanpro=["MP2(CH1)", "MP2(CH2)", "MP2(CH3)", "MP2(CH4)", "MP2(CH5)", "MP2(CH6)"], status=[0, 1, 2, 3, 0, 1],
           df_datecali="20230101", addr_node=1),
]

TEST_DEVLIST2_FORCE_SENSORS = [SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.01",df_idcust="P-14520",df_nameapp="F1", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.02",df_idcust="P-14521",df_nameapp="F2", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.03",df_idcust="P-14522",df_nameapp="F3", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.04",df_idcust="P-14523",df_nameapp="F4", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.05",df_idcust="P-14524",df_nameapp="F5", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.06",df_idcust="P-14525",df_nameapp="F6", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.07",df_nameapp="F7", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.08",df_nameapp="F8", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.09",df_nameapp="F9", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.10",df_nameapp="F10", status=[1],df_chanpro=['g']),
                      SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM, df_idpro="123456.11",df_nameapp="F11", status=[1],df_chanpro=['g'])]
TEST_DEVLIST2_PRESSURE_SENSORS_SINGLE = [SensorXKM(appdef.DEF_SENSORTYPES.PRO_PINT_W_CH1,df_idpro="123456.12",df_idcust="P-14526",df_nameapp="P1", status=[1],df_chanpro=['g']),
                                SensorXKM(appdef.DEF_SENSORTYPES.PRO_PINT_W_CH1,df_idpro="123456.13",df_nameapp="P2", status=[1],df_chanpro=['g'])]
TEST_DEVLIST2_PRESSURE_SENSORS_MULTI = [
    SensorXKM(appdef.DEF_SENSORTYPES.PRO_PINT_W_CH4, df_idpro="123456.14",df_idcust="P-14527",df_nameapp="PM1", status=[0, 1, 2, 3],df_chanpro=['g','g','g','g']),
    SensorXKM(appdef.DEF_SENSORTYPES.PRO_PINT_W_CH8, df_idpro="123456.15",df_nameapp="PM2", status=[0, 1, 2, 3, 0, 1, 2, 3],df_chanpro=['g','g','g','g','g','g','g','g']),
]

TEST_DEVLIST3_FORCE_SENSORS = [
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.01",df_idcust="P-14520",df_nameapp="F1", status=[1],df_chanpro=['g'],addr_node="1"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.02",df_idcust="P-14521",df_nameapp="F2", status=[1],df_chanpro=['g'],addr_node="2"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.03",df_idcust="P-14522",df_nameapp="F3", status=[1],df_chanpro=['g'],addr_node="3"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.04",df_idcust="P-14523",df_nameapp="F4", status=[1],df_chanpro=['g'],addr_node="4"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.05",df_idcust="P-14524",df_nameapp="F5", status=[1],df_chanpro=['g'],addr_node="5"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.06",df_idcust="P-14525",df_nameapp="F6", status=[1],df_chanpro=['g'],addr_node="6"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.07",df_idcust="P-14526",df_nameapp="F7", status=[1],df_chanpro=['g'],addr_node="7"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.08",df_idcust="P-14527",df_nameapp="F8", status=[1],df_chanpro=['g'],addr_node="8"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.09",df_idcust="P-14528",df_nameapp="F9", status=[1],df_chanpro=['g'],addr_node="9"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.10",df_idcust="P-14529",df_nameapp="F10", status=[1],df_chanpro=['g'],addr_node="10"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.11",df_idcust="P-14530",df_nameapp="F11", status=[1],df_chanpro=['g'],addr_node="11"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.12",df_idcust="P-14531",df_nameapp="F12", status=[1],df_chanpro=['g'],addr_node="12"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.13",df_idcust="P-14532",df_nameapp="F13", status=[1],df_chanpro=['g'],addr_node="13"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.14",df_idcust="P-14533",df_nameapp="F14", status=[1],df_chanpro=['g'],addr_node="14"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.15",df_idcust="P-14534",df_nameapp="F15", status=[1],df_chanpro=['g'],addr_node="15"),
                        SensorXKM(appdef.DEF_SENSORTYPES.PRO_RKM_W_2CH, df_idpro="123456.16",df_idcust="P-14535",df_nameapp="F16", status=[1],df_chanpro=['g'],addr_node="16")
                        ]
'''
TODO
TEST_VIRTUAL_SENSORS = [
    Sensor(TYPE_VIRTUAL, str_id="123456.07", mchans=["kN"], mvals=[30.1]),
    Sensor(TYPE_VIRTUAL, str_id="123456.08",mchans=["pA"], mvals=[40.1])
]

TEST_BPA_SENSORS = [
    Sensor(TYPE_BPA, "123456.09", mchans=["pA","pA","pA"], mvals=[50.1,50.2,50.3])
]'''

#TEST_SENSORS = TEST_PRESSURE_SENSORS_MULTI + TEST_PRESSURE_SENSORS_SINGLE + TEST_FORCE_SENSORS + TEST_VIRTUAL_SENSORS +  TEST_BPA_SENSORS
#TEST_SENSORS = TEST_PRESSURE_SENSORS_MULTI + TEST_PRESSURE_SENSORS_SINGLE + TEST_FORCE_SENSORS
TEST_DEVLIST2 = TEST_DEVLIST2_FORCE_SENSORS + TEST_DEVLIST2_PRESSURE_SENSORS_SINGLE + TEST_DEVLIST2_PRESSURE_SENSORS_MULTI

def test_usage_regular():
    #create a sensor - with minimum information
    mysen = SensorXKM(appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM)
    print(mysen)

    
if __name__ == '__main__':
    DBG_OUT = True
