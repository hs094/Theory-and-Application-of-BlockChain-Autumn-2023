const https = require("https");
const projectId = "de1273cc3a46479dacbdc3d7b3ae777e";
const data = JSON.stringify({
  jsonrpc: "2.0",
  method: "net_peerCount",
  params: [],
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
      // I. Number of peers connected to your Geth client
      const peerCount = parseInt(result.result, 16);

      // II. JSON RPC payload
      console.log("JSON RPC Payload:", data);

      // III. Response
      console.log("Response:", result);

      console.log("Number of peers connected to your Geth client:", peerCount);
    } else {
      console.error("Error retrieving peer count information");
    }
  });
});

req.on("error", (error) => {
  console.error(error);
});

req.write(data);
req.end();
