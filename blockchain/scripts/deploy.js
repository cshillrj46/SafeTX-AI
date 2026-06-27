// File: blockchain/scripts/deploy.js

const hre = require("hardhat");

async function main() {
  const DelayTransaction = await hre.ethers.getContractFactory("DelayTransaction");

  // You can change the delay time here (e.g., 1800 = 30 minutes)
  const delayInSeconds = 1800;
  const delayContract = await DelayTransaction.deploy(delayInSeconds);

  await delayContract.waitForDeployment();

  console.log(`DelayTransaction deployed to: ${await delayContract.getAddress()}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
