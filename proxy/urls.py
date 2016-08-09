"""lazy_balancer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views
#from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^$', views.view),
    url(r'^save/$', views.save),
    url(r'^status/$', views.change_status),
    url(r'^checkhttp/$', views.check_http_status),
    url(r'^delete/$', views.delete_proxy),
    url(r'^query/$', views.query_proxy),
    url(r'^logs/$', views.proxy_logs),
    #url(r'^/(?P<action>.*)$', views.action),
]
