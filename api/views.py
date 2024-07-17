# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework.permissions import IsAuthenticated
from api.authentication import APIKeyPermission
from rest_framework.decorators import action, permission_classes, authentication_classes, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, filters, status
from api.serializers import ProxySerializers
from proxy.models import proxy_config
from settings.models import system_settings, sync_status
from settings.views import save_sync, get_config, import_config
from django_filters import rest_framework as filters
from nginx.views import get_sys_info, get_sys_status, get_req_status, get_proxy_upstream_status, test_config
from datetime import datetime
import logging

logger = logging.getLogger('django')

class ProxySetView(viewsets.ReadOnlyModelViewSet):
    """
    ## 获取负载均衡规则
    - GET: 支持 `ssl/protocol/listen/config_id/server_name` 条件过滤，参数均为可选，不填写参数则返回所有结果
    > `ssl:` 是否启用 HTTPS `[True/False]`
    > `protocol:` 协议为 HTTP 或 TCP `[True/False]`
    > `listen:` 规则监听端口 `[1-7999, 8001-65535]`
    > `config_id:` 配置/配置文件 ID `[UUID]`
    > `server_name:` 规则绑定域名，支持模糊查询
    """
    permission_classes = [IsAuthenticated|APIKeyPermission]
    filter_backends = (filters.DjangoFilterBackend,)
    # filterset_fields = ('config_id',) 
    filterset_fields = {
        'config_id': ['exact'],
        'protocol': ['exact'],
        'listen': ['exact'],
        'ssl': ['exact'],
        'server_name': ['icontains']
    }
    queryset = proxy_config.objects.all().order_by('-pk')
    def get_serializer_class(self):
        return ProxySerializers

    @action(methods=["GET"], detail=False)
    def get_cert_status(self, request):
        """
        ## 获取规则 HTTPS 证书状态
        - GET:
        > 参数同 `/proxy/` API
        """
        data=[]
        config_id = request.query_params.get('config_id')
        if config_id:
            p = proxy_config.objects.filter(config_id=config_id).filter(ssl=True)
            if p:
                data.append({config_id:p[0].get_cert_status()})
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            p = proxy_config.objects.filter(ssl=True)
            if p:
                for i in p:
                    data.append({i.config_id:i.get_cert_status()})
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=False)
    def get_upstream_status(self, request):
        """
        ## 获取规则后端节点状态
        - GET:
        > 参数同 `/proxy/` API
        """
        config_id = request.query_params.get('config_id')
        upstream_status = get_proxy_upstream_status()
        if config_id:
            p = proxy_config.objects.filter(config_id=config_id).filter(protocol=True)
            if p:
                data = p[0].get_upstream_status(upstream_status)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            p = proxy_config.objects.filter(protocol=True)
            if p:
                data = upstream_status
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated|APIKeyPermission])
def GetSystemStatus(request):
    """
    ## 获取系统实时状态
    - GET: 获取实时状态统计信息，包括 `服务状态/资源指标/系统信息` 等
    """
    if request.method == 'GET':
        data = {
            'sys_info': get_sys_info(),
            'sys_status': get_sys_status()
        }
        return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated|APIKeyPermission])
def GetReqStatus(request):
    """
    ## 获取系统请求统计
    - GET: 获取所有规则的实时访问请求统计信息，包括 `源/域名/流量/状态码` 等
    """
    if request.method == 'GET':
        req_status = get_req_status()
        data = {
            'sys_req': req_status
        }
        return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated|APIKeyPermission])
def UpdateAccessKey(request):
    """
    ## 更新 API Access Key
    - POST: `{'disable': True}`
    > `disable` 为 `True` 则清空并禁用 Access Key
    > `disable` 为 `False` 则更新并启用 Access Key
    """
    if request.method == 'POST':
        try:
            post = request.data
            s_config = system_settings.objects.all()[0]
            if post.get('disable', False):
                s_config.update_access_key(True)
                if s_config.config_sync_type != 2:
                    save_sync({'config_sync_master_api': '', 'config_sync_interval': '', 'config_sync_type': '0', 'config_sync_access_key': ''})
                return Response({'flag':'Success', 'msg':'access key is disabled.'}, status=status.HTTP_200_OK)
            else:
                s_config.update_access_key(False)
                return Response({'flag':'Success', 'msg':'access key is updated.'}, status=status.HTTP_200_OK)
            pass
        except Exception as e:
            return Response({'flag':'Error', 'msg':str(e)}, status=status.HTTP_400_BAD_REQUEST)
            pass

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated|APIKeyPermission])
def Config(request):
    """
    ## 获取配置文件
    - GET: 导出配置文件 
    - POST: 导入配置文件
    `scope:` `[0, 1, 2]`
        ```
        0 - proxy/upstream config
        1 - main/proxy/upstream config
        2 - system/main/proxy/upstream config
        ```
    """
    if request.method == 'GET':
        try:
            scope = int(request.query_params.get('scope', 2))

            if test_config()['status'] != 0:
                content = {"flag":"Error", "context": "Master nginx config is bad"}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            
            config = get_config(scope)
            if config:
                content = {"flag":"Success", "context": config}
            else:
                content = {"flag":"Error", "context": "get config error"}
        except Exception as e:
            content = {"flag": "Error", "context": str(e)}
    elif request.method == 'POST':
        try:
            post = request.data
            if import_config(post):
                content = {"flag":"Success"}
            else:
                content = {"flag":"Error"}
        except Exception as e:
            content = {"flag": "Error", "context": str(e)}

    return Response(content, status.HTTP_200_OK)

def get_ip(meta):
    x_forwarded_for = meta.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = meta.get('REMOTE_ADDR')
    return ip

@api_view(['POST'])
@permission_classes([IsAuthenticated|APIKeyPermission])
def SyncAck(request):
    """
    ## 配置同步状态通知
    - POST: 通知配置同步状态
    `status` `[1, 2]`
    ```
        1 - sync start
        2 - sync finished
    ```
    """
    try:
        ack = int(request.data.get('status', 0))
        node_ip = get_ip(request.META)
        sync_task = sync_status.objects.filter(address=node_ip)
        if ack == 1:
            # print(system_settings.objects.last().get('config_sync_type', 0))
            logger.info('config sync starting from ' + node_ip)
            if system_settings.objects.last().config_sync_type:
                if sync_task.count():
                    sync_task.delete()

                sync_status.objects.create(
                    address=node_ip,
                    update_time=datetime.now(),
                    status=1
                )
                content = {"flag":"Success"}
                return Response(content, status=status.HTTP_200_OK)
            else:
                logger.error('config sync is disabled')
                content = {"flag":"Error", "context": "config sync is disabled"}
                return Response(content, status=status.HTTP_403_FORBIDDEN)
        elif ack == 2:
            if sync_task.count():
                logger.info('config sync finished from ' + node_ip)
                task = sync_task[0]
                task.update_time = datetime.now()
                task.status = ack
                task.save()
                content = {"flag":"Success"}
                return Response(content, status=status.HTTP_200_OK)
            else:
                content = {"flag":"Error", "context": "task not found"}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
        elif ack == 3:
            if sync_task.count():
                logger.info('config sync failed from ' + node_ip)
                task = sync_task[0]
                task.update_time = datetime.now()
                task.status = ack
                task.save()
                content = {"flag":"Success"}
                return Response(content, status=status.HTTP_200_OK)
            else:
                content = {"flag":"Error", "context": "task not found"}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
        else:
            content = {"flag":"Error", "context": "ack is bad"}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        content = {"flag":"Error", "context": str(e)}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def TestSetView(request):
    """
    ## 测试接口
    """
    if request.method == 'GET':
        return Response({'msg':'Hello World!'}, status=status.HTTP_200_OK)
