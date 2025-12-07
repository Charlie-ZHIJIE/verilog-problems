# RX MAC Stream Module Specification

## 1. Overview

The `rx_mac_stream` module is an Ethernet MAC receive path component that:
1. Receives streaming data from a PHY/PCS layer via AXI-Stream interface
2. Computes CRC-32 on the payload using a `slicing_crc` submodule
3. Verifies the computed CRC against the received FCS (Frame Check Sequence)
4. Passes data through with a CRC status indicator

This is a **hierarchical design** that requires implementing both modules.

## 2. Module Interfaces

### 2.1 rx_mac_stream (Top-Level Module)

```systemverilog
module rx_mac_stream #(
    parameter int DATA_WIDTH   = 32,
    localparam int DATA_NBYTES = DATA_WIDTH / 8
) (
    input  wire                     i_clk,
    input  wire                     i_reset,
    input  wire [DATA_WIDTH-1:0]    s_axis_tdata,
    input  wire [DATA_NBYTES-1:0]   s_axis_tkeep,
    input  wire                     s_axis_tvalid,
    input  wire                     s_axis_tlast,
    input  wire [31:0]              i_rx_fcs,
    input  wire                     i_rx_fcs_valid,
    output logic [DATA_WIDTH-1:0]   m_axis_tdata,
    output logic [DATA_NBYTES-1:0]  m_axis_tkeep,
    output logic                    m_axis_tvalid,
    output logic                    m_axis_tlast,
    output logic                    m_axis_tuser
);
```

### 2.2 slicing_crc (CRC Calculation Module)

```systemverilog
module slicing_crc #(
    parameter int SLICE_LENGTH = 8,
    parameter int INITIAL_CRC = 32'hFFFFFFFF,
    parameter bit INVERT_OUTPUT = 1,
    parameter bit REGISTER_OUTPUT = 1,
    localparam int MAX_SLICE_LENGTH = 16
) (
    input wire i_clk,
    input wire i_reset,
    input wire [8*SLICE_LENGTH-1:0] i_data,
    input wire [SLICE_LENGTH-1:0] i_valid,
    output wire [31:0] o_crc
);
```

**CRC Tables**: A pre-computed lookup table file `crc_tables.mem` is provided. It contains `logic [31:0] crc_tables [16][256]` for the slicing-by-N algorithm using polynomial `0x04C11DB7` (Ethernet CRC-32).

## 3. Behavioral Requirements

### 3.1 rx_mac_stream Behavior

**State Machine**: Use a 2-state FSM (IDLE, DATA) to manage frame reception.

**Data Passthrough**: AXI-Stream signals (`tdata`, `tkeep`, `tvalid`, `tlast`) must be passed from input to output with appropriate timing.

**CRC Verification**:
- Instantiate `slicing_crc` to compute CRC-32 on incoming data
- On the last beat of a frame (`tlast` asserted):
  - Compare computed CRC with `i_rx_fcs`
  - Set `m_axis_tuser = 1` if CRC matches AND `i_rx_fcs_valid = 1`
  - Set `m_axis_tuser = 0` if CRC mismatch OR `i_rx_fcs_valid = 0`

**Frame Boundaries**: CRC calculation must reset between frames to prepare for the next packet.

### 3.2 slicing_crc Behavior

**Algorithm**: Implement the Slicing-by-N CRC calculation algorithm (Sarwate, 1988) using table lookups.

**CRC Tables**: Read the provided `crc_tables.mem` file using `$readmemh`. The table structure is `[16][256]` where:
- First dimension: Related to byte position in the slice
- Second dimension: Indexed by byte value

**State Management**:
- Maintain internal CRC state that accumulates across multiple bytes
- Reset to `INITIAL_CRC` when `i_reset` is asserted
- Update CRC state each cycle when valid data is present

**Byte Masking**: The `i_valid` signal indicates which bytes in `i_data` are valid. Only valid bytes contribute to the CRC calculation.

**Output Modes**:
- `REGISTER_OUTPUT = 1`: Output is registered (1 cycle delay)
- `REGISTER_OUTPUT = 0`: Output is combinational (no delay)
- `INVERT_OUTPUT = 1`: Final output is bitwise inverted

## 4. Special Cases

### Single-Beat Frames
A frame may consist of only one beat (both `tvalid` and `tlast` asserted simultaneously). The design must handle CRC calculation and verification in this case.

### Partial Bytes
The last beat of a frame may have `tkeep` indicating only some bytes are valid (e.g., `4'b0011` for 2 bytes). CRC must only include valid bytes.

### Multiple Frames
When processing consecutive frames, ensure CRC state is properly reset between frames.

### Missing FCS
When `i_rx_fcs_valid = 0`, the design must report an error regardless of the computed CRC value.

## 5. CRC-32 Algorithm Background

The Slicing-by-N algorithm is an optimization of the standard CRC calculation that processes multiple bytes in parallel using lookup tables. 

**Key Concept**: Instead of processing bits sequentially, pre-compute partial CRC results for all possible byte values and combine them using XOR operations.

**Standard Parameters for Ethernet**:
- Polynomial: 0x04C11DB7 (CRC-32-IEEE)
- Initial value: 0xFFFFFFFF
- Final XOR: 0xFFFFFFFF (invert output)

For detailed algorithm explanation and examples, refer to Sarwate (1988) or standard CRC-32 references.

## 6. Timing Considerations

The design should maintain proper timing alignment between data beats and CRC results. Consider whether CRC output should be combinational or registered based on when comparison needs to occur.

## 7. Test Scenarios

Your implementation will be validated against various test cases including:
- Single and multi-beat frames
- Frames with correct and incorrect CRC
- Partial bytes on last beat
- Back-to-back frames with no idle cycles
- FCS validity edge cases
