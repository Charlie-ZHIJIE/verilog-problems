# Skid Buffer Specification

## Module Name
`skid_buffer`

## Overview
A configurable ready/valid decoupling component for streaming interfaces. Must support two distinct behavioral modes selected at elaboration time.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DATA_WIDTH` | 64 | Width of data signals |
| `BYPASS` | 1 | Mode selector: `0` or `1` |
| `DEPTH` | 2 | Capacity parameter (interpretation depends on mode) |

## Interface

### Inputs
- `clk`: Clock signal
- `rst_n`: Reset signal (active-low, asynchronous effect)
- `s_data[DATA_WIDTH-1:0]`: Upstream data
- `s_valid`: Upstream valid indicator
- `m_ready`: Downstream ready indicator

### Outputs
- `s_ready`: Upstream ready indicator
- `m_data[DATA_WIDTH-1:0]`: Downstream data
- `m_valid`: Downstream valid indicator

---

## Behavioral Requirements

### Mode Selection (BYPASS Parameter)

The component must exhibit fundamentally different observable behaviors based on the `BYPASS` parameter value.

### Mode A: When BYPASS = 0

**Observable Properties:**

1. **Capacity Behavior**
   - Can accept up to `DEPTH` data transfers before blocking
   - After `DEPTH` consecutive acceptances (without any consumptions), must deassert ready
   - Must resume accepting after at least one consumption

2. **Ordering Behavior**
   - Output data sequence must exactly match input data sequence
   - If input sequence is [A, B, C], output sequence must be [A, B, C]
   - Order preservation must hold regardless of handshake timing

3. **Latency Behavior**
   - Data must not appear on output immediately when input is empty
   - Output must reflect internally stored information
   - Minimum observable delay between input acceptance and output availability

4. **Simultaneity Behavior**
   - Must support concurrent input acceptance and output consumption in same clock cycle
   - During concurrent operations, capacity must not change
   - Data must flow through without accumulation or loss

5. **Capacity Scaling**
   - Behavior must correctly scale with different `DEPTH` values
   - Must work identically for DEPTH=2, DEPTH=4, DEPTH=8, etc.
   - No fixed assumptions about capacity size

### Mode B: When BYPASS = 1

**Observable Properties:**

1. **Latency Behavior**
   - When no data is stored, output must reflect input data immediately
   - Zero combinational delay path must exist from input to output when empty
   - When storing data, output reflects stored information

2. **Capacity Behavior**
   - Can store at most one data item
   - After storing, must block further acceptances until consumption occurs
   - Must resume accepting immediately after consumption

3. **Ordering Behavior**
   - Output sequence must match input sequence
   - First-in must be first-out

4. **State Transitions**
   - Empty → Occupied: When accepting data while downstream is blocked
   - Occupied → Empty: When downstream consumes stored data
   - Empty → Empty: When input flows directly through to output

### Common Requirements (Both Modes)

#### Reset Behavior
- When `rst_n = 0`: Component must become empty immediately (asynchronous)
- All outputs must reach known states
- After reset release, must be ready to accept new data

#### Handshake Protocol
- **Data Transfer Rule**: Data moves when both `valid` and `ready` are high on clock edge
- **Independence Rule**: Valid signals must not depend on ready signals in same direction
- **Stability Rule**: Data and valid must remain stable until transfer completes

#### Ordering Guarantee
- For any input sequence I = [i₁, i₂, i₃, ..., iₙ]
- Output sequence O = [o₁, o₂, o₃, ..., oₙ]
- Must satisfy: I = O (exact order preservation)

#### Completeness Guarantee
- Every accepted data item must eventually appear on output
- No data loss under any valid handshake pattern
- No data duplication under any valid handshake pattern

#### Throughput Goal
- Should sustain one transfer per cycle under favorable conditions
- Must not introduce unnecessary idle cycles
- Mode A: Sustained throughput when downstream is ready
- Mode B: Zero-latency throughput when empty

---

**Document Version**: 7.1 (Pure Behavioral - No Edge Case Hints)  
**Last Updated**: November 2025  
**Focus**: Observable behavior without implementation guidance or edge case enumeration
