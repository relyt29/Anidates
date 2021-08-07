//import { Web3 } from web3;
//var Web3 = require('web3');

async function onLogin() {
  if (typeof window.ethereum == undefined || typeof window.web3 == undefined) {
    window.alert("Please install MetaMask first.");
    return;
  }
  const ethereum = window.ethereum || window.web3.currentProvider;
  ethereum.autoRefreshOnNetworkChange = false;
  var account = await ethereum.enable();
  if (!account) {
    window.alert("You need to allow MetaMask.");
    return;
  }

  var web3 = new Web3(ethereum);
  var coinbase = await web3.eth.getCoinbase();
  if (!coinbase) {
    window.alert("Please activate Metamask first.");
    return;
  }
  console.log(coinbase);
  var message = "Logging into Anidates";
  try {
    var signature = await web3.eth.personal.sign(message, coinbase, "");
  } catch (err) {
    window.alert("You need to sign the message to be able to log in.");
    return;
  }
  var url = window.location.href + "authenticate/";
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
      if (result.success) window.location.href = "/dashboard/" + result.body;
      else window.alert("Bad User!");
    })
    .fail(function (err) {
      // console.log("After verification - Error");
      // console.log(err);
      window.alert("You are not the user.");
    });
}

function login() {
  console.log("Logging in...");
  onLogin();
}

function main() {
  const metamask_button = document.getElementById("metamask-button");
  const metamask_logo = document.getElementById("metamask-logo");
  const options = { passive: true, once: false };

  metamask_button.addEventListener("click", login, options);
  metamask_logo.addEventListener("click", login, options);
}

main();
