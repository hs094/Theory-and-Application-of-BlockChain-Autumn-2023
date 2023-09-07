const https = require("https");
const projectId = "de1273cc3a46479dacbdc3d7b3ae777e";
const address = "0xBaF6dC2E647aeb6F510f9e318856A1BCd66C5e19"; // Replace with the Ethereum address you want to check
const data = JSON.stringify({
  jsonrpc: "2.0",
  method: "eth_getBalance",
  params: [address, "latest"], // "latest" for the most recent block
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

  res.on("data", (d) => {
    process.stdout.write(d);
  });
});

req.on("error", (error) => {
  console.error(error);
});

req.write(data);
req.end();
