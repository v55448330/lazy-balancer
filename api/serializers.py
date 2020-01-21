from rest_framework import serializers
from proxy.models import proxy_config,upstream_config 

class ProxySerializers(serializers.ModelSerializer):
    class Meta:
        model = proxy_config 
        fields = '__all__' 
        depth = 2