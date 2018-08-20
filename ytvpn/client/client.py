import sys
import os
from oslo_config import cfg
PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import logging
import select
from logging.handlers import RotatingFileHandler
from common.tun_connector import TunConnector
from common.connector import CON_STATE
from common.connector import ConnectorClient
from common import epoll_recever
import conf
import worker_manager
logger = logging.getLogger('my_logger')


def run():
    recver = epoll_recever.Epoll_receiver()

    _outer_con = ConnectorClient(cfg.CONF.SERVER_IP,cfg.CONF.SERVER_PORT)
    _outer_con.connect()
    if _outer_con.con_state != CON_STATE.CON_CONNECTED:
        logger.error('connect to remote failed')
        return

    _outer_con.set_blocking(False)

    # init inner_worker
    _tun_con = TunConnector('yt_tun')

    _tun_con.connect()

    if _tun_con.con_state != CON_STATE.CON_CONNECTED:
        logger.error('tun connector failed')
        return

    _worker_manager = worker_manager.WorkerManager()
    _outer_worker = _worker_manager.set_outer_worker(_outer_con)
    _inner_worker = _worker_manager.set_inner_worker(_tun_con)

    recver.add_receiver(_outer_con.get_fileno(), select.EPOLLIN, _outer_worker.handler_event)
    recver.add_receiver(_tun_con.get_fileno(), select.EPOLLIN, _inner_worker.handler_event)

    while True:
        try:
            _worker_manager.all_worker_do()
            recver.run()
        except worker_manager.WorkerDoneException,e:
            logger.info('Process exit')
            return


def log_config(level):
    if not os.path.isdir('/var/log/ytvpn'):
        os.makedirs('/var/log/ytvpn')
    logger.setLevel(logging._levelNames[level])
    handler = RotatingFileHandler("/var/log/ytvpn/client.log", maxBytes=10000000, backupCount=10)
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(process)d %(levelname)s %(filename)s:%(lineno)s %(funcName)s [-] %(message)s ')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(console)

def main():
    conf.register_core_common_config_opts(cfg.CONF)
    log_config(cfg.CONF.LOG_LEVEL)
    logger.info("Process start!")
    run()

if __name__ == '__main__':
    cfg.CONF(sys.argv[1:])
    sys.exit(main())