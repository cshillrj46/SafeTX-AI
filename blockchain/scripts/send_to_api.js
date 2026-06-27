// File: blockchain/scripts/send_to_api.js

const axios = require("axios");

async function sendTransactionToAPI() {
  const transactionData = {
    sender: "0x1234567890abcdef1234567890abcdef12345678",
    recipient: "0x0000000000000000000000000000000000000001",
    amount_eth: 0.01
  };

  try {
    const response = await axios.post("http://127.0.0.1:8000/analyze", transactionData);
    console.log("Risk analysis result:", response.data);
  } catch (error) {
    console.error("Failed to send transaction to API:", error.message);
  }
}

sendTransactionToAPI();
