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
    // In a real application this would be done only when a new user was required to be added
    // and would be part of an administrative flow
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

// Main workflow : usecase details at asset-transfer-private-data/chaincode-go/README.md
// This app uses fabric-samples/test-network based setup and the companion chaincode
// For this usecase illustration, we will use both Org1 & Org2 client identity from this same app
// In real world the Org1 & Org2 identity will be used in different apps to achieve asset transfer.
async function main() {
    try {

        /** ******* Fabric client init: Using Org1 identity to Org1 Peer ********** */

        // accept oranzation number as an argument
        if (process.argv.length < 3) {
            console.log('Usage: node app.js <org number>');
            process.exit(1);
        }
        const orgNumber = process.argv[2];
        console.log(`Org number: ${orgNumber}`);
        // assign gateway network and contract based on org number
        // define variables for gateway, network and contract
        let gateway;
        let network;
        let contract;
        if(orgNumber == 1) {
            gateway= await initContractFromOrg1Identity();
            network = await gateway.getNetwork(myChannel);
            contract= network.getContract(myChaincodeName);
        // Since this sample chaincode uses, Private Data Collection level endorsement policy, addDiscoveryInterest
        // scopes the discovery service further to use the endorsement policies of collections, if any
            contract.addDiscoveryInterest({ name: myChaincodeName, collectionNames: [memberAssetCollectionName, org1PrivateCollectionName] });
        } else if(orgNumber == 2) {
            /** ~~~~~~~ Fabric client init: Using Org2 identity to Org2 Peer ~~~~~~~ */
            gateway = await initContractFromOrg2Identity();
            network = await gateway.getNetwork(myChannel);
            contract = network.getContract(myChaincodeName);
            contract.addDiscoveryInterest({ name: myChaincodeName, collectionNames: [memberAssetCollectionName, org2PrivateCollectionName] });
        }

        if (process.argv.length == 7) {
            const inputData = {
                item: {
                    name: process.argv[4],
                    count: process.argv[5],
                    price: process.argv[6]
                }
            };

            if (process.argv[3] === 'ADD_ITEM') {
                const result = await contract.submitTransaction('AddItem', JSON.stringify(inputData));
                console.log('Result:', result.toString());
            }else {
                console.error('Invalid command. Use ADD_MONEY, ADD_ITEM, QUERY_BALANCE, or GET_ITEM.');
            }
        }
        else if (process.argv.length == 5) {
            const inputData = {
                amount: process.argv[4],
            };

            if (process.argv[3] === 'ADD_MONEY') {
                const result = await contract.submitTransaction('AddBalance', JSON.stringify(inputData));
                console.log('Result:', result.toString());
            }else {
                console.error('Invalid command. Use ADD_MONEY, ADD_ITEM, QUERY_BALANCE, or GET_ITEM.');
            }
        }
        else {
            if (process.argv[3] === 'QUERY_BALANCE') {
                const result = await contract.evaluateTransaction('GetBalance');
                console.log('Result:', result.toString());
            } else if (process.argv[3] === 'GET_ITEM') {
                const result = await contract.evaluateTransaction('GetItem');
                console.log('Result:', result.toString());
            } else {
                console.error('Invalid command. Use ADD_MONEY, ADD_ITEM, QUERY_BALANCE, or GET_ITEM.');
            }
        }

        await gateway.disconnect();

    } catch (error) {
        console.error(`Error in transaction: ${error}`);
        if (error.stack) {
            console.error(error.stack);
        }
        process.exit(1);
    }
}

main();

// How to run this file:
// node app.js 1 ADD_MONEY 100
// node app.js 1 QUERY_BALANCE
// node app.js 1 ADD_ITEM item1 10 100
// node app.js 1 GET_ITEM item1