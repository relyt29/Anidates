/* eslint @typescript-eslint/no-var-requires: "off" */
import Web3Modal from "web3modal";
import WalletConnectProvider from "@walletconnect/web3-provider";
const Web3 = require("web3");

const providerOptions = {
  walletconnect: {
    package: WalletConnectProvider,
    options: {
      infuraId: "acd431a9d6a0461ab7b3011ae5a3a7b0",
    },
  },
};

const web3Modal = new Web3Modal({
  network: "mainnet",
  cacheProvider: false,
  providerOptions,
});

async function doWalletConnecting() {
  const provider = await web3Modal.connect();
  //await provider.enable();

  const web3 = new Web3(provider);

  // Subscribe to accounts change
  provider.on("accountsChanged", (accounts: string[]) => {
    console.log(accounts);
  });

  // Subscribe to chainId change
  provider.on("chainChanged", (chainId: number) => {
    console.log(chainId);
  });

  // Subscribe to provider connection
  provider.on("connect", (info: { chainId: number }) => {
    console.log(info);
  });

  // Subscribe to provider disconnection
  provider.on("disconnect", (error: { code: number; message: string }) => {
    console.log(error);
  });

  const coinbase = await web3.eth.getCoinbase();
  if (!coinbase) {
    window.alert("Please activate Metamask first.");
    return;
  }
  //console.log(coinbase);
  const message = "Logging into Anidates";
  try {
    const signature = await web3.eth.personal.sign(message, coinbase, "");
    const url = window.location.href + "authenticate/";
    $.ajax({
      contentType: "application/json",
      data: JSON.stringify({
        address: coinbase,
        signature: signature,
        message: message,
      }),
      success: function (data) {
        return data;
      },
      error: function (error) {
        return error;
      },
      processData: false,
      type: "POST",
      url: url,
    })
      .done(function (result) {
        // console.log("After verification");
        if (result.success) {
          //console.log(result.body);
          window.location.href = result.body;
        }
        else window.alert("Bad User!");
      })
      .fail(function (err) {
        // console.log("After verification - Error");
        //console.log(err);
        window.alert(`Error logging in: ${err["responseJSON"]["body"]}`);
      });
  } catch (err) {
    window.alert("You need to sign the message to be able to log in.");
    return;
  }
}

function login() {
  if (web3Modal) {
    web3Modal.clearCachedProvider();
  }
  console.log("Logging in...");
  doWalletConnecting();
}

function main() {
  const metamask_button = document.getElementById("metamask-button");
  const options = { passive: true, once: false };
  metamask_button.addEventListener("click", login, options);
}

main();
