import argparse
import re
import json
import os


SPEC_DIR = '/tmp/specs'
BRINGUP_SPEC_PREFIX = 'bringup'
ADD_HOST_SPEC_PREFIX = 'add-host'
REMOVE_HOST_SPEC_PREFIX = 'remove-host'
ADD_CLUSTER_SPEC_PREFIX = 'add-cluster'
REMOVE_CLUSTER_SPEC_PREFIX = 'remove-cluster'
ESX_IP_START = 4


def generate_bringup_spec(ip_start, esx_count = 3):
	"""
	Return bringup spec file path
	:param ip_start: ESXi IP start value. eg if ip_start=4 and esx_count=3, then esxi IPs will be x.x.x.4, x.x.x.5 and x.x.x.6
	:param esx_count: Number of ESXi hosts for bringup operation
	"""
	spec_path = os.path.join(SPEC_DIR, BRINGUP_SPEC_PREFIX + '-%s-host.json' % esx_count)
	try:
		with open 
	except IOError as err:
		raise err
	except Exception as e:
		raise e
	return spec_path


def generate_add_host_spec(ip_start, esx_count = 3):
	"""
	Return add-host spec file path
	:param ip_start: ESXi IP start value. eg if ip_start=4 and esx_count=3, then esxi IPs will be x.x.x.4, x.x.x.5 and x.x.x.6
	:param esx_count: Number of ESXi hosts for add-host operation
	"""


def generate_remove_host_spec():
	pass


def generate_add_cluster_spec():
	pass


def generate_remove_cluster_spec():
	pass


def generate_spec(args):
	"""
	Returns dictionary of spec file paths
	:param args: command-line args from main
	"""
	spec = dict()
	spec["bringup_spec"] = generate_bringup_spec(ip_start=ESX_IP_START, esx_count=args.bringup_host_count)
	if args.add_host:
		spec["add_host_spec"] = generate_add_host_spec(ip_start=ESX_IP_START + args.bringup_host_count, esx_count=args.add_host_count)
	elif args.remove_host:
		spec["remove_host_spec"] = generate_remove_host_spec()
	elif args.add_cluster:
		spec["add_cluster_spec"] = generate_add_cluster_spec()
	elif args.remove_cluster:
		spec["remove_cluster_spec"] = generate_remove_cluster_spec()
	return spec


if __name__ == '__main__':
	parser = argparse.ArgumentParser("Spec util")
	parser.add()
	parser.add_argument('-n', '--bringup-host-count', action='store', default=3, help="Number of ESXi hosts to generate the bringup spec for. Default is 3 hosts")
	parser.add_argument('-N', '--add-host-count', action='store', default=3, help="Number of ESXi hosts to generate the add-host spec for. Default is 3 hosts")
	parser.add_argument('-a', '--add-host', action='store_true', default=False, help="Generate add-host spec")
	parser.add_argument('-r', '--remove-host', action='store_true', default=False, help="Generate remove-cluster spec")
	parser.add_argument('-A', '--add-cluster', action='store_true', default=False, help="Generate add-cluster spec")
	parser.add_argument('-R', '--remove-cluster', action='store_true', default=False, help="Generate remove-cluster spec")
	args = parser.parse_args()

	generate_spec(args)
