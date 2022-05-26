import configparser, getopt
from time import time
import sys

def readWalletInformation(configurationFile):
    config = configparser.ConfigParser()
    config.read(configurationFile)
    sections = config.sections()
    MAIN_WALLET = config[sections[0]]['MAIN_WALLET']
    KEY = config[sections[0]]['KEY']
    return MAIN_WALLET, KEY

def readNodeConnection(configurationFile):
    config = configparser.ConfigParser()
    config.read(configurationFile)
    sections = config.sections()

    IPC_PATH = config[sections[1]]['IPC_PATH']
    if IPC_PATH != 0:
        return IPC_PATH, 'IPC_PATH'

    HTTP_PROVIDER = config[sections[1]]['HTTP_PROVIDER']
    if HTTP_PROVIDER != 0:
        return HTTP_PROVIDER, 'HTTP_PROVIDER'

    WEB_SOCKET = config[sections[1]]['WEB_SOCKET']
    if WEB_SOCKET != 0:
        return WEB_SOCKET, 'WEB_SOCKET'

    return 0, 0

def exportWallets(WalletsPasswords):
    with open(f"Wallets_{time()}.txt", "w") as f:
        for wallet in WalletsPasswords:
            f.write(wallet + "\t" + WalletsPasswords[wallet] + "\n")
        f.close()

def readArguments(argv):
    numberOfWallets = False
    receiverWallets = False
    transactionsPerSecond = False
    transactionSize = False
    try:
      opts, args = getopt.getopt(argv, "n:r:t:s:")
    except getopt.GetoptError as error:
      print('Main.py -n <numberOfWallets> -r <receiverWallet1,receiverWallet2,...> -t <transactionsPerSecond> -s <transactionSize>')
      sys.exit(2)
    for opt, arg in opts:
      if opt == '-n':
         numberOfWallets = int(arg)
      elif opt == '-r':
         receiverWallets = arg.split(',')
      elif opt == '-t':
          transactionsPerSecond = int(arg)
      elif opt == '-s':
          transactionSize = int(arg)

    return numberOfWallets, receiverWallets, transactionsPerSecond, transactionSize