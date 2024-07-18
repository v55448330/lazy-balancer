from django.conf.urls import include,url
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import *

schema_view = get_schema_view(
   openapi.Info(
      title="Lazy Balancer API",
      default_version='v1',
      description="如果你想使用 Access Key 方式认证，请先通过管理页面创建 Access Key，并在请求 URL 增加 '?access_key={{AccessKey}}' 即可",
      contact=openapi.Contact(email="zhang@xiaobao.cool"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
 
route = routers.DefaultRouter()
route.register(r'proxy', ProxySetView)
# route.register(r'test', TestSetView)
 
urlpatterns = [
    url('', include(route.urls)),
    url(r'^docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   #  url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    url(r'^sys/status/$', GetSystemStatus),
    url(r'^sys/req/$', GetReqStatus),
    url(r'^settings/update_accesskey/$', UpdateAccessKey),
    url(r'^settings/config/$', Config),
    url(r'^settings/sync_ack/$', SyncAck),
    url(r'^settings/sync_status/$', GetSyncStatus),
    url(r'^test/$', TestSetView),
]