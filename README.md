![](./Logo.png)
## Introduction
This is my solution for the Bell-Labs Coding Challenge. The solution has been declared correct by the members of the Bell Labs team.
<br>
This software connects to any [Ethereum](https://www.ethereum.org) node and allows you to interact with the blockchain.
The main functionality is to create massive transactions and send them to the blockchain, then, obtain the validation time benchmarks.
<br>
## Prerequisites
- [Ethereum Node](https://www.ethereum.org)
- [Go Ethereum Console](https://geth.ethereum.org/)
- [Python 3.6+](https://www.python.org/downloads/)
- [Web3.py](https://web3py.readthedocs.io/en/stable/)

## Configuration
To launch the program, you need to fill the Configuration file with the correct information.
```ini
[BASIC_INFORMATION]
MAIN_WALLET = EXAMPLE_ADDRESS
KEY = EXAMPLE_KEY

[NODE_INFORMATION]
IPC_PATH = /Your/Local/Node/Path/Geth.ipc
HTTP_PROVIDER = YourHttpProvider
WEB_SOCKET = YourWebSocketProvider
```
Note that for the Node Information section, you can choose between the:
- IPC_PATH
- HTTP_PROVIDER
- WEB_SOCKET

## Usage
To use the program, you need to run the following command:
```shell
python3 Main.py -n NumberOfSenders -r Addr1,Addr2,... -t TransactionsPerSecond -s TransactionBytesSize
```
- n: Number of wallets from which the transactions will be sent.
- r: List of receivers addresses, separated by commas without spaces.
- t: Number of transactions to be sent every second.
- s: Size in bytes of the transactions.

## Results
The program runs on an infinite loop, when the users interrupt the main process, the program will stop.
The results are going to be found inside the "Benchmark_*.txt" file.