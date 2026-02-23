// Created: 2026-02-12

# GLM-5 Optimization: Reducing Energy & Cost Per Response

## The Problem

GLM-5 (750B parameters) is expensive to run:
- **8× A100 80GB** = $12-15/hour
- **8× H100 80GB** = $20-30/hour

**Goal:** Reduce compute/energy per response by 50%+ to improve profitability.

---

## Solution: Model Quantization

### What is Quantization?

Quantization reduces the precision of model weights from 16-bit (BF16) to lower precision (FP8, INT8, INT4), dramatically reducing:
1. **VRAM requirements** → Fewer GPUs needed
2. **Memory bandwidth** → Faster inference
3. **Energy consumption** → Lower cost per token

### Quantization Options for GLM-5

| Quantization | VRAM Required | GPUs Needed | Cost/Hour | Quality Loss |
|--------------|---------------|-------------|-----------|--------------|
| **BF16 (baseline)** | ~1,500 GB | 16× A100 | $24.00 | 0% |
| **FP8** | ~750 GB | 8× A100 | $12.00 | ~1-2% |
| **INT8** | ~375 GB | 5× A100 | $7.50 | ~2-5% |
| **INT4 (GPTQ/AWQ)** | ~188 GB | 3× A100 | $4.50 | ~5-10% |
| **INT4 + KV Cache** | ~150 GB | 2× A100 | $3.00 | ~5-10% |

### Recommended: INT8 Quantization

**Why INT8?**
- **50% cost reduction** ($12/hr → $6/hr)
- **Minimal quality loss** (~2-5%)
- **Well-supported** by vLLM and HuggingFace
- **Sweet spot** between cost and quality

---

## Implementation: INT8 Quantized GLM-5

### Step 1: Check for Pre-quantized Model

```bash
# Check HuggingFace for quantized versions
# Option A: Official quantized release
huggingface-cli download zai-org/GLM-5-INT8 --local-dir /models/glm-5-int8

# Option B: Community quantized version
huggingface-cli download zai-org/GLM-5-GPTQ-INT4 --local-dir /models/glm-5-gptq
```

### Step 2: Quantize Yourself (if no pre-quantized)

```python
# quantize_glm5.py
from transformers import AutoModelForCausalLM, AutoTokenizer
from optimum.bettertransformer import BetterTransformer
import torch

print("Loading GLM-5 in BF16...")
model = AutoModelForCausalLM.from_pretrained(
    "zai-org/GLM-5",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)

print("Quantizing to INT8...")
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)

print("Saving quantized model...")
quantized_model.save_pretrained("/models/glm-5-int8")
tokenizer = AutoTokenizer.from_pretrained("zai-org/GLM-5")
tokenizer.save_pretrained("/models/glm-5-int8")

print("Done! INT8 model saved to /models/glm-5-int8")
```

### Step 3: Run Quantized Model

```bash
# INT8 GLM-5 on 5× A100 (50% cost reduction)
python -m vllm.entrypoints.openai.api_server \
    --model /models/glm-5-int8 \
    --host 0.0.0.0 --port 8000 \
    --tensor-parallel-size 5 \
    --dtype int8 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95 \
    --enable-prefix-caching \
    --trust-remote-code
```

---

## Alternative: INT4 Quantization (Maximum Savings)

### Using GPTQ or AWQ

```bash
# Install AutoGPTQ
pip install auto-gptq optimum

# Quantize to INT4
python -c "
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
from transformers import AutoTokenizer

quantize_config = BaseQuantizeConfig(
    bits=4,
    group_size=128,
    desc_act=False
)

model = AutoGPTQForCausalLM.from_pretrained(
    'zai-org/GLM-5',
    quantize_config
)
tokenizer = AutoTokenizer.from_pretrained('zai-org/GLM-5')

# Calibrate with sample data
model.quantize(calibration_data)

model.save_quantized('/models/glm-5-gptq-int4')
tokenizer.save_pretrained('/models/glm-5-gptq-int4')
"
```

### Run INT4 Model

```bash
# INT4 GLM-5 on 3× A100 (75% cost reduction!)
python -m vllm.entrypoints.openai.api_server \
    --model /models/glm-5-gptq-int4 \
    --host 0.0.0.0 --port 8000 \
    --tensor-parallel-size 3 \
    --dtype int4 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95
```

---

## Additional Energy-Saving Techniques

### 1. KV Cache Optimization

```bash
# Enable KV cache quantization (reduces memory by 50%)
python -m vllm.entrypoints.openai.api_server \
    --model /models/glm-5-int8 \
    --kv-cache-dtype int8 \
    --max-model-len 8192
```

### 2. Speculative Decoding

Use a smaller "draft" model to predict tokens, then verify with GLM-5:

```bash
# Speculative decoding with Qwen 7B as draft model
python -m vllm.entrypoints.openai.api_server \
    --model /models/glm-5-int8 \
    --speculative-model /models/qwen-2.5-7b \
    --num-speculative-tokens 4
```

**Benefit:** 30-50% faster inference = more tokens per dollar

### 3. Batching Optimization

```bash
# Increase batch size for better GPU utilization
python -m vllm.entrypoints.openai.api_server \
    --model /models/glm-5-int8 \
    --max-num-seqs 64 \
    --max-num-batched-tokens 32768
```

### 4. Context Length Reduction

```bash
# Reduce max context length (saves memory)
python -m vllm.entrypoints.openai.api_server \
    --model /models/glm-5-int8 \
    --max-model-len 2048  # Instead of 8192
```

---

## Cost Comparison: Optimized vs Baseline

### Baseline (BF16, 8× A100)
```
Hourly Cost: $12.00
Tokens/Hour: ~50,000
Cost per 1M tokens: $240
```

### Optimized (INT8, 5× A100)
```
Hourly Cost: $6.00
Tokens/Hour: ~45,000 (slightly slower)
Cost per 1M tokens: $133
SAVINGS: 45%
```

### Maximum Optimization (INT4, 3× A100)
```
Hourly Cost: $3.60
Tokens/Hour: ~40,000
Cost per 1M tokens: $90
SAVINGS: 62.5%
```

---

## Profitability Impact

### Before Optimization
| Utilization | Daily Revenue | Daily Cost | Daily Profit |
|-------------|---------------|------------|--------------|
| 50% | $360 | $288 | **$72** |
| 70% | $504 | $288 | **$216** |

### After INT8 Optimization (50% cost reduction)
| Utilization | Daily Revenue | Daily Cost | Daily Profit |
|-------------|---------------|------------|--------------|
| 50% | $360 | $144 | **$216** |
| 70% | $504 | $144 | **$360** |

### After INT4 Optimization (62.5% cost reduction)
| Utilization | Daily Revenue | Daily Cost | Daily Profit |
|-------------|---------------|------------|--------------|
| 50% | $360 | $86 | **$274** |
| 70% | $504 | $86 | **$418** |

---

## Recommended Configuration

### Best Balance: INT8 Quantization

```bash
# GLM-5 INT8 on RunPod 5× A100
# Cost: $6-7.50/hour
# Quality: 95-98% of original

python -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5-INT8 \
    --host 0.0.0.0 --port 8000 \
    --tensor-parallel-size 5 \
    --dtype int8 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95 \
    --enable-prefix-caching \
    --kv-cache-dtype int8 \
    --max-num-seqs 32 \
    --trust-remote-code
```

### Maximum Savings: INT4 Quantization

```bash
# GLM-5 INT4 on RunPod 3× A100
# Cost: $3.60-4.50/hour
# Quality: 90-95% of original

python -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5-GPTQ-INT4 \
    --host 0.0.0.0 --port 8000 \
    --tensor-parallel-size 3 \
    --dtype int4 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95 \
    --enable-prefix-caching
```

---

## Quality vs Cost Trade-off

| Configuration | Quality | Cost/Hour | Break-even Utilization |
|---------------|---------|-----------|------------------------|
| BF16 (baseline) | 100% | $12.00 | 80% |
| FP8 | 98% | $12.00 | 60% |
| **INT8** | 95% | $6.00 | **35%** |
| **INT4** | 90% | $3.60 | **25%** |

**Recommendation:** Use INT8 for best balance of quality and cost. Use INT4 if quality loss is acceptable for your use case.

---

## Quick Start: Optimized GLM-5

```bash
# 1. Check for pre-quantized model
pip install vllm optimum auto-gptq

# 2. Try INT8 first (recommended)
python -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5 \
    --load-format int8 \
    --tensor-parallel-size 5

# 3. If quality acceptable, you're saving 50%!
```

---

*Created: 2026-02-12*
*Author: Kerne Protocol Team*