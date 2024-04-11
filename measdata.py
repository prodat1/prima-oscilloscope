'''
measdata.py .. measurement data abstractions for collected measurement data of a measurement

TODO:
    * BKM Oszilloskop Messung mit Erfassung und Auswertung steigender und fallender Flanken
    --> Messwertarray muss asynchrone Befuellung unterstuetzen bzw. befuellung mit eigenen zeitmesswerten
'''
#python standard
import time
from dataclasses import dataclass
import threading #thread safe data access support
#3rd party
import numpy as np
import pandas as pd
import pytest

#project specific
try:
    from libxkm import appdef
    from libxkm import meassys
except ModuleNotFoundError:
    import appdef
    import meassys #need measurement channel specification
    
DEF_DATATYPE = np.float32 #in case float only -> throws depreciation warning
DEF_DEPTHSHORT = 50
DEF_DEPTHFULL  = 1000

#at end of names of attributes
DEF_PYOBJ_FIELDSTR = "_f" #identifier for field names in python object attributes (attribute name based processing)
DEF_PYOBJ_VASTR = "_v" #identifiert for value names in python object attributes (attribute name based processing)

DBG_OUT = False #enable/disable debugging output
CFG_ZEROMONITOR = True #enable/disable zero monitor
CFG_INITVAL = np.nan #initialization value for measurement data arrays (y-data, t-data)


class ErrorFinalizedWrite(Exception):
    '''
    raised, if a user tries to write to finalized Measurement data
    '''
    pass

@dataclass
class MeasurementInfoData():
    ''' Measurements - additional information to a measurment process, as needed for the report '''    
    #measurement information fields for permanent storage ('minf') | for measurment data handling
    minf_report_f : str = "Protokoll-Nr:" #
    minf_report_v : str = "X" #the report this measurement belongs to
    minf_customerid_f : str = "Customer M-ID" #customer measurement name (if needed)
    minf_customerid_v : str = "X" #customer information field value
    minf_date_f : str = "Datum:" #finalisierte Messung
    minf_date_v : str = "1.1.2020" 
    minf_time_f : str = "Time:" 
    minf_time_v : str = "24:00" 
    minf_comment_f : str = "Kommentar (Messung):"
    minf_comment_v : str = "X"  #a comment to the current measurement a user can make
    
    #Fahrzeugausrichtung relativ zum Messsystem
    minf_direction_f : str = "Fahrzeug-Ausrichtung:"
    minf_direction_v : str = "SYS-L=F-R oder SYS-L=F-L" #linke seite messsystem = linke seite fahrzeug 
    minf_direction_customer_f : str = "Fahrzeug-Ausrichtung:" #Ausrichtung lt. Kundenbezeichnung
    minf_direction_customer_v : str = ""
        
class MeasurementData(MeasurementInfoData):
    '''
    Measurement data base class as central data storage object.
    - we are working with functionality layers
    - we can handle different application cases
    
    Measurement data is organized in numpy arrays, created via self.init_data(). Numpy arrays are organized in channels:
    
    (1) Y-values self.md_current_y .. current measurement values -> 2D numpy array [zeile : spalte]
        - newest values are first (zeile 0)
        - oldest values are last  (zeile -1)
        
        CH0 CH1 CH2 .. CHN (oldest value)
        ..
        CH0 CH1 CH2 .. CHN (newest value)
        
    (2) t-values self.md_current_t 
        - newest values are first (zeile 0)
        - oldest values are last (zeile -1)    
    '''
    
    def __init__(self, chans=[], chans_info=[], chan_sel = None,
                 max_long=DEF_DEPTHFULL, max_short=DEF_DEPTHSHORT, dtype = DEF_DATATYPE):
        '''
        chans .. the measurement data channels to use, we store a measurement data channel list
        depth .. time history depth to work with (number of values) default = 2048 [big data array]
        depthshort = time history depth for short measurement data default = 100
        chan_sel .. channel selection support a dictionary with channel lists to support grouping (TODO)
            {
            'multimeter':[1,2,3],
            'force':[0,1,2],
            }
            -> with this approach we allow
        '''
        #general information data init (from MeasurementInfoData) -> data class
        self.init_infodata()
        
        self.chans = chans #the description list of measurement data channels
        self.chans_info = chans_info  #optional: measurement channel information 
        self.max_chans = len(self.chans)
        self.dtype = dtype
        self.max_y_long = int(max_long) 
        self.max_y_short = int(max_short)
        self.init_data()
        self.init_flags()

        #external object handles (if needed)
        self.h_report = None #handle to a measurement report, this file can be a part of
        self.h_vehic = None #handle to the current vehicle and its vehicle information for the current measurement
    
    def init_infodata(self):
        super(MeasurementData, self).__init__() #should work? data class must handle everything
        
    def init_data(self, keeptime=False):
        '''
        clearing all measurement data (a clean reset) and ensuring a default state after initialization
        '''
        if not keeptime: self.time_start = time.time()
        
        #a global row counter for row-wise updates
        self.index = 0  #current data index to write to 
        
        #index for saved measurement data
        self.index_saved = 0
        
        #an individual channel index counter, for channel-wise updates
        self.index_chan = np.zeros(shape=(1, self.max_chans), dtype=int) #individual update conter
                
        #measurement data variables
        self.md_current_t  = np.full(shape=(self.max_y_short, self.max_chans), fill_value= CFG_INITVAL, dtype=self.dtype)  #layer: values
        self.md_current_y  = np.full(shape=(self.max_y_short, self.max_chans), fill_value= CFG_INITVAL, dtype=self.dtype)  #layer: times
        self.md_saved_t    = np.full(shape=(self.max_y_short, self.max_chans), fill_value= CFG_INITVAL, dtype=self.dtype)  #layer: saved - valed
        self.md_saved_y    = np.full(shape=(self.max_y_short, self.max_chans), fill_value= CFG_INITVAL, dtype=self.dtype)  #layer: values
        self.md_saved_info = {}
        self.md_zero_y     = np.zeros(shape=(1, self.max_chans), dtype=self.dtype) #zero y-value for each channel
        self.md_zero_t     = np.zeros(shape=(1, self.max_chans), dtype=self.dtype) #optinoal zero t-value for each channel (= start of measurement)
        
        #saved data including 
        
        #oldest value is last, newest is first
        #self.md_full = np.zeros(shape=(max_long, self.max_cols), dtype=dtype) #layer: channel measurement data -> current data | for each channel time and value
    
    def init_flags(self):
        self.is_finalized = False #in case finalized, now changes are possible anymore
        self.is_zeroed = False #in case of first zeroing is true
        
    def datasets(self):
        ''' 
            returns a dictionary with datasets names and their data handles -> numpy arrays
            ATTENTION: reading/writing data in background
        '''
        datasets = {
            'current_t':  self.md_current_t,
            'current_y':  self.md_current_y,
            'saved_t':    self.md_saved_t,
            'saved_y':    self.md_saved_y,
            'saved_info': self.md_saved_info, #additional measurement info for saved data
            'zero_y':     self.md_zero_y,
            'zero_t':     self.md_zero_t,
        }
        return datasets
    
    def zero_set(self, vals=None, vals_t=None, by_chansel=None, by_index=None):
        '''
        set zero measurement data for each measurement channel for all measurement channels
        if vals == None .. use the last entries for each channel 
        by_index .. not None -> means update for a list of measurement channels indexes i.e., [0,2,4,3] and values
        vals_t .. optional time values
        ''' 
        self.is_zeroed = True
        if vals==None: vals = self.md_current_y[self.index-1,:] #last entry is self.index - 1
        if vals_t==None: vals_t = self.md_current_t[self.index-1,:] #last entry is self.index - 1
        
        #default case, no channel selection is active -> store zero values, without additional selection
        if self.index >= 1:    
            self.md_zero_y[0,:] = vals
            self.md_zero_t[0,:] = vals_t
        else:
            pass #use initialization data
        return [self.md_zero_y[0,:], self.md_zero_t[0,:]]
    
    def zero_y(self):
        ''' returns zero measurement value information '''
        return self.md_zero_y[0,:] 
                    
    def zero_t(self):
        ''' returns zero measurement time information '''
        return self.md_zero_t[0,:]
    
    def save(self, myident="", index=None, saveinfo="Was, wo und in welchem Zusammenhang"):
        '''
        save current measurement data  into saved measurement data set, provide saving information 
        
        can be used for "HOLD" functionality of current measurement.
        '''
        if index == None: index = self.index_saved
        
        self.md_saved_t[index,:] = self.md_current_t[self.index,:]
        self.md_saved_y[index,:] = self.md_current_y[self.index,:]
        self.md_saved_info[index] = saveinfo 

        if DBG_OUT: 
            print("S(%04i): V=" % self.index_saved + str(self.md_saved_y[index,:]) + "\t t=" + str(self.md_saved_t) )
        
        self.index_saved = index + 1
        return [self.index_saved, myident]
    
    def update(self, data_y=[], data_t=None):
        ''' 
        a user is adding measurement data to our array, by adding a full data line row.
        in the default case, timing information is added automatically
        
        checktype .. True -> we are checking/converting the data type, to make sure, correct data is added. The user should work with 
        the expected data types, to speed things up
        
        returns:
            None .. in case nothing was done, measurement data is finalized
            index .. the current row index, we wrote measurement dat
        '''
        if self.is_finalized: raise ErrorFinalizedWrite()
        if len(data_y) != self.max_chans: raise TypeError("data length missmatch for data_y -> synchronous data is required!")

        #in case saturated, we will roll data and first element will be last element?
        #rolling large data consumes a lot of memory? / rolling data will make things slower?
        if self.index >= self.max_y_short:
            self.md_current_t = np.roll(self.md_current_t, shift=-1, axis=0)
            self.md_current_y = np.roll(self.md_current_y, shift=-1, axis=0)
            self.index -= 1
        
        #adding t_data (timing or x values) / internal timestamp is used in case of None.      
        if data_t==None: 
            self.md_current_t[self.index] = [time.time()-self.time_start]*self.max_chans
        else: 
            if len(data_t) != self.max_chans: raise TypeError("data length missmatch for data_t!")
            self.md_current_t[self.index] = [time.time()-self.time_start]*self.max_chans
        
        #adding y-data (values)
        self.md_current_y[self.index] = data_y
        
        #optinal debugging output
        if DBG_OUT: 
            print(">(%04i): V=" % self.index + str(data_y) + "\t t=" + str(data_t) )
            print("=Z:%04i: V=" % self.index + str(self.md_current_y[self.index]) + "\t t=" + str(self.md_current_t[self.index]) )
        
        #adding data, we keep track of the latest data
        self.index = self.index+1
        return self.index

    def calculate(self):
        '''
        calculate all dependent data -> zero data and any user specific data
        '''
        pass

    def finalize(self, finalized=True):
        '''
        will finalize measurement data, no changes are possible anymore  
        '''
        self.is_finalized  = finalized
        self.calculate()
             
    #convenience functions
    def last(self):
        '''
        return the last channel data with a time vector and a value vector 
            (t[..], y[..])
        '''
        return (self.md_current_t[self.index], self.md_current_t[self.index] )
    
    def last_y(self):
        ''' returns last values (y) '''
        return self.md_current_y[self.index-1]
   
    def last_t(self):
        ''' returns last values (t) '''
        return self.md_current_t[self.index-1]
            
    def show_current(self):
        print(self.md_current_y)
    
    #########################################
    # reporting and data conversion support #
    #########################################
    def to_report_xkm_as_html(self):
        ''' output as HTML XKM report '''
        pass
    
    def to_report_xkm_as_excel(self):
        ''' output as EXCEL XKM report '''
       
    def __str__(self):
        '''
        show measurement channel information
        '''
        return f"MDATA {self.minf_report_v} with CH={self.max_chans} | ZERO= {self.is_zeroed} | DATA={self.index-1} / MAX=self.is_zeroed "
      
class MeasurementDataRKM(MeasurementData):
    '''
    RKM measurement data (extends and overrides measurement data)
    '''

class MeasurementDataBKM(MeasurementData):
    '''
    BKM measurement data (extends and overrides measurement data)
    '''

def generate_mdata(max_channels):
    '''
    generates a test measurement data array
    '''
    mdata = MeasurementData([x for x in range(0,max_channels)]) #whatever the user chooses as channel objects?
    return mdata

def testdata_oscilloscope_block_update(max_channels):
    '''
    usage for the oscilloscope plugin 
    '''
    print("testdata creation: used for an oscilloscope block update")
    mdata = MeasurementData([x for x in range(0,max_channels)]) #whatever the user chooses as channel objects?
    
    #input data is added from a source (i.e., via aggregator thread) 
    for i in range(0,20):
        y_data = [i*10.0 + (x+1)*1000 for x in range(0, max_channels)]
        t_data = [i*0.1  + (x+1)      for x in range(0, max_channels)]
        mdata.update(y_data, t_data)
    return (mdata.md_current_y[:,0:5], mdata.md_current_t[:,0:5])

def test_usage_regular():
    '''
    general test case demonstrating the regular usage
    '''
    print("creating measurement data array")
    max_chans = 10 #-> use a list of measurement channels, to which we have access. We expect a specific channel class if required.
    chans=[x for x in range(0,max_chans)]
    
    mdata = MeasurementData(chans) #whatever the user chooses as channel objects?
    assert mdata.index == 0 #must be always zero
    
    print("filling in measurement data -> filling up to the maximum")
    for i in range(0,DEF_DEPTHSHORT):
        assert mdata.index == i
        tmp = mdata.update([i for x in range(0,max_chans)])
        assert mdata.index == i+1
        assert mdata.index == tmp
        
    #adding more values after saturation 
    for i in range(500,510):
        mdata.update([i for x in range(0,max_chans)])

    mdata.show_current()

    print("only allow writing to non-finalized data, otherwise we expect an exception")
    mdata.finalize(finalized=True)
    with pytest.raises(ErrorFinalizedWrite) as excinfo:
        mdata.update([i for x in range(0,max_chans)])
    mdata.finalize(finalized=False)
    mdata.update([i for x in range(0,max_chans)])    
    mdataRKM = MeasurementDataRKM()
    mdataBKM = MeasurementDataBKM()
        
    return True
    
if __name__ == '__main__':
    print("running: measdata.py")
    test_usage_regular()
    print(testdata_oscilloscope_block_update(7))
    print("done")