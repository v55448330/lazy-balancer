from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse
from nginx.views import *
import os
import json
import time
 
# Create your views here.
def view(request):
    conf_content = build_main_config()
    write_config("/home/ubuntu/nginx.conf",conf_content)

    return render_to_response('main/view.html')
    pass
#return render_to_response('proxy/proxy.html', {'key': val,}

