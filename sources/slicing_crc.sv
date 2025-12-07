/*
 *   Module: slicing_crc
 *
 *   Description: Slicing-by-N CRC calculator, designed for Ethernet. Based on Sarwate's
 *                algorithm.
 *
 */

`default_nettype none
`timescale 1ns/1ps

module slicing_crc #(
    parameter int SLICE_LENGTH = 8,
    parameter int INITIAL_CRC = 32'hFFFFFFFF,
    parameter bit INVERT_OUTPUT = 1,
    parameter bit REGISTER_OUTPUT = 1,
    localparam int MAX_SLICE_LENGTH = 16 // Number of lines in crc_tables.mem
) (
    input wire i_clk,
    input wire i_reset,
    input wire [8*SLICE_LENGTH-1:0] i_data,
    input wire [SLICE_LENGTH-1:0] i_valid,
    output wire [31:0] o_crc
);

    // Read CRC lookup tables
    logic [31:0] crc_tables [MAX_SLICE_LENGTH][256];
    initial begin
        $readmemh("crc_tables.mem", crc_tables);
    end

    // TODO: Implement the Slicing-by-N CRC calculation logic
    //
    // Requirements:
    // 1. Calculate num_input_bytes based on i_valid (count how many bytes are valid)
    // 2. Maintain a CRC state register (prev_crc) that updates on each valid cycle
    // 3. Implement table-based lookup using Sarwate's algorithm:
    //    - For first 4 bytes: XOR input byte with corresponding prev_crc byte
    //    - For bytes beyond 4: Use input byte directly
    //    - Look up in crc_tables[num_input_bytes - byte_position - 1][lookup_value]
    // 4. XOR all table outputs together
    // 5. XOR with shifted prev_crc: result = xor_result XOR (prev_crc >> (8*num_input_bytes))
    // 6. Output handling:
    //    - If REGISTER_OUTPUT=1: output prev_crc (1 cycle delayed)
    //    - If REGISTER_OUTPUT=0: output crc_calc (combinational)
    //    - Apply INVERT_OUTPUT if set
    //
    // See docs/Specification.md for detailed algorithm explanation.

    // Placeholder - replace with your implementation
    assign o_crc = 32'h0;

endmodule

`default_nettype wire
