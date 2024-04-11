###########
# Imports #
########### 

#python standard lib imports first 
import random
import time
import os
import logging

#python 3rd party imports 
import matplotlib
#matplotlib._png = None
#matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
#optimized draw on Agg backend
matplotlib.rcParams['path.simplify'] = True
matplotlib.rcParams['path.simplify_threshold'] = 1
matplotlib.rcParams['agg.path.chunksize'] = 10000

#define some matplotlib figure parameters
matplotlib.rcParams['font.family'] = 'Verdana'
matplotlib.rcParams['axes.spines.top'] = False
matplotlib.rcParams['axes.spines.right'] = False
matplotlib.rcParams['axes.linewidth'] = 1.0

mplstyle.use('fast')

from matplotlib.widgets import Button as matplotButton

import numpy as np
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ColorProperty,NumericProperty,StringProperty
from matplotlib.backend_bases import MouseEvent
from matplotlib.backend_bases import PickEvent
from kivy_matplotlib_widget.uix.hover_widget import add_hover,HoverVerticalText,InfoHover,BaseHoverFloatLayout


import designeles_guikv
import guitools_kv
import dbg
import top_menue_bar
import meassys
import appdef
import measdata
import osci_guikv
import appglobals
    
    
    
GLOB = appglobals.GLOB  # global variables
CFG = GLOB.CFG  # global app configuration except guis

TOP_MENUE = top_menue_bar.TopMenueBar

Window.clearcolor = (1, 1, 1, 1)

class DiaSelect(BoxLayout):
    '''
    Functionality for changing the diagramm data e.g. group selection
    '''
    def diagselected(self,value):
        if dbg.DBG_OUT: print("DiaSelect diagselected() called, value:" + value)
        self.ids.spinner_id.text = value
        osciWidget =guitools_kv.find_element_by_class_parent_recursive(self, MeasureOscilloscopeMainWidget)
        osciWidget.livePlot.changedata(value)

class MarkerSelect(BoxLayout):
    '''
    Functionality for changing the marker for the osci grafical evaluation
    '''
    def markerselected(self,value):
        self.ids.spinner_id.text = value


KVSTR_TEMPLATES = f'''
<DataGuiSeparator@Widget>:
    canvas:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size
            
            
<HDataGuiSeparator@DataGuiSeparator>:
    size_hint_y: None
    height: dp(2)  
'''


KVSTR_MeasureMultimeterEntry = f'''
<LabelCFG@Label>:
    text: '0.00'
    color: (0,0,0,1)
    background_color: (1, 1, 1, 1)
    font_size:'{appglobals.GLOB.GUI.fonsize_lab}'
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos

<MeasureOscilloscopeEntry>
    orientation:'vertical'
    size_hint_y: None 
    height:30
    BoxLayout:
        size_hint_y: 1 
        height: self.minimum_height
        Button:
            id: entry_sensorname
            size_hint_y: 1
            text_size:self.size
            halign:'center'
            valign:'middle'
            text:"F1"         
            font_size:'{appglobals.GLOB.GUI.fonsize_lab}'
        LabelCFG
            id: entry_sensorvalue
            valign:'middle'
        Label:
            id: entry_sensorunit
            size_hint_y: 1
            #text_size:self.size
            valign:'middle'
            text:"g"   
            font_size:'{appglobals.GLOB.GUI.fonsize_lab}'                
'''


class MeasureOscilloscopeEntry(BoxLayout):
    '''
    OscilloscopeEntry represents an entry consisting of Sensor-Shortdescription (e.g. F1, P1, etc.), 
    the current value as Label and the unit of the measure value
    '''
    def __init__(self, **kwargs):
        super(MeasureOscilloscopeEntry, self).__init__(**kwargs)

    def build_gui(self):
        pass


# KV STRING
KVSTR_MeasureMultiMainWidget = f'''
#:import Factory kivy.factory

<MySpinnerOptionCFG@SpinnerOption>: #notwendig um auch die Auswahlmöglichkeiten mit einer Schriftart zu belegen
    font_size:'{appglobals.GLOB.GUI.fontsize_but}'
    data: None


<DiaSelect>
    Spinner:
        id:spinner_id
        text:"Sensoren"
        option_cls: "MySpinnerOptionCFG"
        values: ['A-Sensor','Z-Sensor','A+Z-Sensor']
        on_text: root.diagselected(spinner_id.text)
        font_size:'{appglobals.GLOB.GUI.fontsize_but}'

<MarkerSelect>
    Spinner:
        id:spinner_id
        text:"Marker"
        option_cls: "MySpinnerOptionCFG"
        values: ["Marker1", "Marker2", "Marker3", "Marker4", "Marker5"]
        on_text: root.markerselected(spinner_id.text)
        font_size:'{appglobals.GLOB.GUI.fontsize_but}'        

<PlotlyHover>
    custom_color: [0,0,0,1]
    BoxLayout:
        id:main_box
        x:
            root.x_hover_pos + dp(4)
        y:
            root.y_hover_pos - root.hover_height/2
        size_hint: None, None
        height: label.texture_size[1]+ dp(4)
        width: 
            self.minimum_width + dp(12) if root.show_cursor \
            else dp(0.0001)            
        orientation:'vertical'
        padding: 0,-dp(1),0,0
        
        canvas:            
            Color:
                rgba: root.custom_color if root.custom_color else [0,0,0,1]
            Rectangle:
                pos: self.pos
                size: self.size
            Triangle:
                points:
                    [ \
                    root.x_hover_pos, root.y_hover_pos, \
                    main_box.x, root.y_hover_pos+ dp(4), \
                    main_box.x, root.y_hover_pos- dp(4)  \
                    ]
            SmoothLine:
                width:dp(1)
                points:
                    [ \
                    root.x_hover_pos, root.y_hover_pos, \
                    main_box.x, root.y_hover_pos \
                    ]                           
             
        BoxLayout:
            size_hint_x:None
            width:label.texture_size[0]
            padding: dp(12),0,0,0
            Label:
                id:label
                text: 
                    '(' + root.label_x_value  +','+ root.label_y_value +')'
                font_size:root.text_size
                color:
                    [0,0,0,1] if (root.custom_color[0]*0.299 + \
                    root.custom_color[1]*0.587 + root.custom_color[2]*0.114) > 186/255 \
                    else [1,1,1,1]
                font_name : root.text_font

                font_name : root.text_font
                
        FloatLayout:
            size_hint: None,None
            width: dp(0.01) 
            height: dp(0.01) 
            BoxLayout:
                size_hint:None,None
                x:main_box.x + main_box.width + dp(4)
                y:main_box.y + main_box.height/2 - label3.texture_size[1]/2
                width:label3.texture_size[0]
                height:label3.texture_size[1]
                Label:
                    id:label3
                    text: 
                        root.custom_label if root.custom_label else ''  
                    font_size:root.text_size
                    color: root.text_color
                    font_name : root.text_font      

        
<MeasureOscilloscopeMainWidget>
    orientation:'vertical'
    size_hint_y: 1
    spacing: 3
    padding: {GLOB.GUI.padding_m}   
    TopMenueBar:
        size_hint: 1,None
        height: 65
        id: id_top_menu_bar
    GridLayout:
        cols:5
        size_hint_y: 0.05
        row_force_default: True
        row_default_height: 35
        spacing:{appglobals.GLOB.GUI.spacing_m}    
        Button:
            size_hint_y: 0.1
            size_hint_x: 0.8
            text:"Null" 
            on_press: root.ev_btn_null()
            font_size:'{appglobals.GLOB.GUI.fontsize_but}'
        Button:
            size_hint_y: 0.1
            size_hint_x: 0.8
            text:"Start" 
            on_press: root.ev_btn_start()
            font_size:'{appglobals.GLOB.GUI.fontsize_but}'
        Button:
            size_hint_y: 0.1
            size_hint_x: 0.8
            text:"Stopp" 
            on_press: root.ev_btn_stop()
            font_size:'{appglobals.GLOB.GUI.fontsize_but}'            
        Button:
            size_hint_y: 0.1
            size_hint_x: 0.8
            text:"Speichern" 
            on_press: root.ev_btn_save()
            font_size:'{appglobals.GLOB.GUI.fontsize_but}'   
        Button:
            size_hint_y: 0.1
            size_hint_x: 0.8
            text:"Halten" 
            on_press: root.ev_btn_hold()
            font_size:'{appglobals.GLOB.GUI.fontsize_but}'                                  
    GridLayout:
        cols:2
        #cols_minimum:''' + '''{0: 620, 1: 100}'''+f'''        
        size_hint_y: 1
        
        spacing:{appglobals.GLOB.GUI.spacing_m}    
        BoxLayout:
            orientation: 'vertical'
            size_hint:3.5,1
            height: self.minimum_height 
            #pos_hint:  '''+'''{'center_x': 0.9, 'center_y': 0.9}'''+f'''
            #id: plotscreenLive
            MatplotFigureCustom:
                id:plotscreenLive
        BoxLayout:
            orientation: 'vertical'
            size_hint:1,1
            height: self.minimum_height 
            GridLayout:
                cols:2          
                size_hint_y: 1
                spacing:{appglobals.GLOB.GUI.spacing_m}            
                Label:
                    text: "Diagramm"
                    font_size:'{appglobals.GLOB.GUI.fonsize_lab}'
                DiaSelect:
            ScrollView:
                id:sensorscroll       
                size_hint_y: None
                size_hint_x: 1
                height: 550 
                #width:200 #WEG    
                GridLayout:
                    cols:1
                    size_hint_y: None  
                    id: sensormeasure_column   
                    height: self.minimum_height      
                    width:50 #WEG
                    BoxLayout:
                        id:col_BKMsensors
                        orientation:'vertical' 
                        size_hint_y: None
                        height: self.minimum_height                                                                                           
                        Label:
                            size_hint_y: None
                            height:30
                            text_size:self.size
                            halign:'left'
                            valign:'top'                        
                            text:"Beschleunigungssensor" 
                            font_size:'{appglobals.GLOB.GUI.fonsize_lab}'
                    DesignSepHori                  
                    BoxLayout:
                        id:col_PSINGsensors
                        orientation:'vertical' 
                        size_hint_y: None
                        height: self.minimum_height     
                        Label:
                            size_hint_y: None
                            height:30
                            text_size:self.size
                            halign:'left'
                            valign:'top'                        
                            text:"Zusatzsensor 1CH" 
                            font_size:'{appglobals.GLOB.GUI.fonsize_lab}'
                    DesignSepHori                                                                                                    
                    BoxLayout:
                        id:col_PMULT4sensors
                        orientation:'vertical'                                                        
                        size_hint_y: None
                        height: self.minimum_height                                         
                        Label:
                            size_hint_y: None
                            height:30
                            text_size:self.size
                            halign:'left'
                            valign:'top'                        
                            text:"Zusatzsensor 4CH" 
                            font_size:'{appglobals.GLOB.GUI.fonsize_lab}'                                                             
                    DesignSepHori                                                                                                                   
                    BoxLayout:
                        id:col_PMULT6sensors
                        orientation:'vertical'                                                        
                        size_hint_y: None
                        height: self.minimum_height    
                        Label:
                            size_hint_y: None
                            height:30
                            text_size:self.size
                            halign:'left'
                            valign:'top'                        
                            text:"Zusatzsensor 6CH" 
                            font_size:'{appglobals.GLOB.GUI.fonsize_lab}'  
                    DesignSepHori                                                                                                                                      
'''
KVSTR_MeasureMultiMainWidget = KVSTR_MeasureMultiMainWidget #+ "\n" + TOP_MENUE_KV_STR

class MeasureOscilloscopeMainWidget(BoxLayout):
    '''
    Oscilloscope Widget for dynamic generation/adding of the different sensor types in a scroll view / main plot etc
    '''
    def __init__(self, **kwargs):
        super(MeasureOscilloscopeMainWidget, self).__init__(**kwargs)
        
        self.initial_measuresystem = None
        #Dict mit GUI-Elementen vom Typ MeasureOscilloscopeEntry (Darstellung der Messwert und Einheitlabels)
        self.sensor_dict = {}
        #Anzahl der Datenpakete bis Update des Diagramms
        #TODO Parameter definiert appfdef / cfg
        self.batch_update_count = 50
        #Hält die gepufferten Daten vor --> [[zeit,y,sensorID]]
        self.plot_batch_data = []
        
        #back button functionality
        self.screen_manager = None
        self.screen_back = None
        self.update_plot = True
        #Referenz zum MatplotFigureCustom-Objket
        self.matplotfigure = None   
        self.timeidx = 0
    def build_gui(self):
        
        #TODO ggf. komplett automatisch erstellen? Dazu muss auch der KV-String teil dynamisiert werden...
        self.scroll_grid_force = GridLayout(width=100, cols=1, size_hint_y=None, spacing=10, height=50)
        self.scroll_grid_force.cols = 2
        self.scroll_grid_force.height = self.minimum_height
        self.scroll_grid_force.bind(minimum_height=self.scroll_grid_force.setter('height'))
        self.ids.col_BKMsensors.add_widget(self.scroll_grid_force)
        

        self.scroll_grid_pressure = GridLayout(width=100,cols=1, size_hint_y=None, spacing=10, height=100)
        self.scroll_grid_pressure.height = self.minimum_height
        self.scroll_grid_pressure.cols = 2
        self.scroll_grid_pressure.bind(minimum_height=self.scroll_grid_pressure.setter('height'))
        self.ids.col_PSINGsensors.add_widget(self.scroll_grid_pressure)
        
        self.scroll_grid_pressuremult4 = GridLayout(width=100,cols=1, size_hint_y=None, spacing=10, height=100)
        self.scroll_grid_pressuremult4.height = self.minimum_height
        self.scroll_grid_pressuremult4.cols = 2
        self.scroll_grid_pressuremult4.bind(minimum_height=self.scroll_grid_pressuremult4.setter('height'))
        self.ids.col_PMULT4sensors.add_widget(self.scroll_grid_pressuremult4)

        self.scroll_grid_pressuremult6 = GridLayout(width=100,cols=1, size_hint_y=None, spacing=10, height=100)
        self.scroll_grid_pressuremult6.height = self.minimum_height
        self.scroll_grid_pressuremult6.cols = 2
        self.scroll_grid_pressuremult6.bind(minimum_height=self.scroll_grid_pressuremult6.setter('height'))
        self.ids.col_PMULT6sensors.add_widget(self.scroll_grid_pressuremult6)
        
        '''
        self.scroll_grid_virtual = GridLayout(width=100,cols=1, size_hint_y=None, spacing=10, height=100)
        self.scroll_grid_virtual.height = self.minimum_height
        self.scroll_grid_virtual.cols = 2
        self.scroll_grid_virtual.bind(minimum_height=self.scroll_grid_virtual.setter('height'))
        self.ids.col_VIRTUALsensors.add_widget(self.scroll_grid_virtual)

        self.scroll_grid_BPA = GridLayout(width=100,cols=1, size_hint_y=None, spacing=10, height=100)
        self.scroll_grid_BPA.height = self.minimum_height
        self.scroll_grid_BPA.cols = 2
        self.scroll_grid_BPA.bind(minimum_height=self.scroll_grid_BPA.setter('height'))
        self.ids.col_BPAsensors.add_widget(self.scroll_grid_BPA)        
        '''
        
        #self.ids.sensorscroll()
        self.livePlot = LivePlot()
        self.matplotfigure = self.ids["plotscreenLive"]

        self.matplotfigure.figure = self.livePlot.fig
        self.livePlot.register_matplotwidget(self.matplotfigure)

        #self.ids["plotscreenLive"].register_cursor()
        #add_hover(self.ids["plotscreenLive"],mode='desktop',hover_widget=PlotlyHover())
        self.build_meas_gui()

    def ev_btn_stop(self):
        if dbg.DBG_OUT: print("screen_measosci_guikv: ev_btn_stop")
        self.update_plot = False
        self.livePlot.stop_plot()

    def ev_btn_start(self):   
        if dbg.DBG_OUT: print("screen_measosci_guikv: ev_btn_start")     
        self.update_plot = True
        self.livePlot.start_plot()

    def ev_btn_null(self):   
        if dbg.DBG_OUT: print("screen_measosci_guikv: ev_btn_null")    
        GLOB.USER_LOGGER.write_message('Execution of zeroing') 

    def ev_btn_save(self):   
        if dbg.DBG_OUT: print("screen_measosci_guikv: ev_btn_save")     

    def ev_btn_hold(self):   
        if dbg.DBG_OUT: print("screen_measosci_guikv: ev_btn_hold")    

    def ev_btn_sensor(self,button,sensor):
        if dbg.DBG_OUT: print("screen_measosci_guikv: ev_btn_sensor " + button.text + " " + sensor.df_type_v)    



    def change_size(self,window_size):
        self.ids.sensorscroll.height = (window_size[1] ) - 145
        '''self.ids.col_BKMsensors.height = (window_size[1] / 2)- 120
        self.ids.col_PSINGsensors.height = (window_size[1] / 2) - 120
        self.ids.col_PMULT4sensors.height = (window_size[1] / 2) 
        self.ids.col_PMULT6sensors.height = (window_size[1] / 2) '''
       # print(self.ids.scrollview_measure_mulit_main_widget.height)
       # self.scroll_grid_force.change_size(window_size)

    def screenback(self, sm, screen_back):
        '''
        sets the screen to go back to, provide screenmanager sm and name of screen 'screen_back'
        '''
        if dbg.DBG_OUT: print("vehicle_guikv: set back screen to", screen_back)
        self.screen_manager = sm
        self.screen_back = screen_back

    '''dynamisch GUI Komponenten basierende auf dem gesetzten System erzeugen'''
    def build_meas_gui(self):

        for sensor in self.initial_measuresystem.sensors:
            sensorname = ""    
            scroll_grid = None
            sensorname = sensor.df_nameapp_v
            if sensor.devtype == appdef.DEF_SENSORTYPES.PRO_BKM_W_2CH_SUM:
                scroll_grid = self.scroll_grid_force
                

            if  sensor.devtype == appdef.DEF_SENSORTYPES.PRO_PINT_W_CH1:               
                scroll_grid =  self.scroll_grid_pressure

            if  sensor.devtype == appdef.DEF_SENSORTYPES.PRO_PINT_W_CH4:               
                scroll_grid =  self.scroll_grid_pressuremult4                

            if  sensor.devtype == appdef.DEF_SENSORTYPES.PRO_PINT_W_CH8:               
                scroll_grid =  self.scroll_grid_pressuremult6
            '''
            if  sensor.type == TYPE_BPA:               
                numSensorBPA += 1
                sensorname = "pX"+str(numSensorBPA)
                scroll_grid =  self.scroll_grid_BPA

            if  sensor.type == TYPE_VIRTUAL:               
                numSensorVIRTUAL += 1
                sensorname = "V"+str(numSensorVIRTUAL)
                scroll_grid =  self.scroll_grid_virtual'''

            channel = 0
            for i in range(0,len(sensor.chans_out)):
                sensor_ident = sensor.df_idpro_v + "_" + str(channel)
                sensor.chans_out[i].df_nameapp_v = sensorname

                measure_osci_entry = MeasureOscilloscopeEntry()
                self.sensor_dict[sensor_ident] = measure_osci_entry
                measure_osci_entry.ids.entry_sensorvalue.text = str(sensor.chans_out[i].val)
                measure_osci_entry.ids.entry_sensorunit.text = sensor.chans_out[i].unit
                measure_osci_entry.ids.entry_sensorname.text = sensor.chans_out[i].df_nameapp_v
                measure_osci_entry.ids.entry_sensorname.bind(on_press= lambda x: self.ev_btn_sensor(x,sensor))
                if scroll_grid :
                    scroll_grid.add_widget(measure_osci_entry)

                
                channel = channel+1

    ''' setzt die aktive Messkonfiguration.
        Eine Liste der zu verwendenden Sensoren. Die GUI wird damit aufgebaut. Akualisierung erfolgt über 
        Kanalliste in der update_vals() Methode.
    '''
    def set_measure_config(self,measuresystem):
        self.initial_measuresystem = measuresystem
       

    '''
        Aktualisiert die GUI mit den Daten aus numpy-Arrays für Daten und Zeit.
        Achtung: Die Liste muss genausoviele Elemente haben, wie sie durch die festgelegten
        Sensoren und damit einhergehenden Kanalanzahl in set_measure_config() definiert wurden

    '''
    def update_numpy_data(self, data_y,data_t):
        if not np.all(np.isnan(data_y)): 
            daty = data_y.copy()        
            datt = data_t.copy()
            self.update_vals(daty,timelist= datt)
    '''
        Aktualisiert die GUI mit den Daten aus dem MeasurementData-Objekt.
        Achtung: Die Liste muss genausoviele Elemente haben, wie sie durch die festgelegten
        Sensoren und damit einhergehenden Kanalanzahl in set_measure_config() definiert wurden

    '''
    def update_measurement_data(self,measurement_data):
        self.update_numpy_data(measurement_data.md_current_y[0],measurement_data.md_current_t[0])

    ''' Aktualisiert die GUI mit den angegebenen Messwerten.
        Achtung: Die Liste muss genausoviele Elemente haben, wie sie durch die festgelegten
        Sensoren und damit einhergehenden Kanalanzahl in set_measure_config() definiert wurden
        wird keine Zeitliste angegeben, wird automatisch die time.time() verwendet
    '''
    def update_vals(self, channellist,timelist=[],update_osci = True, update_text = True):
        
        #TODO prüfen, dass die channellist-Länge nicht kürzer ist, als sie sein darf, analog dann timelist    

        channel = 0
        for sensor_ident in self.sensor_dict:
            try:
                measure_osci_entry = self.sensor_dict[sensor_ident]
                measure_osci_entry.ids.entry_sensorvalue.text = str(channellist[channel])
             
                if self.update_plot:
                    if self.batch_update_count > 0:
                        self.batch_update_count = self.batch_update_count-1
                        if timelist != []:
                            t = time.time()
                            self.timeidx = self.timeidx+1
                            t = self.timeidx
                        else:
                            t = timelist[channel]
                        self.plot_batch_data.extend([[t,channellist[channel],measure_osci_entry.ids.entry_sensorname.text]])
                    else:
                        self.batch_update_count = 50
                        self.livePlot.update_data_batch(self.plot_batch_data)
            except Exception as e: 
                print(e)
                pass
        
            channel = channel+1


# KVSTR_MeasureOscilloscopeScreen = KVSTR_CFG_WIDGET + KVSTR_MeasureMultimeterScreen
class MeasureOscilloscopeScreen(Screen):
    '''
    build the oscilooscope measurement Screen
    '''
    def __init__(self, **kwargs):
        super(MeasureOscilloscopeScreen, self).__init__(**kwargs)
        #Builder.load_string(KVSTR_TEMPLATES)
        #Builder.load_string(designeles_guikv.get_kvstr(GLOB.GUI))
        designeles_guikv.load_kvstr()
        Builder.load_string(KVSTR_MeasureMultimeterEntry)
        Builder.load_string(KVSTR_MeasureMultiMainWidget)
        top_menue_bar.load_top_menu()
        Builder.load_string(GLOB.GUI_KVSTR_GLOB)  # globals shall rule (this is the last import)
        self.active = False
        self.measurement_data = None

    def build_gui(self, measuresystem=None):
        '''
        build the gui, clear everything if already built (so you can built a new screen)
        '''
        if not dbg.DBG_SIMU_OSCI and not measuresystem:
            raise Exception("Kein Messsystem konfiguriert")
        
        # creating the main widget MeasureMultiMainWidget
        self.measure_osci_main_widget = MeasureOscilloscopeMainWidget()
        if dbg.DBG_SIMU_OSCI:
            self.measure_osci_main_widget.set_measure_config(meassys.TEST_SYS)
        else:
            self.measure_osci_main_widget.set_measure_config(measuresystem)

        self.size = (Window.width, Window.height)
        self.measure_osci_main_widget.build_gui()
        self.add_widget(self.measure_osci_main_widget)

    def on_enter(self):
        self.active = True
        print("ON_ENTER")

    def on_leave(self):
        self.active = False
        print("ON_LEAVE")

    def set_measurement_data(self, measurement_data):
        self.measurement_data = measurement_data

    def change_size(self,window_size):
        self.measure_osci_main_widget.change_size(window_size)

    def update_gui(self, mdata):
        '''
        update the gui elements to show correct measurement values

        mdata is measurement data
        '''

    def update_vals(self,channellist):
        self.measure_osci_main_widget.update_vals(channellist)
 
    def update_measurement_data(self):
        self.measure_osci_main_widget.update_measurement_data(self.measurement_data)

    def simu_vals(self):
        if not self.active:
            return 
        cnt = 0
        channellist = []
        for sensor in meassys.TEST_SYS.sensors:
            cnt = cnt+1
            for i in range(0,len(sensor.chans_out)):
                    #sensor.chans_out[i].mval_cur = round(random.uniform(0+cnt, 0.5+cnt),2)
                    channellist.append(round(random.uniform(0+cnt, 0.5+cnt),2))
        if not self.measurement_data:
            self.measurement_data = measdata.MeasurementData(channellist)
        else:
            self.measurement_data.update(channellist)

        #self.update_vals(channellist)
        self.update_measurement_data()

    def screenback(self, sm, screen_back):
        '''
        sets the screen to go back to, provide screenmanager sm and name of screen 'screen_back'
        '''
        if dbg.DBG_OUT: print("osci: set back screen to", screen_back)
        self.measure_osci_main_widget.screenback(sm, screen_back)

def on_motion(event):
    if event.inaxes:
        x, y = event.xdata, event.ydata
        print(f"Mouse is at ({x}, {y})")

class PlotlyHover(BaseHoverFloatLayout):
    ''' PlotlyHover adapt the background and the font color with the line or scatter color''' 
    text_color=ColorProperty([0,0,0,1])
    text_font=StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    hover_height = NumericProperty(dp(24))

    
    def __init__(self, **kwargs):
        """ init class """
        super().__init__(**kwargs)  

class LivePlot(object):
    '''
    Class for generating the mathplot and updating the values
    '''
    def __init__(self, **kwargs):
        super(LivePlot, self).__init__(**kwargs)
        #definiert den aktiven Marke [0..5] entsprechend des geklickten Buttons
        self.activemarker = None
        #speichert die Marker-Lines (Matplot 2DLines)
        self.marker_lines = [None,None,None,None,None]
        #Farben für die Marker-Lines
        self.marker_colors = ["xkcd:purple blue","xkcd:terracotta","xkcd:marine blue","xkcd:steel","xkcd:tan green" ]
        #temporärer Markerlines -> Während der Aktualisierung sollen die Markerlines nicht angezeigt werden, müssen 
        #daher temporär entfernt werden und bei Pausierung wieder angezeigt werden
        self.temp_marker_lines = [None,None,None,None,None]
        # Create the chart and add it to the layout
        self.fig, self.ax = plt.subplots()
        self.lineX = {}
        #self.lineX, = self.ax.plot([], [], label="F1")
        self.lineY, = self.ax.plot([], [])
        self.ax.set_title("Beschleunigung")  # Set the title
        self.ax.set_ylabel("g")
        self.ax.set_xlabel("")
        
        self.ax.annotate("Speicherdauer <xxx>", xy=(0.5, 0.94), xycoords='axes fraction', fontsize=8,ha='center')  # Adjust the position as needed


        self.ax.legend(loc='upper right')
        self.plotstop = False
        self.max_data_points = 50
        #Daten die Gegenwärtig angezeigt werden, begrenzt durch max_data_points --> ältere Daten werden hier gelöscht
        #damit der Plot "wandern" kann
        self.time_data_current = {}
        self.x_data_current = {}
        
        #Alle Daten die der Oszimodus je gesehen hat
        self.time_data = {}
        self.x_data = {}

        self.matplotwidget = None

        self.add_button()

    def register_matplotwidget(self, matplotwidget):
        '''
        Matplotwidget regstrieren um events zu verarbeiten
        '''
        self.matplotwidget = matplotwidget

        self.matplotwidget.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.matplotwidget.figure.canvas.mpl_connect('pick_event',   self.on_pick)
        self.matplotwidget.figure.canvas.mpl_connect('button_press_event', self.on_button_clicked)

        def _on_pressed(instance,event):
            pos = [event.x,event.y]
            newcoord = self.matplotwidget.to_widget(pos[0], pos[1], relative=True)
            x = newcoord[0]
            y = newcoord[1]
            inside = self.matplotwidget.collide_point(*pos)


            if self.is_touch_on_matplotlib_button(self.savebutton,event):
                                #TODO hier oder im on_button_clicked
                    s = 'button_press_event'
                    print("on touch matlabbutton")
                    mouseevent = MouseEvent("savebutton_clicked",self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent) 

            elif self.is_touch_on_matplotlib_button(self.marker1button,event):
                                #TODO hier oder im on_button_clicked
                    s = 'button_press_event'
                    print("on touch maker 1")
                    mouseevent = MouseEvent("marker1button_clicked",self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent)     
            
            elif self.is_touch_on_matplotlib_button(self.marker2button,event):
                                #TODO hier oder im on_button_clicked
                    s = 'button_press_event'
                    print("on touch maker 2")
                    mouseevent = MouseEvent("marker2button_clicked",self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent)                                         

            elif self.is_touch_on_matplotlib_button(self.marker3button,event):
                                #TODO hier oder im on_button_clicked
                    s = 'button_press_event'
                    print("on touch maker 3")
                    mouseevent = MouseEvent("marker3button_clicked",self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent)                                         

            elif self.is_touch_on_matplotlib_button(self.marker4button,event):
                                #TODO hier oder im on_button_clicked
                    s = 'button_press_event'
                    print("on touch maker 4")
                    mouseevent = MouseEvent("marker4button_clicked",self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent)                                         

            elif self.is_touch_on_matplotlib_button(self.marker5button,event):
                                #TODO hier oder im on_button_clicked
                    s = 'button_press_event'
                    print("on touch maker 5")
                    mouseevent = MouseEvent("marker5button_clicked",self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent)  

            elif inside:
                if event.button == 'left':
                    s = 'pick_event'
                    mouseeventPick = MouseEvent(s, self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    pickevent =PickEvent(s, self.matplotwidget.figure.canvas,mouseeventPick,None,guiEvent=None)
                    #TODO Man müsste beim pick_event statt None eigentlich die artist (=Line) angeben, aber wir brauchen das Event nur für die Mausposition
                    self.matplotwidget.figure.canvas.callbacks.process(s, pickevent) 
                    print("left mouse clicked")           
            


        def _on_released(instance,event):
            pos = [event.x,event.y]
            newcoord = self.matplotwidget.to_widget(pos[0], pos[1], relative=True)
            x = newcoord[0]
            y = newcoord[1]
            inside = self.matplotwidget.collide_point(*pos)
            if inside:
                            
                if event.button == 'left':
                    s = 'button_release_event'
                    mouseevent = MouseEvent(s, self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                    self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent) 
                    print("left mouse clicked")           

        def _on_mouse_pos(*args):
            '''Kivy Event to trigger the following matplotlib events
               `motion_notify_event`, `leave_notify_event` and
               `enter_notify_event`.
            '''
            #print(args[1])
            pos = args[1]
            newcoord = self.matplotwidget.to_widget(pos[0], pos[1], relative=True)
            x = newcoord[0]
            y = newcoord[1]
            inside = self.matplotwidget.collide_point(x,y)
            if inside:
                s = 'motion_notify_event'
                mouseevent = MouseEvent(s, self.matplotwidget.figure.canvas, x, y, self.matplotwidget.figure.canvas._button, self.matplotwidget.figure.canvas._key,
                                       guiEvent=None)
                self.matplotwidget.figure.canvas.callbacks.process(s, mouseevent) 
                #self.matplotwidget.figure.canvas.motion_notify_event(x, y, guiEvent=None)
            #TODO event wird nicht benötigt, aber bringt Fehler, im Gegensatz zum Beispiel
            #evtl. Problem bzgl. MatplotFigureCustom??
            '''if not inside and not self.matplotfigure.figure.canvas.entered_figure:
                self.matplotfigure.figure.canvas.leave_notify_event(guiEvent=None)
                self.matplotfigure.figure.canvas.entered_figure = True
            elif inside and self.matplotfigure.figure.canvas.entered_figure:
                self.matplotfigure.figure.canvas.enter_notify_event(guiEvent=None, xy=(pos[0], pos[1]))
                self.matplotfigurefigure.canvas.entered_figure = False'''

        Window.bind(mouse_pos=_on_mouse_pos) 
        Window.bind(on_touch_down = _on_pressed) 
        Window.bind(on_touch_up = _on_released) 


    def stop_plot(self):
        self.plotstop = True
        #wenn der Osci gestoppt wird müssen evtl. gesetzte Marker wieder eingetragen werden
        for marker in self.temp_marker_lines:
            if marker:
                self.fig.add_artist(marker)
            
    
    def start_plot(self):
        self.plotstop = False
        for i in  range(len(self.marker_lines)):
            marker = self.marker_lines[i]
            self.temp_marker_lines[i] = marker
            if marker:
                marker.remove()

            



    def on_motion(self,event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            #self.ax2.axvline(x = x)
            #print(event.button)
            #event.canvas.draw()
            if dbg.DBG_OUT: print(f"Mouse is at ({x}, {y})")        


    def on_pick(self,event):
        if self.plotstop :
            if self.activemarker != None:
                if self.marker_lines[self.activemarker]:
                    self.marker_lines[self.activemarker].remove()
                x, y = event.mouseevent.xdata, event.mouseevent.ydata
                if x:
                    self.marker_lines[self.activemarker] = self.ax.axvline(x = x,color=self.marker_colors[self.activemarker])
                    event.canvas.draw()

    
    def is_touch_on_matplotlib_button(self,matplotbutton, touch):
        window_x, window_y = Window.mouse_pos
        matplotlib_button_x, matplotlib_button_y = self.matplotwidget.to_local(matplotbutton.ax.bbox.xmin, matplotbutton.ax.bbox.ymin)
        matplotlib_button_width, matplotlib_button_height = matplotbutton.ax.bbox.width,matplotbutton.ax.bbox.height

        istouched =(
            matplotlib_button_x <= window_x <= matplotlib_button_x + matplotlib_button_width and
            matplotlib_button_y <= window_y <= matplotlib_button_y + matplotlib_button_height
        )

        return istouched

    def on_button_clicked(self, event):
        '''wird aufgerufen wenn ein matplotlib button gedrückt wird'''
        #TODO gibt es vielleicht ein bessere Lösung?? Alle Klicks landen auf dem gleichen Event
        #man für jeden matplotlibbutton prüfen, ob er geklickt wurde und dann einen passenden Event
        #Namen vergeben, der dann geprüft werden muss....
        if event.name == "savebutton_clicked":
            if dbg.DBG_OUT: print("screen_measosci_guikv Liveplot on_button_clicked screenshot")
            #TODO passenden Pfad raussuchen und dort speichern, fortlaufende Nummer?
            self.fig.savefig('plot.png')  
        if event.name == 'marker1button_clicked':
            if dbg.DBG_OUT: print("screen_measosci_guikv Liveplot on_button_clicked Marker 1")
            self.activemarker = 0
        if event.name == 'marker2button_clicked':
            if dbg.DBG_OUT: print("screen_measosci_guikv Liveplot on_button_clicked Marker 2")
            self.activemarker = 1
        if event.name == 'marker3button_clicked':
            if dbg.DBG_OUT: print("screen_measosci_guikv Liveplot on_button_clicked Marker 3")
            self.activemarker = 2
        if event.name == 'marker4button_clicked':
            if dbg.DBG_OUT: print("screen_measosci_guikv Liveplot on_button_clicked Marker 4")
            self.activemarker = 3
        if event.name == 'marker5button_clicked':
            if dbg.DBG_OUT: print("screen_measosci_guikv Liveplot on_button_clicked Marker 5")
            self.activemarker = 4

    def add_button(self):
         # Create and position the buttons
        self.ax_buttons = self.fig.add_axes([0.8, 0.01, 0.09, 0.05])    
        self.savebutton = matplotButton(self.ax_buttons, label='Speichern') 

        self.ax_buttons = self.fig.add_axes([0.1, 0.01, 0.04, 0.05])    
        self.marker1button = matplotButton(self.ax_buttons, label='M 1') 

        self.ax_buttons = self.fig.add_axes([0.15, 0.01, 0.04, 0.05])    
        self.marker2button = matplotButton(self.ax_buttons, label='M 2') 

        self.ax_buttons = self.fig.add_axes([0.2, 0.01, 0.04, 0.05])    
        self.marker3button = matplotButton(self.ax_buttons, label='M 3') 

        self.ax_buttons = self.fig.add_axes([0.25, 0.01, 0.04, 0.05])    
        self.marker4button = matplotButton(self.ax_buttons, label='M 4') 

        self.ax_buttons = self.fig.add_axes([0.3, 0.01, 0.04, 0.05])    
        self.marker5button = matplotButton(self.ax_buttons, label='M 5') 
 
    def changedata(self,modus):
        self.ax.set_title(modus) 
        self.update_data([])    
        #TODO Logik anderen Datenbestand visualisieren

        
    def on_layout_size_change(self, instance, value):
        # Update figure size when layout size changes
        if value[0] <= 10 or value[1] <= 10:
            return
        dpi = Window.dpi  # Get the DPI value
        scaled_width = value[0] / dpi
        scaled_height = ((value[1]-25) / dpi)

        self.fig.set_size_inches(scaled_width, scaled_height)
        self.fig.canvas.draw_idle()    

    def update_measurement_data(self, measurementdata):
        ...
        

    def update_data(self, data):
        # Generate new data for the chart
        startP = time.time()
        if dbg.DBG_OUT: print("LivePlot: update_data")
        if data:
            timestamp = [data[0]]
            x = [data[1]]
           # y = [data[2]]
            lineID = data[2]


            if lineID in self.x_data_current:
                    # If it exists, extend the list associated with that ID
                    self.x_data_current[lineID].extend(x)
                    self.time_data_current[lineID].extend(timestamp)
                    self.time_data[lineID].extend(x)
                    self.x_data[lineID].extend(timestamp)
            else:
                # If it doesn't exist, create a new list with the data
                self.x_data_current[lineID] = x
                self.time_data_current[lineID] = timestamp
                self.time_data[lineID] = x
                self.x_data[lineID] = timestamp
                self.lineX[lineID], = self.ax.plot([], [], label=lineID,)
                #added_line,=self.fig.axes.plot([], [], label=lineID)

            while len(self.time_data_current[lineID]) > self.max_data_points:
                self.time_data_current[lineID].pop(0)
                self.x_data_current[lineID].pop(0)

            # Update the chart data
            self.lineX[lineID].set_data(self.time_data_current[lineID], self.x_data_current[lineID])
        
            self.ax.legend(loc='upper right')

            endP = time.time()
            
           # if dbg.DBG_OUT: 
               #print("LivePlot: update_data duration data processing: " + str(startP-endP))
            

            startD = time.time()
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            self.fig.canvas.draw_idle()
            endD = time.time()
            if dbg.DBG_OUT: print("LivePlot: update_data duration draw chart: " + str(startD-endD))
            
            if dbg.DBG_OUT: print("LivePlot: update_data total time: " + str(startP-endD))
            #self.fig.canvas.flush_events()

    '''
        Akualisiert einen Block Daten (data_batch)
        data_batch: liste [ZEITstempel,Messwert, SensorBezeichnung]
                    SensorBezeichnung ist dabei df_nameapp_v aus dem Sensor bzw. der zugehörigen chans_out liste
    '''
    def update_data_batch(self, data_batch):
        if not data_batch:
            return
        
        startP = time.time()
        if dbg.DBG_OUT: print("LivePlot: update_data_batch")
        # Create temporary dictionaries to batch updates
        temp_x_data = {}
        temp_time_data = {}

        
        for data in data_batch:
            if data:
                timestamp = data[0]
                x = data[1]
                lineID = data[2]

                if lineID in temp_x_data:
                    temp_x_data[lineID].extend([x])
                    temp_time_data[lineID].extend([timestamp])

                    self.time_data[lineID].extend([x])
                    self.x_data[lineID].extend([timestamp])

                else:
                    temp_x_data[lineID] = [x]
                    temp_time_data[lineID] = [timestamp]

                    self.time_data[lineID] =[x]
                    self.x_data[lineID] = [timestamp]

                while len(temp_time_data[lineID]) > self.max_data_points:
                    temp_time_data[lineID].pop(0)
                    temp_x_data[lineID].pop(0)

            # Update plot for each line
        for lineID in temp_x_data:
            if not lineID in self.lineX:
                self.lineX[lineID], = self.ax.plot([], [], label=lineID)

            self.lineX[lineID].set_data(temp_time_data[lineID], temp_x_data[lineID])

        endP = time.time()
            
        self.ax.legend(loc='upper right')

        startD = time.time()
        
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)
        self.fig.canvas.draw_idle()
        endD = time.time()

        #if dbg.DBG_OUT: print("LivePlot: updateupdate_data_batch_data duration: data processing ({0}) / draw chart ({1}) / total ({2}): "\
        #                      .format(round(startP-endP,4),
        #                              round(startD-endD,4),
        #                              round(startP-endD,4) 
        #                              ))
          



class MeasureOscilloscopeApp(App):
    '''
    Standallone-Test-App class
    '''
    def __init__(self, **kwargs):
        super(MeasureOscilloscopeApp, self).__init__(**kwargs)

    def build(self):
        self.SM = ScreenManager()
        # creating the screen
        self.screen = MeasureOscilloscopeScreen(name='screen_measure_oscilloscope')

        self.SM.add_widget(self.screen)
        Window.bind(size=self.on_resize)
        return self.SM
    

    def on_start(self):
        if dbg.DBG_OUT: print("MeasureOscilloscopeApp on_start")
        self.screen.build_gui()
        self.screen.measure_osci_main_widget.ids.id_top_menu_bar.set_clb_back(self.stop)
        self.screen.measure_osci_main_widget.ids.id_top_menu_bar.set_clb_settings(self.ev_btn_settings)
        self.screen.change_size(Window.size)

    def ev_btn_settings(self,instance):
        short_description_list = [
            "y-Skale",
            "Sensor-Bezeichnung",
            "Speicherdauer"
        ]
        long_description_list = [
            "Festlegung des Bereichs für die y-Skala",
            "Festlegung der individuellen Bezeichner für die Sensoren fest",
            "Festlegung der Speicherdazer"
        ]

    
        #popup.p_decision_n_options(short_description_list, long_description_list, [None, None, None],title="Einstellungen")		


    def on_resize(self, instance, window_size):
        self.screen.change_size(window_size)

    def update_vals(self):
        self.screen.simu_vals()

  
if __name__ == '__main__':
    path = os.getcwd()
    #Pfad zum Logo für Standalone umbiegen
    appglobals.GLOB.GUI.image_prodat_logo = os.path.join("../"+appglobals.GLOB.GUI.image_prodat_logo)
    test = MeasureOscilloscopeApp()
    Window.size = (GLOB.GUI.appsize_x, GLOB.GUI.appsize_y)
    if dbg.DBG_SIMU_OSCI:
        Clock.schedule_interval(lambda x: test.update_vals(), 0.01)
        
    test.run()