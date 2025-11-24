# Verilog Problems

A curated collection of Verilog RTL design problems for AI agent evaluation and reinforcement learning training.

## 📋 Overview

This repository contains systematically designed Verilog coding problems with multiple difficulty levels, specifically tailored for evaluating and training AI agents using the [HUD.AI](https://hud.ai) platform.

## 🎯 Problem Set

### Easy Difficulty

#### 1. Simple Adder
- **Description**: 8-bit synchronous adder
- **Interface**: Clock, two 8-bit inputs, one 8-bit output
- **Evaluation**: 100% success rate with Claude Sonnet 4.5
- **Branches**: `simple_adder_baseline`, `simple_adder_test`, `simple_adder_golden`

#### 2. Simple Counter
- **Description**: 8-bit synchronous counter with reset, enable, and load
- **Features**: Priority logic (load > reset > enable)
- **Evaluation**: 100% success rate with Claude Sonnet 4.5
- **Branches**: `simple_counter_baseline`, `simple_counter_test`, `simple_counter_golden`

### Medium Difficulty

#### 3. Skid Buffer
- **Description**: 2-entry AXI-Stream skid buffer with backpressure handling
- **Interface**: 64-bit data path with valid/ready handshake
- **Evaluation**: 75% success rate (with critical hints)
- **Branches**: `skid_buffer_baseline`, `skid_buffer_test`, `skid_buffer_golden`
- **Challenge**: Requires understanding of FIFO ordering and simultaneous dequeue/enqueue

## 🌿 Branch Structure

Each problem follows a consistent three-branch structure:

```
<problem_name>_baseline  → Starter code with TODO comments
<problem_name>_test      → Baseline + cocotb test suite  
<problem_name>_golden    → Verified working implementation
```

### Branch Purpose

- **`_baseline`**: Starting point for agents, contains module interface and TODO comments
- **`_test`**: Adds hidden test cases (cocotb-based) for evaluation
- **`_golden`**: Reference solution that passes all tests (100% verified)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Icarus Verilog (`iverilog`) for local testing
- Docker (for HUD evaluation)

### Local Testing

```bash
# Clone the repository
git clone https://github.com/Charlie-ZHIJIE/verilog-problems.git
cd verilog-problems

# Install dependencies
uv pip install -e .

# Run tests for a specific problem (example: skid_buffer)
git checkout skid_buffer_golden
uv run pytest tests/test_skid_buffer_hidden.py -v
```

### HUD Evaluation

This repository is designed to work with the [verilog-coding-template](https://github.com/Charlie-ZHIJIE/verilog-coding-template) framework:

1. Clone the evaluation framework
2. Copy this repository to `local-repos/problems`
3. Register problems in `src/hud_controller/problems/basic.py`
4. Build and validate Docker images
5. Run agent evaluations

## 📊 Evaluation Results

| Problem | Difficulty | Agent Success Rate | Notes |
|---------|-----------|-------------------|-------|
| simple_adder | Easy | 100% | Stable, reliable baseline |
| simple_counter | Easy | 100% | Requires clear English comments |
| skid_buffer | Medium | 60% (no hints)<br>75% (with hints) | Benefits from explicit guidance on edge cases |

**Evaluation Model**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)  
**Sample Size**: 10 episodes per configuration

## 🧪 Testing Framework

All problems use **cocotb** (Coroutine-based Cosimulation Testbench) for verification:

- **Language**: Python-based testbenches
- **Simulator**: Icarus Verilog (`iverilog`)
- **Runner**: pytest integration
- **Coverage**: Multiple test scenarios per problem

### Example Test Structure

```python
@cocotb.test()
async def test_basic_functionality(dut):
    """Test basic operation"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Test implementation...
    await RisingEdge(dut.clk)
    assert dut.output.value == expected_value
```

## 📁 Repository Structure

```
verilog-problems/
├── sources/              # Verilog source files (.sv)
├── tests/                # cocotb test files (.py)
├── docs/                 # Problem specifications
├── pyproject.toml        # Python dependencies
└── README.md            # This file
```

## 🎓 Problem Design Philosophy

### Easy Problems (100% target)
- Single RTL concept
- Clear specifications
- Minimal edge cases
- Suitable for basic agent capabilities

### Medium Problems (70-80% target)
- Multiple interacting concepts
- Complex state machines
- Edge case handling required
- Tests agent's reasoning ability

### Hard Problems (Future: 40-60% target)
- Advanced protocols
- Timing-critical designs
- Complex verification requirements

## 🔧 Development Workflow

### Adding a New Problem

1. **Create branches**: `<problem>_baseline`, `<problem>_test`, `<problem>_golden`
2. **Write specification**: Add to `docs/` with clear requirements
3. **Implement baseline**: Module interface + TODO comments
4. **Write tests**: cocotb test suite covering all requirements
5. **Verify golden**: Ensure 100% test pass rate
6. **Register**: Add to evaluation framework
7. **Validate**: Docker build and validation checks
8. **Evaluate**: Run with multiple agent configurations

### Testing Guidelines

- ✅ All tests must pass with golden implementation
- ✅ All tests must fail with baseline implementation
- ✅ Tests should cover normal cases, edge cases, and corner cases
- ✅ Use meaningful assertion messages for debugging

## 📈 Success Metrics

### Golden Implementation
- ✅ Must pass 100% of tests
- ✅ Must compile without errors/warnings
- ✅ Must handle all specified edge cases

### Agent Evaluation
- **Easy**: Target 90-100% success rate
- **Medium**: Target 70-80% success rate
- **Hard**: Target 40-60% success rate

## 🤝 Integration with HUD.AI

This repository is designed as a problem set for:
- **Agent Evaluation**: Test Claude, GPT, and other LLMs on Verilog tasks
- **RL Training**: Train agents using reinforcement learning
- **Benchmarking**: Compare different models and prompting strategies

### Evaluation Configuration

Each problem can be configured with:
- Allowed tools (e.g., `str_replace_based_edit_tool`)
- Max steps (typically 50-150)
- Model selection
- Custom hints and guidance

## 📝 Lessons Learned

### From Evaluation Results

1. **Explicit hints significantly improve success rates** (+15-20% for medium problems)
2. **English comments work better than Chinese** for Claude models
3. **Tool selection matters**: `str_replace_based_edit_tool` preferred over bash
4. **Edge case hints are crucial**: Particularly for simultaneous operations

### Best Practices

- ✅ Provide clear, detailed specifications
- ✅ Use scenario-based explanations for complex logic
- ✅ Suggest specific implementation approaches (e.g., case statements)
- ✅ Include file paths in instructions
- ✅ Use visual separators to highlight critical information

## 🔗 Related Repositories

- [verilog-coding-template](https://github.com/Charlie-ZHIJIE/verilog-coding-template): Evaluation framework
- [HUD.AI Platform](https://hud.ai): Agent evaluation and RL training

## 📄 License

This repository is for educational and research purposes.

## 👤 Author

**Charlie ZHIJIE**
- GitHub: [@Charlie-ZHIJIE](https://github.com/Charlie-ZHIJIE)

## 🙏 Acknowledgments

- **HUD.AI**: For providing the evaluation platform
- **cocotb**: For the excellent Python-based HDL verification framework
- **Anthropic**: For Claude AI models used in evaluation

---

**Last Updated**: November 2025  
**Status**: ✅ Production Ready  
**Total Problems**: 3 (1 Easy baseline + 1 Easy + 1 Medium)  
**Total Branches**: 12 (including master)
