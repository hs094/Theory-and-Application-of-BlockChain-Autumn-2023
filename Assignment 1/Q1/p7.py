import requests
import json

# Infura Ethereum JSON-RPC URL
infura_url = "https://sepolia.infura.io/v3/d32544fba98b4074bb60a9635b4b1121"

block_no = "0x1132aea"
block_no_int = str(int(block_no, 16))
query_rpc = {
    "jsonrpc": "2.0",
    "method": "eth_getBlockTransactionCountByNumber",
    "params": ["0x1132aea"],
    "id": 1
}

try:
    # Make the HTTP request to Infura
    response = requests.post(infura_url, data=json.dumps(query_rpc), headers={'Content-Type': 'application/json'})
    response_json = response.json()
    print(f"JSON RPC: {query_rpc}")
    print(f"Response: {response_json}")

    if 'result' in response_json and response_json['result'] is not None:
        txn_cnt = int(response_json['result'], 16)
        print(f"#transaction in block-{block_no}: {txn_cnt}")
    else:
        print("Failed to fetch the block")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
