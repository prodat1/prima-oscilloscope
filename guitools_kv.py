'''
gui helper functions, i.e. to detect screensize dimensions
'''
from kivy.core.window import Window


def screen_size():
    ''' return the screens maximum size in pixels (opens a maximized window)'''
    Window.maximize()
    return Window.size

def find_element_by_class_parent_recursive(widget, target_class):
    if isinstance(widget, target_class):
        return widget

    parent = widget.parent
    if parent:
        return find_element_by_class_parent_recursive(parent, target_class)
    else:
        return None
        
def find_element_by_class_child_recursive(widget, target_class):
    if isinstance(widget, target_class):
        return widget


    for child in widget.children:
        result = find_element_by_id_child_recursive(child, target_class)
        if result:
            return result

    return None        



def find_element_by_id_parent_recursive(widget, target_id):
    if hasattr(widget, 'ids') and target_id in widget.ids:
        return widget.ids[target_id]

    parent = widget.parent
    if parent:
        return find_element_by_id_parent_recursive(parent, target_id)
    else:
        return None
        
def find_element_by_id_child_recursive(widget, target_id):
    if hasattr(widget, 'ids') and target_id in widget.ids:
        return widget.ids[target_id]

    for child in widget.children:
        result = find_element_by_id_child_recursive(child, target_id)
        if result:
            return result

    return None            

        
def find_element_by_customid_child_recursive(widget, target_id):
    if hasattr(widget, 'custom_checkbox_id') and target_id in widget.custom_checkbox_id:
        if widget.custom_checkbox_id == target_id:
            return widget
    for child in widget.children:
        result = find_element_by_customid_child_recursive(child, target_id)
        if result:
            return result
    return None

def find_textinput_by_customid_child_recursive(widget, target_id):
    if hasattr(widget, 'custom_text_id') and target_id in widget.custom_text_id:
        if widget.custom_text_id == target_id:
            return widget
    for child in widget.children:
        result = find_textinput_by_customid_child_recursive(child, target_id)
        if result:
            return result
    return None

def value_kn_text_to_float(value_text):
    try: 
        value_text = value_text.replace('[b]','')
        value_text = value_text.replace('[/b]','')
        value_text = value_text.replace('kN', '')
        value_text = value_text.replace(',', '.')
        value_text = value_text.strip()
        value_text = round(float(value_text), 2)

        return value_text
    except ValueError as e: 
        print(e)
if __name__ == '__main__':
    print("screen max. size:", screen_size())