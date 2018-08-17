import os
import ctypes
import fcntl
from connector import CON_STATE
from if_tun import IfReq, TUNSETIFF, IFF_TUN, IFF_TAP, IFF_NO_PI
import tools
import time

class TunConnector(object):
    def __init__(self, tun_name):
        self._tun_name = tun_name
        self.con_state = CON_STATE.CON_NONE


    def __set_blocking(self,if_block):
        fl = fcntl.fcntl(self._fd, fcntl.F_GETFL)

        if if_block:
            fcntl.fcntl(self._fd, fcntl.F_SETFL, fl ^ os.O_NONBLOCK)
        else:
            fcntl.fcntl(self._fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def set_tun_ip(self,ip):
        self.__tun_ip = ip
        cmd = 'ip address add ' + ip + '/24 dev ' + self._tun_name
        tools.execute_cmd(cmd)


    def set_tun_up(self):
        cmd = 'ip link set ' + self._tun_name + ' up'
        tools.execute_cmd(cmd)

    def connect(self):
        if not self._tun_name:
            raise Exception('tun name is None')

        self._fd = os.open("/dev/net/tun", os.O_RDWR)

        if self._fd < 0:
            raise Exception('open /dev/net/tun err!')

        r = IfReq()
        ctypes.memset(ctypes.byref(r), 0, ctypes.sizeof(r))
        r.ifr_ifru.ifru_flags |= IFF_TUN | IFF_NO_PI
        r.ifr_ifrn.ifrn_name = self._tun_name
        try:
            err = fcntl.ioctl(self._fd, TUNSETIFF, r)
        except Exception as e:
            print("err:", e)
            os.close(self._fd)
            self.con_state = CON_STATE.CON_FAILED
            return

        self.__set_blocking(False)
        self.con_state = CON_STATE.CON_CONNECTED

    def recv(self):
        if self.con_state != CON_STATE.CON_CONNECTED:
            return ''

        recv_msg = ''
        while True:
            try:
                recv_msg_temp = os.read(self._fd, 1024 * 1024)

                recv_msg += recv_msg_temp
            except Exception,e:
                return recv_msg

    def send(self,msg):
        try:
            self.__set_blocking(True)
            send_bytes = os.write(self._fd,msg)
            self.__set_blocking(False)

            return send_bytes
        except Exception,e:
            self.close()
            return 0

    def get_fileno(self):
        return self._fd

    def close(self):
        if self.con_state == CON_STATE.CON_NONE:
            self.con_state = CON_STATE.CON_CLOSED
            return
        if self.con_state != CON_STATE.CON_CLOSED:
            os.close(self._fd)
            self.con_state = CON_STATE.CON_CLOSED