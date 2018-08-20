from oslo_config import cfg

core_opts = [
    cfg.StrOpt('SERVER_IP',default='127.0.0.1',help='server ip'),
    cfg.IntOpt('SERVER_PORT',default=9999,help='server port'),
    cfg.StrOpt('LOG_LEVEL', default='INFO', help='log level:CRITICAL ERROR WARNING INFO DEBUG NOTSET'),
    cfg.StrOpt('USER_NAME', default='', help='user name'),
    cfg.StrOpt('PASSWORD', default='', help='password'),
]


def register_core_common_config_opts(cfg=cfg.CONF):
    cfg.register_opts(core_opts)