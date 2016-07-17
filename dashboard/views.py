from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse
from nginx.views import *
import json
import time

def view(request):
    return render_to_response('dashboard/view.html')
