`timescale 1ns/1ps
`default_nettype none

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

    // TODO: Implement the RX MAC Stream module
    //
    // Requirements:
    // 1. State Machine:
    //    - IDLE state: Wait for s_axis_tvalid to start receiving
    //    - DATA state: Pass through data and compute CRC
    //
    // 2. CRC Verification:
    //    - Instantiate the slicing_crc submodule to compute CRC
    //    - Compare computed CRC with i_rx_fcs on tlast
    //    - Report result via m_axis_tuser (1=OK, 0=error)
    //
    // 3. Output Stream:
    //    - Pass through tdata, tkeep, tvalid, tlast from input
    //    - Set tuser=1 if CRC matches, tuser=0 if mismatch or no FCS
    //
    // See docs/Specification.md for complete behavioral requirements.

    // Placeholder outputs
    assign m_axis_tdata  = '0;
    assign m_axis_tkeep  = '0;
    assign m_axis_tvalid = 1'b0;
    assign m_axis_tlast  = 1'b0;
    assign m_axis_tuser  = 1'b0;

endmodule

`default_nettype wire
