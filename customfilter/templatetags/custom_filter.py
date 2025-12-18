from django import template  
import time

register = template.Library()  

@register.filter(name='timestamp_to_date')  
def timestamp_to_date(_timestamp):  
    try:
        if isinstance(_timestamp, int) or isinstance(_timestamp, float):
            _return = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(_timestamp))
        else:
            _return = _timestamp.strftime("%Y-%m-%d %H:%M:%S")
    except:
        _return = None
    return _return
