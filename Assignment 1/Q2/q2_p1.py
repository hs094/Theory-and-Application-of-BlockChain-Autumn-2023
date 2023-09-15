from web3 import Web3
infura_url = "https://sepolia.infura.io/v3/d32544fba98b4074bb60a9635b4b1121"
w3 = Web3(Web3.HTTPProvider(infura_url))

abi = [{"inputs":[{"internalType":"address","name":"addr","type":"address"}],"name":"get","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getmine","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"roll","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"string","name":"newRoll","type":"string"}],"name":"update","outputs":[],"stateMutability":"nonpayable","type":"function"}]
contract_addr = "0xF98bFe8bf2FfFAa32652fF8823Bba6714c79eDd4"

contract_instance = w3.eth.contract(abi=abi, address=contract_addr)

q_addr = "0x328Ff6652cc4E79f69B165fC570e3A0F468fc903"
# q_addr = "0x9b3710f9b284eAC355F1721B00C381c626250439"
roll = contract_instance.functions.get(q_addr).call()
print(f"Roll: {roll}")