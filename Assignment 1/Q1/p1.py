import requests
import json

# Infura Ethereum JSON-RPC URL
infura_url = "https://sepolia.infura.io/v3/d32544fba98b4074bb60a9635b4b1121"

# Ethereum gas price JSON-RPC method
query_rpc = {
    "jsonrpc": "2.0",
    "method": "eth_gasPrice",
    "params": [],
    "id": 1
}

try:
    # Make the HTTP request to Infura
    response = requests.post(infura_url, data=json.dumps(query_rpc), headers={'Content-Type': 'application/json'})
    response_json = response.json()
    print(f"JSON RPC: {query_rpc}")
    print(f"Response: {response_json}")

    if 'result' in response_json:
        # Gas price is returned in hexadecimal format, convert it to Wei (integer)
        gas_price_wei = int(response_json['result'], 16)
        print(f"Current Gas Price (Wei): {gas_price_wei}")
    else:
        print("Failed to fetch gas price.")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
