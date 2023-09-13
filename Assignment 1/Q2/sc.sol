// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Smart Contract Address: 
//      0xF98bFe8bf2FfFAa32652fF8823Bba6714c79eDd4

contract AddressRollMap {
    mapping(address => string) public roll;
    function update(string calldata newRoll) public{
        roll[msg.sender] = newRoll;
    }

    function get(address addr) public view returns (string memory){
        return roll[addr];
    }

    function getmine() public view returns (string memory) {
        return roll[msg.sender]; 
    }
}