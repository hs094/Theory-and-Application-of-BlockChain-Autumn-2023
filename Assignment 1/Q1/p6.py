import requests
import json

# Infura Ethereum JSON-RPC URL
infura_url = "https://sepolia.infura.io/v3/d32544fba98b4074bb60a9635b4b1121"

txn_hash = "0x5d692282381c75786e5f700c297def496e8e54f0a96d5a4447035f75085933cb"
query_rpc = {
    "jsonrpc": "2.0",
    "method": "eth_getTransactionReceipt",
    "params": [txn_hash],
    "id": 1
}

try:
    # Make the HTTP request to Infura
    response = requests.post(infura_url, data=json.dumps(query_rpc), headers={'Content-Type': 'application/json'})
    response_json = response.json()
    print(f"JSON RPC: {query_rpc}")
    print(f"Response: {response_json}")

    if 'result' in response_json and response_json['result'] is not None:
        block_no = int(response_json['result']['blockNumber'], 16)
        block_hash = int(response_json['result']['blockHash'], 16)
        cum_gas = int(response_json['result']['cumulativeGasUsed'], 16)
        txn_index = int(response_json['result']['transactionIndex'], 16)

        print(f"Block no.: {block_no}")
        print(f"Block hash: {block_hash}")
        print(f"Cumulative gas used: {cum_gas}")
        print(f"Transaction index: {txn_index}")
    else:
        print("Invalid txn-hash")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
