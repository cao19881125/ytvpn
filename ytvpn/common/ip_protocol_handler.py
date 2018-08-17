import tools

class IPProtocolHandler(object):

    @classmethod
    def parse_ip_package(self,buf):
        packages = []

        temp_buf = buf
        while True:
            if len(temp_buf) < 20:
                return tuple(packages)
            ip_version = temp_buf[0]/0x10
            if ip_version != 4:
                return tuple(packages)

            pack_len = temp_buf[2]*0x100 + temp_buf[3]

            if len(temp_buf) < pack_len:
                return tuple(packages)

            dist_ip = tools.bytearray_to_ip(temp_buf[16:20])

            packages.append((dist_ip,temp_buf[:pack_len]))
            temp_buf = temp_buf[pack_len:]



if __name__ == '__main__':
    icmp_buf = '45 00 00 54 0a f2 40 00 40 01 1b 9f 0a 05 00 05 0a 05 00 0a 08 00 e3 2d 51 e5 00 01 3a 3e 72 5b 00 00 00 00 4e 7f 09 00 00 00 00 00 10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f 20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f 30 31 32 33 34 35 36 37'
    str_buf = icmp_buf + ' ' + icmp_buf
    icmp_array = tools.strbuf2bytearray(str_buf)

    ip_pro = IPProtocolHandler()
    parsed_pack = ip_pro.parse_ip_package(icmp_array)
    for pack in parsed_pack:
        tools.print_hex_buf(pack[1])
