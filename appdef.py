'''
Python XKM - central definitions and declarations
'''
from enum import Enum
from dataclasses import dataclass
from typing import List

# APPLICATION SCREEN NAME DEFINITIONS (names avaiable here, useable in all modules)
@dataclass(frozen=True)
class APPSCREEN():
    '''
    APPLICATION SCREEN NAMES
    '''
    MULTIMETER = "screen-measure-multimeter"
    OSCI = "screen-measure-oscilloscope"
    MEASURE_CFG = 'screen-measure-cfg' #measurement configuration

################################
# XKM, RKM and BKM definitions #
################################
#MAX VALUES
MAX_SYSTEMS = 99 #maximum number of different measurement systems we support

# Bisherige Hardwareabfragen
##############
# RKM
##############
# RKM-M Funk mobil SeNET Kommunikation: doMeasureRKM (Messwerte kommen automatisch an)
#  Eingang: 2 Kanäle roh
#    Einzelwerte kalibriert
#    Zusatzkalibrierung: Anwendung Mittelwertkennlinie auf Grundlage der beiden kalibrierten Einzeleingänge (ab Schwellwert)
#  Ausgang -> ein Endwert 
#
# RKM-S stationär SeNET Kommunkation: pollende Abfrage via Kommandosatz Protokoll
#  Kommunikation Eingang:
#  Abfrage  / Antwort : Commandset-Protokoll (doXXX)
#  Eingang: 2 Kanäle roh
#    Einzelwerte kalibriert 
#    Zusatzkalibrierung: Anwendung Mittelwertkennlinie auf Grundlage der beiden kalibrierten Einzeleingänge (ab Schwellwert)
#  Ausgang -> ein Endwert 
#
# RKM-S stationär SeNET Kommunkation: pollende Abfrage via Simple-Date Protokoll
#  Kommunikation Eingang:
#  Abfrage  / Antwort : Simple-Data
#  Eingang: 2 Kanäle roh
#    Einzelwerte kalibriert 
#    Zusatzkalibrierung: Anwendung Mittelwertkennlinie auf Grundlage der beiden kalibrierten Einzeleingänge (ab Schwellwert)
#  Ausgang -> ein Endwert 
#
# RKM-S stationär ADAM Kommunikation: pollende Abfrage
#  Kommunikation Eingang:
#  Abfrage / Antwort Adam-Modul
#
#  Eingang: 2 Kanäle roh
#    Einzelwerte kalibriert 
#    Zusatzkalibrierung: Anwendung Mittelwertkennlinie auf Grundlage der beiden kalibrierten Einzeleingänge (ab Schwellwert)
#  Ausgang -> ein Endwert 
##############
# BKM
##############
# BKM Funk mobil Scheibe (+ Klotz bis KG1) SeNET
#  Kommunikation Eingang:
#   doMeasure (Protokoll DD, Messwerte kommen automatisch an)
#
#
#  Eingang: 2 Kanäle roh
#  Ausgang -> Eingänge Summiert, Kalibriert (eine Kennline) 
# BKM Funk mobil Klotz (ab KG-2) SeNET
#  Kommunikation Eingang:
#   doMeasure (Protokoll DD, Messwerte kommen automatisch an)
# 
#  Eingang: 1 Kanale roh (CH0 wird nur verwendet, Kanal 1 wird 0 gesetzt)
#  Ausgang -> Eingang, kalibriert (eine Kennline) 
#
# BKM Funk mobil Single DruckIF SeNET
#  Kommunikation Eingang:
#   doMeasure (Protokoll DD, Messwerte kommen automatisch an)
# 
#  Eingang: 1 Kanale roh * 1.0E-05   
#  Ausgang -> unkalibriert, kann genullt werden
# BKM Funk mobil Multi DruckIF SeNET
#  Kommunikation Eingang:
#   doMeasure (Protokoll DD, Messwerte kommen automatisch an)
# 
#  Eingang: 1 Kanale je Drucksensor: roh * 1.0E-05   
#  Ausgang -> Eingang, unkalibriert, kann genullt werden 
#
# BKM Kabel mit AnalogIF mobil Scheibe
#  Kommunikation Eingang:
#   mit Abfrage, SimpleData
#  Eingang: 2 Kanäle roh
#  Ausgang -> Eingänge Summiert, Kalibriert (eine Kennline) 
# BKM Kabel via LabJack Scheibe
#  Kommunikation Eingang:
#   mit pollender Abfrage
#  Eingang: 2 Kanäle roh
#  Ausgang -> Eingänge Summiert, Kalibriert (eine Kennline) 
##############
# DGP
##############
# DGP BVG
#  Kommunikation Eingang:
#   RS485 - SPS für Zylinderposition, ADAM, Regeleung via Reglerkarten
# DGP - SBahn
#  Kommunikation Eingang:
#   RS485 - ADAM, Reglerkarten
# DGP BSAG, Polen
#  Kommunikation Eingang:
#   RS485 - SPS, ADAM
##

class DEF_SENSORTYPES(Enum):
    '''
    SENSORTYPE DEFINITIONS
    @please note: specified are the used/active raw measurement channels
    
    OLD:
    TYPE_BKM = "BKMS"  # one measurement channel per sensor @NOTE: global definition later
    TYPE_RKM = "RKMS"  # one measurement channel per sensor @NOTE: global definition later
    TYPE_PSING = "PSING"  # single pressure sensor
    TYPE_PMULT4 = "PMULT4"  # multi pressure sensor 4
    TYPE_PMULT6 = "PMULT6"  # single pressure sensor 6
    '''
    NONE = -1 #SENSOR TYPE IS NOT SET - this is an error case
    
    #BKM Wireless
    PRO_BKM_W_1CH0 = 1 #PRODAT BKM WIRELESS -> only CH0 holds valid data and is evaluated -> single calibrated output channel
    PRO_BKM_W_1CH1 = 2 #PRODAT BKM WIRELESS -> only CH1 holds valid data and is evaluated -> single calibrated output channel
    PRO_BKM_W_2CH_SUM  = 3 #PRODAT BKM WIRELESS -> both channels [chan0 and chan1] are evaluated -> single calibrated output channel (summed)
    PRO_BKM_W_2CH_DUAL = 4 #PRODAT BKM WIRELESS -> both channels [chan0 and chan1] are evaluated -> two calibrated output channels
    
    #RKM-M 
    PRO_RKM_W_2CH = 8 #PRODAT BKM WIRELESS -> Two Channels are evaluated and calibrated
    PRO_RKM_RS485_2CH = 9 #PRODAT RKM cable via RS485 communication
    
    #PRODAT pressure sensor interfaces
    PRO_PINT_W_CH1 = 10
    PRO_PINT_W_CH2 = 11
    PRO_PINT_W_CH4 = 12
    PRO_PINT_W_CH6 = 14
    PRO_PINT_W_CH8 = 16
    
    #PRODAT analog interface
    PRO_AINT_S_CH2 = 20 #Analog Interface mit serieller ("S") kommunikation, daten werden automatisch verschickt
    PRO_AINT_W_CH2 = 21 #Analog Interface with wireless communication. Two independent input channels (summed) -> one calibrated output channel 
    
    #ADANTEC ADAM Modules
    PRO_ADAM_4CH = 101 #ADAM ADVANTEC Module with 4 measurement channels
    PRO_ADAM_8CH = 102 #ADAM ADVANTEC Module with 4 measurement channels


'''
measurement system definitions
#measurement system types (hardware) -> @TODO: this is in appdef now
class DEF_SYSTYPES(enum.Enum):
    MEASSYS_XKM   = "0"  #measurement system XKM (default) -> general abstraction
    MEASSYS_RKM_W = "1"   
    MEASSYS_RKM_F = "2"
    MEASSYS_BKM_W = "3"    
'''
class DEF_SYSTEMTYPES(Enum):
    NOTSET = -1 #signals also an error, or something went wrong
    XKM    =  0 
    BKM    =  1 #BKM measurement system (we currently use for the development)
    RKM_W  =  2 #RKM Mobil/Wireless  
    RKM_S  =  3 #RKM Stationary/Cable 
     
    
class DEF_GATEWAYTYPES(Enum):
    '''
    @TODO: is this still needed -> move into comdevs?
    '''
    BASESTATION = 1 

class DEF_SENSORGROUPES(Enum):
    '''
    DEFAULT SENSORGROUP SPECIFICATION
    '''
    NONE = 0
    FORCE = 1
    PRESSURE = 2
    ADAM_VOLTAGE = 10
    ADAM_CURRENT = 11
