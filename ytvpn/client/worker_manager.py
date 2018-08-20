import inner_worker
import outer_worker
from common import forward_event
from common import rsa_handler

class WorkerDoneException(Exception):
    pass

class WorkerManager(object):
    def __init__(self):
        self.__inner_worker = None
        self.__outer_worker = None
        self.__rsa_handler = rsa_handler.RSAHandlerClient()

    def set_inner_worker(self, tun_connector):
        self.__inner_worker = inner_worker.InnerWorker(tun_connector,self.__inner_to_outer_channel())
        return self.__inner_worker

    def set_outer_worker(self,outer_connector):
        self.__outer_worker = outer_worker.OuterWorker(outer_connector,self.__outer_to_inner_channel())
        return self.__outer_worker

    def all_worker_do(self):
        scheduler_event = forward_event.SchedulerEvent()

        if self.__inner_worker:
            if self.__inner_worker.has_done():
                raise WorkerDoneException()
            self.__inner_worker.handler_event(scheduler_event)

        if self.__outer_worker:
            if self.__outer_worker.has_done():
                raise WorkerDoneException()
            self.__outer_worker.handler_event(scheduler_event)

    def __inner_to_outer_channel(self):
        def channel(event):
            if event.event_type == forward_event.TRANSDATAEVENT:
                if self.__outer_worker:
                    self.__outer_worker.handler_event(event)

        return channel

    def __outer_to_inner_channel(self):
        def channel(event):
            if event.event_type in (forward_event.TRANSDATAEVENT,forward_event.ALLOCATEIPEVENT):
                if self.__inner_worker:
                    self.__inner_worker.handler_event(event)
            elif event.event_type == forward_event.RSAEVENT:
                if event.rsa_type == forward_event.RSAEvent.Rsa_type.ENCODE:
                    return self.__rsa_handler.encode(*event.data)
        return channel