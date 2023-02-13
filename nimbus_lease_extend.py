import argparse
import os.path
import logging

import requests
import json
from pprint import pformat
from retry import retry
from threading import Thread, Lock


NIMBUS_API_BASE_URL = 'http://nimbus-api.eng.vmware.com/api'
EXECUTE_NIMBUS_COMMAND = '/v1/launcher/nimbus/ctl'
GET_COMMAND_EXECUTION_STATUS = '/v1/launcher/nimbus/{0}/status'
OUT_DIR = 'out'
SUCCESS_FILE = 'success.txt'
FAILURE_FILE = 'failure.txt'
DELAY = 20
TIMEOUT = 120
RETRY_COUNT = TIMEOUT // DELAY


class NimbusLeaseExtend:
    def __init__(self):
        self.success_messages = []
        self.failure_messages = []
        self.lock = Lock()

    @staticmethod
    def execute_nimbus_command(payload):
        try:
            api_url = NIMBUS_API_BASE_URL + EXECUTE_NIMBUS_COMMAND
            logging.debug(f'Method: POST API: {api_url} Payload: {payload}')
            r = requests.post(api_url, data=json.dumps(payload))
            if r.status_code == requests.codes.ok:
                return r.json()
            else:
                message = f'Execute command failed. \n Status code: {r.status_code} \n Response: {r.text}'
                logging.error(message)
                raise IOError(message)
        except Exception as ex:
            message = f"Failed to execute command.\nError: {ex}"
            logging.error(message)
            raise IOError(message)

    @staticmethod
    def get_command_execution_status(task_id):
        try:
            api_url = NIMBUS_API_BASE_URL + GET_COMMAND_EXECUTION_STATUS.format(task_id)
            logging.debug(f'Method: GET API: {api_url}')
            r = requests.get(api_url)
            if r.status_code == requests.codes.ok:
                return r.json()
            else:
                logging.error(f'Get command status failed. \n Status code: {r.status_code} \n Response: {r.text}')
        except Exception as e:
            logging.error("Failed to execute command." + e)
    
    @staticmethod
    def dump_to_file(file_path, contents, append=False):
        mode = 'a' if append else 'w'
        try:
            with open(file_path, mode) as fout:
                fout.write(contents)
        except IOError as ex:
            logging.error(f"Failed to write to file: {file_path};\nError: {ex}")
            return
        logging.info(f"Updated {file_path} successfully.")
    
    @staticmethod    
    def dump_success(message, append=False):
        file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), OUT_DIR, SUCCESS_FILE)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        logging.debug(f"Success file path: {file_path}")
        NimbusLeaseExtend.dump_to_file(file_path, message, append)
    
    @staticmethod
    def dump_failure(message, append=False):
        file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), OUT_DIR, FAILURE_FILE)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        logging.debug(f"Failure file path: {file_path}")
        NimbusLeaseExtend.dump_to_file(file_path, message, append)

    @staticmethod
    def get_location(params, testbed=True):
        if not testbed and params.vm_location:
            return params.vm_location
        if testbed and params.testbed_location:
            return params.testbed_location
        return params.location

    def _get_testbeds(self, params):
        payload = {
            "user": params.user,
            "args": ["--testbed", "list"],
            "opts": {
                "nimbusLocation": NimbusLeaseExtend.get_location(params)
            }
        }
        return self.execute_nimbus_command(payload=payload)['id']

    def _get_vms(self, params):
        payload = {
            "user": params.user,
            "args": ["list"],
            "opts": {
                "nimbusLocation": NimbusLeaseExtend.get_location(params, False)
            }
        }
        return self.execute_nimbus_command(payload=payload)['id']

    def _extend_testbed_lease(self, params, testbed_name):
        payload = {
            "user": params.user,
            "args": ["--testbed", "extend_lease", testbed_name],
            "opts": {
                "lease": 7,
                "nimbusLocation": params.location
            }
        }
        return self.execute_nimbus_command(payload=payload)['id']

    def _extend_vm_lease(self, params, vm_name):
        payload = {
            "user": params.user,
            "args": ["extend_lease", vm_name],
            "opts": {
                "lease": 7,
                "nimbusLocation": params.location
            }
        }
        return self.execute_nimbus_command(payload=payload)['id']

    @retry(ValueError, delay=DELAY, tries=RETRY_COUNT)
    def _poll_task(self, task_id):
        res = self.get_command_execution_status(task_id)
        status = res['status'].upper()
        if status == "SUCCEEDED":
            logging.debug(f'Task status is {status}')
            return res
        if status == "FAILED":
            logging.debug(f'Task status is {status}')
            return None
        else:
            raise ValueError(f'Current task status is {status}, polling task status in {DELAY} seconds')
    
    def get_testbed_names(self, params):
        if params.testbed_name:
            return [params.testbed_name]
        else:
            logging.info('Getting available testbeds')
            task_id = self._get_testbeds(params)
            response = self._poll_task(task_id)
            testbeds = []
            if response:
                pods_map = response['result']
                logging.debug(pformat(pods_map))
                for _, v in pods_map.items():
                    for testbed in v.values():
                        testbeds.append(testbed["name"])
            return testbeds

    def get_vm_names(self, params):
        if params.vm_name:
            return [params.vm_name]
        else:
            logging.info('Getting available VMs')
            task_id = self._get_vms(params)
            response = self._poll_task(task_id)
            vms = []
            if response:
                pods_map = response['result']
                logging.debug(pformat(pods_map))
                for _, v in pods_map.items():
                    for vm_name in v.keys():
                        vms.append(vm_name)
            return vms

    def testbed_workflow(self, params):
        try:
            testbed_names = self.get_testbed_names(params)
            for index, testbed in enumerate(testbed_names):
                logging.info(f'Extending lease of testbed [{testbed}] ...')
                if not params.dry_run:
                    task_id = self._extend_testbed_lease(args, testbed)
                    response = self._poll_task(task_id)
                    if response:
                        logging.info(f'Successfully extended lease for testbed [{testbed}]')
            if len(testbed_names) > 0:
                success_message = f"Successfully extended lease for testbeds: {testbed_names}"
            else:
                success_message = "No testbeds found for extending lease."
            # NimbusLeaseExtend.dump_success(success_message)
            logging.info(success_message)
            with self.lock:
                self.success_messages.append(success_message)
            logging.info('*************** Finished Testbed Workflow *************')
        except Exception as ex:
            failure_message = f"Failed to extend lease for testbeds: {testbed_names[index:]}\n{ex}"
            logging.error(failure_message)
            with self.lock:
                self.failure_messages.append(failure_message)
            # NimbusLeaseExtend.dump_failure(
            #     f"Failed to extend testbed lease for testbeds: {testbed_names[index:]}\n{ex}")

    def vm_workflow(self, params):
        try:
            vm_names = self.get_vm_names(params)
            for index, vm in enumerate(vm_names):
                logging.info(f'Extending lease of VM [{vm}] ...')
                if not params.dry_run:
                    task_id = self._extend_vm_lease(args, vm)
                    response = self._poll_task(task_id)
                    if response:
                        logging.info(f'Successfully extended lease for VM [{vm}]')
            if len(vm_names) > 0:
                success_message = f"Successfully extended lease for VMs: {vm_names}"
            else:
                success_message = "No VMs found for extending lease."

            logging.info(success_message)
            with self.lock:
                self.success_messages.append(success_message)
            logging.info('*************** Finished VM Workflow *************')
        except Exception as ex:
            failure_message = f"Failed to extend lease for VMs: {vm_names[index:]}\n{ex}"
            logging.error(failure_message)
            with self.lock:
                self.failure_messages.append(failure_message)
    
    def nimbus_lease_extend_workflow(self, params):
        testbed_thread = Thread(name= "testbed_workflow", target=self.testbed_workflow, args=[params])
        vm_thread = Thread(name="vm_workflow", target=self.vm_workflow, args=[params])
        testbed_thread.start()
        vm_thread.start()

        testbed_thread.join()
        vm_thread.join()

        NimbusLeaseExtend.dump_success('\n'.join(self.success_messages) if self.success_messages else "")
        NimbusLeaseExtend.dump_failure('\n'.join(self.failure_messages) if self.failure_messages else "")
        if self.failure_messages:
            raise RuntimeError(' '.join(self.failure_messages))
        logging.info('*************** Finished *************')


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Nimbus lease extender")
    parser.add_argument('-u', '--user', required=True, help='Provide your VMware username for extending testbed lease.')
    parser.add_argument('-l', '--location', required=False, choices=['sc', 'wdc'], help='Nimbus site where resources'
                                                                                       ' are deployed.')
    parser.add_argument('-t', '--testbed-name', required=False,
                        help='Specify testbed name to extend lease of. If not specified, '
                             'lease will be extended for all available testbeds.')
    parser.add_argument('-tl', '--testbed-location', required=False, choices=['sc', 'wdc'],
                        help='Nimbus site where testbeds'
                             ' are deployed. Overrides global --location flag for testbeds')
    parser.add_argument('-vm', '--vm-name', required=False,
                        help='Specify VM name to extend lease of. If not specified, '
                             'lease will be extended for all available VMs.')
    parser.add_argument('-vl', '--vm-location', required=False, choices=['sc', 'wdc'],
                        help='Nimbus site where VMs'
                             ' are deployed. Overrides global --location flag for VMs')
    parser.add_argument('-d', '--dry-run', required=False, action="store_true",
                        help='Dry run the command. This does not calls the lease extend APIs')

    args = parser.parse_args()
    if not args.location and not all([args.vm_location, args.testbed_location]):
        parser.error("Either specify --location or both --vm-location and --testbed-location")
    logging.basicConfig(format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARN)
    logging.getLogger("retry.api").setLevel(logging.WARN)

    lease_extender = NimbusLeaseExtend()
    lease_extender.nimbus_lease_extend_workflow(args)
