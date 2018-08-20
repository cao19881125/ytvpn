import select
from oslo_config import cfg
from enum import Enum
from common import forward_event
from common import forward_data
from common.connector import CON_STATE
from common.tun_connector import TunConnector
from common.ip_protocol_handler import IPProtocolHandler
import logging
import traceback
logger = logging.getLogger('my_logger')
import time

class InnerWorker(object):
    class State(Enum):
        NONE = 0
        WORKING = 1
        CLOSED = 2
        DONE = 3

    def __init__(self,worker_id,tun_ip,tun_connectr,north_interface_channel):
        self.__id = worker_id
        self.__tun_ip = tun_ip
        self.__state = self.State.NONE
        self.__north_interface_channel = north_interface_channel
        self.__tun_connector = tun_connectr

    def has_done(self):
        return self.__state == self.State.DONE

    def __sourth_interface_event(self, event):
        if self.__state == self.State.WORKING:
            self.__handle_working_event(event)

    def __north_interface_transdata_event(self, event):
        if not isinstance(event,forward_event.TransDataEvent):
            return
        if self.__state == self.State.WORKING:
            if event.forward_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
                ip_packages = IPProtocolHandler.parse_ip_package(event.forward_data.data)
                for package in ip_packages:
                    send_bytes = self.__tun_connector.send(package[1])
                    if send_bytes <= 0:
                        logger.error("InnerWorker %d trans bytes <=0 change state to CLOSED", self.__id)
                        self.__state = self.State.CLOSED
                        return
                # self.__dispatch_data(event.forward_data.data,cfg.CONF.CLIENT_TO_CLIENT)

    def __dispatch_data(self,data,allow2other):
        ip_packages = IPProtocolHandler.parse_ip_package(data)
        ip_msg_map = {}

        for package in ip_packages:
            if package[0] == self.__tun_ip:
                send_bytes = self.__tun_connector.send(package[1])
                if send_bytes <= 0:
                    logger.error("InnerWorker %d trans bytes <=0 change state to CLOSED", self.__id)
                    self.__state = self.State.CLOSED
                    return
            else:
                if not ip_msg_map.has_key(package[0]):
                    ip_msg_map[package[0]] = package[1]
                else:
                    ip_msg_map[package[0]] += package[1]

        if not allow2other:
            return

        for ip, data in ip_msg_map.items():
            trans_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, 0, ip, data)
            trans_data_event = forward_event.TransDataEvent(ip, trans_data)
            self.__north_interface_channel(trans_data_event)

    def __scheduler_event(self, event):
        if self.__state == self.State.NONE:
            if self.__tun_connector.con_state != CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
            else:
                try:
                    self.__tun_connector.set_tun_ip(self.__tun_ip)
                    self.__tun_connector.set_tun_up()
                except Exception,e:
                    logger.error('Innerworker set tun ip & up failed,change state to close')
                    self.__state = self.State.CLOSED
                    return
                self.__state = self.State.WORKING
        elif self.__state == self.State.CLOSED:
            self.__tun_connector.close()
            self.__state = self.State.DONE

    def __handle_working_event(self, event):
        error_happen = False
        if event.fd_event & select.EPOLLIN:
            recv_msg = self.__tun_connector.recv()
            if len(recv_msg) > 0:
                # trans data
                try:
                    ip_packages = IPProtocolHandler.parse_ip_package(bytearray(recv_msg))
                    ip_msg_map = {}
                    for package in ip_packages:

                        if not ip_msg_map.has_key(package[0]):
                            ip_msg_map[package[0]] = package[1]
                        else:
                            ip_msg_map[package[0]] += package[1]

                    for ip, data in ip_msg_map.items():
                        trans_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, 0, ip, data)
                        trans_data_event = forward_event.TransDataEvent(ip, trans_data)
                        self.__north_interface_channel(trans_data_event)
                    #self.__dispatch_data(bytearray(recv_msg),True)
                except Exception, e:
                    error_happen = True
                    logger.error("InnerWorker %d current state:WORKING send data error" % (self.__id))
                    logger.debug(traceback.format_exc())

            else:
                if self.__tun_connector.con_state != CON_STATE.CON_CONNECTED:
                    error_happen = True
                    logger.error("InnerWorker %d current state:WORKING recv data error" % (self.__id))

        elif event.fd_event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker %d current state:WORKING change state to CLOSED" % (self.__id))

    @forward_event.event_filter
    def handler_event(self, event):
        if event.event_type == forward_event.FDEVENT:
            # socket receive msg
            self.__sourth_interface_event(event)
        elif event.event_type == forward_event.TRANSDATAEVENT:
            self.__north_interface_transdata_event(event)
        elif event.event_type == forward_event.SCHEDULEREVENT:
            self.__scheduler_event(event)