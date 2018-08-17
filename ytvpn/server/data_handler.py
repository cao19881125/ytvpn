from common import forward_data, protocol_handler
from common import connector
from common.data_handler import DataHandler
from common import tools
import logging
logger = logging.getLogger('my_logger')

class OuterDataHandler(DataHandler):
    def __init__(self):
        super(OuterDataHandler,self).__init__()
        self.__one_package_size = 2 ** 31

    def send_login_reply(self, worker_id,ip, outer_connector):
        data = tools.ip_to_bytearray(ip)
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.LOGIN, worker_id, '', data)
        protocol_parser = protocol_handler.ProtocolHandler()
        send_package = protocol_parser.build_data(forw_data)
        outer_connector.send(send_package)

    def trans_data(self,forward_id,data,outer_connector):
        ori = 0
        total_len = len(data)

        while ori < total_len:
            if total_len - ori <= self.__one_package_size:
                send_data = data[ori:total_len]
            else:
                send_data = data[ori:ori + self.__one_package_size]

            _protocol_handler = protocol_handler.ProtocolHandler()
            forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, forward_id,'', send_data)
            send_package = _protocol_handler.build_data(forw_data)
            if outer_connector and outer_connector.con_state == connector.CON_STATE.CON_CONNECTED:
                send_bytes = outer_connector.send(send_package)
                if send_bytes <= 0:
                    logger.error("TransData to inner send failed,forward_id:%d " % (
                    forward_id))
                    raise Exception("Send data failed")
                    # print 'inner_connector send package'
                    # tools.print_hex_buf(send_package)
            ori += self.__one_package_size
