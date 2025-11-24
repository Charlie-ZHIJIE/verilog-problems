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

    // Two-entry skid buffer using explicit front/back registers
    reg [DATA_WIDTH-1:0] buffer0, buffer1;
    reg [1:0]            count;   // number of valid entries: 0, 1, or 2

    wire fifo_full  = (count == 2'd2);
    wire fifo_empty = (count == 2'd0);

    wire do_dequeue = !fifo_empty && m_ready;
    wire do_enqueue = !fifo_full && s_valid;

    assign s_ready = !fifo_full;
    assign m_valid = !fifo_empty;
    assign m_data  = buffer0;

    reg [DATA_WIDTH-1:0] buffer0_next, buffer1_next;
    reg [1:0]            count_next;

    always @(*) begin
        buffer0_next = buffer0;
        buffer1_next = buffer1;
        count_next   = count;

        case ({do_dequeue, do_enqueue})
            2'b00: begin
                // no dequeue, no enqueue: hold state
            end

            2'b10: begin
                // dequeue only
                case (count)
                    2'd0: begin
                        // should not happen
                    end
                    2'd1: begin
                        // drop the only entry
                        count_next = 2'd0;
                    end
                    2'd2: begin
                        // shift back entry to front
                        buffer0_next = buffer1;
                        count_next   = 2'd1;
                    end
                    default: begin end
                endcase
            end

            2'b01: begin
                // enqueue only
                case (count)
                    2'd0: begin
                        buffer0_next = s_data;
                        count_next   = 2'd1;
                    end
                    2'd1: begin
                        buffer1_next = s_data;
                        count_next   = 2'd2;
                    end
                    2'd2: begin
                        // should not happen because do_enqueue implies !full
                    end
                    default: begin end
                endcase
            end

            2'b11: begin
                // dequeue and enqueue in the same cycle
                case (count)
                    2'd0: begin
                        // cannot happen: cannot dequeue from empty
                    end
                    2'd1: begin
                        // one entry was at front and is consumed; new data becomes the sole entry
                        buffer0_next = s_data;
                        count_next   = 2'd1;
                    end
                    2'd2: begin
                        // two entries: front is consumed, back moves forward, new data becomes back
                        buffer0_next = buffer1;
                        buffer1_next = s_data;
                        count_next   = 2'd2;
                    end
                    default: begin end
                endcase
            end

            default: begin
                // no-op
            end
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buffer0 <= {DATA_WIDTH{1'b0}};
            buffer1 <= {DATA_WIDTH{1'b0}};
            count   <= 2'd0;
        end else begin
            buffer0 <= buffer0_next;
            buffer1 <= buffer1_next;
            count   <= count_next;
        end
    end

endmodule