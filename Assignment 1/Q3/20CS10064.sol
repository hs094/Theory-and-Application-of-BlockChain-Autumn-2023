// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TicketBooking {
    constructor(uint _quota, uint _price) {
       owner = msg.sender;
       numTicketsSold = 0;
       quota = _quota;
       price = _price;
    }

    function buyTicket(string memory email, uint numTickets) public payable soldOut {
        ...
    }

    modifier soldOut() {
       require(numTicketsSold < quota, "All tickets have beensold"); _;
    }

    modifier onlyOwner() { 
        ...
    }

    function withdrawFunds() public onlyOwner { 
        ...
    }

    function refundTicket(address buyer) public onlyOwner { 
        ...
    }
}