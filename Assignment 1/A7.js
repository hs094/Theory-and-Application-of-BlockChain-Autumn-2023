const https = require("https");
const projectId = "de1273cc3a46479dacbdc3d7b3ae777e";
const blockNumber = "0x1132aea"; // Replace with the block number in hexadecimal format
const data = JSON.stringify({
  jsonrpc: "2.0",
  method: "eth_getBlockTransactionCountByNumber",
  params: [blockNumber],
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
      // I. Number of transactions in the block (integer)
      const transactionCount = parseInt(result.result, 16);

      // II. JSON RPC payload
      console.log("JSON RPC Payload:", data);

      // III. Response
      console.log("Response:", result);

      console.log("Number of transactions in the block:", transactionCount);
    } else {
      console.error("Error retrieving transaction count for the block");
    }
  });
});

req.on("error", (error) => {
  console.error(error);
});

req.write(data);
req.end();
