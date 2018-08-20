from oslo_config import cfg

core_opts = [
    cfg.IntOpt('LISTEN_PORT',default=9999,help='listen port'),
    cfg.StrOpt('LOG_LEVEL',default='INFO',help='log level:CRITICAL ERROR WARNING INFO DEBUG NOTSET'),
    cfg.StrOpt('BANDWIDTH',default='100',help='the max network bandwidth,use M as unit'),
    cfg.BoolOpt('CLIENT_TO_CLIENT',default=False,help='allow or deny connection between clients'),
    cfg.StrOpt('SERVERIP',default='10.5.0.1',help='the server tun ip'),
    cfg.StrOpt('DHCP_POOL',default='10.5.0.10-20',help='IP pool assigned to client'),
    cfg.StrOpt('user_file',default='/etc/tcp-forward/user_file',help='user file'),
]


def register_core_common_config_opts(cfg=cfg.CONF):
    cfg.register_opts(core_opts)