'''
    PRODAT XKM - measurement channel abstraction
        - measurement channel stores information about itsself (i.e., type, plotting color and so on)
        - measurement channels are part of sensors
'''
import enum

try:
    from libxkm import appdef
except ModuleNotFoundError:
    import appdef
    
class DEF_CHANTYPES(enum.Enum):
    PHYSICAL = 0    # default type, a physical measurement channel ('real')
    VIRTUAL = 1 #virtual channel type, it is based on a calculation (i.e., the sum of two measurement channels)
    SIMULATED = 2 #simulated values -> to make clear we use this in the system

class Channel():
    ''' 
    PRODAT XKM measurement channel specification as used in the sytem 
    we have to maintain a lot of large data in case of many channels -> we are doing the data maintainance on a per 
    measurement basis (large arrays). Measurement channels can support data handling, but must not use it
    '''
    ID = 0 #a unique id counter, shared among all measurement channels
     
    def __init__(self, sensorhandle=None, systemhandle=None):    
        #IMPORTANT INDEX POSITIONS IN 
        self.chantype = DEF_CHANTYPES.PHYSICAL #we are using physical measurement channels by default
        self.index_sys = -1  #channel index (list position) in the measurement system configuration
        self.index_meas = -1 #the index position in the measurement setup (actual measurement position)
    
        #SUPPORT INFORMATION OF TYPE DF
        self.df_nameapp_f = "CH" #application name of the channel -> field name in the app, can be parsed 
        self.df_nameapp_v = "F10"  #application name of the channel -> the actual value        
        self.df_nameuser_f = "CH(U)"
        self.df_nameuser_v = "Kraft links (blaue marke)" #an optional name the user can give to the channel
        
        self.df_pospro_f = "POS" #the measurement position name as used by prodat
        self.df_pospro_v = "Rechts"
        self.df_poscust_f = "POSU" #the measurement position name as used by the customer
        self.df_poscust_v = "Rechtes"

        self.DATAFIELDS = {}
        #for item in sorted(dir(self),reverse=True):
            #values shall rule the dictionary. exceptions are handled by programmer -> must define always both
        #    if appdef.DEF_PYOBJ_ID in item and appdef.DEF_PYOBJ_FIELD in item:
        #        self.DATAFIELDS[getattr(self,item)] = getattr(self,item.replace(appdef.DEF_PYOBJ_FIELD,appdef.DEF_PYOBJ_VAL))
        
        
        #additional class working variables
        self.unit = 'g' #unit string 
        self.freq = 1 #frequency in Hz 
        self.dt = float(1)/float(self.freq) #dt in  
        
        #see: https://matplotlib.org/2.1.1/api/_as_gen/matplotlib.pyplot.plot.html
        self.plt_color = "" #default color to use in diagrams for plotting
        self.plt_style = "" #default line style to use in diagrams for plotting
        self.plt_str = self.plt_color + self.plt_style 
        
        self.h_func_conv = None #any conversion function to convert the channel
        self.h_sensor = sensorhandle #handle to the sensor the measurement channel belongs to
        self.h_system = systemhandle
        self.h_func_calib = None #calibration 
        
        #optional: measurement value support (if needed, i.e., for simple data exchange) and posting
        self.val = 0.0
        
        #optional: measurement value history support
        self.h_mval_curhist = None #handle to get the measurement data history of this channel
    
    def get_information(self):
        '''
        returns important information to show in the GUI. Returns a dictionary with field and value
        '''
        return self.DATAFIELDS    
    
    def __str__(self):
        '''
        returns measurement channel information
        '''
        return f'''CH:{self.df_nameapp_v}-{self.df_nameuser_f} = {self.val} in {self.unit} | {self.chantype} [{self.index_sys} {self.index_meas}] SEN={self.h_sensor}'''

if __name__ == '__main__':
    print("running: meas_channel")
    chan = Channel()
    print(str(chan))
    print(chan.get_information())
    print("done")