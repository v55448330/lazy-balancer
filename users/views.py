from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.forms.models import model_to_dict
from django.core import serializers
from django.http import HttpResponse
from lazy_balancer.views import is_auth, is_admin
from settings.models import system_settings
import time
import json

@property
def last_login_timestamp(self):
    if self.last_login:
        return int(self.last_login.timestamp())
    return None

@login_required(login_url="/login/")
@is_admin
def view(request):
    users = User.objects.all().prefetch_related('groups')
    #users = User.objects.all()
    user_data = []
    for user in users:
        user.last_login_timestamp = last_login_timestamp
        user_info = {
            'user': user,
            'is_admin': user.groups.filter(name='Admin').exists(),
        }
        user_data.append(user_info)
    
    if system_settings.objects.all():
        s_config = system_settings.objects.all()[0]
    else:
        s_config = {}
    
    NUM_PER_PAGE = 10

    if s_config:
        NUM_PER_PAGE = s_config.num_per_page
        paginator = Paginator(user_data, NUM_PER_PAGE)
        page = request.GET.get('page')

    try:
        contexts = paginator.page(page)
    except PageNotAnInteger:
        contexts = paginator.page(1)
    except EmptyPage:
        contexts = paginator.page(paginator.num_pages)
    
    user = {
        'info':request.user,
        'is_admin':request.user.groups.filter(name='Admin').exists(),
        'date':time.time()
    }

    return render_to_response('users/view.html', {'users': contexts, 'user': user })

@is_auth
@is_admin
def query_user(request):
    try:
        post = json.loads(request.body.decode('utf-8'))
        pk = post.get('user_id','')
        if pk:
            user = User.objects.get(pk=pk)
            user.last_login_timestamp = last_login_timestamp
            p = model_to_dict(user)
            p['is_admin'] = user.groups.filter(name='Admin').exists()
            del p['password']
            del p['last_login']
            del p['date_joined']
            del p['groups']
            content = { "flag":"Success","context":{'user': p}}
        else:
            content = { "flag":"Error","context":"UserNotFound" }
    except Exception as e:
        content = { "flag":"Error","context":str(e) }
    return HttpResponse(json.dumps(content))

@is_auth
@is_admin
def change_status(request):
    try:
        post = json.loads(request.body.decode('utf-8'))
        user = User.objects.get(pk=post['user_id'])
        if user.is_superuser:
            content = { "flag":"Error","context":"ChangeDeny" }
            status = 403 
        else:
            user.is_active = bool(int(post.get('status',0)))
            user.save()
            content = { "flag":"Success" }
            status = 200
    except Exception as e:
        content = { "flag":"Error","context":str(e) }
        status = 400

    return HttpResponse(json.dumps(content), status=status)

@is_auth
@is_admin
def save(request):
    try:
        post = json.loads(request.body.decode('utf-8'))
        is_create = not bool(int(post.get('user_id', 0)))
        group, _ = Group.objects.get_or_create(name='Admin')

        if is_create:
            user = User.objects.create_user(username=post.get('username'), password=post.get('user_verify_password'), email=post.get('email',''), first_name=post.get('user_first_name',''))
            if post.get('user_is_admin',''):
                user.groups.add(group)
        else:
            user_id = int(post.get('user_id'))
            if User.objects.filter(pk=user_id).exists():
                user = User.objects.get(pk=user_id)
                user.email = post.get('email','')
                user.first_name= post.get('user_first_name','')
                if post.get('user_is_admin',''):
                    user.groups.add(group)
                else:
                    if user.is_superuser:
                        content = {"flag":"Error", "context": "ChangeGroupDeny"}
                        status = 403
                        return HttpResponse(json.dumps(content), status = status)

                    user.groups.remove(group)

                user_password = post.get('user_password','')
                verify_password = post.get('user_verify_password','')

                if not (user_password == verify_password == ''):
                    user.set_password(verify_password)

                user.save()
            else:
                content = {"flag":"Error", "context": "UserNotFound"}
                status = 404
                return HttpResponse(json.dumps(content), status = status)
        content = {"flag":"Success"}
        status = 200

    except Exception as e:
        content = {"flag":"Error","context":str(e)}
        status = 400

    return HttpResponse(json.dumps(content), status=status)
