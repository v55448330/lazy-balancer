from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse
import json
import time

# Create your views here.
def view(request):
    return render_to_response('proxy/view.html')
    pass
#return render_to_response('proxy/proxy.html', {'key': val,}
