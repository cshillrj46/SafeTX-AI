// File: smart_contracts/DelayContract.sol

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DelayTransaction {

    address public owner;
    uint256 public delayTimeInSeconds;

    struct DelayedTx {
        address recipient;
        uint256 amount;
        uint256 releaseTime;
    }

    mapping(address => DelayedTx) public pendingTxs;

    event TransactionQueued(address indexed sender, address indexed recipient, uint256 amount, uint256 releaseTime);
    event TransactionExecuted(address indexed sender, address indexed recipient, uint256 amount);

    constructor(uint256 _delayTimeInSeconds) {
        owner = msg.sender;
        delayTimeInSeconds = _delayTimeInSeconds;
    }

    function queueTransaction(address _recipient) external payable {
        require(msg.value > 0, "Amount must be greater than 0");

        uint256 release = block.timestamp + delayTimeInSeconds;
        pendingTxs[msg.sender] = DelayedTx(_recipient, msg.value, release);

        emit TransactionQueued(msg.sender, _recipient, msg.value, release);
    }

    function executeTransaction() external {
        DelayedTx memory txData = pendingTxs[msg.sender];
        require(block.timestamp >= txData.releaseTime, "Transaction still delayed");
        require(txData.amount > 0, "No transaction queued");

        delete pendingTxs[msg.sender];
        payable(txData.recipient).transfer(txData.amount);

        emit TransactionExecuted(msg.sender, txData.recipient, txData.amount);
    }
}
