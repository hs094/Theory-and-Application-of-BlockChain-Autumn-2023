import requests
import json

# Infura Ethereum JSON-RPC URL
infura_url = "https://sepolia.infura.io/v3/d32544fba98b4074bb60a9635b4b1121"

txn_hash = "0xdcae4a84a5780f62f18a9afb07b3a7627b9a28aa128a76bfddec72de9a0c2606"
query_rpc = {
    "jsonrpc": "2.0",
    "method": "eth_getTransactionByHash",
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
        nonce = int(response_json['result']['nonce'], 16)
        value = int(response_json['result']['value'], 16)

        print(f"prior #transaction: {nonce}")
        print(f"value transferred (inWei): {value}")
    else:
        print("Invalid txn-hash")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
