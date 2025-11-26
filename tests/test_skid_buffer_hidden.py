import os
import random
from pathlib import Path

import pytest
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb_tools.runner import get_runner


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

async def initialize(dut):
    """Common async reset + initial signal setup."""
    dut.s_valid.value = 0
    dut.s_data.value = 0
    dut.m_ready.value = 0
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


def _get_param(dut, name, default=None):
    """Safely read a Verilog parameter (BYPASS / DEPTH) from DUT."""
    try:
        obj = getattr(dut, name)
    except AttributeError:
        return default
    try:
        return int(obj)
    except Exception:
        try:
            return int(obj.value)
        except Exception:
            return default


def get_bypass(dut) -> int:
    """Return 1 if BYPASS mode, 0 if FIFO mode."""
    val = _get_param(dut, "BYPASS", 0)
    return 1 if val else 0


def get_depth(dut) -> int:
    """Return FIFO depth (if meaningful)."""
    return _get_param(dut, "DEPTH", 2)


# -----------------------------------------------------------------------------
# 1. Reset behavior (both modes)
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_reset_flush(dut):
    """
    Async reset must:
    - clear all stored data
    - drop m_valid immediately
    - reopen s_ready (buffer empty)
    """
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    bypass = get_bypass(dut)
    depth  = get_depth(dut)

    await initialize(dut)

    # Force data into the buffer by stalling downstream
    dut.m_ready.value = 0

    if bypass:
        # BYPASS=1: skid can hold exactly 1 beat
        dut.s_valid.value = 1
        dut.s_data.value = 0xAA
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        dut.s_valid.value = 0

        assert int(dut.m_valid.value) == 1, "bypass: skid should hold 1 beat before reset"
        assert int(dut.s_ready.value) == 0, "bypass: skid full => s_ready=0"
    else:
        # BYPASS=0: FIFO can hold DEPTH beats
        # Fill strategy: keep sending until FIFO reports full (s_ready drops)
        dut.s_valid.value = 1
        fill_cnt = 0
        for i in range(depth + 2):  # try a bit more than depth
            dut.s_data.value = 0x100 + i
            # Check s_ready BEFORE the clock edge
            ready_before = int(dut.s_ready.value)
            
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            
            # If s_ready was 1 before clock, data was accepted
            if ready_before == 1:
                fill_cnt += 1
            
            # Check if FIFO is now full (for next iteration)
            if int(dut.s_ready.value) == 0:
                break
                
        dut.s_valid.value = 0

        assert fill_cnt == depth, f"FIFO: expected to fill {depth}, got {fill_cnt}"
        assert int(dut.m_valid.value) == 1, "FIFO should be non-empty before reset"
        assert int(dut.s_ready.value) == 0, "FIFO full => s_ready=0"

    # Async reset
    dut.rst_n.value = 0
    await Timer(1, units="ns")

    assert int(dut.m_valid.value) == 0, "m_valid must drop on async reset"
    assert int(dut.s_ready.value) == 1, "s_ready must be 1 after reset (empty)"

    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.m_valid.value) == 0, "No stray m_valid after reset"


# -----------------------------------------------------------------------------
# 2. Full-throughput stream (downstream always ready)
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_full_throughput_stream(dut):
    """
    Downstream always ready:

    - BYPASS=1: behaves as 0-latency pass-through when skid is empty.
    - BYPASS=0: behaves as FIFO with >=1-cycle latency, but must not drop or reorder.
    """
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    bypass = get_bypass(dut)

    await initialize(dut)
    dut.m_ready.value = 1  # no backpressure

    data_words = [0x10 + i for i in range(8)]
    exp_queue = []
    recv = []

    for word in data_words:
        dut.s_valid.value = 1
        dut.s_data.value = word

        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        # Upstream handshake
        if int(dut.s_valid.value) and int(dut.s_ready.value):
            exp_queue.append(word)

            if bypass:
                # 0-latency: same cycle s_valid&s_ready, m_valid/m_data must match
                assert int(dut.m_valid.value) == 1, "bypass: m_valid must follow s_valid"
                assert int(dut.m_data.value) == word, "bypass: m_data must be 0-latency"

        # Downstream handshake
        if int(dut.m_valid.value) and int(dut.m_ready.value):
            assert exp_queue, "Output beat with empty expected queue"
            got = int(dut.m_data.value)
            exp = exp_queue.pop(0)
            assert got == exp, f"Out-of-order: expected {exp:#x}, got {got:#x}"
            recv.append(got)

    dut.s_valid.value = 0

    # Drain remaining beats
    for _ in range(len(exp_queue) + 8):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.m_valid.value) and int(dut.m_ready.value):
            assert exp_queue, "Unexpected extra beat during drain"
            got = int(dut.m_data.value)
            exp = exp_queue.pop(0)
            assert got == exp
            recv.append(got)
        if not exp_queue:
            break

    assert recv == data_words, "Stream mismatch under full throughput"
    assert not exp_queue, "Expected queue not empty after drain"
    assert int(dut.m_valid.value) == 0, "All beats should be drained"


# -----------------------------------------------------------------------------
# 3. Latency behavior (bypass vs FIFO)
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_latency_mode(dut):
    """
    - BYPASS=1: when empty, can have 0-cycle combinational path (bypass).
    - BYPASS=0: always uses registered output (but may appear as 0-latency in same-cycle handshake).
    
    This test verifies bypass behavior more carefully.
    """
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    bypass = get_bypass(dut)

    await initialize(dut)
    
    if bypass:
        # BYPASS mode: when empty, should have combinational path
        dut.m_ready.value = 1
        dut.s_valid.value = 0
        
        # Start with buffer empty
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.m_valid.value) == 0, "Should be empty"
        
        # Apply data and check if it appears immediately (combinational)
        test_word = 0xDEAD
        dut.s_valid.value = 1
        dut.s_data.value = test_word
        await Timer(1, units="ns")  # No clock edge, just settling time
        
        # In bypass mode with empty buffer, m_data should follow s_data combinationally
        if int(dut.s_ready.value) == 1:
            assert int(dut.m_valid.value) == 1, "bypass: m_valid should follow s_valid when empty"
            assert int(dut.m_data.value) == test_word, "bypass: m_data should be combinational"
    else:
        # FIFO mode: uses registered output, but we just verify it works correctly
        # Don't enforce strict latency requirements as FIFO behavior can vary
        dut.m_ready.value = 1
        dut.s_valid.value = 1
        test_word = 0xBEEF
        dut.s_data.value = test_word
        
        received = False
        for _ in range(10):
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            
            if int(dut.m_valid.value) and int(dut.m_ready.value):
                assert int(dut.m_data.value) == test_word, "FIFO: data mismatch"
                received = True
                break
        
        assert received, "FIFO: data never appeared on output"


# -----------------------------------------------------------------------------
# 4. Alternating backpressure (both modes)
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_alternating_backpressure_preserves_order(dut):
    """Alternating m_ready pattern must preserve ordering."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    await initialize(dut)

    values = [0x200 + i for i in range(6)]
    send_idx = 0
    recv_idx = 0

    for cycle in range(40):
        dut.m_ready.value = 1 if (cycle % 2 == 0) else 0
        drive = send_idx < len(values)

        dut.s_valid.value = 1 if drive else 0
        if drive:
            dut.s_data.value = values[send_idx]

        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        # source side
        if drive and int(dut.s_ready.value):
            send_idx += 1
            if send_idx == len(values):
                dut.s_valid.value = 0

        # sink side
        if int(dut.m_ready.value) and int(dut.m_valid.value):
            assert int(dut.m_data.value) == values[recv_idx], "Ordering violated"
            recv_idx += 1
            if recv_idx == len(values):
                break

    # flush
    dut.m_ready.value = 1
    dut.s_valid.value = 0
    while recv_idx < len(values):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.m_valid.value):
            assert int(dut.m_data.value) == values[recv_idx]
            recv_idx += 1

    assert recv_idx == len(values), "Not all beats observed downstream"


# -----------------------------------------------------------------------------
# 5. Randomized ready/valid stress (both modes)
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_random_handshake_stress(dut):
    """Randomized ready/valid stress with scoreboard (both BYPASS/FIFO)."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    await initialize(dut)

    rng = random.Random(2024)
    total_words = 40
    sent = []
    received = []
    next_word = 0
    driving = False
    current_word = 0

    for _ in range(120):
        dut.m_ready.value = rng.choice([0, 1])

        if not driving and next_word < total_words and rng.random() < 0.7:
            driving = True
            current_word = 0x500 + next_word
            dut.s_valid.value = 1
            dut.s_data.value = current_word

        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        # Source handshake
        if driving and int(dut.s_ready.value):
            sent.append(current_word)
            next_word += 1
            if next_word >= total_words or rng.random() < 0.4:
                driving = False
                dut.s_valid.value = 0
            else:
                current_word = 0x500 + next_word
                dut.s_data.value = current_word

        # Sink handshake
        if int(dut.m_ready.value) and int(dut.m_valid.value):
            received.append(int(dut.m_data.value))

    # Flush remaining data
    dut.s_valid.value = 0
    dut.m_ready.value = 1
    for _ in range(20):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.m_valid.value):
            received.append(int(dut.m_data.value))

    assert received == sent, "Buffer lost/duplicated/reordered data under stress"


# -----------------------------------------------------------------------------
# 6. FIFO-only: fill / drain / wrap-around
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_fifo_fill_drain_wrap(dut):
    """FIFO-only: fill, drain, and exercise wrap-around with continuous flow."""
    if get_bypass(dut):
        # In bypass mode, this test is not applicable - just return success
        return

    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    depth = get_depth(dut)
    await initialize(dut)

    # Use scoreboard approach: track all sent and received data
    sent = []
    received = []
    
    # Phase 1: Fill FIFO with m_ready=0
    dut.m_ready.value = 0
    dut.s_valid.value = 1
    
    fill_data = [0xF00 + i for i in range(depth)]
    for word in fill_data:
        dut.s_data.value = word
        ready_before = int(dut.s_ready.value)
        
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        
        if ready_before:
            sent.append(word)
    
    dut.s_valid.value = 0
    assert len(sent) == depth, f"Should have filled {depth} entries, got {len(sent)}"
    assert int(dut.s_ready.value) == 0, "FIFO should be full"
    assert int(dut.m_valid.value) == 1, "FIFO should have data"
    
    # Phase 2: Enable output and send more data (test wrap-around)
    dut.m_ready.value = 1
    
    extra_data = [0xE00 + i for i in range(depth * 2)]
    send_idx = 0
    
    for _ in range(len(extra_data) + depth + 5):
        # Drive source if we have more to send
        if send_idx < len(extra_data):
            dut.s_valid.value = 1
            dut.s_data.value = extra_data[send_idx]
        else:
            dut.s_valid.value = 0
        
        # Sample before clock
        ready_before = int(dut.s_ready.value)
        valid_before = int(dut.m_valid.value)
        data_before = int(dut.m_data.value) if valid_before else None
        
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        
        # Check source handshake
        if send_idx < len(extra_data) and ready_before and int(dut.s_valid.value or 1):
            sent.append(extra_data[send_idx])
            send_idx += 1
        
        # Check sink handshake
        if valid_before and int(dut.m_ready.value):
            received.append(data_before)
        
        # Stop if all data sent and received
        if send_idx >= len(extra_data) and len(received) >= len(sent):
            break
    
    # Verify ordering
    assert len(received) == len(sent), f"Lost data: sent {len(sent)}, received {len(received)}"
    for i, (exp, got) in enumerate(zip(sent, received)):
        assert got == exp, f"Mismatch at position {i}: expected 0x{exp:x}, got 0x{got:x}"


# -----------------------------------------------------------------------------
# Pytest wrapper: 在这里用 parameters 切 BYPASS/DEPTH
# -----------------------------------------------------------------------------

def test_skid_buffer_all_configs():
    """
    Run the same cocotb test module against multiple BYPASS/DEPTH configs.

    - BYPASS=0, DEPTH=2  (small FIFO)
    - BYPASS=0, DEPTH=4  (deeper FIFO)
    - BYPASS=1, DEPTH=2  (bypass+skid)
    """
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "sources/skid_buffer.sv"]

    configs = [
        {"BYPASS": 0, "DEPTH": 2},
        {"BYPASS": 0, "DEPTH": 4},
        {"BYPASS": 1, "DEPTH": 2},
    ]

    for cfg in configs:
        cfg_tag = "_".join(f"{k}{v}" for k, v in cfg.items())

        runner = get_runner(sim)
        runner.build(
            sources=sources,
            hdl_toplevel="skid_buffer",   # 顶层就是你的 skid_buffer
            parameters=cfg,               # ★ 这里就是切 BYPASS/DEPTH 的地方
            build_dir=str(proj_path / f"sim_build_{cfg_tag}"),
            always=True,
        )
        runner.test(
            hdl_toplevel="skid_buffer",
            test_module="test_skid_buffer_hidden",
        )
