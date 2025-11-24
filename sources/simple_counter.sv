`timescale 1ns/1ps

module simple_counter (
    input wire clk,
    input wire rst,
    input wire ena,
    input wire [7:0] load_value,
    input wire load,
    output reg [7:0] count
);
    // Golden实现：优先级 load > rst > ena
    always @(posedge clk) begin
        if (load) begin
            // 最高优先级：加载
            count <= load_value;
        end else if (rst) begin
            // 第二优先级：复位
            count <= 8'd0;
        end else if (ena) begin
            // 第三优先级：使能计数
            count <= count + 8'd1;
        end
        // else: 保持当前值
    end
endmodule

