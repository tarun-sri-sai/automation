const ws = require("ws");
const yargs = require("yargs");
const { hideBin } = require("yargs/helpers");

class ServerMessage {
  #message;

  constructor(message) {
    this.#message = message;
  }

  getMessage() {
    return this.#message;
  }

  setMessage(message) {
    this.#message = message;
  }
}

const sendMessages = (socket, serverMessage, intervalMs, client) => {
  const interval = setInterval(() => {
    if (socket.readyState === ws.OPEN) {
      const message = serverMessage.getMessage();
      console.log(`${client} - send: ${message}`);
      socket.send(message);
    } else {
      clearInterval(interval);
    }
  }, intervalMs);
};

const main = () => {
  const argv = yargs(hideBin(process.argv))
    .command("$0 <port> <interval>", false, (yargs) => {
      yargs
        .positional("port", {
          describe: "websocket server port",
          type: "number",
        })
        .positional("interval", {
          describe: "message send interval in milliseconds",
          type: "number",
        });
    })
    .help().argv;

  const server = new ws.Server({ port: argv.port });
  console.log(`server is listening on ws://localhost:${argv.port}`);

  server.on("connection", (socket, request) => {
    const serverMessage = new ServerMessage(
      `hello! i'll keep sending a message once every ` +
        `${parseFloat((argv.interval / 1000).toFixed(2))} seconds. update it by sending ` +
        `a new message to the server`
    );

    const { remoteAddress, remotePort } = request.socket;
    const client = `${remoteAddress}:${remotePort}`;
    console.log(`${client} - connection established`);

    sendMessages(socket, serverMessage, argv.interval, client);

    socket.on("message", (message) => {
      console.log(`${client} - message: ${message}`);
      serverMessage.setMessage(message.toString());
    });

    socket.on("close", () => {
      console.log(`${client} - connection closed`);
    });
  });
};

main();
