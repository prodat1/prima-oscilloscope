""" Custom MatplotFigure 
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
from kivy_matplotlib_widget.uix.graph_widget import MatplotFigure 
from kivy_matplotlib_widget.uix.hover_widget import add_hover
from kivy.utils import get_color_from_hex
from matplotlib.colors import to_hex
from kivy.metrics import dp
from kivy_matplotlib_widget.tools.cursors import cursor
from kivy.properties import NumericProperty,BooleanProperty
from kivy.graphics.texture import Texture
from kivy.graphics.transformation import Matrix

from kivy.properties import ObjectProperty, ListProperty, BooleanProperty, BoundedNumericProperty, AliasProperty, \
    NumericProperty


class MatplotlibEvent:
    x:None
    y:None
    pickradius:None
    inaxes:None
    projection:False
    compare_xdata:False

class MatplotFigureCustom(MatplotFigure):
    """Custom MatplotFigure
    """
    _box_pos = ListProperty([0, 0])
    _box_size = ListProperty([0, 0])
    _img_texture = ObjectProperty(None)
    _alpha_box = NumericProperty(0)   
    _bitmap = None
    do_update=False
    figcanvas = ObjectProperty(None)
    translation_touches = BoundedNumericProperty(1, min=1)
    do_scale = BooleanProperty(False)
    scale_min = NumericProperty(0.01)
    scale_max = NumericProperty(1e20)
    transform = ObjectProperty(Matrix())
    _alpha_hor = NumericProperty(0)
    _alpha_ver = NumericProperty(0)
    pos_x_rect_hor=NumericProperty(0)
    pos_y_rect_hor=NumericProperty(0)
    pos_x_rect_ver=NumericProperty(0)
    pos_y_rect_ver=NumericProperty(0)  
    invert_rect_ver = BooleanProperty(False)
    invert_rect_hor = BooleanProperty(False)
    legend_instance = ObjectProperty(None, allownone=True)
    legend_do_scroll_x = BooleanProperty(False)
    legend_do_scroll_y = BooleanProperty(False)
    interactive_axis = BooleanProperty(False) 
    do_pan_x = BooleanProperty(False)
    do_pan_y = BooleanProperty(False)    
    do_zoom_x = BooleanProperty(False)
    do_zoom_y = BooleanProperty(False)  
    fast_draw = BooleanProperty(True) #True will don't draw axis
    xsorted = BooleanProperty(False) #to manage x sorted data
    minzoom = NumericProperty(dp(40))
    compare_xdata = BooleanProperty(False)   
    hover_instance = ObjectProperty(None, allownone=True)
    nearest_hover_instance = ObjectProperty(None, allownone=True)
    compare_hover_instance = ObjectProperty(None, allownone=True)
    disable_mouse_scrolling = BooleanProperty(False) 
    disable_double_tap = BooleanProperty(False)     
    cursor_cls=None
    pickradius = NumericProperty(dp(50))
    projection = BooleanProperty(False)
    hist_range = BooleanProperty(False)
    disable_mouse_scrolling = BooleanProperty(False) 
    disable_double_tap = BooleanProperty(False) 
    myevent = MatplotlibEvent()

    def __init__(self, **kwargs):
        super(MatplotFigureCustom, self).__init__(**kwargs)
    
    
    def register_cursor(self,pickables=None):
        print("custom: register Cursor")
        remove_artists=[]
        if hasattr(self,'horizontal_line'):
            remove_artists.append(self.horizontal_line)
        if hasattr(self,'vertical_line'):
            remove_artists.append(self.vertical_line) 
        if hasattr(self,'text'):
            remove_artists.append(self.text)
            
        self.cursor_cls = cursor(self.figure,pickables=pickables,remove_artists=remove_artists)

    def transform_with_touch(self, event):
        """ manage touch behaviour. based on kivy scatter method"""
        print("transform with touch")
        # just do a simple one finger drag
        #changed = False


    def on_touch_down (self, touch, ):
        print("on touch down")
    def on_touch_move (self, touch, ):
        print("on touch move")
    def on_touch_up (self, touch, ):
        print("on touch up")
    def on_kv_post(self, base_widget, ):
        print("here")
    
    def hover(self, event) -> None:
        """ hover cursor method (cursor to nearest value)
        
        Args:
            event: touch kivy event
            
        Return:
            None
        
        """
        print("HOVER-HERE")