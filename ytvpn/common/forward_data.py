

class DATA_TYPE(object):
    LOGIN = 0x00
    LOGIN_FAILED = 0x01
    TRANS_DATA = 0x20
    HEART_BEAT = 0x30


class ForwardData(object):
    def __init__(self,data_type=0,forward_id=0,dst_ip='' ,data=''):
        self.data_type = data_type
        self.id = forward_id
        self.dst_ip = dst_ip
        self.data = data
