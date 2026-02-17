// Created: 2026-02-12

# 4-Hour Sprint: OpenRouter Inference Provider Setup

## Can You Do This in Under 4 Hours?

**YES.** Here's the realistic timeline breakdown for non-stop execution.

---

## Timeline Breakdown

### Hour 1: Accounts & GPU Provisioning (60 min)

| Task | Time | Running Clock |
|------|------|---------------|
| Create RunPod account | 5 min | 0:05 |
| Add payment method | 5 min | 0:10 |
| Create OpenRouter account | 5 min | 0:15 |
| Apply as OpenRouter provider | 10 min | 0:25 |
| Get HuggingFace token | 5 min | 0:30 |
| Accept Llama 3.1 license on HF | 5 min | 0:35 |
| Provision RTX 4090 on RunPod | 10 min | 0:45 |
| Wait for instance to start | 15 min | **1:00** |

### Hour 2: Model Deployment (60 min)

| Task | Time | Running Clock |
|------|------|---------------|
| SSH into RunPod instance | 2 min | 1:02 |
| Install vLLM (`pip install vllm`) | 10 min | 1:12 |
| Login to HuggingFace | 2 min | 1:14 |
| **Model download** (Llama 3.1 8B ~16GB) | 20-30 min | 1:44 |
| Start vLLM server | 2 min | 1:46 |
| Wait for model to load into VRAM | 5 min | 1:51 |
| Test inference locally | 5 min | **2:00** |

### Hour 3: OpenRouter Integration (60 min)

| Task | Time | Running Clock |
|------|------|---------------|
| Get RunPod public IP/endpoint | 5 min | 2:05 |
| Configure OpenRouter provider settings | 10 min | 2:15 |
| Add endpoint URL to OpenRouter | 5 min | 2:20 |
| Set pricing (prompt $0.12/M, completion $0.25/M) | 5 min | 2:25 |
| Verify health check passes | 5 min | 2:30 |
| Submit provider application | 5 min | 2:35 |
| **Wait for OpenRouter approval** | 20 min | **3:00** |

### Hour 4: Monitoring & Go-Live (60 min)

| Task | Time | Running Clock |
|------|------|---------------|
| Upload monitor.py to instance | 2 min | 3:02 |
| Set up monitoring dashboard | 10 min | 3:12 |
| Verify first requests coming through | 10 min | 3:22 |
| Check GPU utilization | 5 min | 3:27 |
| Optimize settings if needed | 10 min | 3:37 |
| Document setup for future reference | 10 min | 3:47 |
| Celebrate - You're live! | 13 min | **4:00** |

---

## Critical Path Items (Must Do)

These are the minimum steps to be live and earning:

1. ✅ RunPod account + payment (10 min)
2. ✅ HuggingFace token + license accept (10 min)
3. ✅ Provision RTX 4090 instance (25 min including wait)
4. ✅ Install vLLM + download model (40 min)
5. ✅ Start vLLM server (7 min)
6. ✅ OpenRouter provider setup (30 min)
7. ✅ Test and verify (18 min)

**Minimum total: ~2.5 hours** (if everything goes smoothly)

---

## Time-Saving Tips for 4-Hour Sprint

### Before Starting (Pre-Flight Checklist)
- [ ] Have credit card ready for RunPod
- [ ] Have HuggingFace account ready
- [ ] Have OpenRouter account ready
- [ ] Clear your schedule for 4 hours
- [ ] Have stable internet connection

### Parallel Task Opportunities
During the **model download** (20-30 min), you can:
- Set up OpenRouter provider account
- Configure OpenRouter settings
- Write down your pricing strategy

During **OpenRouter approval wait** (20 min), you can:
- Set up monitoring
- Test local inference thoroughly
- Document your setup

### Potential Delays (Plan For These)

| Delay | Impact | Mitigation |
|-------|--------|------------|
| Slow model download | +15 min | Use RunPod instance with fast network |
| OpenRouter approval delay | +30 min | Can still test locally |
| GPU instance provisioning delay | +10 min | Have backup provider (Vast.ai) |
| Payment verification issues | +15 min | Use card, not bank transfer |

---

## Realistic Timeline Summary

| Scenario | Time | Notes |
|----------|------|-------|
| **Best case** | 2.5 hours | Everything goes perfectly |
| **Realistic** | 3-4 hours | Minor delays, parallel work |
| **With issues** | 4-5 hours | Payment issues, slow downloads |

---

## What About GLM-5?

**GLM-5 adds significant time:**

| Task | Time |
|------|------|
| Find/provision 8× A100 instance | 30-60 min |
| Model download (GLM-5 ~300GB) | 60-90 min |
| Configuration and testing | 30 min |

**GLM-5 total: +2-3 hours**

**Recommendation:** Start with Llama 3.1 8B first (4 hours). Add GLM-5 later once Tier 1 is proven profitable.

---

## Sprint Execution Checklist

Print this and check off as you go:

```
□ RunPod account created
□ Payment method added  
□ HuggingFace token obtained
□ Llama 3.1 license accepted
□ RTX 4090 instance provisioned
□ SSH connected to instance
□ vLLM installed
□ HuggingFace authenticated
□ Model downloaded
□ vLLM server started
□ Local inference tested
□ OpenRouter provider account created
□ Endpoint URL added to OpenRouter
□ Pricing configured
□ Health check passing
□ First request from OpenRouter received
□ Monitor.py running
□ GPU utilization verified
□ YOU'RE LIVE AND EARNING!
```

---

## After 4 Hours: What You'll Have

1. **Live inference server** on RunPod RTX 4090
2. **OpenRouter provider account** approved
3. **Earning per-token fees** from OpenRouter traffic
4. **Monitoring dashboard** tracking profit
5. **Documented setup** for scaling

**Expected earnings by end of day 1: $20-50** (depending on traffic)

---

*Created: 2026-02-12*