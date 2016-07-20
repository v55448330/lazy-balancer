from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
 
def login_view(request):
    return render_to_response('login.html')

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')


