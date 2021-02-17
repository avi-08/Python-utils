import argparse
import requests
import time
import json
from pprint import pprint


NIMBUS_API_BASE_URL = 'http://nimbus-api.eng.vmware.com/api'
EXECUTE_NIMBUS_COMMAND = '/v1/launcher/nimbus/ctl'
GET_COMMAND_EXECUTION_STATUS = '/v1/launcher/nimbus/{0}/status'


class NimbusLeaseExtend:

    def __init__(self):
        pass

    @staticmethod
    def _execute_nimbus_command(payload):
        try:
            api_url = NIMBUS_API_BASE_URL + EXECUTE_NIMBUS_COMMAND
            print(f'Method: POST API: {api_url} Payload: {payload}')
            r = requests.post(api_url, data=json.dumps(payload))
            if r.status_code == requests.codes.ok:
                return r.json()
            else:
                print(f'Execute command failed. \n Status code: {r.status_code} \n Response: {r.text}')
        except Exception as e:
            print("Failed to execute command." + e.with_traceback())

    @staticmethod
    def _get_command_execution_status(task_id):
        try:
            api_url = NIMBUS_API_BASE_URL + GET_COMMAND_EXECUTION_STATUS.format(task_id)
            print(f'Method: GET API: {api_url}')
            r = requests.get(api_url)
            if r.status_code == requests.codes.ok:
                return r.json()
            else:
                print(f'Get command status failed. \n Status code: {r.status_code} \n Response: {r.text}')
        except Exception as e:
            print("Failed to execute command." + e)

    def _get_testbeds(self, params):
        payload = {
            "user": params.user,
            "args": ["--testbed", "list"],
            "opts": {
                "nimbusLocation": params.location
            }
        }
        return self._execute_nimbus_command(payload=payload)['id']

    def _extend_lease(self, params, testbed_name):
        payload = {
            "user": params.user,
            "args": ["--testbed", "extend_lease", testbed_name],
            "opts": {
                "lease": 7,
                "nimbusLocation": params.location
            }
        }
        return self._execute_nimbus_command(payload=payload)['id']

    def _poll_task(self, task_id, timeout=120, interval=10):
        retry_count = timeout // interval
        while retry_count > 0:
            res = self._get_command_execution_status(task_id)
            status = res['status'].upper()
            if status == "SUCCEEDED":
                print(f'Task status is {status}')
                return res
            if status == "FAILED":
                print(f'Task status is {status}')
                return None
            else:
                print(f'Current task status is {status}, polling task status in {interval} seconds')
            time.sleep(interval)
            retry_count = retry_count - 1
        print("Poll Nimbus task timed out after %s seconds" % timeout)
        return None

    def nimbus_lease_extend_workflow(self, params):
        if params.testbed_name:
            print(f'Extending lease of specified testbed [{params.testbed_name}] ...')
            task_id = self._extend_lease(args, params.testbed_name)
            response = self._poll_task(task_id)
            if response:
                print(f'Successfully extended lease for testbed [{params.testbed_name}]')
        else:
            print('Getting available testbeds...')
            task_id = self._get_testbeds(params)
            response = self._poll_task(task_id)
            if response:
                pods_list = response['result']
                pprint(pods_list)
                for _, v in pods_list.items():
                    for testbed in v.values():
                        print(f'Extending lease of testbed [{testbed["name"]}] ...')
                        task_id = self._extend_lease(args, testbed["name"])
                        response = self._poll_task(task_id)
                        if response:
                            print(f'Successfully extended lease for testbed [{testbed["name"]}]')
        print('*************** Finished *************')


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Nimbus lease extender")
    parser.add_argument('-u', '--user', required=True, help='Provide your VMware username for extending testbed lease.')
    parser.add_argument('-l', '--location', required=True, choices=['sc', 'wdc'], help='Nimbus site where testbeds'
                                                                                       ' are deployed.')
    parser.add_argument('-t', '--testbed-name', required=False,
                        help='Specify testbed name to extend lease of. If not specified, '
                             'lease will be extended for all available testbeds.')

    args = parser.parse_args()

    lease_extender = NimbusLeaseExtend()
    lease_extender.nimbus_lease_extend_workflow(args)
