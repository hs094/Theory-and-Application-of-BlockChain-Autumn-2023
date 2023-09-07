const https = require("https");
const projectId = "de1273cc3a46479dacbdc3d7b3ae777e";
const transactionHash = "0xdcae4a84a5780f62f18a9afb07b3a7627b9a28aa128a76bfddec72de9a0c2606";
const data = JSON.stringify({
  jsonrpc: "2.0",
  method: "eth_getTransactionByHash",
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
      // I. Number of transactions made by the sender prior to this one in the block
      const nonce = parseInt(result.result.nonce, 16);

      // II. Value transferred in Wei (as an integer)
      const valueWei = parseInt(result.result.value, 16);

      // III. JSON RPC payload
      console.log("JSON RPC Payload:", data);

      // IV. Response
      console.log("Response:", result);

      console.log("Number of transactions made by the sender prior to this one in the block:", nonce);
      console.log("Value transferred in Wei:", valueWei);
    } else {
      console.error("Error retrieving transaction information");
    }
  });
});

req.on("error", (error) => {
  console.error(error);
});

req.write(data);
req.end();
