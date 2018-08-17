import socket
from binascii import hexlify
import commands

def print_hex_buf(buf):
    current_buf = bytearray(buf)
    print ' '.join(['0x%.2x' % x for x in current_buf])


def strbuf2bytearray(str_buf):

    str_array = str_buf.split(' ')
    result_array = bytearray(len(str_array))
    for s in range(len(str_array)):
        result_array[s] = int(str_array[s],16)

    return result_array

def ip_to_bytearray(ip):
    packed_ip_addr = socket.inet_aton(ip)
    hexStr = hexlify(packed_ip_addr)
    result_array = bytearray(4)
    result_array[0] = int(hexStr[0:2],16)
    result_array[1] = int(hexStr[2:4],16)
    result_array[2] = int(hexStr[4:6],16)
    result_array[3] = int(hexStr[6:8],16)

    return result_array

def bytearray_to_ip(ip_array):

    array2ip = lambda x:'.'.join([ str(x[i]) for i in range(4) ])

    return array2ip(ip_array)

def execute_cmd(cmd):
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        raise Exception(output)


if __name__ == '__main__':
    str_buf = '45 00 00 54 0a f2 40 00 40 01 1b 9f 0a 05 00 05 0a 05 00 0a 08 00 e3 2d 51 e5 00 01 3a 3e 72 5b 00 00 00 00 4e 7f 09 00 00 00 00 00 10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f 20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f 30 31 32 33 34 35 36 37'

    strbuf2bytearray(str_buf)