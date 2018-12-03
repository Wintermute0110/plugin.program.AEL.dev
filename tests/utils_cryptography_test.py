import unittest
import mock
from mock import *
from fakes import *

import os

from resources.utils import *

# pip install pyopenssl
from OpenSSL import crypto, SSL

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# pip install pycrypto
# http://aka.ms/vcpython27
from Crypto.PublicKey import RSA 
from Crypto.Signature import PKCS1_v1_5 
from Crypto.Hash import SHA256 

class Test_cryptography_test(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        set_log_level(LOG_DEBUG)
        
    def test_get_public_key_from_certificate(self):
        
        # arrange
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cert_path = FakeFile(test_dir + '/nv_client_test.crt')
        key_path = FakeFile(test_dir + '/nv_client_test.key')

        # act
        create_self_signed_cert("NVIDIA GameStream Client", cert_path, key_path)
        certificate_data = cert_path.getFakeContent()
        actual = getCertificatePublicKey(certificate_data)

        # assert
        self.assertIsNotNone(actual)

    def test_create_certificates(self):

        cert_name = "NVIDIA GameStream Client"
        cert_file_path = 'c:\\temp\\keys\\nvidia.crt'
        key_file_path = 'c:\\temp\\keys\\nvidia.key'

        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        now    = datetime.now()
        expire = now + timedelta(days=365)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "GL"
        cert.get_subject().ST = "GL"
        cert.get_subject().L = "Kodi"
        cert.get_subject().O = "ael"
        cert.get_subject().OU = "ael"
        cert.get_subject().CN = cert_name
        cert.set_serial_number(1000)
        cert.set_notBefore(now.strftime("%Y%m%d%H%M%SZ").encode())
        cert.set_notAfter(expire.strftime("%Y%m%d%H%M%SZ").encode())
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')

        data = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
        with open(cert_file_path, "wb") as f:
            f.write(data)

        data = crypto.dump_privatekey(crypto.FILETYPE_PEM, k)
        with open(key_file_path, "wb") as f:
            f.write(data)

    def test_hashing_a_value(self):

        # arrange
        target = HashAlgorithm(256)

        inputHex = "3e72d22e02dbb0596637d9a02b93156b5e094f0998a28a85acede2c4669ac632bcc47b32f78a1c04ec54ab4632fcb82e043b7f6563ef4182efc8dd973e36079d423d7bc14474908b12f09652bb5641a8a0842161b15fb1f8dd79f2ab3a1f2d99ed8f73a3abb0862aa97bd7bd149deca32f87ada1b46df9f840deb8a76bf76d6aa549f93312043617efdc843f3e16416bf7756f79a6a50c9f5e42424f1014058da6b4f045c426a682cd81921a2ac8d02a0b93031f3bfa05e50b79987f99b68bb3f4d23cc591df7c427b80e1f9ed4a45fcb4b1bc4c866c232d98a6cd5744676ad6ba239026dafd85ff6ce59c7065fa0ebd2e214068b6a7c8d4d2f909067a6ca929f810d5ffdfeade2c3900e62fd47c73c650ca25d03b4ac53368875b9a1bfb50cc"
        expected = "b38b92ee89db21842c6173cffc27d4a58c7a58ce965b7155a5caba711ccba86a"
        input = bytearray.fromhex(inputHex)

        # act
        actual = target.hashToHex(input)
        actual2 = target.hashToHex(input)

        print actual
        print actual2

        # assert
        self.assertEquals(expected, actual)
        self.assertEquals(expected, actual2)
        
    @unittest.skip('PEM conversion testing with an original key')
    def test_converting_pkcs8_to_pem(self):
         # arrange
        test_file = "C:\\Projects\\Kodi\\AEL\\plugin.program.advanced.emulator.launcher\\tests\\assets\\nvidia.key" 
          
        file_contents = ''
        with open(test_file, 'r') as f:
            file_contents = f.read()

        #print file_contents
        print '----------------------------'
        print binascii.hexlify(file_contents)
        print '----------------------------'
        print binascii.hexlify(ssl.DER_cert_to_PEM_cert(file_contents))
        print '----------------------------'
        hex = base64.b64encode(binascii.hexlify(file_contents))
        print hex
        print '----------------------------'
        encoded = base64.b64encode(file_contents)
        print encoded

if __name__ == '__main__':
    unittest.main()
