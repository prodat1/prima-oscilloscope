'''
The zero monitor (stores raw and calibrated data) in a file. Managed module by a user,
should be called, whenever a user does a zeroing. Best is to integrate it in the measurement
system functionality. Zeroing for each configured sensor and measurement channel).

'''
import os
import datetime

CFG_SEPARATOR = ";"
CFG_WITHHEADER = True #if enabled include a file header

class MeasurementZeroMonitor():
    CFG_RAW_AS_HEXSTR = True  #if enabled write output as hexstring for raw channel data
    CFG_CAL_AS_HEXSTR = False #for calibrated measurement channel data
    
    def __init__(self, p_dir, p_file="zeromonitor.txt"):
        if not os.path.isdir(p_dir): os.makedirs(p_dir)
        self.fp = os.path.abspath(os.path.join(p_dir,p_file))
        self.f = None
        self.count = 0
    
    def open(self):
        self.f = open(self.fp, "a")
        return self.f

    def close(self): 
        self.f.close()
        self.f = None
        
    def write(self, rawchans=[], calchans=[], statinfo=[]):
        
        self.count += 1
        strout = str( datetime.datetime.today() ) + ";" + str(self.count) +";"
        #raw measurement channel data (uncalibrated values)
        strout += "R;"
        for i, val in enumerate(rawchans):
            if self.CFG_RAW_AS_HEXSTR: 
                strout += "%04x" % (val) + ";"
            else: 
                strout += strout + str(val) + ";"
        #calibrated measurement channel data (calibrated values)
        strout += "C;"
        for i, val in enumerate(statinfo):
            if self.CFG_CAL_AS_HEXSTR: 
                strout += "%04x" % (val) + ";"
            else: 
                strout += str(val) + ";"
        #optional status information / status channel
        strout += "S;"
        for i, val in enumerate(statinfo):
            strout += str(val) + ";"
        strout = strout + "\n" 
        #write to our file
        self.f.write(strout)
        self.f.flush()
        
    
    #NEEDED/OPTION:
    ''' 
    def callbacks()

    def update()
    '''
    def __str__(self):
        return f"ZEROMONITOR in {self.fp} wrote: {self.count}"
    
if __name__ == '__main__':
    print("measzeromon.py: is started")
    zmon = MeasurementZeroMonitor(p_dir="../tests/zeromon/", 
                                  p_file="zeromonitor.txt")
    zmon.open()
    zmon.write(rawchans=[16,15,34,32], calchans=[12, 45, 44, 23],
               statinfo=["mixed", 1, 2.0, "what i want"] )
    zmon.write(rawchans=[16,15,34,32], calchans=[12, 45, 44, 23],
               statinfo=["mixed", 1, 2.0, "what i want"] )
    zmon.write(rawchans=[16,15,34,32], calchans=[12, 45, 44, 23],
               statinfo=["mixed", 1, 2.0, "what i want"] )
    zmon.write(rawchans=[16,15,34,32], calchans=[12, 45, 44, 23],
               statinfo=["mixed", 1, 2.0, "what i want"] )
    print(zmon)
    
    zmon.close()
    print("done")