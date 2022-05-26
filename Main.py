def fillMainWallet(W3, mainWallet, walletKey, fillTo):
    initialAmount = W3.fromWei(W3.eth.getBalance(mainWallet), 'ether')
    if initialAmount < fillTo:
        W3.parity.personal.unlock_account(mainWallet, walletKey)
        W3.geth.miner.start(1)
        while W3.fromWei(W3.eth.getBalance(mainWallet), 'ether') < fillTo: None
        W3.geth.miner.stop()
        W3.geth.personal.lock_account(mainWallet)
    return W3.fromWei(W3.eth.getBalance(mainWallet), 'ether')

def GenerateWallets(W3, nInputWallets, nOutputWallets, MAIN_WALLET, KEY):
    for i in range(len(W3.eth.accounts)): # To avoid any problems, start without any account.
        W3.geth.personal.lock_account(W3.eth.accounts[i])
    WalletsPasswords = {}
    InputWallets, OutputWallets = [], []

    W3.parity.personal.unlock_account(MAIN_WALLET, KEY)

    for i in range(nInputWallets):
        password = sha256(str(time()).encode('utf-8')).hexdigest()
        accountHash = W3.parity.personal.newAccount(password)
        InputWallets.append(accountHash)
        WalletsPasswords[accountHash] = password

        # Add some funds to the wallet.
        print(f"Creating Wallet {i+1}/{nInputWallets}")
        transaction = Transaction(W3, MAIN_WALLET, accountHash, value=10)
        transaction.launch()
        while not transaction.isVerified(): None # Wait for the transaction to be mined.
        print(f"\t Account {i+1} Balance: {W3.fromWei(W3.eth.getBalance(accountHash), 'ether')} ETH")
        W3.geth.personal.lock_account(accountHash)

    for _ in range(nOutputWallets):
        password = sha256(str(time()).encode('utf-8')).hexdigest()
        accountHash = W3.parity.personal.newAccount(password)
        OutputWallets.append(accountHash)
        WalletsPasswords[accountHash] = password
    return InputWallets, OutputWallets, WalletsPasswords

def run(numberOfWallets, toWallets, transactionsPerSecond, transactionSize, # This arguments are passed trough the command line.
        VERIFICATION_TIMES, threads,
        IPC_PATH = None, HTTP_PROVIDER=None, WEB_SOCKET=None):
    foundProvider = False
    print("Connecting to Ethereum Client", end=" ")
    if IPC_PATH is not None:
        W3 = Web3(Web3.IPCProvider(IPC_PATH))
        foundProvider = True
    elif HTTP_PROVIDER is not None:
        W3 = Web3(Web3.HTTPProvider(HTTP_PROVIDER))
        foundProvider = True
    elif WEB_SOCKET is not None:
        W3 = Web3(Web3.WebsocketProvider(WEB_SOCKET))
        foundProvider = True

    if W3.isConnected() and foundProvider:
        print("✔")

        toWallets = [W3.toChecksumAddress(w) for w in toWallets] # Convert to checksum addresses.

        fillMainWallet(W3, MAIN_WALLET, KEY, 15*numberOfWallets)

        print("Generating Wallets & Mining")
        fromWallets, _, WalletsPasswords = GenerateWallets(W3, numberOfWallets, 0, MAIN_WALLET, KEY)

        global walletsLocks
        walletsLocks = {}
        for wallet in fromWallets: walletsLocks[wallet] = threading.Lock()

        exportWallets(WalletsPasswords) # Store the wallets in a file.
        i = 1
        print("Starting Transactions\n")
        while True:
            t0 = time()
            print(f"--- Pool of Transactions {i} ---")
            myPool = TransactionPool(W3, fromWallets, toWallets,
                                     transactionsPerSecond,
                                     WalletsPasswords,
                                     transactionSize)
            myPool.initializeTransactions(fillRandomData=True)
            thrd = threading.Thread(target=myPool.launch, args=(walletsLocks, VERIFICATION_TIMES,))
            thrd.start()
            threads.append(thrd)
            i+=1
            print("------------------------------")
            tt = time() - t0
            sleep(max(0, 1-tt))

    else:
        print("✘")
        sys.stderr.write("Connection failed, check network credentials.")
        sys.exit(1)

if __name__ == "__main__":
    from Imports import *

    MAIN_WALLET, KEY = readWalletInformation('Configuration.ini')
    MAIN_WALLET = Web3.toChecksumAddress(MAIN_WALLET)
    info, infoType = readNodeConnection('Configuration.ini')

    args = readArguments(sys.argv[1:])
    if not all(args):
        print('Main.py -n <numberOfWallets> '
              '-r <receiverWallet1,receiverWallet2,...> '
              '-t <transactionsPerSecond> '
              '-s <transactionSize>')
        sys.stderr.write("Missing arguments.\n")
        sys.exit(1)
    else:
        numberOfWallets, receiverWallets = args[0], args[1]
        transactionsPerSecond, transactionSize = args[2], args[3]
        print("--> Network Benchmarking <--")
        print("Number of Sender Wallets:", numberOfWallets)
        print("Number of Receiver Wallets:", len(receiverWallets))
        print("Transactions per Second:", transactionsPerSecond)
        print("Transaction Size:", transactionSize)
        print("----------------------------")

    VERIFICATION_TIMES, threads = {}, []
    hasBreak = False

    try:
        if infoType == 'IPC_PATH':
            run(numberOfWallets, receiverWallets, transactionsPerSecond, transactionSize, VERIFICATION_TIMES,
                threads, IPC_PATH=info)
        elif infoType == 'HTTP_PROVIDER':
            run(numberOfWallets, receiverWallets, transactionsPerSecond, transactionSize, VERIFICATION_TIMES,
                threads, HTTP_PROVIDER=info)
        elif infoType == 'WEB_SOCKET':
            run(numberOfWallets, receiverWallets, transactionsPerSecond, transactionSize, VERIFICATION_TIMES,
                threads, WEB_SOCKET=info)
        else:
            sys.stderr.write("Invalid Connection Type\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n")
        for thread, i in zip(threads, range(1, len(threads)+1)):
            thread.join()
            print(f"Thread {i}/{len(threads)} Finished.")
        file = open(f"Benchmark_{time()}.txt", "w")
        for verificationTime in VERIFICATION_TIMES.values():
            if verificationTime is not None:
                file.write(f"{verificationTime}\n")
        file.close()
        hasBreak = True

    finally:
        if not hasBreak:
            print("\n")
            for thread, i in zip(threads, range(1, len(threads) + 1)):
                thread.join()
                print(f"Thread {i}/{len(threads)} Finished.")
            file = open(f"Benchmark_{time()}.txt", "w")
            for verificationTime in VERIFICATION_TIMES.values():
                if verificationTime is not None:
                    file.write(f"{verificationTime}\n")
            file.close()
