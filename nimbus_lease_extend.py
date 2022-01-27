import argparse
import requests
import json
from pprint import pprint
from retry import retry


NIMBUS_API_BASE_URL = 'http://nimbus-api.eng.vmware.com/api'
EXECUTE_NIMBUS_COMMAND = '/v1/launcher/nimbus/ctl'
GET_COMMAND_EXECUTION_STATUS = '/v1/launcher/nimbus/{0}/status'
DELAY = 15
TIMEOUT = 120
RETRY_COUNT = TIMEOUT // DELAY


class NimbusLeaseExtend:
    @staticmethod
    def execute_nimbus_command(payload):
        try:
            api_url = NIMBUS_API_BASE_URL + EXECUTE_NIMBUS_COMMAND
            print(f'Method: POST API: {api_url} Payload: {payload}')
            r = requests.post(api_url, data=json.dumps(payload))
            if r.status_code == requests.codes.ok:
                return r.json()
            else:
                message = f'Execute command failed. \n Status code: {r.status_code} \n Response: {r.text}'
                print(message)
                raise IOError(message)
        except Exception as ex:
            message = f"Failed to execute command.\nError: {ex}"
            print(message)
            raise IOError(message)

    @staticmethod
    def get_command_execution_status(task_id):
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
    
    @staticmethod
    def dump_to_file(file_path, contents):
        try:
            with open(file_path, 'w') as fout:
                fout.write(contents)
        except IOError as ex:
            print(f"Failed to write to file: {file_path};\nError: {ex}")
        print(f"Updated {file_path} succcessfully.")
    
    @staticmethod    
    def dump_success(message):
        NimbusLeaseExtend.dump_to_file('success.txt', message)
    
    @staticmethod
    def dump_failure(message):
        NimbusLeaseExtend.dump_to_file('failure.txt', message)

    def _get_testbeds(self, params):
        payload = {
            "user": params.user,
            "args": ["--testbed", "list"],
            "opts": {
                "nimbusLocation": params.location
            }
        }
        return self.execute_nimbus_command(payload=payload)['id']

    def _extend_lease(self, params, testbed_name):
        payload = {
            "user": params.user,
            "args": ["--testbed", "extend_lease", testbed_name],
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
            print(f'Task status is {status}')
            return res
        if status == "FAILED":
            print(f'Task status is {status}')
            return None
        else:
            raise ValueError(f'Current task status is {status}, polling task status in 15 seconds')
    
    def get_testbed_names(self, params):
        if params.testbed_name:
            return [params.testbed_name]
        else:
            print('Getting available testbeds...')
            task_id = self._get_testbeds(params)
            response = self._poll_task(task_id)
            testbeds = []
            if response:
                pods_list = response['result']
                pprint(pods_list)
                for _, v in pods_list.items():
                    for testbed in v.values():
                        testbeds.append(testbed["name"])
            return testbeds
    
    def nimbus_lease_extend_workflow(self, params):
        try:
            testbed_names = self.get_testbed_names(params)
            for index, testbed in enumerate(testbed_names):
                print(f'Extending lease of testbed [{testbed}] ...')
                task_id = self._extend_lease(args, testbed)
                response = self._poll_task(task_id)
                if response:
                    print(f'Successfully extended lease for testbed [{testbed}]')
            if len(testbed_names) > 0:
                success_message = f"Successfully extended lease for testbeds: {testbed_names}"
            else:
                success_message = "No testbeds found for extending lease."
            NimbusLeaseExtend.dump_success(success_message)
            print('*************** Finished *************')
        except Exception as ex:
            NimbusLeaseExtend.dump_failure(f"Failed to extend testbed lease for testbeds: {testbed_names[index:]}\n{ex}")
            raise ex


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
