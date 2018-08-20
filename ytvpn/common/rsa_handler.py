from Crypto import Random
from Crypto.Hash import SHA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.PublicKey import RSA
import base64

class RSAHandlerServer(object):
    def __init__(self):
        self.__private_pem = None
        self.__public_pem = None
        self.generate_key_pair()

    def generate_key_pair(self):
        self.__random_generator = Random.new().read
        rsa = RSA.generate(1024, self.__random_generator)
        self.__private_pem = rsa.exportKey()

        self.__public_pem = rsa.publickey().exportKey()

    def get_pub_key(self):
        if not self.__public_pem:
            self.generate_key_pair()

        return self.__public_pem

    def decode(self,msg):
        if not self.__private_pem or not self.__random_generator:
            return None
        rsakey = RSA.importKey(self.__private_pem)
        cipher = Cipher_pkcs1_v1_5.new(rsakey)
        text = cipher.decrypt(base64.b64decode(msg), self.__random_generator)
        return text

class RSAHandlerClient(object):

    def encode(self,pub_key,msg):
        rsakey = RSA.importKey(pub_key)
        cipher = Cipher_pkcs1_v1_5.new(rsakey)
        cipher_text = base64.b64encode(cipher.encrypt(msg))
        return cipher_text