// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract IdentityVerification {
    struct Identity {
        bytes32 faceHash;
        uint256 timestamp;
        bool isRegistered;
    }
    
    mapping(address => Identity) private identities;
    mapping(bytes32 => address) private hashToAddress;
    
    event IdentityRegistered(address indexed user, uint256 timestamp);
    event IdentityVerified(address indexed user, bool success, uint256 timestamp);
    
    // Register a new identity
    function registerIdentity(bytes32 _faceHash) external {
        require(!identities[msg.sender].isRegistered, "Identity already registered");
        require(hashToAddress[_faceHash] == address(0), "Face hash already registered");
        
        identities[msg.sender] = Identity({
            faceHash: _faceHash,
            timestamp: block.timestamp,
            isRegistered: true
        });
        
        hashToAddress[_faceHash] = msg.sender;
        
        emit IdentityRegistered(msg.sender, block.timestamp);
    }
    
    // Verify an identity
    function verifyIdentity(address _user, bytes32 _faceHash) external view returns (bool) {
        require(identities[_user].isRegistered, "Identity not registered");
        
        return identities[_user].faceHash == _faceHash;
    }
    
    // Update an existing identity
    function updateIdentity(bytes32 _oldFaceHash, bytes32 _newFaceHash) external {
        require(identities[msg.sender].isRegistered, "Identity not registered");
        require(identities[msg.sender].faceHash == _oldFaceHash, "Old face hash doesn't match");
        
        // Remove old mapping
        delete hashToAddress[_oldFaceHash];
        
        // Update with new hash
        identities[msg.sender].faceHash = _newFaceHash;
        identities[msg.sender].timestamp = block.timestamp;
        hashToAddress[_newFaceHash] = msg.sender;
    }
    
    // Revoke an identity
    function revokeIdentity() external {
        require(identities[msg.sender].isRegistered, "Identity not registered");
        
        delete hashToAddress[identities[msg.sender].faceHash];
        delete identities[msg.sender];
    }
    
    // Check if an address has a registered identity
    function hasIdentity(address _user) external view returns (bool) {
        return identities[_user].isRegistered;
    }
} 