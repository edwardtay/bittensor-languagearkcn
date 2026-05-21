// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title  LanguageArk Speaker DAO
/// @notice On-chain 2-of-3 attestation + stake registry for native-speaker
///         validators. The Python validator queries `isRegistered` and
///         `recordVote` here instead of trusting an off-chain JSON shim.
///
///         In production this would deploy to the Subtensor EVM precompile
///         space and use the native staking precompile (0x...0805). For the
///         demo we deploy to a local anvil node and stake in the native gas
///         token.
contract SpeakerDAO {
    address public immutable owner;
    uint256 public immutable minStake;

    struct Speaker {
        address addr;
        bytes32 lang;
        uint256 stake;
        uint8 attestationCount;
        bool slashed;
    }

    // speaker-address ⇒ lang ⇒ record
    mapping(address => mapping(bytes32 => Speaker)) public speakers;
    // (speaker, lang, attester) ⇒ already attested?
    mapping(bytes32 => bool) public hasAttested;

    // (miner-uid, lang) ⇒ rating  (Glicko-2 rating × 1e6, default 1500e6)
    mapping(bytes32 => uint256) public minerRating;

    event SpeakerStaked(address indexed speaker, bytes32 indexed lang, uint256 stake);
    event Attested(address indexed speaker, bytes32 indexed lang, address indexed attester, uint8 count);
    event Slashed(address indexed speaker, bytes32 indexed lang, uint256 amount);
    event VoteRecorded(
        address indexed speaker,
        bytes32 indexed lang,
        uint64 minerA,
        uint64 minerB,
        uint64 winner
    );

    constructor(uint256 _minStake) {
        owner = msg.sender;
        minStake = _minStake;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    /// @notice Stake to register as a candidate speaker for `lang`.
    ///         Caller must subsequently receive ≥2 distinct attestations.
    function stake(bytes32 lang) external payable {
        require(msg.value >= minStake, "stake below minStake");
        Speaker storage s = speakers[msg.sender][lang];
        require(s.addr == address(0), "already staked for this lang");
        speakers[msg.sender][lang] = Speaker({
            addr: msg.sender,
            lang: lang,
            stake: msg.value,
            attestationCount: 0,
            slashed: false
        });
        emit SpeakerStaked(msg.sender, lang, msg.value);
    }

    /// @notice Attest that `speaker` is a genuine native speaker of `lang`.
    ///         Each attester address can only count once per (speaker, lang).
    function attest(address speaker, bytes32 lang) external {
        Speaker storage s = speakers[speaker][lang];
        require(s.addr != address(0), "speaker has not staked");
        require(!s.slashed, "speaker slashed");
        require(msg.sender != speaker, "self-attest forbidden");
        bytes32 key = keccak256(abi.encodePacked(speaker, lang, msg.sender));
        require(!hasAttested[key], "already attested");
        hasAttested[key] = true;
        s.attestationCount += 1;
        emit Attested(speaker, lang, msg.sender, s.attestationCount);
    }

    /// @notice True iff `speaker` has ≥2 distinct attestations and is not slashed.
    function isRegistered(address speaker, bytes32 lang) public view returns (bool) {
        Speaker storage s = speakers[speaker][lang];
        return s.addr != address(0) && !s.slashed && s.attestationCount >= 2;
    }

    /// @notice Owner can slash a speaker proven to be fraudulent. Burns stake.
    function slash(address speaker, bytes32 lang) external onlyOwner {
        Speaker storage s = speakers[speaker][lang];
        require(s.addr != address(0), "no such speaker");
        require(!s.slashed, "already slashed");
        s.slashed = true;
        uint256 amt = s.stake;
        s.stake = 0;
        emit Slashed(speaker, lang, amt);
        // burn — send to dead address
        (bool ok, ) = address(0xdead).call{value: amt}("");
        require(ok, "burn failed");
    }

    /// @notice Registered speakers record pairwise comparisons. We only store
    ///         the event + a tiny Elo summary so the contract stays cheap;
    ///         the off-chain validator does the Glicko-2 math and writes the
    ///         final rating back via `setRating` if it has the speaker key.
    function recordVote(bytes32 lang, uint64 minerA, uint64 minerB, uint64 winner) external {
        require(isRegistered(msg.sender, lang), "not a registered speaker");
        require(minerA != minerB, "minerA == minerB");
        require(winner == minerA || winner == minerB || winner == 0, "winner must be A, B, or 0 (draw)");
        emit VoteRecorded(msg.sender, lang, minerA, minerB, winner);
    }

    /// @notice Off-chain Glicko-2 update is written back here so dApps can read it.
    ///         Only the contract owner (validator-coordinator) may write.
    function setRating(uint64 minerUid, bytes32 lang, uint256 rating1e6) external onlyOwner {
        bytes32 key = keccak256(abi.encodePacked(minerUid, lang));
        minerRating[key] = rating1e6;
    }

    function getRating(uint64 minerUid, bytes32 lang) external view returns (uint256) {
        bytes32 key = keccak256(abi.encodePacked(minerUid, lang));
        uint256 r = minerRating[key];
        return r == 0 ? 1500 * 1e6 : r;
    }
}
