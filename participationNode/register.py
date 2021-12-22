import json
import time
import base64
import os
from algosdk import algod
from algosdk import mnemonic
from algosdk import transaction
from algosdk import encoding
from algosdk import account
# python3 -m pip install py-algorand-sdk
import dotenv
# python3 -m pip install python-dotenv

def wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception(
                'pool error: {}'.format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception(
        'pending tx not found in timeout rounds, timeout value = : {}'.format(timeout))

def loadEnvs():
    config = dotenv.dotenv_values("./context.env")
    return config
# utility to connect to node
def connect_to_network(config):
    algod_address = "http://127.0.0.1:8080"
    algod_token = config['token']
    algod_client = algod.AlgodClient(algod_token, algod_address)
    return algod_client

def write_unsigned(config):
    # setup connectionon
    algod_client = connect_to_network(config)

    # get suggested parameters
    params = algod_client.suggested_params()

    b64votekey = config['voteKey']
    votekey_addr = encoding.encode_address(base64.b64decode(b64votekey))
    b64selkey = config['selKey']
    selkey_addr = encoding.encode_address(base64.b64decode(b64selkey))

    status = algod_client.status()
    current_round = status['lastRound']
    avg_blocktime = 3
    avg_no_of_blocks = 200/avg_blocktime
    first_valid_round = int(current_round + avg_no_of_blocks)
    last_valid_round = int(first_valid_round + 1000)
    # create transaction
    data = {
        "sender": config['address'],
        "votekey": votekey_addr,
        "selkey": selkey_addr,
        "votefst": 6000000,
        "votelst": 9000000,
        "votekd": 1730,
        "fee": 1000,
        "flat_fee": True,
        "first": first_valid_round,
        "last": last_valid_round,
        "gen": params.get('genesisID'),
        "gh": params.get('genesishashb64')
    }
    txn = transaction.KeyregTxn(**data)
    while(1):
        status = algod_client.status()
        current_round = int(status['lastRound'])
        print("wait")
        if current_round > first_valid_round:
            print("success")
            signed_txn = txn.sign(mnemonic.to_private_key(config['passphrase']))
            txid = algod_client.send_transaction(signed_txn) # send the transaction
            print(f"Successfully sent transaction with txID: {txid}") # prints the transaction id
            break
    try:
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        # wait for confirmation
    except Exception as err:
        print(err)
        return
    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))
    print("Decoded note: {}".format(base64.b64decode(
        confirmed_txn["txn"]["txn"]["note"]).decode()))

values = loadEnvs()
write_unsigned(values)
