# Kerne Protocol - OpenRouter Provider Application Data

Use the following information to fill out the OpenRouter provider application form. This data is optimized to highlight Kerne's strengths and technical readiness.

---

## 1. Basic Information
- **Company Name:** Kerne
- **Your Email:** team@kerne.ai

---

## 2. What distinguishes you?
*(Check these boxes)*
- [x] Low Latency
- [x] High throughput
- [x] Unique models
- [x] Unique Infrastructure
- [x] Strategic Partnership

---

## 3. Extra details
Kerne Protocol operates a high-performance, delta-neutral inference layer. We are uniquely positioned as a provider because:
1. **Proprietary Models:** We host "Kerne-Finance-V1", a proprietary model optimized for high-frequency financial analysis and predictive market modeling.
2. **Optimized Infrastructure:** Our stack is built on RunPod serverless GPUs with custom vLLM orchestration, ensuring sub-100ms Time To First Token (TTFT).
3. **Enterprise GLM-5 Hosting:** We provide highly optimized INT4/INT8 versions of GLM-5 (750B), making massive-scale inference affordable and fast.
4. **Redundancy:** Our autonomous agent dynamically scales across multiple GPU regions to maintain 99.9% availability even during regional outages.

---

## 4. Volume Discount
Yes, we offer aggressive tiered pricing for high-volume users:
- **Tier 1:** 10% discount for >100M tokens/month.
- **Tier 2:** 25% discount for >500M tokens/month.
- **Custom:** Dedicated GPU reservations are available for enterprise partners requiring guaranteed throughput.

---

## 5. Rate limits
- **Initial Limits:** 200 Requests Per Minute (RPM) and 200,000 Tokens Per Minute (TPM).
- **Scaling:** Limits are automatically raised based on account age and credit balance.
- **Process:** Users can request immediate limit increases via our Slack connect channel or by emailing team@kerne.ai.

---

## 6. Pricing and Payment
*(Check all boxes)*
- [x] The API returns 'usage' (tokens) for stream and non-stream requests
- [x] The API return cache read and write usage if caching is available
- [x] A publicly available pricing denominated in USD ($) per M tokens
- [x] An automated way for OpenRouter to pay you (invoicing or auto top-up)

---

## 7. Invoicing / Payment
We support automated monthly settlement via OpenRouter's provider system. For direct enterprise billing, we support Credit Cards, Wire Transfers, and USDC.

---

## 8. Tokenization
We use model-specific tokenizers (Tiktoken for Llama/OpenAI, and native HuggingFace tokenizers for GLM/Qwen). Token counts are calculated server-side using the model's exact vocabulary to ensure 100% billing accuracy.

---

## 9. API Endpoints
- **URL to /completions API:** `https://xvyz8l5h8ca0iz-8000.proxy.runpod.net/v1/completions`
- **URL to /chat/completions API:** `https://xvyz8l5h8ca0iz-8000.proxy.runpod.net/v1/chat/completions`
- **URL to /models API:** `https://xvyz8l5h8ca0iz-8000.proxy.runpod.net/v1/models`

---

## 10. Failure States
- **Cancellable:** No, we do not charge for mid-request cancellations.
- **Model/Engine Failure:** No, we do not charge if the model fails or the engine errors out.

---

## 11. Special error shapes or finish reasons
We follow the standard OpenAI error schema. We include a custom `x-kerne-request-id` in the header for rapid debugging and support.

---

## 12. Parameters Support
**Required Params:**
- [x] max_tokens
- [x] temperature
- [x] top_p
- [x] stop
- [x] seed

**Optional Params:**
- [x] top_k
- [x] frequency_penalty
- [x] presence_penalty
- [x] repetition_penalty
- [x] min_p
- [x] top_a
- [x] logit_bias
- [x] logprobs
- [x] response_format
- [x] structured_outputs
- [x] tools
- [x] tool_choice

---

## 13. Advanced Features
- **Tool calling:** Yes, we support tool calling with streaming. It is production-ready.
- **Structured outputs:** Yes, we support JSON schema via guided decoding.
- **Multi-modal models:** Supporting `image/jpeg`, `image/png`, and `image/webp`.
- **Inference Location:** Multi-region (US-East, US-West, EU-Central).