from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from nginx.views import *
import json
 
@login_required(login_url="/login/") 
def view(request):
    return render_to_response('settings/view.html')

def modify_pass(request):
    try:
        _post = json.loads(request.body)
        _old_pass = _post['old_password']
        _new_pass = _post['new_password']
        _verify_pass = _post['verify_password']
        if _old_pass and _new_pass and _verify_pass:
            _user = User.objects.get(username="admin")
            if _user.check_password(_old_pass) and _new_pass == _verify_pass:
                _user.set_password(_verify_pass)
                _user.save()
                _content = "Success"
            else:
                _content = "VerifyFaild"
    except Exception,e:
        _content = str(e)

    return HttpResponse(_content)

