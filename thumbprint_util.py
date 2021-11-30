import hashlib
import ssl
import subprocess
import re


class Encryption(str, Enum):
    SHA1 = "sha1"
    SHA256 = "sha256"
    MD5 = "md5"


def get_thumbprint_cmd(hostname, port=443, algorithm: Encryption = Encryption.SHA256):
	"""
	Returns SSL thumbprint for specified host using openssl cmd

	:param hostname: FQDN or IP of the host
	:param port: port number of the host. Default is 443
	:param algorithm: Hashing algorithm. Default is sha256
	"""
	try:
		cmd = "openssl s_client -connect %s:%s < /dev/null 2>/dev/null | openssl x509 -fingerprint -noout -%s -in /dev/stdin" % (hostname, port, algorithm)
		output = subprocess.check_output(['/bin/sh', '-c', cmd])
		thumbprint = output.decode().strip()
		return thumbprint
	except subprocess.CalledProcessError as err:
		raise err
	except Exception as e:
		raise e


def get_pem_cert(address, port=443):
	"""
	Returns certificate for specified host in pem format

	:param adddress: FQDN or IP of the host
	:param port: port number of the host. Default is 443
	"""
    try:
        cert = ssl.get_server_certificate((address, port))
    except Exception as ex:
        raise Exception(f"Failed to connect to address: {address}. Exception: {ex}")
    return cert


def get_thumbprint(hostname, port=443, algorithm: Encryption = Encryption.SHA256):
	"""
	Returns SSL thumbprint for specified host

	:param hostname: FQDN or IP of the host
	:param port: port number of the host. Default is 443
	:param algorithm: Hashing algorithm. Default is sha256
	"""
	cert = get_pem_cert(address, port)
	der_cert_bin = ssl.PEM_cert_to_DER_cert(cert)

    if encryption == Encryption.SHA1:
        thumbprint = hashlib.sha1(der_cert_bin).hexdigest()
    elif encryption == Encryption.SHA256:
        thumbprint = hashlib.sha256(der_cert_bin).hexdigest()
    elif encryption == Encryption.MD5:
        thumbprint = hashlib.md5(der_cert_bin).hexdigest()
    else:
        return der_cert_bin
    return thumbprint


def format_thumbprint(thumbprint):
	"""
	Returns SSL thumbprint without colon seperators

	:param thumbprint: thumbrpint string of the format "SHAx thumbprint=y"
	"""
	thumbprint_string = thumbprint.split("=")[1]
	return re.sub(":", "", thumbprint_string).lower()
