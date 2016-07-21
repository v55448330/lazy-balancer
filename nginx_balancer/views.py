from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.sessions.models import Session
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
from django.utils import timezone
 
def logout_view(request):
    Session.objects.filter(expire_date__lte=timezone.now()).delete()
    logout(request)
    return HttpResponseRedirect('/login/')


