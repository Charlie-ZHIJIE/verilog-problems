# Skid Buffer Specification

## Module Name
`skid_buffer`

## Parameter
- `DATA_WIDTH` (default = 64): Width of the data path in bits.

## Interface

### Inputs
- `clk`: System clock, operations occur on the rising edge.
- `rst_n`: Asynchronous reset, active low. Clears all stored data when asserted.
- `s_data[DATA_WIDTH-1:0]`: Upstream payload.
- `s_valid`: Indicates the upstream has a valid beat on `s_data`.
- `m_ready`: Downstream back-pressure signal. High when the consumer can accept the current beat.

### Outputs
- `s_ready`: High when the buffer can accept a beat from the upstream interface.
- `m_data[DATA_WIDTH-1:0]`: Payload driven to the downstream interface.
- `m_valid`: Indicates that `m_data` is valid and must be consumed when `m_ready` is also high.

## Behavior

### Storage Model
- Two entries (`buffer0`, `buffer1`) provide up to two beats of elasticity between source (`s_*`) and sink (`m_*`).
- `s_ready = 1` exactly when at least one entry is free (i.e., not "skid full").
- `m_valid` reflects whether `buffer0` currently holds valid data.

### Reset
- When `rst_n = 0`, both buffers are marked invalid immediately (asynchronous clear). Data contents are don't-care.
- Upon deasserting reset, normal operation resumes on the next rising edge.

### Dequeue (downstream consumption)
- On every rising edge, if `buffer0` is valid and `m_ready = 1`, the beat in `buffer0` is considered consumed.
- After consumption, `buffer1` slides forward (if valid) to keep ordering, otherwise `buffer0_valid` clears.

### Enqueue (upstream acceptance)
- On every rising edge, if `s_valid = 1` and `s_ready = 1`, the incoming beat is accepted.
- Accepted beats occupy the first empty buffer entry:
  1. If `buffer0_valid = 0`, load `buffer0`.
  2. Else if `buffer1_valid = 0`, load `buffer1`.
- If both entries are valid, `s_ready = 0` and no new data may enter (back-pressure).

### Ordering & Throughput Guarantees
- Beats leave the module in exactly the order received.
- When the downstream never stalls (`m_ready = 1` every cycle), the module behaves like simple pass-through (one cycle latency at most).
- When the downstream deasserts `m_ready`, up to two additional beats can be absorbed before `s_ready` deasserts, preventing data loss.

## Example Timing Highlights
- **Pass-through**: `m_ready=1` -> each accepted `s_valid` beat appears on `m_*` the next cycle.
- **Skid Event**: If `m_ready` goes low for one cycle while `s_valid` stays high, the module stores the beat in `buffer1` and keeps `m_valid` asserted with the earlier beat until consumption resumes.
- **Back-pressure**: When both buffer entries are full, `s_ready` stays low so the upstream pauses automatically.

## Test Cases
1. **Reset Flush**: Assert `rst_n=0` while buffers hold data; ensure `m_valid` drops and both buffers clear immediately.
2. **Zero-Stall Pass-through**: Keep `m_ready=1`; apply a burst of beats and verify they appear on `m_data` in-order every cycle.
3. **Single-Cycle Skid**: Deassert `m_ready` for one cycle while `s_valid` stays high; confirm data is held, no loss, and `s_ready` only drops when both entries fill.
4. **Full Buffer Back-pressure**: Hold `m_ready=0` and continue asserting `s_valid`; after two accepted beats, `s_ready` must deassert until space frees.
5. **Ordering Under Burst**: Alternate `m_ready` between 0/1 while issuing unique tags on `s_data`; verify the output ordering always matches arrival order.

