import select
import logging
from enum import Enum
from common import connector
from common import ring_buffer
from common import forward_data
from common import forward_event
import data_handler
import json
import time

logger = logging.getLogger('my_logger')
class OuterWorker(object):
    class State(Enum):
        NONE = 0
        LOGIN = 1
        WORKING = 3
        CLOSED = 4
        DONE = 5

    def __init__(self,worker_id,tun_ip,outer_socket,address,sourth_interface_channel):
        self.__worker_id = worker_id
        self.__tun_ip = tun_ip
        self.__address = address
        self.__connector = connector.Connector(outer_socket)
        self.__data_handler = data_handler.OuterDataHandler()
        self.__ring_buffer = ring_buffer.TimeoutRingbuffer(10240 * 10240, 5)
        self.__state = self.State.NONE
        self.__sourth_interface_channel = sourth_interface_channel

    def get_con_fd(self):
        return self.__connector.get_fileno()

    def get_tun_ip(self):
        return self.__tun_ip

    def has_done(self):
        return self.__state == self.State.DONE

    def __north_interface_event(self, event):
        if self.__state in (self.State.LOGIN,self.State.WORKING):
            self.__handle_working_event(event)

    def __handle_working_event(self, event):
        error_happen = False
        if event.fd_event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                # pass data
                self.__ring_buffer.put(bytearray(recv_msg))
                # self.__ring_buffer.print_buf()
            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                    logger.error("OuterWorker %d current state:WORKING recv data error"%(self.__worker_id))

        elif event.fd_event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__state = self.State.CLOSED
            logger.debug("OuterWorker %d current state:WORKING change state to DISCONNECTED"%(self.__worker_id))

    def send_heart_beat_reply(self):
        try:
            self.__data_handler.send_heart_beat_reply(self.__connector)
        except Exception, e:
            logger.error("OuterWorker %d current state:WORKING send heartbeat reply error,change state to DISCONNECTED"%(self.__worker_id))
            self.__state = self.State.DISCONNECTED

    def __handle_data(self):


        datas = self.__data_handler.get_forward_datas(self.__ring_buffer)



        if len(datas) <= 0:
            return

        if self.__state == self.State.LOGIN:
            for data in datas:
                if data.data_type == forward_data.DATA_TYPE.LOGIN_PUBKEY:
                    # self.__data_handler.send_login_reply(self.__worker_id,self.__tun_ip,self.__connector)
                    # self.__state = self.State.WORKING
                    # logger.debug('OutWorker %d current state:LOGIN change state to WORKING'%(self.__worker_id))
                    get_pub_key_event = forward_event.RSAEvent(forward_event.RSAEvent.Rsa_type.GET_PUB_KEY)
                    pubkey = self.__sourth_interface_channel(get_pub_key_event)
                    if not pubkey:
                        logger.error('OuterWorker %d get pubkey failed change state to CLOSED'%(self.__worker_id))
                        self.__state = self.State.CLOSED
                        return
                    self.__data_handler.send_pubkey_reply(self.__worker_id,pubkey,self.__connector)
                elif data.data_type == forward_data.DATA_TYPE.LOGIN_USERINFO:
                    parse_data_event = forward_event.RSAEvent(forward_event.RSAEvent.Rsa_type.DECODE,data.data)
                    json_str = self.__sourth_interface_channel(parse_data_event)
                    try:
                        user_info = json.loads(json_str)
                    except Exception,e:
                        logger.error('OuterWorker %d pars user info failed:user info:%s'%(self.__worker_id,json_str))

                    user_check_event = forward_event.UserVerifyEvent(user_info['user_name'],user_info['password'])
                    result = self.__sourth_interface_channel(user_check_event)
                    if result:
                        info_to_client = {'tun_ip':self.__tun_ip,'gateway_ip':''}
                        self.__data_handler.send_login_reply(True,self.__worker_id,json.dumps(info_to_client),self.__connector)
                        self.__state = self.State.WORKING
                        logger.info('OuterWorker %d login success,change state to WORKING'%(self.__worker_id))
                    else:
                        self.__data_handler.send_login_reply(False,self.__worker_id,'',self.__connector)
                        self.__state = self.State.CLOSED
                        logger.info('OuterWorker %d login failed,change state to CLOSED'%(self.__worker_id))
        elif self.__state == self.State.WORKING:
            for data in datas:
                if data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
                    trans_event = forward_event.TransDataEvent(data.id, data)
                    self.__sourth_interface_channel(trans_event)
                elif data.data_type == forward_data.DATA_TYPE.HEART_BEAT:
                    self.send_heart_beat_reply()
                    logger.debug("OuterWorker %d send heartbeat reply " % (self.__worker_id))

    def __scheduler_event(self, event):
        if not isinstance(event,forward_event.SchedulerEvent):
            return

        if self.__state == self.State.NONE:
            self.__state = self.State.LOGIN
            self.__login_begin_time = time.time()
            #self.__state = self.State.WORKING
        elif self.__state == self.State.LOGIN:
            if time.time() - self.__login_begin_time > 5:
                logger.error('OuterWorker %d current state:LOGIN wait client over 5 seconds,closed'%(self.__worker_id))
                #self.__state = self.State.CLOSED
                return
        elif self.__state == self.State.WORKING:
            if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
                logger.debug("OuterWorker current state:WORKING change state to CLOSED due connector state error:%s"%(str(self.__connector.con_state)) )
                return
        elif self.__state == self.State.CLOSED:
            self.__connector.close()
            self.__state = self.State.DONE
            logger.debug("OuterWorker current state:CLOSED change state to DONE")
            return
        self.__handle_data()

    def __sourth_interface_closecon_event(self, event):
        if not isinstance(event,forward_event.CloseConEvent):
            return
        self.__state = self.State.CLOSED


    def __sourth_interface_transdata_event(self, event):
        if not isinstance(event,forward_event.TransDataEvent):
            return

        f_data = event.forward_data
        if event.forward_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
            self.__data_handler.trans_data(f_data.id, f_data.data, self.__connector)




    @forward_event.event_filter
    def handler_event(self,event):
        if event.event_type == forward_event.FDEVENT:
            # socket receive msg
            self.__north_interface_event(event)
        elif event.event_type == forward_event.TRANSDATAEVENT:
            self.__sourth_interface_transdata_event(event)
        elif event.event_type == forward_event.CLOSECONEVENT:
            self.__sourth_interface_closecon_event(event)
        elif event.event_type == forward_event.SCHEDULEREVENT:
            self.__scheduler_event(event)