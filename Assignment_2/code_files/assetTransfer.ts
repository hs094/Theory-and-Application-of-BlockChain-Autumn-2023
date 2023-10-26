/*
 * SPDX-License-Identifier: Apache-2.0
 */

import { Object, Property } from 'fabric-contract-api';
import { Context, Contract, Info, Transaction } from 'fabric-contract-api';
import stringify from 'json-stringify-deterministic';
import sortKeysRecursive from 'sort-keys-recursive';

const assetCollection = 'assetCollection';
const transferAgreementObjectType = 'transferAgreement';

@Object()
export class Account {
    @Property()
    public ID: string;
    @Property()
    public AccountBalance: number;
}

@Object()
export class Item {
    @Property()
    public ItemName: string;
    @Property()
    public ItemPrice: number;
    @Property()
    public ItemQuantity: number;
}

@Object()
export class MarketPlace {
    @Property()
    public Owner: string;
    @Property()
    public ItemName: string;
    @Property()
    public ItemPrice: number;
    @Property()
    public ItemQuantity: number;
}

@Info({ title: 'AssetTransfer', description: 'Smart contract for trading assets' })
export class AssetTransfer extends Contract {
    /*
        SETTERS
    */
    @Transaction()
    public async AddBalance(ctx: Context, acc: string, amount: number): Promise<Account> {
        // Check if asset already exists
        const accComposedKey = ctx.stub.createCompositeKey(assetCollection, [acc]);
        const accAsBytes = await ctx.stub.getPrivateData(assetCollection, accComposedKey);
        // No Asset found, return empty response
        if (accAsBytes.length === 0) {
            // Add new account
            const account: Account = {
                ID: acc,
                AccountBalance: 0,
            };
            await ctx.stub.putPrivateData(assetCollection, accComposedKey, Buffer.from(stringify(sortKeysRecursive(account))));
        }

        // Update account balance by adding amount
        const jsonBytesToString = String.fromCharCode(...accAsBytes);
        const jsonFromBytes = JSON.parse(jsonBytesToString);
        const account: Account = {
            ID: jsonFromBytes.ID,
            AccountBalance: jsonFromBytes.AccountBalance + amount,
        };
        await ctx.stub.putPrivateData(assetCollection, accComposedKey, Buffer.from(stringify(sortKeysRecursive(account))));
        return account;
    }
    
    @Transaction()
    public async AddItem(ctx: Context, itemName: string, itemPrice: number, itemQuantity: number): Promise<Item> {
        // Check if asset already exists
        const orgCollection = await this.getCollectionName(ctx);
        const itemAsBytes = await ctx.stub.getPrivateData(orgCollection, itemName);
        // No Asset found, return empty response
        if (itemAsBytes.length === 0) {
            // Add new item
            const item: Item = {
                ItemName: itemName,
                ItemPrice: itemPrice,
                ItemQuantity: itemQuantity,
            };
            await ctx.stub.putPrivateData(orgCollection, item.ItemName, Buffer.from(stringify(sortKeysRecursive(item))));
            return item;
        }

        // Update item quantity by adding amount
        const jsonBytesToString = String.fromCharCode(...itemAsBytes);
        const jsonFromBytes = JSON.parse(jsonBytesToString);
        const item: Item = {
            ItemName: jsonFromBytes.ItemName,
            ItemPrice: itemPrice,
            ItemQuantity: jsonFromBytes.ItemQuantity + itemQuantity,
        };
        await ctx.stub.putPrivateData(orgCollection, item.ItemName, Buffer.from(stringify(sortKeysRecursive(item))));
        return item;
    }

    // Add item to marketplace
    //     async AddToMarket(item, price)
    //     - check private data of the organization to ensure that the item is present in the inventory
    //     - add to marketplace and remove from the inventory
    //     - emit event to notify all the organizations about the addition to the marketplace
    @Transaction()
    public async AddToMarket(ctx: Context, itemName: string, itemPrice: number, itemQuantity : number ): Promise<MarketPlace> {
        // Check if asset already exists
        const orgCollection = await this.getCollectionName(ctx);
        const itemAsBytes = await ctx.stub.getPrivateData(orgCollection, itemName);
        // No Asset found, return empty response
        if (itemAsBytes.length === 0) {
            throw new Error(itemName + ' does not exist');
        }

        const sellerID = ctx.clientIdentity.getMSPID();
        if(sellerID !== 'Org1MSP' && sellerID !== 'Org2MSP') {
            throw new Error('Only Org1 and Org2 can add to marketplace');
        }


        // check if item is already in marketplace
        const itemMarketKey = `${sellerID}_${itemName}`;
        const itemMarketComposedKey = ctx.stub.createCompositeKey(assetCollection, [itemMarketKey]);
        const itemMarketAsBytes = await ctx.stub.getPrivateData(assetCollection, itemMarketComposedKey);

        if (itemMarketAsBytes.length !== 0) {
            // update item price and quantity in marketplace
            const jsonBytesToString = String.fromCharCode(...itemMarketAsBytes);
            const jsonFromBytes = JSON.parse(jsonBytesToString);
            const item: MarketPlace = {
                Owner: sellerID,
                ItemName: jsonFromBytes.ItemName,
                ItemPrice: itemPrice,
                ItemQuantity: jsonFromBytes.ItemQuantity + itemQuantity
            };

            // update inventory item quantity
            const jsonBytesToString2 = String.fromCharCode(...itemAsBytes);
            const jsonFromBytes2 = JSON.parse(jsonBytesToString2);
            const item2: Item = {
                ItemName: jsonFromBytes2.ItemName,
                ItemPrice: jsonFromBytes2.ItemPrice,
                ItemQuantity: jsonFromBytes2.ItemQuantity - itemQuantity
            };
            await ctx.stub.putPrivateData(orgCollection, item2.ItemName, Buffer.from(stringify(sortKeysRecursive(item2))));
            await ctx.stub.putPrivateData(assetCollection, itemMarketComposedKey, Buffer.from(stringify(sortKeysRecursive(item))));

            // emit event to notify all the organizations about the addition to the marketplace
            ctx.stub.setEvent('AddToMarketEvent', Buffer.from(JSON.stringify(item)));
            return item;
        } else {
            // Add new item to marketplace
            const item: MarketPlace = {
                Owner: sellerID,
                ItemName: itemName,
                ItemPrice: itemPrice,
                ItemQuantity: itemQuantity,
            };
            // update inventory item quantity
            const jsonBytesToString2 = String.fromCharCode(...itemAsBytes);
            const jsonFromBytes2 = JSON.parse(jsonBytesToString2);
            const item2: Item = {
                ItemName: jsonFromBytes2.ItemName,
                ItemPrice: jsonFromBytes2.ItemPrice,
                ItemQuantity: jsonFromBytes2.ItemQuantity - itemQuantity
            };
            await ctx.stub.putPrivateData(orgCollection, item2.ItemName, Buffer.from(stringify(sortKeysRecursive(item2))));
            await ctx.stub.putPrivateData(assetCollection, itemMarketComposedKey, Buffer.from(stringify(sortKeysRecursive(item))));

            // emit event to notify all the organizations about the addition to the marketplace
            ctx.stub.setEvent('AddToMarketEvent', Buffer.from(JSON.stringify(item)));
            return item;
        }
    }

    // -Buy an item from marketplace
    //     async BuyFromMarket(item)
    //     - check private data to ensure if sufficient balance to buy the item
    //     - Deduct from the balance of the buyer and add to the balance of the seller
    //     - Remove item from the marketplace
    //     - Emit event to notify all the organizations about the purchase
    @Transaction()
    public async BuyFromMarket(ctx: Context, itemMarketKey: string, itemQuantity: number): Promise<MarketPlace> {
        // if asset exists in marketplace
        const itemMarketComposedKey = ctx.stub.createCompositeKey(assetCollection, [itemMarketKey]);
        const itemMarketAsBytes = await ctx.stub.getPrivateData(assetCollection, itemMarketComposedKey);

        if (itemMarketAsBytes.length === 0) {
            throw new Error(itemMarketKey + ' does not exist in marketplace');
        } 

        // get item from marketplace
        const jsonBytesToString = String.fromCharCode(...itemMarketAsBytes);
        const jsonFromBytes = JSON.parse(jsonBytesToString);
        const item: MarketPlace = {
            Owner: jsonFromBytes.Owner,
            ItemName: jsonFromBytes.ItemName,
            ItemPrice: jsonFromBytes.ItemPrice,
            ItemQuantity: jsonFromBytes.ItemQuantity,
        };

        // check if buyer has enough balance to buy item from marketplace using getBalance function
        const buyerID = ctx.clientIdentity.getMSPID();
        const buyerAccount = await this.GetBalance(ctx, buyerID);
        if(buyerAccount.AccountBalance < item.ItemPrice * itemQuantity) {
            throw new Error('Buyer does not have enough balance to buy item');
        }

        // update buyer balance
        const buyerAccountComposedKey = ctx.stub.createCompositeKey(assetCollection, [buyerID]);
        const buyerAccountAsBytes = await ctx.stub.getPrivateData(assetCollection, buyerAccountComposedKey);
        const jsonBytesToString2 = String.fromCharCode(...buyerAccountAsBytes);
        const jsonFromBytes2 = JSON.parse(jsonBytesToString2);
        const buyerAccount2: Account = {
            ID: jsonFromBytes2.ID,
            AccountBalance: jsonFromBytes2.AccountBalance - item.ItemPrice * itemQuantity,
        };
        await ctx.stub.putPrivateData(assetCollection, buyerAccountComposedKey, Buffer.from(stringify(sortKeysRecursive(buyerAccount2))));

        // update seller balance
        const sellerAccountComposedKey = ctx.stub.createCompositeKey(assetCollection, [item.Owner]);
        const sellerAccountAsBytes = await ctx.stub.getPrivateData(assetCollection, sellerAccountComposedKey);
        const jsonBytesToString3 = String.fromCharCode(...sellerAccountAsBytes);
        const jsonFromBytes3 = JSON.parse(jsonBytesToString3);
        const sellerAccount: Account = {
            ID: jsonFromBytes3.ID,
            AccountBalance: jsonFromBytes3.AccountBalance + item.ItemPrice * itemQuantity,
        };
        await ctx.stub.putPrivateData(assetCollection, sellerAccountComposedKey, Buffer.from(stringify(sortKeysRecursive(sellerAccount))));

        // update marketplace item quantity
        const itemMarket: MarketPlace = {
            Owner: item.Owner,
            ItemName: item.ItemName,
            ItemPrice: item.ItemPrice,
            ItemQuantity: item.ItemQuantity - itemQuantity,
        };
        await ctx.stub.putPrivateData(assetCollection, itemMarketComposedKey, Buffer.from(stringify(sortKeysRecursive(itemMarket))));

        // update buyer inventory item quantity using AddItem function
        const buyerInventory = await this.AddItem(ctx, item.ItemName, item.ItemPrice, itemQuantity);

        // emit event to notify all the organizations about the purchase
        ctx.stub.setEvent('BuyFromMarketEvent', Buffer.from(JSON.stringify(itemMarket)));
        return itemMarket;

    }

    // -Get all items on the marketplace
    //     async GetItemsInMarket()
    //     - Return all the items in the marketplace along with their price and quantity
    @Transaction()
    public async GetItemsInMarket(ctx: Context): Promise<MarketPlace[]> {
        const results: MarketPlace[] = [];
        // Get a range iterator
        const iterator = await ctx.stub.getPrivateDataByRange(assetCollection, 'Org1MSP_', 'Org2MSP_');
        // Iterate through result set and for each asset found, transfer to the calling org
        let result = await iterator.next();
        while (!result.done) {
            const strValue = String.fromCharCode(...result.value.value);
            const item: MarketPlace = JSON.parse(strValue);
            results.push(item);
            result = await iterator.next();
        }
        await iterator.close();
        return results;
    }

    /*
        GETTERS
    */
   @Transaction()
    public async GetBalance(ctx: Context, acc: string): Promise<Account> {
        // Check if asset already exists
        const accComposedKey = ctx.stub.createCompositeKey(assetCollection, [acc]);
        const accAsBytes = await ctx.stub.getPrivateData(assetCollection, accComposedKey);
        // No Asset found, return empty response
        if (accAsBytes.length === 0) {
            throw new Error(acc + ' does not exist');
        }

        const jsonBytesToString = String.fromCharCode(...accAsBytes);
        const jsonFromBytes = JSON.parse(jsonBytesToString);
        const account: Account = {
            ID: jsonFromBytes.ID,
            AccountBalance: jsonFromBytes.AccountBalance,
        };
        return account;
    }
    
    @Transaction()
    public async GetItem(ctx: Context, itemName: string): Promise<Item> {
        // - send the details as transient data
        // - store the details in the private data for the org

        // Check if asset already exists
        const orgCollection = await this.getCollectionName(ctx);
        const itemAsBytes = await ctx.stub.getPrivateData(orgCollection, itemName);
        // No Asset found, return empty response
        if (itemAsBytes.length === 0) {
            throw new Error(itemName + ' does not exist');
        }

        const jsonBytesToString = String.fromCharCode(...itemAsBytes);
        const jsonFromBytes = JSON.parse(jsonBytesToString);
        const item: Item = {
            ItemName: jsonFromBytes.ItemName,
            ItemPrice: jsonFromBytes.ItemPrice,
            ItemQuantity: jsonFromBytes.ItemQuantity,
        };
        return item;
    }
    
    
    // GetAssetByRange performs a range query based on the start and end keys provided. Range
    // queries can be used to read data from private data collections, but can not be used in
    // a transaction that also writes to private data.
    @Transaction()
    public async GetItemsByRange(ctx: Context, startKey: string, endKey: string): Promise<Item[]> {
        const results: Item[] = [];
        // Get a range iterator
        const iterator = await ctx.stub.getPrivateDataByRange(assetCollection, startKey, endKey);
        // Iterate through result set and for each asset found, transfer to the calling org
        let result = await iterator.next();
        while (!result.done) {
            const strValue = String.fromCharCode(...result.value.value);
            const item: Item = JSON.parse(strValue);
            results.push(item);
            result = await iterator.next();
        }
        await iterator.close();
        return results;
    }

    /*
        HELPERS
    */
    // getCollectionName is an internal helper function to get collection of submitting client identity.
    public async getCollectionName(ctx: Context): Promise<string> {
        // Get the MSP ID of submitting client identity
        const clientMSPID = ctx.clientIdentity.getMSPID();
        // Create the collection name
        const orgCollection = clientMSPID + 'PrivateCollection';

        return orgCollection;
    }
}
