# Created: 2026-02-19
"""Quick test script to verify inference works."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import torch
from src.yield_predictor import YieldTransformer

HORIZONS = ["1h", "24h", "7d", "30d"]

def test_inference():
    """Test the trained model with synthetic data."""
    print("=" * 60)
    print("Testing Yield Predictor Inference")
    print("=" * 60)
    
    # Load the trained model (saved to project root models folder)
    model_path = Path(__file__).parent.parent / "models" / "yield_predictor" / "best_model.pt"
    
    if not model_path.exists():
        print(f"ERROR: Model not found at {model_path}")
        return False
    
    print(f"\nLoading model from: {model_path}")
    
    # Load checkpoint to get model config
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    # Initialize model with correct dimensions (20 features as trained)
    model = YieldTransformer(
        n_features=20,
        d_model=128,
        n_heads=8,
        n_encoder_layers=4,
        n_decoder_layers=2,
        d_ff=512,
        n_horizons=4,
        dropout=0.1
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    model.to(device)
    print(f"Model loaded successfully on {device}")
    
    # Get normalization params from checkpoint
    norm_params = checkpoint.get("normalization_params", {})
    X_mean = norm_params.get("mean", 0)
    X_std = norm_params.get("std", 1)
    
    # Create synthetic test data (168 timesteps, 20 features)
    seq_length = 168
    n_features = 20
    
    # Generate realistic yield-like data (APY around 5%, TVL around 1M)
    np.random.seed(42)
    
    # Create base features that look like real yield data
    test_input = np.zeros((seq_length, n_features), dtype=np.float32)
    
    # Feature 0: APY (around 0.05 = 5%)
    test_input[:, 0] = 0.05 + np.cumsum(np.random.randn(seq_length) * 0.001)
    
    # Feature 1: APY MA7
    test_input[:, 1] = 0.05
    
    # Feature 2: APY MA30
    test_input[:, 2] = 0.05
    
    # Feature 3: APY volatility
    test_input[:, 3] = 0.01
    
    # Feature 4: log10(TVL) (around 6-8 for $1M-$100M)
    test_input[:, 4] = 7.0
    
    # Feature 5: TVL change
    test_input[:, 5] = 0.0
    
    # Remaining features: small random values
    for f in range(6, 20):
        test_input[:, f] = np.random.randn(seq_length) * 0.01
    
    # Normalize using training params
    test_input = (test_input - X_mean.squeeze()) / (X_std.squeeze() + 1e-8)
    
    print(f"\nTest input shape: {test_input.shape}")
    print(f"Using normalization from training data")
    
    # Run prediction
    print("\nRunning prediction...")
    
    # Convert to tensor and add batch dimension
    x = torch.tensor(test_input).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(x, return_uncertainty=True)
    
    # Extract predictions
    predictions = output["predictions"].cpu().numpy().flatten()
    uncertainties = output["uncertainties"].cpu().numpy().flatten()
    trend_logits = output["trend_logits"].cpu().numpy().flatten()
    
    # Determine trend
    trend_idx = np.argmax(trend_logits)
    trend_map = {0: "up", 1: "stable", 2: "down"}
    trend = trend_map[trend_idx]
    
    # Display results
    print("\n" + "=" * 60)
    print("PREDICTION RESULTS")
    print("=" * 60)
    print(f"Trend: {trend}")
    print(f"Trend logits: up={trend_logits[0]:.3f}, stable={trend_logits[1]:.3f}, down={trend_logits[2]:.3f}")
    
    print("\nPredicted APY by Horizon:")
    for i, horizon in enumerate(HORIZONS):
        pred_val = predictions[i]
        std = np.exp(0.5 * uncertainties[i])
        lower = pred_val - 1.96 * std
        upper = pred_val + 1.96 * std
        print(f"  {horizon:>4}: {pred_val*100:.2f}% (95% CI: [{lower*100:.2f}%, {upper*100:.2f}%])")
    
    print("\n" + "=" * 60)
    print("✓ Inference test PASSED!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_inference()
    sys.exit(0 if success else 1)