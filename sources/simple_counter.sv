`timescale 1ns/1ps

module simple_counter (
    input wire clk,
    input wire rst,
    input wire ena,
    input wire [7:0] load_value,
    input wire load,
    output reg [7:0] count
);
    // Golden implementation: Priority load > rst > ena
    always @(posedge clk) begin
        if (load) begin
            // Highest priority: load
            count <= load_value;
        end else if (rst) begin
            // Second priority: reset
            count <= 8'd0;
        end else if (ena) begin
            // Third priority: enable counting
            count <= count + 8'd1;
        end
        // else: maintain current value
    end
endmodule

