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
from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import RedirectView
from django.conf import settings
from .views import logout_view,login_view,create_superuser

urlpatterns = [
    url(r'^login/$', login_view),
    url(r'^logout/$', logout_view),
    url(r'^superuser/$', create_superuser),
    url(r'^dashboard/', include('dashboard.urls')),
    url(r'^main/', include('main.urls')),
    url(r'^proxy/', include('proxy.urls')),
    url(r'^settings/', include('settings.urls')),
    url(r'^$', RedirectView.as_view(url='/dashboard/')),
]
urlpatterns += staticfiles_urlpatterns()
