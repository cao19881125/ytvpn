import select
from enum import Enum
from common import forward_event
from common import forward_data
from common.connector import CON_STATE
from common.ip_protocol_handler import IPProtocolHandler
import logging
import traceback
import time
logger = logging.getLogger('my_logger')

class InnerWorker(object):
    class State(Enum):
        NONE = 0
        ALLOCATE_IP = 1
        WORKING = 2
        CLOSED = 3
        DONE = 4

    def __init__(self,tun_connector,north_interface_channel):
        self.__north_interface_channel = north_interface_channel
        self.__tun_connector = tun_connector
        self.__state = self.State.NONE

    def has_done(self):
        return self.__state == self.State.DONE

    def __scheduler_event(self, event):
        if self.__state == self.State.NONE:
            if self.__tun_connector.con_state != CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
            else:

                self.__state = self.State.ALLOCATE_IP
        elif self.__state == self.State.CLOSED:
            self.__tun_connector.close()
            self.__state = self.State.DONE

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
                        logger.error("InnerWorker trans bytes <=0 change state to CLOSED")
                        self.__state = self.State.CLOSED
                        return

    def __allocate_ip_event(self,event):
        if self.__state != self.State.ALLOCATE_IP:
            return
        try:
            self.__tun_connector.set_tun_ip(event.dst_ip)
            self.__tun_connector.set_tun_up()
            self.__state = self.State.WORKING
            logger.info('InnerWorker allocated ip:' + event.dst_ip)
        except Exception,e:
            logger.error('Innerworker set tun ip & up failed,change state to close')
            self.__state = self.State.CLOSED
            return

    def __handle_working_event(self, event):
        error_happen = False
        if event.fd_event & select.EPOLLIN:

            recv_msg = self.__tun_connector.recv()
            if len(recv_msg) > 0:
                # trans data
                try:
                    # ip_packages = IPProtocolHandler.parse_ip_package(bytearray(recv_msg))
                    # ip_msg_map = {}
                    # for package in ip_packages:
                    #
                    #     if not ip_msg_map.has_key(package[0]):
                    #         ip_msg_map[package[0]] = package[1]
                    #     else:
                    #         ip_msg_map[package[0]] += package[1]
                    #
                    # for ip,data in ip_msg_map.items():
                    #     trans_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, 0,ip,data)
                    #     trans_data_event = forward_event.TransDataEvent(ip, trans_data)
                    #     self.__north_interface_channel(trans_data_event)
                    trans_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, 0, '', bytearray(recv_msg))
                    trans_data_event = forward_event.TransDataEvent('', trans_data)
                    self.__north_interface_channel(trans_data_event)
                except Exception, e:
                    error_happen = True
                    logger.error("InnerWorker  current state:WORKING send data error" )
                    logger.debug(traceback.format_exc())

            else:
                if self.__tun_connector.con_state != CON_STATE.CON_CONNECTED:
                    error_happen = True
                    logger.error("InnerWorker  current state:WORKING recv data error" )

        elif event.fd_event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker current state:WORKING change state to CLOSED" )


    @forward_event.event_filter
    def handler_event(self, event):
        if event.event_type == forward_event.FDEVENT:
            # socket receive msg
            self.__sourth_interface_event(event)
        elif event.event_type == forward_event.TRANSDATAEVENT:
            self.__north_interface_transdata_event(event)
        elif event.event_type == forward_event.SCHEDULEREVENT:
            self.__scheduler_event(event)
        elif event.event_type == forward_event.ALLOCATEIPEVENT:
            self.__allocate_ip_event(event)