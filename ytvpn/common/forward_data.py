

class DATA_TYPE(object):
    LOGIN_PUBKEY = 0x00
    LOGIN_USERINFO = 0X01
    LOGIN_SUCCESS = 0X02
    LOGIN_FAILED = 0x03
    TRANS_DATA = 0x20
    HEART_BEAT = 0x30


class ForwardData(object):
    def __init__(self,data_type=0,forward_id=0,dst_ip='' ,data=''):
        self.data_type = data_type
        self.id = forward_id
        self.dst_ip = dst_ip
        self.data = data
