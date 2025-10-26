const readline = require("readline");
const yargs = require("yargs");
const { hideBin } = require("yargs/helpers");

const main = () => {
  const argv = yargs(hideBin(process.argv))
    .command("$0 <url>", false, (yargs) => {
      yargs.positional("url", {
        describe: "websocket server url",
        type: "string",
      });
    })
    .help().argv;

  const socket = new WebSocket(argv.url);

  socket.onopen = () => {
    console.log(`${argv.url} - connection established`);
  };

  socket.onmessage = (event) => {
    console.log(`${argv.url} - message: ${event.data}`);
  };

  socket.onclose = () => {
    console.log(`${argv.url} - connection closed`);
    return;
  };

  socket.onerror = (error) => {
    console.error(`${argv.url} - error: [${error.message}]`);
  };

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false,
  });

  rl.on("line", (input) => {
    if (socket.readyState === WebSocket.OPEN) {
      console.log(`${argv.url} - send: ${input}`);
      socket.send(input);
    }
  });
};

main();
