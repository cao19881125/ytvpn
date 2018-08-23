import inner_worker
import outer_worker
from common import forward_event
from common import connector
from common import rsa_handler
import dhcp_manager
import user_pass


class WorkerDoneException(Exception):
    pass

class WorkerManager(object):
    def __init__(self,epoll_recv):
        self.__outer_workers = {}
        self.__epoll_recv = epoll_recv
        self.__inner_worker = None
        self.__worker_id_seq = 0
        self.__dhcp_manager = dhcp_manager.DHCPManager()
        self.__rsa_handler = rsa_handler.RSAHandlerServer()
        self.__user_pass = user_pass.UserPass()
        self.__tunip2id = {}

    def generate_worker_id(self):
        self.__worker_id_seq += 1
        return self.__worker_id_seq

    def add_outer_worker(self,outer_socket,address):
        tun_ip = self.__dhcp_manager.allocate_ip()
        if not tun_ip:
            return None
        _worker_id = self.generate_worker_id()
        self.__tunip2id[tun_ip] = _worker_id
        _outer_worker = outer_worker.OuterWorker(_worker_id,tun_ip,outer_socket,address,self.__outer_to_inner_channel(_worker_id))

        self.__outer_workers[_worker_id] = _outer_worker
        return _outer_worker

    def set_inner_worker(self,tun_connector):
        self.__inner_worker = inner_worker.InnerWorker(0,self.__dhcp_manager.get_tun_ip(),tun_connector,self.__inner_to_outer_channel())
        return self.__inner_worker


    def remove_outer_worker(self,worker_id):
        if self.__outer_workers.has_key(worker_id):
            tun_ip = self.__outer_workers[worker_id].get_tun_ip()
            self.__dhcp_manager.return_ip(tun_ip)
            self.__tunip2id.pop(tun_ip)
            self.__outer_workers.pop(worker_id)

    def all_worker_do(self):
        scheduler_event = forward_event.SchedulerEvent()
        if self.__inner_worker:
            if self.__inner_worker.has_done():
                raise WorkerDoneException()
            self.__inner_worker.handler_event(scheduler_event)

        for id,worker in self.__outer_workers.items():
            if worker.has_done():
                fd = worker.get_con_fd()
                self.__epoll_recv.del_receiver(fd)
                self.remove_outer_worker(id)
                continue
            worker.handler_event(scheduler_event)

    def __inner_to_outer_channel(self):
        def channel(event):
            if event.event_type == forward_event.TRANSDATAEVENT:
                if not self.__tunip2id.has_key(event.dst_ip):
                    return
                id = self.__tunip2id[event.dst_ip]
                self.__outer_workers[id].handler_event(event)

        return channel

    def __outer_to_inner_channel(self,outer_worker_id):
        def channel(event):

            if event.event_type == forward_event.TRANSDATAEVENT:
                if self.__inner_worker:
                    self.__inner_worker.handler_event(event)
            elif event.event_type == forward_event.RSAEVENT:
                if event.rsa_type == forward_event.RSAEvent.Rsa_type.GET_PUB_KEY:
                    return self.__rsa_handler.get_pub_key()
                elif event.rsa_type == forward_event.RSAEvent.Rsa_type.DECODE:
                    return self.__rsa_handler.decode(event.data)
            elif event.event_type == forward_event.USERVERIFYEVENT:
                try:
                    return self.__user_pass.check_pass_word(event.user,event.password)
                except Exception,e:
                    return False

        return channel