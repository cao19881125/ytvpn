from common.protocol_handler import ProtocolHandler
from common import forward_data
from common import tools


class ClientProtocolHandler(ProtocolHandler):

    def parse_data(self, array_buf):
        result_data = super(ClientProtocolHandler,self).parse_data(array_buf)
        if not result_data:
            return None

        if result_data.data_type == forward_data.DATA_TYPE.LOGIN:
            result_data.dst_ip = tools.bytearray_to_ip(result_data.data)

        return result_data
