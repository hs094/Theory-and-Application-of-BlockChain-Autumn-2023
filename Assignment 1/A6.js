const https = require("https");
const projectId = "de1273cc3a46479dacbdc3d7b3ae777e";
const transactionHash = "0x5d692282381c75786e5f700c297def496e8e54f0a96d5a4447035f75085933cb";
const data = JSON.stringify({
  jsonrpc: "2.0",
  method: "eth_getTransactionReceipt",
  params: [transactionHash],
  id: 1,
});
const options = {
  host: "mainnet.infura.io",
  port: 443,
  path: "/v3/" + projectId,
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
};
const req = https.request(options, (res) => {
  console.log(`statusCode: ${res.statusCode}`);

  let response = "";

  res.on("data", (d) => {
    response += d;
  });

  res.on("end", () => {
    const result = JSON.parse(response);
    if (result && result.result) {
      // I. Block Number (integer)
      const blockNumber = parseInt(result.result.blockNumber, 16);

      // II. Block Hash
      const blockHash = result.result.blockHash;

      // III. Cumulative Gas Used (integer)
      const cumulativeGasUsed = parseInt(result.result.cumulativeGasUsed, 16);

      // IV. Transaction Index (integer)
      const transactionIndex = parseInt(result.result.transactionIndex, 16);

      console.log("Block Number:", blockNumber);
      console.log("Block Hash:", blockHash);
      console.log("Cumulative Gas Used:", cumulativeGasUsed);
      console.log("Transaction Index:", transactionIndex);
    } else {
      console.error("Error retrieving transaction receipt information");
    }
  });
});

req.on("error", (error) => {
  console.error(error);
});

req.write(data);
req.end();
