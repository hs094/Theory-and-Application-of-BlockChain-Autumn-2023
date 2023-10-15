# Theory and Application of Blockchain - Assignment 2
## Contributors
- 20CS10064 - Subhajyoti Halder
- 20CS30019 - Gitanjali Gupta
- 20CS30023 - Hardik Pravin Soni
- 20CS30069 - Priyanshi Dixit

## Instruction
- **Clone fabric-sample repository**
```bash
curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh
./install-fabric.sh docker samples binary
```
- **Replace the following files in the mentioned path**
```bash
"app.js" : ./asset-transfer-private-data/application-javascript/app.js
"assetTransfer.js" : ./asset-transfer-private-data/chaincode-typescript/src/assetTransfer.ts
```
- **Create the test network and a channel (from the test-network folder).**
```bash
sudo ./network.sh up createChannel -c mychannel -ca
```
- **Deploy the smart contract implementations (from the test-network folder).**
```bash
# To deploy the typescript chaincode implementation
sudo ./network.sh deployCC -ccn private -ccp ../asset-transfer-private-data/chaincode-typescript/ -ccl typescript  -ccep "OR('Org1MSP.peer','Org2MSP.peer')" -cccg ../asset-transfer-private-data/chaincode-typescript/collections_config.json 
```
- **Run the application (from the asset-transfer-private-data folder)**
```bash
# To run the Javascript sample application
cd application-javascript
sudo npm install
sudo node app.js
