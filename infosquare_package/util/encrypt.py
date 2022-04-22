import base64
import hashlib
import os
import sys

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util import Padding


class AESCipher:

    def __init__(self) -> None:
        encrypt_key = os.environ["ENCRYPT_KEY"]
        self.key = hashlib.md5(encrypt_key.encode("utf-8")).hexdigest().encode("utf-8")


    def encrypt(self, string: str) -> bytes:
        iv = Random.get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        data = Padding.pad(string.encode("utf-8"), AES.block_size, "pkcs7")

        return base64.b64encode(iv + cipher.encrypt(data))


    def encrypt_file(self, filepath: str) -> None:
        with open(filepath, "r") as f:
            string = f.read()

        enc_data = self.encrypt(string)

        with open(filepath + ".enc", "wb") as f:
            f.write(enc_data)


    def decrypt(self, enc: str) -> str:
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        data = Padding.unpad(cipher.decrypt(enc[AES.block_size:]), AES.block_size, "pkcs7")
    
        return data.decode("utf-8")

    
    def dectypt_file(self, enc_filepath: str, dec_filepath: str) -> None:
        with open(enc_filepath, "rb") as f:
            enc_data = f.read()
        
        dec_data = self.decrypt(enc_data)
        
        with open(dec_filepath, "w") as f:
            f.write(dec_data)


if __name__ == "__main__":
    args = sys.argv
    cipher = AESCipher()

    string = args[1]
    enc = cipher.encrypt(string)
    dec = cipher.decrypt(enc)

    print("Original string: {}".format(string))
    print("Encoded string:  {}".format(enc))
    print("Decoded string:  {}".format(dec))
