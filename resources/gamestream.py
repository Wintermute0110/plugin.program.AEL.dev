# --- Python standard library ---
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from os.path import expanduser

import sys, uuid, random, binascii, urllib2

from net_IO import *
from utils import *

class GameStreamServer(object):
    
    def __init__(self, host, assets_path):

        self.host = host
        self.unique_id = random.getrandbits(16)

        if assets_path:
            self.certificates_path = assets_path.pjoin('certs/')
            self.certificate_file_path = self.certificates_path.pjoin('nvidia.crt')
            self.certificate_key_file_path = self.certificates_path.pjoin('nvidia.key')
        else:
            self.certificates_path = FileNameFactory.create('')
            self.certificate_file_path = FileNameFactory.create('')
            self.certificate_key_file_path = FileNameFactory.create('')

        log_debug('GameStreamServer() Using certificate key file {}'.format(self.certificate_key_file_path.getOriginalPath()))
        log_debug('GameStreamServer() Using certificate file {}'.format(self.certificate_file_path.getOriginalPath()))

        self.pem_cert_data = None
        self.key_cert_data = None

    def _perform_server_request(self, end_point,  useHttps=True, parameters = None):
        
        if useHttps:
            url = "https://{0}:47984/{1}?uniqueid={2}&uuid={3}".format(self.host, end_point, self.unique_id, uuid.uuid4().hex)
        else:
            url = "http://{0}:47989/{1}?uniqueid={2}&uuid={3}".format(self.host, end_point, self.unique_id, uuid.uuid4().hex)

        if parameters:
            for key, value in parameters.iteritems():
                url = url + "&{0}={1}".format(key, value)

        handler = HTTPSClientAuthHandler(self.certificate_key_file_path.getOriginalPath(), self.certificate_file_path.getOriginalPath())
        page_data = net_get_URL_using_handler(url, handler)
    
        if page_data is None:
            return None

        root = ET.fromstring(page_data)
        #log_debug(ET.tostring(root,encoding='utf8',method='xml'))
        return root

    def connect(self):
        log_debug('Connecting to gamestream server {}'.format(self.host))
        self.server_info = self._perform_server_request("serverinfo")
        
        if not self.is_connected():
            self.server_info = self._perform_server_request("serverinfo", False)
        
        return self.is_connected()

    def is_connected(self):
        if self.server_info is None:
            log_debug('No succesfull connection to the server has been made')
            return False

        if self.server_info.find('state') is None:
            log_debug('Server state {0}'.format(self.server_info.attrib['status_code']))
        else:
            log_debug('Server state {0}'.format(self.server_info.find('state').text))

        return self.server_info.attrib['status_code'] == '200'

    def get_server_version(self):

        appVersion = self.server_info.find('appversion')
        return VersionNumber(appVersion.text)
    
    def generatePincode(self):

        i1 = random.randint(1, 9)
        i2 = random.randint(1, 9)
        i3 = random.randint(1, 9)
        i4 = random.randint(1, 9)
    
        return '{0}{1}{2}{3}'.format(i1, i2, i3, i4)

    def is_paired(self):

        if not self.is_connected():
            log_warning('Connect first')
            return False

        pairStatus = self.server_info.find('PairStatus')
        return pairStatus.text == '1'

    def pairServer(self, pincode):
        from utils_cryptography import *

        if not self.is_connected():
            log_warning('Connect first')
            return False

        version = self.get_server_version()
        log_info("Pairing with server generation: {0}".format(version.getFullString()))

        majorVersion = version.getMajor()
        if majorVersion >= 7:
			# Gen 7+ uses SHA-256 hashing
            hashAlgorithm = HashAlgorithm(256)
        else:
            # Prior to Gen 7, SHA-1 is used
            hashAlgorithm = HashAlgorithm(1)

        log_debug('Pin {0}'.format(pincode))
        
        # Generate a salt for hashing the PIN
        salt = randomBytes(16)
        # Combine the salt and pin
        saltAndPin = salt + bytearray(pincode, 'utf-8')

        # Create an AES key from them
        aes_cypher = AESCipher(saltAndPin, hashAlgorithm)

        # get certificates ready
        log_debug('Getting local certificate files')
        client_certificate      = self.getCertificateBytes()
        client_key_certificate  = self.getCertificateKeyBytes()
        certificate_signature   = getCertificateSignature(client_certificate)
        
        # Start pairing with server
        log_debug('Start pairing with server')
        pairing_result = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'phrase': 'getservercert', 
            'salt': binascii.hexlify(salt),
            'clientcert': binascii.hexlify(client_certificate)
            })

        if pairing_result is None:
            log_error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_result.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            return False

        server_cert_data = pairing_result.find('plaincert').text
        if server_cert_data is None:
            log_error('Failed to pair with server. A different pairing session might be in progress.')
            return False
        
        # Generate a random challenge and encrypt it with our AES key
        challenge = randomBytes(16)
        encrypted_challenge = aes_cypher.encryptToHex(challenge)
        
        # Send the encrypted challenge to the server
        log_debug('Sending encrypted challenge to the server')
        pairing_challenge_result = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'clientchallenge': encrypted_challenge })
        
        if pairing_challenge_result is None:
            log_error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_challenge_result.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False
        
		# Decode the server's response and subsequent challenge
        log_debug('Decoding server\'s response and challenge response')
        server_challenge_hex = pairing_challenge_result.find('challengeresponse').text
        server_challenge_bytes = bytearray.fromhex(server_challenge_hex)
        server_challenge_decrypted = aes_cypher.decrypt(server_challenge_bytes)
        
        server_challenge_firstbytes = server_challenge_decrypted[:hashAlgorithm.digest_size()]
        server_challenge_lastbytes  = server_challenge_decrypted[hashAlgorithm.digest_size():hashAlgorithm.digest_size()+16]

        # Using another 16 bytes secret, compute a challenge response hash using the secret, our cert sig, and the challenge
        client_secret               = randomBytes(16)
        challenge_response          = server_challenge_lastbytes + certificate_signature + client_secret
        challenge_response_hashed   = hashAlgorithm.hash(challenge_response)
        challenge_response_encrypted= aes_cypher.encryptToHex(challenge_response_hashed)
        
        # Send the challenge response to the server
        log_debug('Sending the challenge response to the server')
        pairing_secret_response = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'serverchallengeresp': challenge_response_encrypted })
        
        if pairing_secret_response is None:
            log_error('Failed to pair with server. No XML received.')
            return False

        isPaired = pairing_secret_response.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False
        
        # Get the server's signed secret
        log_debug('Verifiying server signature')
        server_secret_response  = bytearray.fromhex(pairing_secret_response.find('pairingsecret').text)
        server_secret           = server_secret_response[:16]
        server_signature        = server_secret_response[16:272]
        
        server_cert = server_cert_data.decode('hex')
        is_verified = verify_signature(str(server_secret), server_signature, server_cert)

        if not is_verified:
            # Looks like a MITM, Cancel the pairing process
            log_error('Failed to verify signature. (MITM warning)')
            self._perform_server_request('unpair', False)
            return False

        # Ensure the server challenge matched what we expected (aka the PIN was correct)
        log_debug('Confirming PIN with entered value')
        server_cert_signature       = getCertificateSignature(server_cert)
        server_secret_combination   = challenge + server_cert_signature + server_secret
        server_secret_hashed        = hashAlgorithm.hash(server_secret_combination)
        
        if server_secret_hashed != server_challenge_firstbytes:
            # Probably got the wrong PIN
            log_error("Wrong PIN entered")
            self._perform_server_request('unpair', False)
            return False

        log_debug('Pin is confirmed')

        # Send the server our signed secret
        log_debug('Sending server our signed secret')
        signed_client_secret = sign_data(client_secret, client_key_certificate)
        client_pairing_secret = client_secret + signed_client_secret

        client_pairing_secret_response = self._perform_server_request('pair', False, {
            'devicename': 'ael', 
            'updateState': 1, 
            'clientpairingsecret':  binascii.hexlify(client_pairing_secret)})
        
        isPaired = client_pairing_secret_response.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False
        
        # Do the initial challenge over https
        log_debug('Initial challenge again')
        pair_challenge_response = self._perform_server_request('pair', True, {
            'devicename': 'ael', 
            'updateState': 1, 
            'phrase':  'pairchallenge'})
        
        isPaired = pair_challenge_response.find('paired').text
        if isPaired != '1':
            log_error('Failed to pair with server. Server returned failed state.')
            self._perform_server_request('unpair', False)
            return False

        return True

    def getApps(self):
        
        apps_response = self._perform_server_request('applist', True)
        appnodes = apps_response.findall('App')
        
        apps = []
        for appnode in appnodes:
            
            app = {}
            for appnode_attr in appnode:
                if len(list(appnode_attr)) > 1:
                    continue
                
                xml_text = appnode_attr.text if appnode_attr.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = appnode_attr.tag
           
                app[xml_tag] = xml_text

            apps.append(app)

        return apps


    def getCertificateBytes(self):
        from utils_cryptography import *
        
        if self.pem_cert_data:
            return self.pem_cert_data

        if not self.certificate_file_path.exists():
            log_info('Client certificate file does not exist. Creating')
            create_self_signed_cert("NVIDIA GameStream Client", self.certificate_file_path, self.certificate_key_file_path)

        log_info('Loading client certificate data from {0}'.format(self.certificate_file_path.getOriginalPath()))
        self.pem_cert_data = self.certificate_file_path.readAll()

        return self.pem_cert_data
    
    def getCertificateKeyBytes(self):
        from utils_cryptography import *
        
        if self.key_cert_data:
            return self.key_cert_data

        if not self.certificate_key_file_path.exists():
            log_info('Client certificate file does not exist. Creating')
            create_self_signed_cert("NVIDIA GameStream Client", self.certificate_file_path, self.certificate_key_file_path)
        
        log_info('Loading client certificate data from {0}'.format(self.certificate_key_file_path.getOriginalPath()))
        self.key_cert_data = self.certificate_key_file_path.readAll()
        
        return self.key_cert_data
    
    def copy_certificates(self, certificates_source_path):

        certificate_source_files = certificates_source_path.scanFilesInPathAsFileNameObjects('*.crt')
        key_source_files = certificates_source_path.scanFilesInPathAsFileNameObjects('*.key')

        if len(certificate_source_files) < 1:
            return False

        if not self.certificates_path.exists():
            self.certificates_path.makedirs()
        
        certificate_source_files[0].copy(self.certificate_file_path)
        key_source_files[0].copy(self.certificate_key_file_path)

        return True

    @staticmethod
    def try_to_resolve_path_to_nvidia_certificates():

        home = expanduser("~")
        homePath = FileNameFactory.create(home)

        possiblePath = homePath.pjoin('Moonlight/')         
        if possiblePath.exists():
            return possiblePath.getOriginalPath()

        possiblePath = homePath.pjoin('Limelight/')        
        if possiblePath.exists():
            return possiblePath.getOriginalPath()
         
        return homePath.getOriginalPath()
