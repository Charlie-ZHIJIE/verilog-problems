`timescale 1ns/1ps

module skid_buffer #(
    parameter DATA_WIDTH = 64
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

    // TODO: Implement skid buffer logic
    // 
    // Requirements:
    // 1. Two-stage buffer (buffer0 for output, buffer1 for skid)
    // 2. Can accept new data when full IF dequeue is happening
    // 3. Preserve strict FIFO ordering
    // 4. Asynchronous reset clears all buffers immediately
    //
    // Hints:
    // - Use two registers: buffer0 and buffer1
    // - Track validity with buffer0_valid and buffer1_valid
    // - Calculate next state in combinational logic (always @(*))
    // - Update registers on clock edge (always @(posedge clk or negedge rst_n))
    // - Handle four cases: {will_dequeue, will_enqueue}

endmodule

