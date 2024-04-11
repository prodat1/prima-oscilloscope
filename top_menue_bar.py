import os
import sys
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout


import appdef
import appglobals

GUI = appglobals.GLOB.GUI # global gui configuration -> need it for the general appearance
DBG_OUT = True
top_menu_str = None

class TopMenueBar(GridLayout):
    ''' 
    XKM main navigation bar - typically shown on top of the screen. It provides screen navigation and go back functionality. 
    It shows information about the current user.
    '''
    def __init__(self, **kwargs):
        super(TopMenueBar, self).__init__(**kwargs)
        self.sm = None #application screen manager object, if None no connected screen manager yet
        self.app = None #handle to the current app -> we access it to get self.sm and if required, additional parameters
        
        self.clb_vehicle = None
        #self.clb_measure = None
        #self.clb_protocol = None
        #self.clb_measure_system = None
        self.clb_back = None #@TODO: this is something we might need
        self.clb_settings = None
        
        #TODO
        #Pfad zu den Bildern ist unterschiedlich, jenachdem, ob man als Standalone startet oder aus der APP
        #Lösung: Der Pfad zum Bild wird angepasst --> wenn konfigurierter Pfad nicht existiert, müssen wir eine
        #Ebene weiter zurück
        #Problem: Beim Aufruf als Standalone ist self.ids == {}---> unklar warum
        #Daher annahme Default: wir sind in der "Standalone"-Ebene, wenn das Logo hier nicht existiert, muss
        #der Pfad ohne .. angegeben werden
        #if not os.path.exists(os.path.join("../", GUI.image_prodat_logo)):
        #  self.ids.prodat_logo.source = GUI.image_prodat_logo
                
    def load_from_app(self):
        '''
        load what we need from the app to perform our duties.
        Try to get the screenmanger directly from the app, in order to switch screens - otherwise it stays None
        '''
        if DBG_OUT: print("topmenue: try to load screenmanager from app if not none")
        self.app = App.get_running_app()
        try:
            self.sm = self.app.GUI_SM
        except AttributeError:
            print("ERROR topmenue: could not get screenmanager app.GUI_SM (not existant)", file=sys.stderr)
    
    def ev_btn_measure(self,args, **kwargs):
        ''' test button functionality, only active in case of debugging - simplifies fast &
            quick testing '''
        if DBG_OUT: print("topmenue: screen current measurement -> TODO", file=sys.stderr)
        self.load_from_app()
        if self.sm is not None:
            self.app.get_screen(appdef.APPSCREEN.OSCI)
            self.sm.current = appdef.APPSCREEN.OSCI
    
    def set_clb_vehicle(self, clb):
        self.clb_vehicle = clb
        if DBG_OUT: print("topmenue: Set Callback Vehicle")

    def ev_btn_vehicle(self,args, **kwargs):
        ''' test button functionality, only active in case of debugging - simplifies fast &
            quick testing '''
        if DBG_OUT: print("topmenue: show screen vehicle")
        if self.clb_vehicle is not None: self.clb_vehicle(args, **kwargs)
        self.load_from_app()
        if self.sm is not None:
            self.app.get_screen(appdef.APPSCREEN.VEHICLES)
            self.sm.current = appdef.APPSCREEN.VEHICLES

    def ev_btn_protocol(self,args, **kwargs):
        ''' test button functionality, only active in case of debugging - simplifies fast &
            quick testing '''
        if DBG_OUT: print("topmenue: show screen protocol (reports) -> TODO", file=sys.stderr)
        self.load_from_app()
        if self.sm is not None:
            self.app.get_screen(appdef.APPSCREEN.REPORTS)
            self.sm.current = appdef.APPSCREEN.REPORTS
        
    def ev_btn_measure_system(self,args, **kwargs):
        ''' test button functionality, only active in case of debugging - simplifies fast &
            quick testing '''
        if DBG_OUT: print("topmenue: show screen measurement system", file=sys.stderr)
        self.load_from_app()
        if self.sm is not None:
            self.app.get_screen(appdef.APPSCREEN.STARTMENUE_XKM)
            self.sm.current = appdef.APPSCREEN.STARTMENUE_XKM    
                    
    def set_clb_back(self, clb):
        #@TODO: still needed?
        self.clb_back = clb
        if DBG_OUT: print("topmenue: Set Callback Back")

    def ev_btn_back(self,args, **kwargs):
        ''' test button functionality, only active in case of debugging - simplifies fast &
            quick testing '''
        if DBG_OUT: print("topmenue: back top_menue_bar")
        self.load_from_app()
        if self.clb_back is not None: self.clb_back(args, **kwargs)

    def set_clb_settings(self, clb):
        self.clb_settings= clb
        if DBG_OUT: print("topmenue: Set Callback Settings")

    def ev_btn_settings(self,args, **kwargs):
        ''' test button functionality, only active in case of debugging - simplifies fast &
            quick testing '''
        if DBG_OUT: print("topmenue: show screen settings -> TODO", file=sys.stderr)
        self.load_from_app()
        if self.clb_settings is not None: self.clb_settings(args, **kwargs)
        if self.sm is not None: 
            self.app.get_screen(appdef.APPSCREEN.STARTMENUE_XKM)
            self.sm.current = appdef.APPSCREEN.STARTMENUE_XKM    

#KV_Str für TopMenü wird hier geladen, da sonst schon beim Import die Variablen an den String gebunden werden
#Insbesondere der Pfad zum Logo muss aber angepasst werden können, da ein anderer für die Standalone benötigt wird
#Das geht nicht in der TopMenueBar-Klasse selbst, da bei den Standalone-Aufrufen nicht auf die ids zugegriffen werden kann
#@TODO -> Prüfen warum das mit den self.ids nicht geht in der __init__ --> dann kann der KV_STR wieder ganz nach oben
#und mann kann die source des Image in der __init__ ändern, jenachdem ob man von Standalone aufruft oder der App
def load_top_menu():
    global top_menu_str
    KV_STR = f"""
<TopMenueBar>
    id: id_top_menu_bar
    cols:2
    row_force_default: True
    row_default_height: 65
    spacing: {GUI.spacing_m}
    Image: 
        id: prodat_logo
        source:'{GUI.image_prodat_logo}'
        size_hint: None,None
        size: self.texture_size
    GridLayout: 
        rows: 2 \n        """ + "rows_minimum: {0:30,1:35}" + f"""
        BoxLayout:
            orientation: 'horizontal'
            Label:
                id: id_top_menue_bar_title
                size_hint_x: 0.3
                halign: 'left'
                text_size: self.size
                font_size: '{GUI.fonsize_lab}'
                text: ""
                markup: True
            Label: 
                size_hint_x: 0.7
                text: 'Bediener: Max Mustermann | Kran: Musterkran'
                halign: 'right'
                text_size: self.size
                font_size: '{GUI.fonsize_lab}'
        BoxLayout: 
            orientation: 'horizontal'
            spacing: {GUI.spacing_m}
            Button:
                text: 'Messung'
                font_size: '{GUI.fontsize_m}'
                on_release: 
                    root.ev_btn_measure(args)
            Button:
                text: 'Kran'
                font_size: '{GUI.fontsize_m}'
                on_release: 
                    root.ev_btn_vehicle(args)
            Button:
                text: 'Protokoll'
                font_size: '{GUI.fontsize_m}'
                on_release: 
                    root.ev_btn_protocol(args)
            Button:
                text: 'Messsystem'
                font_size: '{GUI.fontsize_m}'
                on_release: 
                    root.ev_btn_measure_system(args)
            Button:
                text:  'Einstellungen'
                font_size: '{GUI.fontsize_m}'
                on_release: 
                    root.ev_btn_settings(args)                    
            Button:
                text:  'Zurück'
                font_size: '{GUI.fontsize_m}'
                on_release: 
                    root.ev_btn_back(args)
"""
    # Check if the KV-String has already been loaded
    if top_menu_str is None:
        # Load the KV-String if it hasn't been loaded yet
        top_menu_str = KV_STR
        print("LOADKV")
        # Load the KV-String into the Builder
        Builder.load_string(top_menu_str)

class TestApp(App):
    def build(self):
        GUI.image_prodat_logo = os.path.join("../"+GUI.image_prodat_logo)
        load_top_menu()
        return TopMenueBar()

if __name__ == '__main__':
    TestApp().run()