`timescale 1ns/1ps

module skid_buffer #(
    parameter DATA_WIDTH = 64,
    parameter BYPASS     = 0,  // 1: skid buffer with bypass, 0: simple FIFO (no bypass)
    parameter DEPTH      = 2   // only for BYPASS=0
)(
    input                    clk,
    input                    rst_n,         // active-low async reset
    input  [DATA_WIDTH-1:0]  s_data,
    input                    s_valid,
    output                   s_ready,
    output [DATA_WIDTH-1:0]  m_data,
    output                   m_valid,
    input                    m_ready
);

    // TODO: Implement parameterized skid buffer logic
    // 
    // Two modes supported:
    // 
    // BYPASS = 0 (FIFO mode):
    //   - Implement circular FIFO with DEPTH entries
    //   - Use read_ptr, write_ptr, and count registers
    //   - Handle four cases: {do_dequeue, do_enqueue} = 00, 01, 10, 11
    //   - Case 11 is critical: simultaneous read and write
    // 
    // BYPASS = 1 (Bypass mode):
    //   - Implement single skid register with bypass mux
    //   - When empty: 0-cycle latency (m_data = s_data combinationally)
    //   - When full: output from skid register
    //
    // Common requirements:
    //   - Asynchronous reset (rst_n=0) clears all buffers immediately
    //   - Preserve strict FIFO ordering (no data loss or duplication)
    //   - Back-pressure: s_ready=0 when buffer is full
    //
    // Implementation structure:
    //   Use SystemVerilog generate blocks to separate the two architectures:
    //   generate
    //     if (BYPASS) begin : g_bypass
    //       // Bypass mode implementation
    //     end else begin : g_fifo
    //       // FIFO mode implementation
    //     end
    //   endgenerate

endmodule
