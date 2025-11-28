`timescale 1ns/1ps

module skid_buffer #(
    parameter DATA_WIDTH = 64,
    parameter BYPASS     = 1,
    parameter DEPTH      = 2
)(
    input                    clk,
    input                    rst_n,
    input  [DATA_WIDTH-1:0]  s_data,
    input                    s_valid,
    output                   s_ready,
    output [DATA_WIDTH-1:0]  m_data,
    output                   m_valid,
    input                    m_ready
);

    // TODO: Implement parameterized ready/valid decoupling buffer
    //
    // This module's behavior is controlled by the BYPASS and DEPTH parameters.
    // Read docs/Specification.md to understand the required behavior for different parameter values.
    //
    // Requirements:
    // - Behavior must vary based on BYPASS parameter value
    // - Support configurable DEPTH parameter
    // - Asynchronous reset (rst_n, active-low)
    // - Preserve data ordering
    // - Comply with ready/valid handshake protocol

endmodule
