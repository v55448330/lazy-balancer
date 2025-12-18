from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
import json

@ensure_csrf_cookie
def login_view(request):
    redirect_to = settings.LOGIN_REDIRECT_URL

    if request.method == "POST":
        redirect_to = request.POST.get('next')
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return HttpResponseRedirect(redirect_to)

    else:
        if 'next' in request.GET:
            redirect_to = request.GET['next']

        if not bool(User.objects.all().count()):
            return HttpResponseRedirect('/superuser/')
            #User.objects.create_superuser('admin','admin@123.com','1234.com')

        form = AuthenticationForm(request)

    context = {
        'form': form,
        'next': redirect_to
    }

    return render_to_response('login.html', context)

def migrate_superuser():
    try:
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        superusers = User.objects.filter(is_superuser=True)
    
        user_list = []
        for user in superusers:
            if not user.groups.filter(name="Admin").exists():
                user.groups.add(admin_group)
                user_list.append(user.username)
    
        return user_list
    except:
        return None

def create_superuser(request):
    redirect_to = settings.LOGIN_REDIRECT_URL

    if bool(User.objects.all().count()):
        return HttpResponseRedirect(redirect_to)

    if request.method == "POST":
        try:
            post = json.loads(request.body.decode('utf-8'))
            user = User.objects.create_superuser(post['username'], 'admin@123.com', post['password'])
            group, _ = Group.objects.get_or_create(name='Admin')
            user.groups.add(group)
            context = {'flag':"Success"}
            status = 200
        except Exception as e:
            context = {"flag":"Error", "context":str(e)}
            status = 403

        return HttpResponse(json.dumps(context), status=status)

    return render_to_response('superuser.html')

def logout_view(request):
    Session.objects.filter(expire_date__lte=timezone.now()).delete()
    logout(request)
    return HttpResponseRedirect('/login/')

def is_auth(view):
    def decorator(request, *args, **kwargs):
        if not request.user.is_authenticated:
            context = {
                'flag':"Error",
                'context':"AuthFailed"
            }
            return HttpResponse(json.dumps(context), status=403)
        else:
            return view(request, *args, **kwargs)
    return decorator

def is_admin(view):
    def decorator(request, *args, **kwargs):
        if not request.user.groups.filter(name='Admin').exists():
            context = {
                'flag':"Error",
                'context':"PermissionDeny"
            }
            return HttpResponse(json.dumps(context), status=403)
        else:
            return view(request, *args, **kwargs)
    return decorator
