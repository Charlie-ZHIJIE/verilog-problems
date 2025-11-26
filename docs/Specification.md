# Skid Buffer Specification (Industry Standard)

## Module Name
`skid_buffer`

## Overview
A parameterized, dual-mode ready/valid decoupling buffer for AXI-Stream interfaces. Supports two distinct operating modes optimized for different design priorities: deep buffering with registered output, or minimal latency with combinational bypass.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DATA_WIDTH` | 64 | Width of the data path in bits |
| `BYPASS` | 0 | Operating mode: `0` = FIFO mode, `1` = Bypass mode |
| `DEPTH` | 2 | Buffer depth in entries (only used when `BYPASS=0`) |

## Interface

### Inputs
- **`clk`**: System clock. All synchronous operations occur on the rising edge.
- **`rst_n`**: Asynchronous reset, **active low**. Clears all stored data immediately when asserted.
- **`s_data[DATA_WIDTH-1:0]`**: Upstream data payload.
- **`s_valid`**: Upstream valid signal. High indicates `s_data` contains a valid beat.
- **`m_ready`**: Downstream ready signal. High indicates the consumer can accept data.

### Outputs
- **`s_ready`**: Upstream ready signal. High when the buffer can accept new data.
- **`m_data[DATA_WIDTH-1:0]`**: Downstream data payload.
- **`m_valid`**: Downstream valid signal. High indicates `m_data` contains valid data.

## Operating Modes

### Mode 1: FIFO (BYPASS=0)

#### Behavior
- Implements a buffering structure with `DEPTH` entries
- Maintains strict **FIFO ordering**: first data in is first data out
- Output is **registered** (data comes from internal storage)
- Can buffer up to `DEPTH` data beats before asserting back-pressure

#### Capacity and Flow Control
- **Full condition**: When buffer contains `DEPTH` entries → `s_ready = 0`
- **Empty condition**: When buffer contains 0 entries → `m_valid = 0`
- **Normal operation**: Accepts data when not full, outputs data when not empty

#### Critical Requirements
1. **Buffer boundaries**: Must correctly handle wrap-around at buffer limits
2. **Occupancy tracking**: Must accurately track how many entries are stored
3. **Simultaneous operations**: When accepting new data AND outputting old data in the same cycle:
   - Both operations must complete successfully
   - FIFO order must be preserved
   - No data loss or duplication

#### Latency
- Data passes through internal storage (registers)
- Introduces at least 1 cycle of latency

#### Use Cases
- Designs requiring deep buffering
- High-frequency implementations where timing closure is critical
- When registered outputs are preferred for timing

---

### Mode 2: Bypass (BYPASS=1)

#### Behavior
- Implements a single-entry buffer with combinational bypass capability
- When buffer is **empty**: data can pass through **combinationally** (0-cycle latency)
- When buffer is **occupied**: behaves as a 1-entry registered buffer
- Optimized for minimal latency in lightly-loaded scenarios

#### Capacity and Flow Control
- **Maximum capacity**: 1 data beat
- **Empty state**: Data bypasses directly from input to output (combinational path)
- **Full state**: Must wait for downstream to consume before accepting new data

#### Critical Requirements
1. **Bypass path**: When empty, `m_data` must reflect `s_data` combinationally
2. **Capture logic**: When data arrives but downstream is not ready, must capture into internal register
3. **Transition handling**: Correctly manage state transitions between empty and occupied

#### Latency
- **Best case**: 0 cycles (combinational bypass when empty)
- **Worst case**: 1 cycle (when internal register is occupied)

#### Use Cases
- Low-latency pipeline stages
- Designs where 0-cycle latency is beneficial
- When buffer depth of 1 is sufficient

---

## Common Requirements (Both Modes)

### Reset Behavior
- **Type**: Asynchronous (takes effect immediately when `rst_n = 0`)
- **Effect**: 
  - All valid flags must be cleared
  - Buffer must be marked as empty
  - Ready signals must be asserted appropriately
- **Recovery**: Normal operation resumes on next rising clock edge after `rst_n = 1`

### FIFO Ordering Guarantee
- **Strict ordering**: Data beats must exit in the exact same order they entered
- **No reordering**: Even under complex ready/valid handshake patterns
- **No duplication**: Each data beat must appear exactly once on output
- **No loss**: When `s_ready = 1` and `s_valid = 1`, that data beat must eventually appear on output

### Ready/Valid Handshake Protocol
- **Data transfer occurs** when: `valid = 1` AND `ready = 1` on same clock edge
- **Valid independence**: `s_valid` must not depend on `s_ready` (upstream cannot wait for ready before asserting valid)
- **Data stability**: Data must remain stable while valid is high until transfer completes
- **Back-pressure**: When buffer is full, `s_ready = 0` prevents further data acceptance

### Throughput
- **Target**: 1 data beat per cycle when not stalled
- **Sustained throughput**: Achievable when `m_ready = 1` continuously
- **Degradation**: Only when upstream provides no data (`s_valid = 0`) or buffer is full

---

## Test Coverage

The design will be verified with the following test suite:

### Core Functional Tests (All Configurations)

1. **Reset Verification**
   - Fill buffer to capacity
   - Assert asynchronous reset
   - Verify immediate clearing of all valid flags
   - Verify buffer marked as empty

2. **Full Throughput Stream**
   - Downstream continuously ready (`m_ready = 1`)
   - Send burst of data
   - Verify all data arrives in correct order

3. **Latency Verification**
   - FIFO mode: Verify registered output behavior
   - Bypass mode: Verify 0-cycle latency when empty

4. **Alternating Back-pressure**
   - Toggle `m_ready` between 0 and 1
   - Verify data ordering is preserved
   - Test simultaneous enqueue and dequeue scenarios

5. **Random Handshake Stress Test**
   - Random patterns for `s_valid` and `m_ready`
   - Verify all sent data is received in order
   - Scoreboard-based verification

### FIFO-Specific Tests (BYPASS=0 only)

6. **Fill, Drain, and Wrap**
   - Fill buffer to `DEPTH` entries
   - Verify full condition and back-pressure
   - Enable output while continuing to send
   - Verify correct wrap-around behavior
   - Test simultaneous operations at boundaries

---

## Verification Summary

The design will be tested with **3 configurations**:
- `BYPASS=0, DEPTH=2` (2-entry FIFO)
- `BYPASS=0, DEPTH=4` (4-entry FIFO)  
- `BYPASS=1, DEPTH=2` (Bypass mode, DEPTH ignored)

**Total**: 6 tests × 3 configurations = **18 test cases**

All tests must pass for the design to be considered correct.

---

**Document Version**: 4.0 (Pure Requirements)  
**Last Updated**: November 2025  
**Focus**: Behavioral requirements only, no implementation guidance  
**Test Suite**: `tests/test_skid_buffer_hidden.py` (18 test cases across 3 configurations)
