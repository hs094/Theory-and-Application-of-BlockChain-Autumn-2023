/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

'use strict';

const { Gateway, Wallets } = require('fabric-network');
const FabricCAServices = require('fabric-ca-client');
const path = require('path');
const { buildCAClient, registerAndEnrollUser, enrollAdmin } = require('../../test-application/javascript/CAUtil.js');
const { buildCCPOrg1, buildCCPOrg2, buildWallet } = require('../../test-application/javascript/AppUtil.js');

const myChannel = 'mychannel';
const myChaincodeName = 'private';

const memberAssetCollectionName = 'assetCollection';
const org1PrivateCollectionName = 'Org1MSPPrivateCollection';
const org2PrivateCollectionName = 'Org2MSPPrivateCollection';
const mspOrg1 = 'Org1MSP';
const mspOrg2 = 'Org2MSP';
const Org1UserId = 'appUser1';
const Org2UserId = 'appUser2';

const RED = '\x1b[31m\n';
const RESET = '\x1b[0m';
const prompt=require("prompt-sync")({sigint:true}); 

function prettyJSONString(inputString) {
    if (inputString) {
        return JSON.stringify(JSON.parse(inputString), null, 2);
    }
    else {
        return inputString;
    }
}

function doFail(msgString) {
    console.error(`${RED}\t${msgString}${RESET}`);
    process.exit(1);
}

async function initContractFromOrg1Identity() {
    console.log('\n--> Fabric client user & Gateway init: Using Org1 identity to Org1 Peer');
    // build an in memory object with the network configuration (also known as a connection profile)
    const ccpOrg1 = buildCCPOrg1();

    // build an instance of the fabric ca services client based on
    // the information in the network configuration
    const caOrg1Client = buildCAClient(FabricCAServices, ccpOrg1, 'ca.org1.example.com');

    // setup the wallet to cache the credentials of the application user, on the app server locally
    const walletPathOrg1 = path.join(__dirname, 'wallet/org1');
    const walletOrg1 = await buildWallet(Wallets, walletPathOrg1);

    // in a real application this would be done on an administrative flow, and only once
    // stores admin identity in local wallet, if needed
    await enrollAdmin(caOrg1Client, walletOrg1, mspOrg1);
    // register & enroll application user with CA, which is used as client identify to make chaincode calls
    // and stores app user identity in local wallet
    await registerAndEnrollUser(caOrg1Client, walletOrg1, mspOrg1, Org1UserId, 'org1.department1');

    try {
        // Create a new gateway for connecting to Org's peer node.
        const gatewayOrg1 = new Gateway();
        // Connect using Discovery enabled
        await gatewayOrg1.connect(ccpOrg1,
            { wallet: walletOrg1, identity: Org1UserId, discovery: { enabled: true, asLocalhost: true } });

        return gatewayOrg1;
    } catch (error) {
        console.error(`Error in connecting to gateway: ${error}`);
        process.exit(1);
    }
}

async function initContractFromOrg2Identity() {
    console.log('\n--> Fabric client user & Gateway init: Using Org2 identity to Org2 Peer');
    const ccpOrg2 = buildCCPOrg2();
    const caOrg2Client = buildCAClient(FabricCAServices, ccpOrg2, 'ca.org2.example.com');

    const walletPathOrg2 = path.join(__dirname, 'wallet/org2');
    const walletOrg2 = await buildWallet(Wallets, walletPathOrg2);

    await enrollAdmin(caOrg2Client, walletOrg2, mspOrg2);
    await registerAndEnrollUser(caOrg2Client, walletOrg2, mspOrg2, Org2UserId, 'org2.department1');

    try {
        // Create a new gateway for connecting to Org's peer node.
        const gatewayOrg2 = new Gateway();
        await gatewayOrg2.connect(ccpOrg2,
            { wallet: walletOrg2, identity: Org2UserId, discovery: { enabled: true, asLocalhost: true } });

        return gatewayOrg2;
    } catch (error) {
        console.error(`Error in connecting to gateway: ${error}`);
        process.exit(1);
    }
}

// This app uses fabric-samples/test-network based setup and the companion chaincode
async function main() {
    try {

        /** ******* Fabric client init: Using Org1 identity to Org1 Peer ********** */
        const gatewayOrg1 = await initContractFromOrg1Identity();
        const networkOrg1 = await gatewayOrg1.getNetwork(myChannel);
        const contractOrg1 = networkOrg1.getContract(myChaincodeName);
        // Since this sample chaincode uses, Private Data Collection level endorsement policy, addDiscoveryInterest
        // scopes the discovery service further to use the endorsement policies of collections, if any
        contractOrg1.addDiscoveryInterest({ name: myChaincodeName, collectionNames: [memberAssetCollectionName, org1PrivateCollectionName] });

        /** ~~~~~~~ Fabric client init: Using Org2 identity to Org2 Peer ~~~~~~~ */
        const gatewayOrg2 = await initContractFromOrg2Identity();
        const networkOrg2 = await gatewayOrg2.getNetwork(myChannel);
        const contractOrg2 = networkOrg2.getContract(myChaincodeName);
        contractOrg2.addDiscoveryInterest({ name: myChaincodeName, collectionNames: [memberAssetCollectionName, org2PrivateCollectionName] });
        
        while(1){
            // get the org from user input using prompt
            const org = prompt('Enter the org name (org1 || org2): ');
            if (org !== 'org1' && org !== 'org2') {
                doFail('Invalid org name');
            }

            const network = org === 'org1' ? networkOrg1 : networkOrg2;
            const contract = org === 'org1' ? contractOrg1 : contractOrg2;
            const privateCollectionName = org === 'org1' ? org1PrivateCollectionName : org2PrivateCollectionName;

            let listener;
            try{
                listener = async (event) => {
                    console.log(`Received event: ${event.eventName}`);
                    if (event.eventName === 'AddToMarketEvent') {
                        // print name of seller, item name, price and quantity
                        const payload = event.payload.toString();
                        const payloadJSON = JSON.parse(payload);
                        console.log(`Seller: ${payloadJSON.seller}, Item: ${payloadJSON.itemName}, Price: ${payloadJSON.price}, Quantity: ${payloadJSON.quantity}`);
                    }
                }; await contract.addContractListener(listener);
            } catch(err){
                console.log(err);
            }

            while(1){
                // take user input for the operation to perform
                // Format:
                // 1. ADD_MONEY <acc> <amount>
                // 2. QUERY_BALANCE <acc>
                // 3. GET_ITEM <itemName>
                // 4. ADD_ITEM <itemName> <itemPrice> <itemQuantity>

                const operation = prompt('Enter the operation to perform: ');
                const args = operation.split(' ');

                if (args[0] === 'ADD_MONEY') {
                    const acc = args[1];
                    const amount = parseInt(args[2]);
                    console.log(`Adding ${amount} to ${acc}`);
                    const response = await contract.submitTransaction('AddBalance', acc, amount);
                    console.log(`Transaction has been submitted. Response: ${prettyJSONString(response.toString())}`);
                } else if (args[0] === 'QUERY_BALANCE') {
                    const acc = args[1];
                    console.log(`Querying balance for ${acc}`);
                    const response = await contract.evaluateTransaction('GetBalance', acc);
                    console.log(`Transaction has been submitted. Response: ${prettyJSONString(response.toString())}`);
                } else if (args[0] === 'GET_ITEM') {
                    const itemName = args[1];
                    console.log(`Getting item ${itemName}`);
                    const response = await contract.evaluateTransaction('GetItem', itemName);
                    console.log(`Transaction has been submitted. Response: ${prettyJSONString(response.toString())}`);
                } else if (args[0] === 'ADD_ITEM') {
                    const itemName = args[1];
                    const itemPrice = parseInt(args[2]);
                    const itemQuantity = parseInt(args[3]);
                    console.log(`Adding item ${itemName} with price ${itemPrice} and quantity ${itemQuantity}`);
                    const response = await contract.submitTransaction('AddItem', itemName, itemPrice, itemQuantity);
                    console.log(`Transaction has been submitted. Response: ${prettyJSONString(response.toString())}`);
                } else if (args[0] === 'exit') {
                    console.log('Exiting the application.');
                    process.exit(0);
                } else {
                    console.log('Invalid operation. Please enter "ADD_MONEY", "QUERY_BALANCE", "GET_ITEM", "ADD_ITEM" or "exit".');
                }
            }
        }
        gatewayOrg1.disconnect();
        gatewayOrg2.disconnect();

    } catch (error) {
        console.error(`Error in transaction: ${error}`);
        if (error.stack) {
            console.error(error.stack);
        }
        process.exit(1);
    }
}

main();

