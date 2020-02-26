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
        self.test_results = []
        return

    def subresult(self, name, success, errormsg, details = None):
        self.test_results.append(success)
        if not success:
            print("FAIL-------------------------------")
        else:
            print("SUCCESS-------------------------------")
        print("mock reporter subresult: {} {} {}".format(name, success, errormsg))
        return




def run_test(test_name, session, rpc_url, reporter):
    print("\nvalidating tests for method: {}".format(test_name))
    #test_filename = 'tests/' + test_name + '.json'
    test_filename = 'tests/' + test_name
    if os.path.isfile(test_filename) is False:
        print("ERROR: couldn't load test file:", test_filename)
        raise Exception("ERROR: couldn't load tests file:", test_filename)
    else:
        print("loaded test file: {}".format(test_filename))
    with open(test_filename) as test_data:
      print("read test_data: {}".format(test_data))
      test_spec = json.load(test_data)

    #chain_config_file = test_spec['chainConfig']['$ref']
    schema_file = test_spec['schema']['$ref']

    with open('tests/' + schema_file) as schema_data:
      rpc_method_schema = json.load(schema_data)
    #print("got rpc_method_schema['response']:", rpc_method_schema['response'])

    for test_case in test_spec['tests']:
        print("running test: {}".format(test_case['title']))
        schemaAbs = 'file://' + os.path.abspath('schemas/' + test_name)
        request_method = test_case['request']['method']
        request_params = test_case['request']['params']
        request_payload = { 'jsonrpc':'2.0',
                            'method':request_method,
                            'params':request_params,
                            'id':1 }
        if 'shouldFailSchema' not in test_case['request']:
            test_case['request']['shouldFailSchema'] = False
        try:
            jsonschema.validate(request_payload,
                                rpc_method_schema['request'],
                                resolver=fixResolver(rpc_method_schema['request'], schemaAbs))
            requestSchemaIsValid = True
        except Exception as e:
            requestSchemaIsValid = False
            requestSchemaError = str(e)

        if (
                (requestSchemaIsValid is True and
                test_case['request']['shouldFailSchema'] is False)
            or
                (requestSchemaIsValid is False and
                test_case['request']['shouldFailSchema'] is True)
            ):
            print("rpc request schema validated.")
            reporter.subresult(test_case['title'] + '. rpc request schema valid', True, None, None)
        else:
            err_msg = "ERROR. couldn't validate rpc request object against schema."
            print(err_msg)
            print("exception:", requestSchemaError)
            details = {
                'schemaException': requestSchemaError,
                'request_object': request_payload,
                'request_schema': rpc_method_schema['request']
            }
            reporter.subresult(test_case['title'] + '. rpc request schema valid', False, err_msg, requestSchemaError)

        expected_response = test_case['expectedResponse']
        expected_response['jsonrpc'] = "2.0"
        expected_response['id'] = 1
        try:
            jsonschema.validate(expected_response,
                                rpc_method_schema['response'],
                                resolver=fixResolver(rpc_method_schema['response'], schemaAbs))
            print("rpc expected response schema validated.")
            reporter.subresult(test_case['title'] + '. rpc expected response schema valid', True, None, None)
        except Exception as e:
            err_msg = "ERROR. couldn't validate expected rpc response against schema."
            print(err_msg)
            print("exception:", str(e))
            details = {
                'schemaException': str(e),
                'expected_response': expected_response,
                'response_schema': rpc_method_schema['response']
            }
            reporter.subresult(test_case['title'] + '. rpc expected response schema valid', False, err_msg, details)


        # jq comparators work on a single json object, so construct one
        assert_dict = { 'receivedResponse': expected_response,
                        'expectedResponse': expected_response }
        details = assert_dict
        for assertion in test_case['asserts']:
            assertion_result = jq(assertion['program']).transform(assert_dict)
            details['assertion_program'] = assertion['program']
            print("{} : {}".format(assertion['description'], assertion_result))
            if assertion_result == True:
                reporter.subresult(test_case['title'] + '. ' + assertion['description'] + '.', True, None, None)
            else:
                reporter.subresult(test_case['title'] + '. ' + assertion['description'] + '.', False, "assertion failed: " + assertion['program'], assert_dict)





def main():
    import taraxa_config as c
    # client_rpc_url = "http://127.0.0.1:8545"
    client_rpc_url = c.NODE
    print("connecting " + c.NODE)
    sesh = requests.Session()

    mock_reporter = MockReporter()

    # test_files = os.listdir("./tests")

    for test_name in c.TEST_NAMES:
        run_test(test_name, sesh, client_rpc_url, mock_reporter)

    print("ran all test cases against the schemas.")
    if False in mock_reporter.test_results:
        print("ERROR! A problematic test case didn't validate against the schemas!")
        sys.exit(1)
    else:
        print("All test cases valided.")
        #sys.exit(0)


def validate_tests():
    main()


if __name__ == '__main__':
    main()
