# Ethereum Interfaces

This repository contains information about / specifications of interfaces between
different components of the Ethereum ecosystem and tests for those specifications.

This includes (but is not limited to):

 - the ABI
 - the RPC specification
 - the EVM-C interface

# Deps
pip2 install -r requirements.txt
# Start Node
this step can be left out if just connect to a public net
## start with docker
to be continued...
# Config
edit rpc-specs-tests/taraxa_config.py
```
NODE='' # a eth compat node
TEST_NAMES='' # name of the tests 
```

# Run

```
-> cd rpc-specs-tests
-> python2 taraxa_validate_tests.py | tee validate.log
-> python2 taraxa_test_rpc_methods.py | tee test_rpc_methods.log
```
