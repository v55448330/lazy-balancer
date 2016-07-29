from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout,login
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from nginx.ip import *
import json

def login_view(request):
    redirect_to = settings.LOGIN_REDIRECT_URL

    if request.method == "POST":
        redirect_to = request.POST.get('next')
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return HttpResponseRedirect(redirect_to)

    else:
        set_firewall()
        if request.GET.has_key('next'):
            redirect_to = request.GET['next']

        if not bool(User.objects.all().count()):
            User.objects.create_superuser('admin','admin@123.com','1234.com')

        form = AuthenticationForm(request)

    context = {
        'form': form,
        'next': redirect_to
    }

    return render_to_response('login.html',context)

def logout_view(request):
    Session.objects.filter(expire_date__lte=timezone.now()).delete()
    logout(request)
    return HttpResponseRedirect('/login/')

def is_auth(view):
    def decorator(request, *args, **kwargs):
        if not request.user.is_authenticated():
            content = {
                'flag':"Error",
                'content':"AuthFailed"
            }
            return HttpResponse(json.dumps(content))
        else:
            return view(request, *args, **kwargs)
    return decorator
