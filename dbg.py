'''
debugging support and definitions. this module is/can be part of all other modules.
'''
import sys
    
ON = True #if disabled, all DBG_ switch are set to False via disable()

#debug switches = "S"
DBG_OUT = False #enable/disable for additional printf debugging
DBG_APPXKM_STARTMENU_TESTBUTTON = True #show an additional button for testing purposes (with a test menue)
DBG_APPXKM_SYSMSGS_TWICE_AFTER_START = False #shows system messages two times, if enabled
DBG_APPXKM_NOLOGIN = True
DBG_SCREENSHOTS = False #if enabled, automatically create screenshots 
DBG_SENSORSTATUS = False # if enable, automatically update sensorstatus

# MEASUREMENT SYSTEM, SENSOR, CHANNEL TESTING AND SO ON
#######################################################
DBG_SYSTEM_USE_DEFAULT_SENSORLIST = True #if enabled, do not use system list from ini but force default on

# VEHICLES - DBG 
class DEF_VEHICLES:
    FROM_TESTLIST = 0
    FROM_INIFILES = 1
    FROM_TESTDB = 2

DBG_VEHICLE_SOURCE = DEF_VEHICLES.FROM_TESTLIST
DBG_USE_TESTVEHICLES = True

# THREAD COLLECTOR TESTING
###########################
DBG_THRCOL_OUTPUT = False #if enabled, additional print output for collector threads
DBG_THRCOL_COMTEST = True #if enabled, we do com object override
DBG_THRCOL_COMOVERRIDE = False # if enabled, override communication
DBG_THRCOL_USETESTMSG = False # if enabled, parse test message
DBG_THRCOL_TESTMSG = True # if enabled, use a testmessage from testdata

DBG_THRAGG_OUTPUT = False #if enabled, addtional output for aggregator & control thread
DBG_CLOCK_OUTPUT = False #if enabled, additional GUI update clock print output (fast & slow)
#MEASUREMENT SYSTEM TESTING
DBG_MSYS_OVERRIDE_INIT = True

#DEBUGGING AND TESTING OF SERIAL PORT & COMMUNICATION
DBG_SERIAL_PORTS = ["COM4","COM6"] #for testing purposes, specify serial ports to use
DBG_SERIAL_BAUD = 57600 


DBG_EULAFORCELANG = "de" #if not empty force specified language
DBG_EULAFORCELANG_ENCODING = "utf-8"

#USE FIX DATA FOR TESTING
DBG_REPORT_FIXDATA = True #use fixed data from a file to generate a report

#DBG MODULE: measyspy
DBG_MEASYS_MDATAINIT_WITH_NODEADDR = True #if enabled, inititalize measurement data array with sensor node addr

# SIMULATED VALUE BEHAVIOUR
############################
class DEF_DATATESTMODES:
    WIDGETSIMU = 0
    REALDATA_CHANCURRENT = 1 #update with current measurement values (from channel data)
    REALDATA_ARYCURRENT = 2 #update with measurement array values (from a large numpy measurement data array)

DBG_DATATESTMODE = DEF_DATATESTMODES.REALDATA_CHANCURRENT
DBG_SIMU_OSCI = True
    
def disable():
    '''
    enable/disable all debugging flag switches starting with 'DBG_' -> function executed during module import
    '''
    global ON
    module = sys.modules[__name__]
    if not ON:
        for para in dir(module):
            if "DBG_" in str(para):
                print("DBG-OPTION:",para)
                setattr(module, para, False)

disable()
 
def dbgmsg(*args,**kwargs):
    ''' print a printf debugging message, in case this output is activated. This is independet from logging '''
    if DBG_OUT: print("DBG:",*args,**kwargs)
  
if __name__ == '__main__':
    print(DBG_OUT, "DBG_OUT should be True = enabled()")
    ON = True
    disable()
    print(DBG_OUT, "DBG_OUT must be False -> since OFF = True")