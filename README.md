# Ethereum Interfaces

This repository contains information about / specifications of interfaces between
different components of the Ethereum ecosystem and tests for those specifications.

This includes (but is not limited to):

 - the ABI
 - the RPC specification
 - the EVM-C interface

# Deps
pip2 install -r requirements.txt
# Standalone Mode
the test script directly connect to a node
## Start Node
this step can be left out if just connect to a existing testnet
### start with docker
to be continued...

# Hive Simulator Mode
refer to hive project which is triangle-arch. 
for taraxa-node, this is to be continued...

# Config
edit rpc-specs-tests/taraxa_config.py
```
NODE='' # a eth compat node you wanna test with, http(s) endpoint
TEST_NAMES='' # names of the tests, a subset of json filenames under test directory 
```

# Run

```
-> cd rpc-specs-tests
-> python2 taraxa_test_rpc_methods.py | tee test_rpc_methods.log
-> cat summary_rpc_method.json
```
