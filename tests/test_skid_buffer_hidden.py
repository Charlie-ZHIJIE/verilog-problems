import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def initialize(dut):
    dut.s_valid.value = 0
    dut.s_data.value = 0
    dut.m_ready.value = 0
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


@cocotb.test()
async def test_reset_flush(dut):
    """Buffers clear immediately on asynchronous reset."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await initialize(dut)

    dut.m_ready.value = 0
    for word in [0xAA, 0x55]:
        dut.s_valid.value = 1
        dut.s_data.value = word
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
    dut.s_valid.value = 0

    assert int(dut.m_valid.value) == 1, "front buffer should hold data before reset"
    assert int(dut.s_ready.value) == 0, "buffer should report full when two beats stored"

    dut.rst_n.value = 0
    await Timer(1, units="ns")
    assert int(dut.m_valid.value) == 0, "m_valid must drop immediately on reset"
    assert int(dut.s_ready.value) == 1, "reset should reopen space for upstream"

    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.m_valid.value) == 0


@cocotb.test()
async def test_full_throughput_stream(dut):
    """Downstream always ready: module behaves like pass-through."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await initialize(dut)
    dut.m_ready.value = 1

    data_words = [0x10 + i for i in range(8)]
    for word in data_words:
        dut.s_valid.value = 1
        dut.s_data.value = word
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.m_valid.value) == 1, "m_valid must stay asserted during streaming"
        assert int(dut.m_data.value) == word, f"Out of order: expected {word:#x}"
    dut.s_valid.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.m_valid.value) == 0, "All beats should be drained"


@cocotb.test()
async def test_alternating_backpressure_preserves_order(dut):
    """Alternating ready/valid still preserves ordering."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    await initialize(dut)

    values = [0x100 + i for i in range(6)]
    send_idx = 0
    recv_idx = 0

    for cycle in range(24):
        dut.m_ready.value = 1 if (cycle % 2 == 0) else 0
        drive = send_idx < len(values)
        dut.s_valid.value = 1 if drive else 0
        if drive:
            dut.s_data.value = values[send_idx]

        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        if drive and int(dut.s_ready.value):
            send_idx += 1
            if send_idx == len(values):
                dut.s_valid.value = 0

        if int(dut.m_ready.value) and int(dut.m_valid.value):
            assert int(dut.m_data.value) == values[recv_idx], "Ordering violated"
            recv_idx += 1
            if recv_idx == len(values):
                break

    # Flush any remaining beats
    dut.m_ready.value = 1
    dut.s_valid.value = 0
    while recv_idx < len(values):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.m_valid.value):
            assert int(dut.m_data.value) == values[recv_idx]
            recv_idx += 1

    assert recv_idx == len(values), "Not all beats were observed downstream"


@cocotb.test()
async def test_random_handshake_stress(dut):
    """Randomized ready/valid stress with scoreboard comparison."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await initialize(dut)

    rng = random.Random(2024)
    total_words = 20
    sent = []
    received = []
    next_word = 0
    driving = False
    current_word = 0

    for _ in range(80):
        dut.m_ready.value = rng.choice([0, 1])

        if not driving and next_word < total_words and rng.random() < 0.7:
            driving = True
            current_word = 0x500 + next_word
            dut.s_valid.value = 1
            dut.s_data.value = current_word

        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        if driving and int(dut.s_ready.value):
            sent.append(current_word)
            next_word += 1
            if next_word >= total_words or rng.random() < 0.4:
                driving = False
                dut.s_valid.value = 0
            else:
                current_word = 0x500 + next_word
                dut.s_data.value = current_word

        if int(dut.m_ready.value) and int(dut.m_valid.value):
            received.append(int(dut.m_data.value))

    # Flush remaining data
    dut.s_valid.value = 0
    dut.m_ready.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.m_valid.value):
            received.append(int(dut.m_data.value))

    assert received == sent, "Skid buffer lost or reordered data under stress"


def test_skid_buffer_hidden_runner():
    """Pytest wrapper for cocotb tests"""
    import os
    from pathlib import Path
    from cocotb_tools.runner import get_runner

    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "sources/skid_buffer.sv"]
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="skid_buffer",
        always=True,
    )
    runner.test(
        hdl_toplevel="skid_buffer",
        test_module="test_skid_buffer_hidden"
    )
