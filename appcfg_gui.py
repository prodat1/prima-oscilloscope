''' Central GUI (KIVY) configuration settings for the app

usage:
    
    import appcfg_gui #in your kivy lib GUI module
    
'''
from kivy import utils
from dataclasses import dataclass, field

import os 

DEF_STD = "STD"
DEF_SMALLSCREEN = "SMALLSCREEN"
DEF_SIZETEST = "SIZETEST"

@dataclass
class ConfigGUI_STD():

    #appplication settings
    appsize_x : int = 1024  #default: 1024
    appsize_y : int = 768   #default: 768
    appclearcolor: tuple = (1.0, 1.0, 1.0, 1.0) #application window background color -> default is white @TODO: pass a string
    image_app_bckgnd: str = "media/pics/welcome.jpg"
    image_prodat_logo: str = "media/pics/logo.jpg"

    # popup settings
    popup_size_hint: tuple = (0.8, 0.8)  # default (0.8,0.8)
    button_heihgt: int = 0.08  # relative button height to use in all popups
    inputtext_heihgt: int = 0.1  # relative input height to use in all popups

    #ATTENTION when using something as fontsize_m : str = fontsize_xyz -> if you inherit internally it breaks

    #using scale independent pixels sp -> https://kivy.org/doc/stable/api-kivy.metrics.html
    #scale-independent Pixels - This is like the dp unit, but it is also scaled by the user’s font size preference. 
    #We recommend you use this unit when specifying font sizes, so the font size will be adjusted to both the screen density and the user’s preference.
    fontsize_xl : str = "36sp" 
    fontsize_l : str = "30sp"
    fontsize_m : str = "20sp"
    fontsize_s : str = "16sp"
    fontsize_xs : str = "12sp"

    fontsize_but: str = fontsize_m #default button fontsize
    fontsize_but_l: str = fontsize_l #large button fontsize
    fontsize_but_s: str = fontsize_s #small button fontsize
    
    fonsize_lab : str = fontsize_s #default label fontsize

    # color settings general
    color_background_normal: str = ''

    # color settings for fonts
    color_font_light: str = "1, 1, 1, 1"
    color_font_inv: str = "0, 0, 0, 1"  # inverted
    color_font_std: str = "0, 0, 0, 1"
    color_font_lbl: tuple = (0, 0, 0, 1)
    color_font_but: tuple = (0, 0, 0, 1)
    
    color_font_lbl_toleranz_rkm_measure: str = "0,1,0,1"

    # color settings for background
    color_bgnd_hex = '#1b077a'
    color_bgnd_std: str = "1, 1, 1, 1"  # white is the normal background color
    color_bgnd_col: str = f'utils.get_color_from_hex(\'{color_bgnd_hex}\')'  # prodat default darkblue (colored background)

    # color settings for buttons
    # sys default = '' # alternative inputs: "0.2, 0.2, 0.2, 1" # PRODAT DEFAULT =
    color_but_hex = '#d9d9d9'
    color_but_bgnd: str = f'utils.get_color_from_hex(\'{color_but_hex}\')'  # prodat default #d9d9d9 .. greyish
    color_but_bg = utils.get_color_from_hex(color_but_hex)
    color_but_font: tuple = (0, 0, 0, 1)
    color_but_bgnd_h1: tuple = (0, 1, 0, 1)
    color_but_bgnd_h2: tuple = (0, 0, 1, 1)

    #color settings for labels
    color_lab_text: str = color_font_std #text color for labels
    color_lab_bgnd : str =  "1, 1, 1, 1" #white, not transparent

    color_lab_background_status_good_value_kv: str= "0.13,0.8,0.13,1"
    color_lab_background_status_default_value_kv: str= color_but_bgnd
    color_lab_background_status_bad_value_kv: str= "1,0,0,1"

    color_lab_background_status_good_value_py: tuple= (0.13,0.8,0.13,1)
    color_lab_background_status_default_value_py: tuple= tuple(color_but_bg)
    color_lab_background_status_bad_value_py: tuple= (1,0,0,1)
    
    # color settings for checkboxes
    color_che: tuple = (0, 0, 1, 1)

    # color settings for popup
    color_pop_bg: tuple = tuple(map(int, color_lab_bgnd.split(', ')))

    #spacing settings
    spacing_l: int = 10
    spacing_m: int = 5 #default spacing
    spacing_s: int = 2

    # padding settings
    padding_xl: int = 20
    padding_l: int = 10
    padding_m: int = 5  # default padding
    padding_s: int = 2

    padding_border: tuple = (10,0)

    # image settings
    ima_width: int = 300
    status_but_height: int = 20

    # icon settings
    info_icon_size: tuple = (125, 125)
    info_icon_source_tuple: tuple = ('media/pics/info_icon.png', 'media/pics/warning_icon.png', 'media/pics/error_icon.png')

    # seperator settings
    line_thickness = 'dp(5)'
    line_color = '0.1, 0.1, 1, 1'
    
@dataclass
class ConfigGUI_SMALLSCREEN(ConfigGUI_STD):
    #alter/override what ever is needed
    fontsize_xl : str = "46sp" 
    fontsize_l : str = "40sp"
    fontsize_m : str = "20sp" 

@dataclass
class ConfigGUI_SIZETEST(ConfigGUI_STD):
    fonsize_lab : str = "80sp"
    fontsize_but : str = "80sp"

def get_kvstr(cfgsel=None):
    '''
    load the kivy string -> do this once in your app or call this in your standalone module test
    
    @param cfg: provide a GUI configuration scheme. None = default / nothing else yet supported  
    '''
    
    if cfgsel == None or cfgsel == DEF_STD:
        gui = ConfigGUI_STD()
    elif cfgsel == DEF_SIZETEST:
        gui = ConfigGUI_SIZETEST()
    else:
        raise Exception("not yet supported") 
    
    kvstr = f'''#:import utils kivy.utils
#:set fontsize_xl '{gui.fontsize_xl}'
#:set fontsize_l '{gui.fontsize_l}'
#:set fontsize_m '{gui.fontsize_m}'
#:set fontsize_s '{gui.fontsize_s}'
#:set fontsize_xs '{gui.fontsize_xs}'

<Window>:
    clear_color: black

<Label>:
    font_size: '{gui.fonsize_lab}'
    color: {gui.color_lab_text}
    markup: True
    canvas.before:
        Color:
            rgba: {gui.color_lab_bgnd}
        Rectangle:
            size: self.size
            pos: self.pos
<Button>:
    font_size: '{gui.fontsize_but}'
    background_normal: '{gui.color_background_normal}' #not sure what normal does
    background_color: {gui.color_but_bgnd}
    color_but_text: 1,0.5,0.5,0.5
    color: {gui.color_font_std}
    
<BoxLayout>
    #canvas.before:
    #    Color:
    #        rgba: {gui.color_bgnd_std}
    #    Rectangle:
    #        size: self.size
    #        pos: self.pos

<GridLayout>
    #canvas.before:
    #    Color:
    #        rgba: {gui.color_bgnd_std}
        #BorderImage:
        #    source: '../examples/widgets/sequenced_images/data/images/button_white.png'
        #    pos: self.pos
        #    size: self.size
'''
    return kvstr

def get_cfg(cfgsel=None):
    if cfgsel == None or cfgsel == DEF_STD:
        return ConfigGUI_STD()

if __name__ == '__main__':
    from kivy.lang import Builder
    print( ConfigGUI_SMALLSCREEN() )
    print( ConfigGUI_STD() )
    Builder.load_string( get_kvstr() ) #globals shall rule< (last import)