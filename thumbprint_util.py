import subprocess
import re


def get_thumbprint(hostname, port=443, algorithm="sha256"):
	"""
	Returns SSL thumbprint for specified host

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


def format_thumbprint(thumbprint):
	"""
	Returns SSL thumbprint without colon seperators

	:param thumbprint: thumbrpint string of the format "SHAx thumbprint=y"
	"""
	thumbprint_string = thumbprint.split("=")[1]
	return re.sub(":", "", thumbprint_string).lower()
