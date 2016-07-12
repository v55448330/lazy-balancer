from django import template  
import time

register = template.Library()  

@register.filter(name='timestamp_to_date')  
def timestamp_to_date(_timestamp):  
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(_timestamp))
