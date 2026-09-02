// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ContentVerifier
 * @notice Minimal registry for proving that a discovered content fingerprint
 *         was registered on-chain at a particular time.
 *
 * Important: the contract stores a fingerprint and reference. It does not
 * prove that the referenced person is the identity claimed by the content.
 */
contract ContentVerifier {
    struct Record {
        string sourceUrl;
        uint64 timestamp;
        address submitter;
    }

    mapping(bytes32 => Record) private records;

    event ContentRegistered(
        bytes32 indexed contentHash,
        string sourceUrl,
        uint64 timestamp,
        address indexed submitter
    );

    function registerContent(bytes32 contentHash, string calldata sourceUrl) external {
        require(contentHash != bytes32(0), "empty hash");
        require(bytes(sourceUrl).length > 0, "empty source");
        require(records[contentHash].timestamp == 0, "already registered");

        uint64 ts = uint64(block.timestamp);
        records[contentHash] = Record({
            sourceUrl: sourceUrl,
            timestamp: ts,
            submitter: msg.sender
        });

        emit ContentRegistered(contentHash, sourceUrl, ts, msg.sender);
    }

    function verifyContent(bytes32 contentHash) external view returns (bool) {
        return records[contentHash].timestamp != 0;
    }

    function getRecord(bytes32 contentHash)
        external
        view
        returns (string memory sourceUrl, uint64 timestamp, address submitter)
    {
        Record memory r = records[contentHash];
        return (r.sourceUrl, r.timestamp, r.submitter);
    }
}
