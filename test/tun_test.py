import fcntl
import os
import sys
import select
import socket
import errno
import ctypes
import struct
import argparse

from if_tun import IfReq, TUNSETIFF, IFF_TUN, IFF_TAP, IFF_NO_PI


def tun_create(devname, flags):
    fd = -1
    if not devname:
        return -1
    fd = os.open("/dev/net/tun", os.O_RDWR)
    if fd < 0:
        print("open /dev/net/tun err!")
        return fd
    r=IfReq()
    ctypes.memset(ctypes.byref(r), 0, ctypes.sizeof(r))
    r.ifr_ifru.ifru_flags |= flags
    r.ifr_ifrn.ifrn_name = devname.encode('utf-8')
    try:
        err = fcntl.ioctl(fd, TUNSETIFF, r)
    except Exception as e:
        print("err:",e)
        os.close(fd)
        return -1
    return fd


def fmt_hex(buf):
	print ' '.join(['%.2x' % x for x in buf])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--listen", help="listen", action="store_true")
    parser.add_argument("-p", "--port", type=int, help="port")
    parser.add_argument("-H", "--host", help="remote host")

    args = parser.parse_args()

    _connector = None
    if args.listen:
        if not args.port:
            print 'server mode must give port'
            return 1

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('0.0.0.0', args.port))
        serversocket.listen(1)
        _connector,address = serversocket.accept()
        print 'accept connection:' + str(_connector.fileno())
    else:
        if not args.host or not args.port:
            print 'client mode must give host and port'
            return 1
        _connector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        _connector.connect((args.host, args.port))
        print 'connect success'

    devFd = tun_create('yt_tun', IFF_TUN | IFF_NO_PI)
    if devFd < 0:
        raise OSError

    _connector.setblocking(0)


    epoll = select.epoll()
    epoll.register(_connector.fileno(), select.EPOLLIN)
    epoll.register(devFd, select.EPOLLIN | select.EPOLLHUP)

    MAXSIZE = 4096
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == devFd:
                buf = os.read(fileno, MAXSIZE)
                _connector.send(buf)
            elif fileno == _connector.fileno():
                error_happen = False
                try:
                    recv_mes = _connector.recv(MAXSIZE)
                    if len(recv_mes) == 0:
                        error_happen = True
                    else:
                        os.write(devFd,recv_mes)
                except socket.error, e:
                    err = e.args[0]
                    if err is not errno.EAGAIN:
                        error_happen = True
                if error_happen:
                    print 'connection closed'
                    _connector.close()
                    return 1
def tun_main():
    if len(sys.argv) != 2:
        print("usage: <tap_name>")
        sys.exit(-1)
    print(sys.argv[1])
    devFd = tun_create(sys.argv[1], IFF_TUN | IFF_NO_PI)
    if devFd < 0:
        raise OSError




    try:
        epfd = select.epoll()
        epfd.register(devFd, select.EPOLLIN | select.EPOLLHUP)
    except Exception as e:
        print("epoll init err",e)
        sys.exit(-1)

    MAXSIZE=4096
    while True:
        epoll_lst = epfd.poll()
        for fd,events in epoll_lst:
            if fd == devFd:
                buf = os.read(fd,MAXSIZE)
                print("read from dev size:%d" % len(buf))
                fmt_hex(bytearray(buf))

if __name__ == "__main__":
    sys.exit(main())



