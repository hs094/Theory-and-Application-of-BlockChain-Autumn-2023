from web3 import Web3
infura_url = "https://sepolia.infura.io/v3/d32544fba98b4074bb60a9635b4b1121"
w3 = Web3(Web3.HTTPProvider(infura_url))

abi = [{"inputs":[{"internalType":"address","name":"addr","type":"address"}],"name":"get","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getmine","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"roll","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"string","name":"newRoll","type":"string"}],"name":"update","outputs":[],"stateMutability":"nonpayable","type":"function"}]
contract_addr = "0xF98bFe8bf2FfFAa32652fF8823Bba6714c79eDd4"
chain_id = 11155111
wallet_addr = "0x9b3710f9b284eAC355F1721B00C381c626250439"
nonce = w3.eth.get_transaction_count(wallet_addr)
acc_private_key = "0x22751dbfeddda2597c6ae0fbb3008ec8dd9f5f3902d29410fa84c3d96f73ffb1"

print(f"Nonce: {nonce}")

contract_instance = w3.eth.contract(abi=abi, address=contract_addr)
new_roll = "20CS10064"
txn = contract_instance.functions.update(new_roll).build_transaction(
    {
        'gas': 1000000,
        'gasPrice': w3.eth.gas_price,
        'chainId': chain_id,
        'nonce': nonce,
    }
)

signed_txn = w3.eth.account.sign_transaction(txn, private_key=acc_private_key)
txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

print(txn_receipt)