// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import {SpeakerDAO} from "../src/SpeakerDAO.sol";

contract SpeakerDAOTest is Test {
    SpeakerDAO dao;
    address owner = address(0xA1);
    address speaker = address(0xB0);
    address attA = address(0xC1);
    address attB = address(0xC2);
    address attC = address(0xC3);
    bytes32 constant NAN = bytes32("nan");

    function setUp() public {
        vm.prank(owner);
        dao = new SpeakerDAO(100 ether);
        vm.deal(speaker, 1000 ether);
        vm.deal(attA, 1 ether);
        vm.deal(attB, 1 ether);
    }

    function test_stake_emits_and_requires_min() public {
        vm.prank(speaker);
        vm.expectRevert(bytes("stake below minStake"));
        dao.stake{value: 50 ether}(NAN);

        vm.prank(speaker);
        dao.stake{value: 100 ether}(NAN);
        assertFalse(dao.isRegistered(speaker, NAN));
    }

    function test_two_of_three_attestation_registers() public {
        vm.prank(speaker);
        dao.stake{value: 100 ether}(NAN);

        vm.prank(attA);
        dao.attest(speaker, NAN);
        assertFalse(dao.isRegistered(speaker, NAN));

        vm.prank(attB);
        dao.attest(speaker, NAN);
        assertTrue(dao.isRegistered(speaker, NAN));
    }

    function test_self_attest_forbidden() public {
        vm.prank(speaker);
        dao.stake{value: 100 ether}(NAN);
        vm.prank(speaker);
        vm.expectRevert(bytes("self-attest forbidden"));
        dao.attest(speaker, NAN);
    }

    function test_double_attest_blocked() public {
        vm.prank(speaker);
        dao.stake{value: 100 ether}(NAN);
        vm.prank(attA);
        dao.attest(speaker, NAN);
        vm.prank(attA);
        vm.expectRevert(bytes("already attested"));
        dao.attest(speaker, NAN);
    }

    function test_slash_burns_stake() public {
        vm.prank(speaker);
        dao.stake{value: 100 ether}(NAN);
        vm.prank(attA);
        dao.attest(speaker, NAN);
        vm.prank(attB);
        dao.attest(speaker, NAN);

        uint256 deadBefore = address(0xdead).balance;
        vm.prank(owner);
        dao.slash(speaker, NAN);

        assertFalse(dao.isRegistered(speaker, NAN));
        assertEq(address(0xdead).balance - deadBefore, 100 ether);
    }

    function test_record_vote_requires_registration() public {
        vm.prank(speaker);
        dao.stake{value: 100 ether}(NAN);

        vm.prank(speaker);
        vm.expectRevert(bytes("not a registered speaker"));
        dao.recordVote(NAN, 1, 2, 1);

        vm.prank(attA);
        dao.attest(speaker, NAN);
        vm.prank(attB);
        dao.attest(speaker, NAN);

        vm.prank(speaker);
        dao.recordVote(NAN, 1, 2, 1);
    }

    function test_record_vote_validates_winner() public {
        vm.prank(speaker);
        dao.stake{value: 100 ether}(NAN);
        vm.prank(attA);
        dao.attest(speaker, NAN);
        vm.prank(attB);
        dao.attest(speaker, NAN);

        vm.prank(speaker);
        vm.expectRevert(bytes("minerA == minerB"));
        dao.recordVote(NAN, 5, 5, 5);

        vm.prank(speaker);
        vm.expectRevert(bytes("winner must be A, B, or 0 (draw)"));
        dao.recordVote(NAN, 1, 2, 99);
    }

    function test_rating_default_and_set() public {
        assertEq(dao.getRating(42, NAN), 1500 * 1e6);
        vm.prank(owner);
        dao.setRating(42, NAN, 1620 * 1e6);
        assertEq(dao.getRating(42, NAN), 1620 * 1e6);
    }
}
