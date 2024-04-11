'''
KIVY DESIGN ELEMENTS TO SPICE UP THE APPLICATION
'''

from dataclasses import dataclass

import kivy
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout

@dataclass
class DesignCfg:
    line_thickness = 'dp(5)' #or 10
    line_color = '0.1, 0.1, 1, 1'
CFG_STD = DesignCfg() #is this needed
designeles_str = None

def load_kvstr(cfg=CFG_STD):
    global designeles_str 
    
    KV_STR = f'''#designeles_guikv
<DesignSeparator@Widget>
    canvas:
        Color:
            rgba: {cfg.line_color}
        Rectangle:
            pos: self.pos
            size: self.size

<DesignSepHori@DesignSeparator>
    size_hint_y: None
    height: {cfg.line_thickness}   

<DesignSepHoriThin@DesignSeparator>
    size_hint_y: None
    height: 0.5*{cfg.line_thickness}   

<DesignSepHoriThick@DesignSeparator>
    size_hint_y: None
    height: 2*{cfg.line_thickness}   


<DesignSepVert@DesignSeparator>
    size_hint_x: None
    width: {cfg.line_thickness}
<DesignSepVertThin@DesignSeparator>
    size_hint_x: None
    width: 0.5*{cfg.line_thickness}
<DesignSepVertThick@DesignSeparator>
    size_hint_x: None
    width: 2*{cfg.line_thickness}  

'''
    # Check if the KV-String has already been loaded
    if designeles_str is None:
        # Load the KV-String if it hasn't been loaded yet
        designeles_str = KV_STR
        print("LOADKV")
        # Load the KV-String into the Builder
        Builder.load_string(designeles_str)

TEST_MAINWIDGET_KVSTR = '''#comment
<MainWidget>:
    cols: 4 
    rows: 5
    DesignSepVert
    Button:        
        text: 'Hello 1'
    DesignSepHori
    DesignSepHoriThin    
    Button:
        text: 'World 1'
    Button:
        text: 'Hello 2'
    DesignSepHoriThick
    Button:        
        text: 'World 2'
    DesignSepVertThick
    BoxLayout:
        orientation: 'horizontal'
        DesignSepVertThick
        Button:
            text: 'World 2'
        DesignSepHoriThick
        Button:
            text: 'World 2'
    BoxLayout:
        orientation: 'vertical'
        DesignSepVertThick
        Button:
            text: 'World 2'
        DesignSepHoriThick
        Button:
            text: 'World 2'
    Button:        
        text: 'World 2'
    Label:        
        text: 'World 2'
'''

class MainWidget(GridLayout): 
    pass

if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.label import Label
    print("running: design_elements")
    mycfg = DesignCfg()
    mycfg.line_thickness = CFG_STD.line_thickness
    print("configure parameters before usage")
    kvstr = load_kvstr(mycfg)
    print(kvstr)
    Builder.load_string(kvstr)
    Builder.load_string(TEST_MAINWIDGET_KVSTR)
    from kivy.app import App
    from kivy.lang import Builder
    
    class TestApp(App):
        def build(self):
            return MainWidget()
    TestApp().run()
    print("done")