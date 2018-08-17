from common import tools
from oslo_config import cfg

class DHCPManager(object):
    def __init__(self):
        self.__tun_ip = cfg.CONF.SERVERIP
        # ip range : 10.5.0.10-20
        self.__range_str = cfg.CONF.DHCP_POOL
        self.__parse_range(self.__range_str)


    def __parse_range(self,range_str):
        sufix_int_list = range(*[ int(x) for x in range_str.split('.')[-1].split('-') ] )
        sufix_int_list.append(sufix_int_list[-1] + 1)
        frefix_str = '.'.join(range_str.split('.')[:-1])
        ip_str_list = [frefix_str + '.' + str(a) for a in sufix_int_list]

        allocate_struct = {
            'allocated':False
        }
        self.__ip_allocated = {ip_str:allocate_struct.copy() for ip_str in ip_str_list}

    def get_tun_ip(self):
        return self.__tun_ip


    def allocate_ip(self):
        for ip,info in self.__ip_allocated.items():
            if not info['allocated']:
                info['allocated'] = True
                return ip
        return None

    def return_ip(self,ip):
        if self.__ip_allocated.has_key(ip):
            self.__ip_allocated[ip]['allocated'] = False

    def print_allocated(self):
        for key,value in self.__ip_allocated.items():
            print key + str(value)

if __name__ == '__main__':
    ma = DHCPManager()
    #ma.parse_range('10.5.0.10-15')
    ip = ma.allocate_ip(12)
    print '******:' + ip
    ma.print_allocated()
    print '------------------'
    ma.return_ip(ip)
    ma.print_allocated()