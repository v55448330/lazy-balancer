from settings.models import system_settings
from nginx.views import *
import iptc

def ip_into_int(ip):
    return reduce(lambda x,y:(x<<8)+y,map(int,ip.split('.')))

def is_internal_ip(ip):
    ip = ip_into_int(ip)
    net_a = ip_into_int('10.255.255.255') >> 24
    net_b = ip_into_int('172.31.255.255') >> 20
    net_c = ip_into_int('192.168.255.255') >> 16
    return ip >> 24 == net_a or ip >>20 == net_b or ip >> 16 == net_c

def set_internal_firewall(network,port_list):
    chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "INPUT")
    chain.flush()

    for port in port_list:
        rule = iptc.Rule()
        rule.target = iptc.Target(rule, "ACCEPT")
        rule.protocol = "tcp"
        rule.src = network
        match = iptc.Match(rule, "tcp")
        match.dport = str(port)
        rule.add_match(match)
        chain.insert_rule(rule)

    rule = iptc.Rule()
    rule.target = iptc.Target(rule, "ACCEPT")
    match = iptc.Match(rule, "state")
    match.state = "RELATED,ESTABLISHED"
    rule.add_match(match)
    chain.insert_rule(rule)

    rule = iptc.Rule()
    rule.target = iptc.Target(rule, "ACCEPT")
    rule.in_interface = "lo"
    chain.insert_rule(rule)

    chain.set_policy("DROP")

def set_public_firewall(port_list):
    chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "INPUT")

    for port in port_list:
        rule = iptc.Rule()
        rule.target = iptc.Target(rule, "ACCEPT")
        rule.protocol = "tcp"
        match = iptc.Match(rule, "tcp")
        match.dport = str(port)
        rule.add_match(match)
        chain.insert_rule(rule)

def set_firewall():
    if system_settings.objects.all().count() != 0:
        internal_nic = system_settings.objects.all()[0].internal_nic
        if internal_nic != "":
            internal_port = [22,8000]
            public_port = []

            for proxy in proxy_config.objects.all():
                public_port.append(proxy.listen)
            public_port = list(set(public_port))

            address = ""
            nics = get_sys_info()['nic']

            for nic in nics:
                if nic['nic'] == internal_nic:
                    for i in nic['address'].split('.')[:2]:
                        address += i + '.'
                    address += '0.0/16'

            set_internal_firewall(address,internal_port)
            set_public_firewall(public_port)
