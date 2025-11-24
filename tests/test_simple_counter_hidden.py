import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_reset(dut):
    """Test synchronous reset"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize - set count to non-zero first
    dut.rst.value = 0
    dut.ena.value = 1  # Enable counting
    dut.load.value = 0
    dut.load_value.value = 0
    
    # Count up a few times to set count to non-zero
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Now test reset - count should go to 0
    dut.ena.value = 0
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.count.value == 0, f"Reset failed: expected 0, got {dut.count.value}"
    
    # Verify reset持续生效
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.count.value == 0, f"Reset持续失败: expected 0, got {dut.count.value}"

@cocotb.test()
async def test_count(dut):
    """Test counting functionality"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset to known state
    dut.rst.value = 1
    dut.ena.value = 0
    dut.load.value = 0
    dut.load_value.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Disable reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Enable counting - this should increment
    dut.ena.value = 1
    for i in range(1, 6):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert dut.count.value == i, f"Count error: expected {i}, got {dut.count.value}"

@cocotb.test()
async def test_load(dut):
    """Test load functionality"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.ena.value = 0
    dut.load.value = 0
    dut.load_value.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst.value = 0
    
    # Load value 42
    dut.load.value = 1
    dut.load_value.value = 42
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.count.value == 42, f"Load failed: expected 42, got {dut.count.value}"
    
    # Disable load, count should stay at 42
    dut.load.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.count.value == 42, f"Hold failed: expected 42, got {dut.count.value}"

@cocotb.test()
async def test_priority(dut):
    """Test priority: load > rst > ena"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset first
    dut.rst.value = 1
    dut.ena.value = 0
    dut.load.value = 0
    dut.load_value.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst.value = 0
    
    # Test: load has priority over ena
    dut.load.value = 1
    dut.load_value.value = 100
    dut.ena.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.count.value == 100, f"Load priority failed: expected 100, got {dut.count.value}"
    
    # Test: load has priority over rst
    dut.load.value = 1
    dut.load_value.value = 200
    dut.rst.value = 1
    dut.ena.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.count.value == 200, f"Load over rst failed: expected 200, got {dut.count.value}"

def test_simple_counter_hidden_runner():
    """Pytest wrapper for cocotb tests"""
    import os
    from pathlib import Path
    from cocotb_tools.runner import get_runner

    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "sources/simple_counter.sv"]
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="simple_counter",
        always=True,
    )
    runner.test(
        hdl_toplevel="simple_counter",
        test_module="test_simple_counter_hidden"
    )
