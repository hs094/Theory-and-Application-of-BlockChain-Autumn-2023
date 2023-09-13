import requests
import json

# Infura Ethereum JSON-RPC URL
infura_url = "https://sepolia.infura.io/v3/d32544fba98b4074bb60a9635b4b1121"

query_rpc = {
    "jsonrpc": "2.0",
    "method": "eth_getBalance",
    "params": ["0xBaF6dC2E647aeb6F510f9e318856A1BCd66C5e19", "latest"],
    "id": 1
}

try:
    # Make the HTTP request to Infura
    response = requests.post(infura_url, data=json.dumps(query_rpc), headers={'Content-Type': 'application/json'})
    response_json = response.json()
    print(f"Response: {response_json}")

    if 'result' in response_json:
        block_no = int(response_json['result'], 16)
        print(f"Current account balance: {block_no}")
    else:
        print("Failed to fetch current block no.")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
