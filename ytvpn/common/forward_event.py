from enum import Enum

FDEVENT = 'FDEvent'
TRANSDATAEVENT = 'TransDataEvent'
CLOSECONEVENT = 'CloseConEvent'
SCHEDULEREVENT = 'SchedulerEvent'
ALLOCATEIPEVENT = 'AllocateIPEvent'
RSAEVENT = 'RSAEvent'
USERVERIFYEVENT = 'UserVerifyEvent'

class ForwardEvent(object):
    def __init__(self,event_type):
        self.event_type = event_type

class FDEvent(ForwardEvent):
    def __init__(self,fd_event):
        super(FDEvent,self).__init__(FDEVENT)
        self.fd_event = fd_event

class SchedulerEvent(ForwardEvent):
    def __init__(self):
        super(SchedulerEvent,self).__init__(SCHEDULEREVENT)

class TransDataEvent(ForwardEvent):
    def __init__(self,dst_ip,forward_data):
        super(TransDataEvent,self).__init__(TRANSDATAEVENT)
        self.dst_ip = dst_ip
        self.forward_data = forward_data

class CloseConEvent(ForwardEvent):
    def __init__(self,forward_id):
        super(CloseConEvent,self).__init__(CLOSECONEVENT)
        self.forward_id = forward_id

class AllocateIPEvent(ForwardEvent):
    def __init__(self,ip):
        super(AllocateIPEvent,self).__init__(ALLOCATEIPEVENT)
        self.dst_ip = ip

class UserVerifyEvent(ForwardEvent):
    def __init__(self,user,password):
        super(UserVerifyEvent,self).__init__(USERVERIFYEVENT)
        self.user = user
        self.password = password


class RSAEvent(ForwardEvent):
    class Rsa_type(Enum):
        GET_PUB_KEY = 1
        ENCODE = 2
        DECODE = 3
    def __init__(self,type,data = ''):
        super(RSAEvent,self).__init__(RSAEVENT)
        self.rsa_type = type
        self.data = data

class LoginEvent(ForwardEvent):
    def __init__(self,user,passwd):
        self.user = user
        self.passwd = passwd

def event_filter(func):
    def filter(*args,**kwargs):
        if type(args[1]) == int:
            f_event = FDEvent(args[1])
        else:
            f_event = args[1]

        if not isinstance(f_event,ForwardEvent):
            raise Exception('event_filter event is not subclass of ForwardEvent:' + str(type(f_event)))

        return func(args[0],f_event,*args[2:],**kwargs)
    return filter