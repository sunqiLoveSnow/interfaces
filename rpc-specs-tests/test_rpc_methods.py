import json
from jq import jq
import os
import sys
import jsonschema
import requests


#fixResolver from https://github.com/Julian/jsonschema/issues/313#issuecomment-269361225
class fixResolver(jsonschema.RefResolver):
    def __init__( self, schema, schemaAbs ):
      jsonschema.RefResolver.__init__( self,
                                       base_uri = schemaAbs,
                                       referrer = None )
      self.store[ schemaAbs ] = schema




class MockReporter:

    def __init__(self):
        return

    def subresult(self, name, success, errormsg, details = None):
        print("mock reporter subresult:", name, success, errormsg)
        return




def run_test(test_name, session, rpc_url, reporter):
    print("\nrunning tests for method: {}".format(test_name))
    test_filename = 'tests/' + test_name
    if os.path.isfile(test_filename) is False:
        print("ERROR: couldn't load test file: {}".format(test_filename))
        raise Exception("ERROR: couldn't load tests file:", test_filename)
    with open(test_filename) as test_data:
      test_spec = json.load(test_data)

    # chainConfig is not yet active (all current test cases use the same chainConfig)
    #chain_config_file = test_spec['chainConfig']['$ref']

    schema_file = test_spec['schema']['$ref']

    with open('tests/' + schema_file) as schema_data:
      rpc_method_schema = json.load(schema_data)

    for test_case in test_spec['tests']:
        print("running test: {}".format(test_case['title']))
        schemaAbs = 'file://' + os.path.abspath('schemas/' + test_name)
        request_method = test_case['request']['method']
        request_params = test_case['request']['params']
        request_payload = { 'jsonrpc':'2.0',
                            'method':request_method,
                            'params':request_params,
                            'id':1 }

        expected_response = test_case['expectedResponse']

        # test_case['request'] and test_case['expectedResponse'] are validated
        # against the schemas in validate_tests.py

        try:
            print("sending rpc request: {}".format(request_payload))
            received_response = session.post(rpc_url, json=request_payload, timeout=10)
            received_response_json = received_response.json()
            print("recieved_response: {}".format(received_response_json))
            reporter.subresult(test_case['title'] + ' rpc request got response.', True, None, None)
        except Exception as e:
            err_msg = "ERROR. json-rpc request failed: " + str(e)
            print(err_msg)
            details = {
                'rpc_request': test_case['request'],
                'response_schema': rpc_method_schema['response']
            }
            reporter.subresult(test_case['title'], False, err_msg, details)
            received_response_json = {}
            #continue

        # got response, now validate response against schema
        try:
            jsonschema.validate(received_response_json,
                                rpc_method_schema['response'],
                                resolver=fixResolver(rpc_method_schema['response'], schemaAbs))
            print("rpc response schema validated.")
            reporter.subresult(test_case['title'] + '. rpc received response schema valid', True, None, None)
        except Exception as e:
            err_msg = "ERROR. couldn't validate rpc received response against schema."
            print(err_msg)
            print("exception: {}".format(str(e)))
            details = {
                'schemaException': str(e),
                'received_response': received_response_json,
                'response_schema': rpc_method_schema['response']
            }
            reporter.subresult(test_case['title'] + '. rpc received response schema valid', False, err_msg, details)

        # check received response against expected response, using jq assertions
        # jq comparators work on a single json object, so construct one
        assert_dict = { 'receivedResponse': received_response_json,
                        'expectedResponse': expected_response }
        details = assert_dict
        for assertion in test_case['asserts']:
            assertion_result = jq(assertion['program']).transform(assert_dict)
            details['assertion_program'] = assertion['program']
            print("{} : {}".format(assertion['description'], assertion_result))
            if assertion_result == True:
                reporter.subresult(test_case['title'] + '. ' + assertion['description'] + '.', True, None, None)
            else:
                assert_dict['requestObject'] = test_case['request']
                reporter.subresult(test_case['title'] + '. ' + assertion['description'] + '.', False, "assertion failed: " + assertion['program'], assert_dict)





def main(args):
    client_rpc_url = "http://127.0.0.1:8545"
    sesh = requests.Session()

    mock_reporter = MockReporter()

    for test_name in TEST_NAMES:
        run_test(test_name, sesh, client_rpc_url, mock_reporter)

    print("all tests done.")



if __name__ == '__main__':
    main(sys.argv[1:])
