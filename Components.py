from time import time
from os import fdopen
from web3 import exceptions
from random import randbytes, choice
import threading

class Transaction():
    def __init__(self, W3, fromAdress, toAdress, size=0, data=None, value=0):
        """
        This class stores a transaction to be sent to the network.
        :param W3: Web3 instance.
        :param fromAdress: Address of the sender.
        :param toAdress: Address of the receiver.
        :param size: Size in bytes of the transaction data. Default = 0
        :param data: The data to be sent. Default = None
        :param value: The amount of ether to be sent in Ether. Default = 0
        """
        self.W3 = W3
        if self.W3.isAddress(fromAdress) and self.W3.isAddress(toAdress):
            if not self.W3.isChecksumAddress(fromAdress):
                self.fromAdress = self.W3.toChecksumAddress(fromAdress)
                print("WARNING: Sender Address is not checksummed, automatically checksummed it.")
            else:
                self.fromAdress = fromAdress
            if not self.W3.isChecksumAddress(toAdress):
                self.toAdress = self.W3.toChecksumAddress(toAdress)
                print("WARNING: Receiver Address is not checksummed, automatically checksummed it.")
            else:
                self.toAdress = toAdress
            self.size, self.value, self.data = size, value, data
            self.status = 0 # 0: Pending, 1: Success, -1: Failed
            self.hash = None
        else:
            raise ValueError("Invalid Address")

    def isReady(self):
        if self.data is None and self.size > 0:
            # If we want to send data but don't have it.
            return False
        else:
            return True

    def fillRandomData(self):
        # Create self.size random bytes.
        self.data = randbytes(self.size)

    def launch(self): # Launch the transaction and returns the final status and time.
        if self.isReady():
            try: # Sign & Send the transaction.
                t0 = time()
                # https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.send_transaction
                if self.data is None:
                    self.hash = self.W3.eth.send_transaction({
                        "from": self.fromAdress,
                        "to": self.toAdress,
                        "value": self.W3.toWei(self.value, "ether")})
                else:
                    self.hash = self.W3.eth.send_transaction({
                        "from": self.fromAdress,
                        "to": self.toAdress,
                        "value": self.W3.toWei(self.value, "ether"),
                        "data": self.data})
                tt = time() - t0
            except Exception as errorCode:
                print(errorCode)
                self.status, tt = -1, -1
            else:
                self.status = 1

            return self.status, tt

        else: # If the transactions is not ready, try to fill it and send it.
            print("WARNING: Transaction data is empty, filling with random data.")
            self.fillRandomData()
            return self.launch()

    def isVerified(self):
        # Check if the transaction is verified on the network.
        # https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.get_transaction_receipt
        if self.hash is not None:
            try:
                receipt = self.W3.eth.getTransactionReceipt(self.W3.toHex(self.hash))
            except exceptions.TransactionNotFound:
                return False
            else:
                return True
        else:
            return False

    def __int__(self): return self.status
    def __bool__(self): return self.isReady()
    def __hash__(self): return self.hash
    def __bytes__(self): return self.data
    def __len__(self): return self.size
    def __str__(self): return self.fromAdress + " --> " + self.toAdress

class TransactionPool():
    def __init__(self, W3, fromWallets, toWallets, ntransactions, passwords=False, size=0, data=None, value=0):
        self.W3 = W3
        self.fromWallets = fromWallets
        self.toWallets = toWallets
        self.ntransactions = ntransactions
        self.size, self.data, self.value = size, data, value
        self.verificationTime = None
        self.transactions = []
        self.status = 0 # 0: Pending, 1: Success, -1: Failed
        self.passwords = {} if not passwords else passwords # This is a dictionary of passwords for all the wallets.
        # If a password is not found, the wallet should be unlocked previously.

    def initializeTransactions(self, fillRandomData=False):
        for _ in range(self.ntransactions):
            # Create a transaction from a random wallet.
            fromWallet = choice(self.fromWallets)
            toWallet = choice(self.toWallets)
            transaction = Transaction(self.W3, fromWallet, toWallet, # The wallets are chosen randomly.
                                      self.size, self.data, self.value) # This data is the same for all transactions.
            if fillRandomData:
                transaction.fillRandomData()
            self.transactions.append(transaction)

    def launch(self, walletsLocks, storeAt=None):
        tt, failed = 0, 0
        for transaction in self.transactions:
            ### RACE CONDITION ZONE ###
            walletsLocks[transaction.fromAdress].acquire()  # LOCK ZONE
            if transaction.fromAdress in self.passwords:
                key = self.passwords[transaction.fromAdress]
                self.W3.parity.personal.unlock_account(transaction.fromAdress, key)
            else:
                print(f"WARNING: Password for wallet {transaction.fromAdress} not found.")
            status, time = transaction.launch()
            if status == 1:
                tt += time
            else:
                failed += 1
            self.W3.geth.personal.lock_account(transaction.fromAdress) # Wathever the status is, lock the wallet.
            walletsLocks[transaction.fromAdress].release() # UNLOCK ZONE
            ### END OF RACE CONDITION ZONE ###
        if storeAt is not None: storeAt[id(self)] = self.storeVerificationTime(tt)
        self.status = 1 if failed == 0 else -1
        return failed, tt # Return the number of failed transactions and the total time spent for the launch.

    def isReady(self):
        return all([t.isReady() for t in self.transactions])

    def verifiedTransactions(self):
        return [t for t in self.transactions if t.isVerified()]

    def unverifiedTransactions(self):
        return [t for t in self.transactions if not t.isVerified()]

    def allVerified(self):
        return len(self.verifiedTransactions()) == len(self.transactions)

    def storeVerificationTime(self, extraTime=0):
        t0 = time()
        while not self.allVerified(): None
        tt = time() - t0

        self.verificationTime = tt + extraTime
        return self.verificationTime

    def __getitem__(self, item):
        if item >= len(self.transactions):
            print("WARNING: Index out of range, returning the last transaction.")
            return self.transactions[-1]
        else:
            return self.transactions[item]

    def __add__(self, transaction):
        if types(transaction) is Transaction:
            self.transactions.append(transaction)
            return self
        else:
            print("ERROR: Cannot add a non-transaction object to the transaction pool.")
            return -1

    def __iter__(self):
        return iter(self.transactions)

    def __len__(self):
        return len(self.transactions)

    def __str__(self):
        stringList = []
        for transaction in self.transactions:
            stringList.append(str(transaction))
        return str(stringList)
