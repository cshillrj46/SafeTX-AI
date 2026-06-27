// File: blockchain/scripts/interact.js

const hre = require("hardhat");

async function main() {
  const [sender] = await hre.ethers.getSigners();

  // 💡 Substitua este endereço pelo que foi exibido no deploy
  const contractAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";

  // ✅ Forma correta de obter a instância com getContractAt
  const delayContract = await hre.ethers.getContractAt("DelayTransaction", contractAddress);

  console.log("Queuing transaction...");
  const tx = await delayContract.queueTransaction("0x0000000000000000000000000000000000000001", {
    value: hre.ethers.parseEther("0.01"),
  });
  await tx.wait();

  console.log("Transaction queued. Now trying to execute...");

  try {
    const exec = await delayContract.executeTransaction();
    await exec.wait();
    console.log("Transaction executed!");
  } catch (err) {
    console.error("Execution failed (probably due to delay):", err.message);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});