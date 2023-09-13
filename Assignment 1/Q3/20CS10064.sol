// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Group Members:
//      20CS10064 - Subhajyoti Halder
//      20CS30019 - Gitanjali Gupta
//      20CS30023 - Hardik Pravin Soni
//      20CS30069 - Priyanshi Dixit

contract TicketBooking {
    struct Buyer {
        uint totalPrice;
        uint numTickets;
        string email;
    }
    
    address public owner;
    uint public numTicketsSold;
    uint public maxOccupancy;
    uint public price;

    mapping(address => Buyer) public buyersPaid;

    constructor(uint _quota, uint _price) {
        owner = msg.sender;
        numTicketsSold = 0;
        // quota = _quota;
        maxOccupancy = _quota;
        price = _price;
    }

    modifier soldOut() {
       require(numTicketsSold < maxOccupancy, "All tickets have been sold"); _;
    }

    modifier onlyOwner() { 
        require(msg.sender == owner, "Only the owner can call this function"); _;
    }

    function buyTicket(string memory email, uint numTickets) public payable soldOut {
        require(numTickets > 0, "Number of tickets must be greater than 0");
        require(numTicketsSold + numTickets <= maxOccupancy, "Not enough tickets available");

        Buyer storage buyer = buyersPaid[msg.sender];

        if (buyer.numTickets == 0) {
            buyer.email = email;
        }

        buyer.numTickets += numTickets;
        buyer.totalPrice += msg.value;

        numTicketsSold += numTickets;

        // Refund excess payment
        if (msg.value > (numTickets * price)) {
            payable(msg.sender).transfer(msg.value - (numTickets * price));
        }
    }

    function refundTicket(address buyer) public onlyOwner { 
        Buyer storage B = buyersPaid[buyer];
        require(B.numTickets > 0, "Buyer has not purchased any tickets");

        uint refundAmount = B.totalPrice;
        B.totalPrice = 0;
        B.numTickets = 0;

        payable(buyer).transfer(refundAmount);
    }

    function withdrawFunds() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    function getBuyerAmountPaid(address buyer) public view returns (uint) {
        return buyersPaid[buyer].totalPrice;
    }

    function kill() public onlyOwner {
        selfdestruct(payable(owner));
    }
}