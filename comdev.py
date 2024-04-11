'''
PRODAT XKM comdev.py - application communication device abstractions with a standartized programming interface
Support for:
    * serialport (hardware) = SERIALPORT -> serialport data exchange
    * measurement data files = MDATATFILE -> file system data exchange

'''
#python data types
import os
import time
import queue
import struct
import sys
from enum import Enum

#3rd party (needs installation)
import serial
import serial.tools.list_ports_windows


DBG_OUT = False #enable/disable additional print debugging output

COMDEVS = [] #holds our  list of communication objects (i.e., queried serial ports) for thr_xkm_collector 

class COMTYPES(Enum):
    '''
    XKM Communication Module Type
        - we can sort classes
    '''
    NONE = -1 #NOTHING/UNINITIALIZED
    SERIALPORT = 1 #serial port (pyserial)
    MDATATFILE = 2 #data file in file system holding measurement value (sensor data file)
    XKMSERV_REST = 3 #XKM server via REST API
    XBEE_GENERIC = 4 #general xbee module type
    BASESTATION_XBEE = 5 #XBEE basestation module

class COMMODES(Enum):
    ''' operation modes '''
    NOTEXISTANT = -10   #the device does not exist
    ERROR = -1          #error state -> i.e., serial port blocked by another application
    DISCONNECTED = 0    #initial state
    CONNECTED = 1       #connected state

class RXSTATES(Enum):
    ERROR_CHKSUM = -11 #checksum verification error
    ERROR = -10 #reception error (general)
    OVERFLOW = -2 #to much data is incoming, processing not fast enough
    TIMEOUT = -1 #timeout occurred
    IDLE = 0  #waiting for reception
    BUSY = 1  #reception is ongoing
    DONE = 2  #finished, we have a packet 
    
class ComDev:
    '''
    generic communication device (master class)
    '''
    devtype = COMTYPES.NONE
    
    def __init__(self, ident="ComDev", mode=COMMODES.DISCONNECTED):
        ''' initialize communication device '''
        self.comdev = None #communication device object, None means not initialized
        self.mode = mode #communication device mode
        self.ident = ident
        
        self.df_nameapp_f = "COMDEV"        #application name -> fieldname to use in the app (SEN)
        self.df_nameapp_v = str(self.ident)      #application name -> the actual value to use in the app

    def write(self):
        ''' write to the communication device (will return device specific data)'''
        pass
    
    def read(self):
        ''' read from the communication device (will return device specific data)'''
        pass
    
    def open(self):
        ''' connect/establish communication connection'''
        pass
    
    def close(self):
        ''' close communication connection '''
        pass
    
    def flush(self):
        ''' flush (clear) the communication device '''
        pass
    
    def get_information(self):
        '''
        returns information about the device as a dictionary (to parse in the gui)
        '''
        return {
            self.df_nameapp_f : self.df_nameapp_v,
            "DEVTYPE": self.devtype,
            "IDENT": self.ident,
            "MODE": self.mode,
        }
        
class ComDevFile(ComDev):
    '''
    sensor measurement data files are used for communication note:
        * one file for reading (one line only)
        * one file for writing (one line only)
    '''
    
    devtype = COMTYPES.MDATATFILE

    def __init__(self, ident="FILE", file_to_read="senval_in.txt", file_to_write="senval_out.txt", chan_to_read=10, chan_to_write=10, **kwargs):
        #initialize super class
        super().__init__(**kwargs)
        self.ident = ident
        
        #files used for reading and writing
        self.comdev_r = None
        self.comdev_w = None
        
        #configure the communication object
        self.cfg_fread = file_to_read
        self.cfg_fwrite = file_to_write
        self.cfg_chanread = chan_to_read #the number of measurement channels to read
        self.cfg_chanwrite = chan_to_write #the number of measurment channels to write
        
    def open(self):
        ''' opening the communication device for reading and writing '''
        if (self.cfg_fread != None) and (self.comdev_r == None):
            if not os.path.exists(self.cfg_fread):
                self.comdev_r = open(self.cfg_fread, "w") #if it does not exist, create it for reading
                self.comdev_r.write("MEASUREMENT DATA UNINITIALIZED")
                self.comdev_r.flush()
                self.comdev_r.close()
            
            self.comdev_r = open(self.cfg_fread, "r") #try to open for reading

        if (self.cfg_fwrite != None) and (self.comdev_w == None):
            self.comdev_w = open(self.cfg_fwrite, "w")
    
    def close(self):
        ''' close the files, we maintain '''
        if self.comdev_r != None: 
            self.comdev_r.close()
            self.comdev_r = None
        if self.comdev_w != None: 
            self.comdev_w.close()
            self.comdev_w = None
    
    def read(self, *args):
        ''' read from our sensor data file '''
        #DBG <print("COMDEV: reading")
        return self.comdev_r.read(*args)
    
    def write(self, *args):
        ''' write to our sensor data file '''
        self.comdev_w.write(*args)
    
    def flush(self):
        ''' flushing the files for reading and writing '''
        if self.comdev_r != None: self.comdev_r.flush()
        if self.comdev_w != None: self.comdev_w.flush()
        
    def __str__(self):
        ''' return device information '''
        return f"COM {self.devtype.name}: F-READ={self.cfg_fread} F-WRITE={self.cfg_fwrite}"

class ComDevSerial(ComDev):
    '''
    a serial hardware port on the system (on windows COM9 / linux tty 
    '''
    devtype = COMTYPES.SERIALPORT
    
    def __init__(self, port : str, baudrate : int, timeout=0.1, 
                 stopbits=serial.STOPBITS_ONE, databits=serial.EIGHTBITS, 
                 parity=serial.PARITY_NONE, xonxoff=0, rtscts=0, 
                 ident : str ="SX", name = "SERIALX", 
                 status = [0],**kwargs):

        #initialize super class
        super().__init__(**kwargs)
        self.ident = ident
        self.name = name #name for application (for GUI)
                
        #configure the actual communication object
        #port='COM1', baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
        self.comdev = serial.Serial() #get a Serial instance and configure/open it later:
        self.comdev.port = port
        self.comdev.timeout = timeout
        self.comdev.baudrate = baudrate
        self.comdev.bytesize = databits
        self.comdev.stopbits = stopbits
        self.comdev.parity = 'N'
        self.comdev.xonxoff = xonxoff
        self.comdev.rtscts = rtscts
        
        self.status = status
    
    #decorators to reduce the required typing
    @property
    def cfg_port(self): return self.comdev.port
    
    @property
    def cfg_baudrate(self): return self.comdev.baudrate

    @property
    def cfg_timeout(self): return self.comdev.timeout
    
    #@TODO: we could extend with the other parameters but do we need them?
    
    #setter support -> is this needed?
    @cfg_port.setter
    def cfg_port(self, p): self.comdev.port = p
    @cfg_baudrate.setter
    def cfg_baudrate(self, p): self.comdev.baudrate = p
    @cfg_timeout.setter
    def cfg_timeout(self, p): self.comdev.timeout = p
    
    def open(self, *args,**kwargs): 
        self.comdev.open(*args,**kwargs)
        self.mode = COMMODES.CONNECTED
    
    def close(self, *args,**kwargs): 
        self.comdev.close(*args,**kwargs)
        self.mode = COMMODES.DISCONNECTED
    
    def read(self, *args, **kwargs): 
        return self.comdev.read(*args, **kwargs)
    
    def write(self, *args, **kwargs): 
        self.comdev.write(*args, **kwargs)
    
    def __str__(self):
        ''' return serial hardware device information '''
        return f"COM {self.devtype.name}: P={self.comdev.port} BAUD={self.comdev.baudrate} T={self.comdev.timeout} |" + \
               f"DAT={self.comdev.bytesize} STO={self.comdev.stopbits} PAR={self.comdev.parity} RTXCTS={self.comdev.rtscts} + X={self.comdev.xonxoff}"

class ComDevXBEE(ComDev):
    '''
    xbee communication device abstraction
    
    THREADS: NOT THREAD SAFE / CURRENTLY USE WITHIN A SINGLE THREAD
    '''
    devtype = COMTYPES.XBEE_GENERIC
    
    def __init__(self, ident="XBEE",
                 rx_packet_max=10, rx_max_buf=1024, chksum : bool = False, **kwargs):
        '''
        rx_packet_max .. maximum number of packets
        rx_max_buf .. maximum number of reception packet buffer
        chksum .. if enabled also calculate the xbee checksum
        '''            
        #initialize super class
        super().__init__(**kwargs)        
        self.ident = ident

        #reception configuration
        self.cfg_timeout_rx = 1.0 #maximum time to wait for finished packet reception    
        self.cfg_rx_buf_max = rx_max_buf #maximum reception buffer length
        self.cfg_rx_q_max = rx_packet_max
        self.cfg_chksum = chksum       
        self.clear()

    def clear(self):
        '''
        bring device into a default state, clears all temporary data, bring everything in a default state 
        '''
        self.rx_state = RXSTATES.IDLE
        self.rx_buf = b'' #reception buffer
        self.rx_buf_index = 0 #start of packet in the current reception buffer
        self.rx_q = queue.SimpleQueue() #the reception queue for finished packets
        self.rx_p_len = 0 #information about current packet, the number of bytes to receive
        self.rx_p_time = 0.0 #information about current packet, start of reception
        self.rx_buf_index = 0
        
    def _packet_done(self):
        '''
        called when a packet has been received
        '''
        if len(self.rx_buf) >= self.rx_buf_index + self.rx_p_len:
            p = self.rx_buf[self.rx_buf_index:self.rx_buf_index+self.rx_p_len]
            self.rx_buf = self.rx_buf[self.rx_buf_index+self.rx_p_len:]
            
          
            self.rx_q.put( p )
            self.rx_state = RXSTATES.DONE   
            if DBG_OUT: print(f"XBEE-RX [Q={self.rx_q.qsize()}]:", p, "BUF: ", self.rx_buf)
            return True
        else:
            return False
        
    def process_rx(self, rx=b'', chk_timeout=True, chk_buffer=True ):
        '''
        RX process loop, can be used from a buffer. We parse bytewise.
        
        do_check_chksum .. if True do a checksum check (but have slower processing time)
        chk_timeout .. if True do a timeout check (reset buffer in case of timeout)
        do_bufferchk .. if True check the buffer
        @TODO: can we do things to speed everything up, i.e., block based analysis
        
        
        @TODO: -> means self.rx_buf can become an integer
        '''        
        self.rx_buf += rx
        
        match self.rx_state:
            #this is ugly -> what about providing a range
            case RXSTATES.IDLE | RXSTATES.DONE | RXSTATES.OVERFLOW | RXSTATES.ERROR_CHKSUM | RXSTATES.ERROR:
                self.rx_state = RXSTATES.IDLE
                #we're still waiting for our startbyte to start a message
                #or we clear old errors
                #@TODO: match / case .. slower or faster than if - else?                
                self.rx_buf_index = 0
                if self.rx_buf_index >= 0:
                    self.rx_state = RXSTATES.BUSY    #okay now, let's resceive the rest of the message
                    self.rx_p_time = time.time()
                    
          
                    #do we have enough information to build a full packet?
                    if self.rx_p_len > 0:
                        if len(self.rx_buf) >= self.rx_buf_index + self.rx_p_len:
                            self._packet_done()
                    
            case RXSTATES.BUSY:
                if self.rx_p_len > 0:
                    if len(self.rx_buf) >= self.rx_buf_index + self.rx_p_len:
                        self._packet_done()
        
        if chk_timeout and self.rx_state == RXSTATES.BUSY:
            if (time.time() - self.rx_p_time) > self.cfg_timeout_rx:
                self.init()
                if DBG_OUT: print("XBEE-RX: TIMEOUT - RESET")
                self.rx_p_time = time.time()
                self.rx_state = RXSTATES.TIMEOUT 
        
        if chk_buffer:
            if len(self.rx_buf) > self.cfg_rx_buf_max:
                self.rx_buf = 0
                self.rx_state = RXSTATES.OVERFLOW
            if type(self.rx_buf) != type(b''): #error can happen due to array indexing?
                self.rx_buf = b''
            if self.rx_q.qsize() >= self.cfg_rx_q_max:
                if DBG_OUT: print("XBEE-RX: ERROR RX-QUEUE OVERFLOW DISCARDED PACKET")
                self.rx_q.get()
                
        return self.rx_state
    
    def read(self):
        ''' 
            read a raw binary packet from the XBEE device 
            return None in case there is nothing
        '''
        if self.rx_q.qsize() > 0:
            return self.rx_q.get()
        else:
            return None
                                                                
    def __str__(self):
        return f"{self.devtype} - {self.ident} RX-B: {len(self.rx_buf)} RX-Q: {self.rx_q.qsize()}"


class ComDevBasestation(ComDevXBEE):
    '''
    PRODAT BASESTATION a standard communication gateway
    '''
    devtype = COMTYPES.BASESTATION_XBEE
    #our default basestation configuration (@see: apps.prodat.basisstation) -> we need an import as module or as code
    DEF_HWCFG_STANDARD = {
        'PL':None,
        'CH':None,
    }
    
    def __init__(self, ident="Basestation", name=["B1"], comport=1, baudrate=57600, parity="N", stopbits=8, databits=1,
                 status=[0], **kwargs):
        super().__init__(**kwargs) 
        self.ident = ident  # basestation name/identification
        self.name = name
        self.comport = comport  # com-port --> 1,2,3 ...
        self.baudrate = baudrate  # bautrate --> 9600, 19200, 57600
        self.parity = parity  # parity --> None(N), Even(E), Odd(O), Mark(M), Space(S)
        self.stopbits = stopbits  # Stopbits --> 8
        self.databits = databits  # databits --> 1
        self.status = status
    
    def config_read(self):
        '''
        read base station configuration (the most important fields)
        '''
    
    def config_write(self):
        '''
        write base station configuration 
        '''
    
    def __str__(self):
        return f"Basestation: COM:{self.comport} BAUD:{self.baudrate} MODE: {self.mode}"

      
def tool_serialports_list():
    '''
    listing available serial ports -> return a serial.tools.list_ports_common.ListPortInfo object  
    we have available: 
        'description', 'device', 'hwid', 'interface', 'location', 'manufacturer', 'name', 
        'pid', 'product', 'serial_number', 'usb_description', 'usb_info', 'vid']
    
    '''
    return(serial.tools.list_ports_windows.comports())

def tool_serialports_xbeebasestation():
    '''
    listing serialports, of which we think these are base statoins
    '''
    bases = []
    ports = tool_serialports_list()
    for p in ports:
        if DBG_OUT:
            print(f"device={p.device} name={p.name} description={p.description} manufacturer={p.manufacturer} product={p.product}")
        
        #logic to check if it is a basestation or not
        if p.manufacturer.lower() == 'ftdi' and "usb serial port" in p.description.lower() :
            bases.append(p.device)
    return bases


#SUPPORT FOR TESTING
TEST_DEVLIST__BASESTATION = [
    ComDevBasestation(ident="Basestation 1", name=["B1"], comport=1, baudrate=57600, parity='N', stopbits=8, databits=1,
            status=[1]),
    ComDevBasestation(ident="Basestation 2", name=["B2"], comport=2, baudrate=57600, parity='N', stopbits=8, databits=1,
            status=[2])
]

def test_basestation_regularusage():
    '''
    simple testing, do we have everything we need - can we work with the abstraction?
    '''

###########################
# TESTCASES WITH HARDWARE #
###########################

def test_hw_comdevserial_regularusage(port, baudrate=57600):
    ''' test case and regular usage demonstration '''
    print("testing: comdevserial regular usage")
    sertest2 = ComDevSerial(port=None, baudrate=baudrate) #is this possible, it is
    sertest = ComDevSerial(port=port, baudrate=baudrate)
    print("using property decorator: sertest.cfg_port ", sertest.cfg_port)
    newport = "COM10"
    sertest.cfg_port = newport
    sertest.cfg_baudrate = "19200" #is float tolerant?
    sertest.cfg_baudrate = 19200.0 #is float tolerant?
    sertest.cfg_timeout = None
    print(sertest)
    #port
    assert sertest.cfg_port == newport
    assert sertest.comdev.port == newport
    #timeout
    assert sertest.comdev.timeout == None
    assert sertest.cfg_timeout == None
    #baudrate
    assert sertest.cfg_baudrate == 19200
    assert sertest.comdev.baudrate == 19200

    ret = tool_serialports_list()
    print("Identified serial ports:")
    for item in ret:
        print(item.device, item.name)
    ret = tool_serialports_xbeebasestation()
    print("Ports with identified basestations:" + str(ret))

def test_hw_comdevxbee_regularusage(comport="", baudrate=57600):
    ''' test case for regular xbee com dev usage '''
    print("Testing XBEE module with regular hardware on comport: %s" % comport)

    import serial
    import serial.tools.list_ports_windows
    
    print("active serialports")
    print("------------------")
    for index,item in enumerate(serial.tools.list_ports_windows.comports()):
        print(" ", str(index), "|", str(item))
    
    ser = ComDevSerial(port=comport, baudrate=baudrate)
    ser.open()
    ser.close()
    ser.open()
    print(ser)
    xbee = ComDevXBEE(ident="testdevice")
    print(xbee)
    
    while 1:
        rx = ser.read(200)
        if rx != b"":
            print("RAW: " + str(rx))
            print("HEX: "+"".join([str("%02X " % b) for b in rx]))
            print( xbee.process_rx(rx[0:2]) )
            print( xbee.process_rx() )
            print( xbee.process_rx() )
            print( xbee.process_rx() )
            print(xbee)
            
            stresstest = False
            if stresstest:
                print(xbee.process_rx(b'')   ) #process a second time
                print(xbee.process_rx(b'')   )
                print("TIMING TEST")
                time_start = time.time()
                for i in range(1,100):
                    xbee.process_rx(rx)
                time_stop = time.time() - time_start
                print("RUNTIME=%f per 100" % time_stop)            

def test_comdevxbee_regularusage():
    print("testing comdevxbee: regularusage")
    import testdata
    xbee = ComDevXBEE(ident="testdevice", chksum=True)
    p_test = testdata.senet_sensor_raw_msgstatus_bkm_1[0]
    p_test_error = testdata.senet_sensor_raw_msgstatus_bkm_1[0][:-1] + b'\23' #checksum error
    
    ret = xbee.process_rx(p_test)
    assert RXSTATES.DONE == ret    
    assert RXSTATES.ERROR_CHKSUM == xbee.process_rx(p_test_error)
    assert RXSTATES.DONE == xbee.process_rx(p_test)
    
    
if __name__ == '__main__':
    print("running: xkm comdev.py - standalone testing")
    cfg_comport = "COM4"
    cfg_baudrate = 57600
    cfg_hwsupport = False
    c_senfile = ComDevFile()
    print(c_senfile)
    c_senfile.open()
    c_senfile.write("WROTE MEASUREMENT VALUES TO A FILE")
    ret = c_senfile.read()
    print("read measurement data file: ", ret)
    c_senfile.close()
    
    
    test_basestation_regularusage()
    test_comdevxbee_regularusage()
    
    if cfg_hwsupport:
        #tests which require connected hardware: with serialport
        test_hw_comdevserial_regularusage(port=cfg_comport, baudrate=cfg_baudrate)
        test_hw_comdevxbee_regularusage(comport=cfg_comport, baudrate=cfg_baudrate)
    
    
    print("demonstration is done")