const http = require("http");

const server = http.createServer((req, res) => {
  res.end("Hello");
});

server.listen(4000, () => {
  console.log("Listening on 4000");
  console.log(server.address());
});

process.on("exit", (code) => {
  console.log("EXIT:", code);
});