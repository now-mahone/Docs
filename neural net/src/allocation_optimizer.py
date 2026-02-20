# Created: 2026-02-19
"""
Kerne Allocation Optimizer - RL Agent for Capital Allocation
=============================================================

Reinforcement Learning agent for optimizing capital allocation across
DeFi yield strategies. Uses PPO (Proximal Policy Optimization) for
stable learning in the complex DeFi environment.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .utils import load_config, setup_logging


@dataclass
class AllocationDecision:
    """Container for allocation decision results."""
    weights: Dict[str, float]  # strategy_id -> weight (0-1)
    expected_apy: float
    expected_risk_score: float
    rebalance_trades: List[Dict[str, Any]]  # List of trades to execute
    gas_estimate: float  # Estimated gas cost in USD
    confidence: float  # Model confidence in decision
    timestamp: str
    model_version: str


@dataclass
class Strategy:
    """Definition of a yield strategy."""
    id: str
    protocol: str
    chain: str
    asset: str
    current_apy: float
    predicted_apy: float
    risk_score: int
    tvl: float
    max_capacity: float
    current_allocation: float = 0.0


class AllocationEnvironment:
    """
    Gym-style environment for allocation optimization.
    
    Simulates the DeFi yield environment for RL training.
    """
    
    def __init__(
        self,
        strategies: List[Strategy],
        initial_tvl: float = 1_000_000,
        transaction_cost: float = 0.001,
        gas_cost_weight: float = 0.0001,
        max_steps: int = 1000
    ):
        """
        Initialize the environment.
        
        Args:
            strategies: List of available strategies
            initial_tvl: Initial total value to allocate
            transaction_cost: Cost per transaction (fraction)
            gas_cost_weight: Weight for gas costs in reward
            max_steps: Maximum steps per episode
        """
        self.strategies = strategies
        self.n_strategies = len(strategies)
        self.initial_tvl = initial_tvl
        self.transaction_cost = transaction_cost
        self.gas_cost_weight = gas_cost_weight
        self.max_steps = max_steps
        
        # State variables
        self.current_step = 0
        self.current_allocations = np.zeros(self.n_strategies)
        self.tvl = initial_tvl
        self.history = []
        
        # Action and observation spaces
        self.action_dim = self.n_strategies
        self.obs_dim = self._get_obs_dim()
    
    def _get_obs_dim(self) -> int:
        """Get observation dimension."""
        # For each strategy: current_apy, predicted_apy, risk_score, tvl, current_allocation
        # Plus: global features (total_tvl, step, market_conditions)
        return self.n_strategies * 5 + 3
    
    def reset(self) -> np.ndarray:
        """Reset the environment."""
        self.current_step = 0
        self.current_allocations = np.zeros(self.n_strategies)
        self.tvl = self.initial_tvl
        self.history = []
        
        return self._get_observation()
    
    def _get_observation(self) -> np.ndarray:
        """Get current observation."""
        obs = []
        
        for i, strategy in enumerate(self.strategies):
            obs.extend([
                strategy.current_apy,
                strategy.predicted_apy,
                strategy.risk_score / 100.0,
                strategy.tvl / 1e9,  # Normalize to billions
                self.current_allocations[i]
            ])
        
        # Global features
        obs.extend([
            self.tvl / 1e9,
            self.current_step / self.max_steps,
            0.5  # Placeholder for market conditions
        ])
        
        return np.array(obs, dtype=np.float32)
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Take a step in the environment.
        
        Args:
            action: Target allocation weights (will be normalized)
            
        Returns:
            Tuple of (observation, reward, done, info)
        """
        self.current_step += 1
        
        # Normalize action to valid allocation
        weights = self._normalize_action(action)
        
        # Calculate rebalancing costs
        rebalance_amounts = np.abs(weights - self.current_allocations) * self.tvl
        total_rebalance = np.sum(rebalance_amounts)
        transaction_costs = total_rebalance * self.transaction_cost
        gas_costs = self.n_strategies * self.gas_cost_weight * 100  # Simplified gas estimate
        
        # Update allocations
        old_allocations = self.current_allocations.copy()
        self.current_allocations = weights
        
        # Calculate yield (simplified simulation)
        yield_earned = self._calculate_yield()
        
        # Calculate risk penalty
        risk_penalty = self._calculate_risk_penalty()
        
        # Calculate concentration penalty
        concentration_penalty = self._calculate_concentration_penalty()
        
        # Total reward
        reward = (
            yield_earned 
            - risk_penalty 
            - concentration_penalty 
            - transaction_costs 
            - gas_costs
        )
        
        # Update TVL
        self.tvl = self.tvl * (1 + yield_earned) - transaction_costs - gas_costs
        
        # Record history
        self.history.append({
            "step": self.current_step,
            "allocations": weights.copy(),
            "reward": reward,
            "tvl": self.tvl
        })
        
        # Check if done
        done = self.current_step >= self.max_steps
        
        # Info dict
        info = {
            "yield_earned": yield_earned,
            "risk_penalty": risk_penalty,
            "transaction_costs": transaction_costs,
            "tvl": self.tvl
        }
        
        return self._get_observation(), reward, done, info
    
    def _normalize_action(self, action: np.ndarray) -> np.ndarray:
        """Normalize action to valid allocation weights."""
        # Ensure non-negative
        weights = np.maximum(action, 0)
        
        # Normalize to sum to 1
        total = np.sum(weights)
        if total > 0:
            weights = weights / total
        else:
            # Equal allocation if all zeros
            weights = np.ones(self.n_strategies) / self.n_strategies
        
        # Apply constraints
        for i, strategy in enumerate(self.strategies):
            # Max allocation based on risk score
            max_alloc = self._get_max_allocation(strategy.risk_score)
            weights[i] = min(weights[i], max_alloc)
            
            # Max allocation based on capacity
            if strategy.max_capacity > 0:
                capacity_weight = strategy.max_capacity / self.tvl
                weights[i] = min(weights[i], capacity_weight)
        
        # Re-normalize after constraints
        total = np.sum(weights)
        if total > 0:
            weights = weights / total
        
        return weights
    
    def _get_max_allocation(self, risk_score: int) -> float:
        """Get maximum allocation based on risk score."""
        if risk_score >= 90:
            return 0.15
        elif risk_score >= 80:
            return 0.10
        elif risk_score >= 70:
            return 0.05
        elif risk_score >= 50:
            return 0.02
        else:
            return 0.0
    
    def _calculate_yield(self) -> float:
        """Calculate yield earned from current allocations."""
        total_yield = 0.0
        
        for i, strategy in enumerate(self.strategies):
            # Use predicted APY with some noise
            actual_apy = strategy.predicted_apy * (1 + np.random.normal(0, 0.1))
            allocation_yield = actual_apy * self.current_allocations[i]
            total_yield += allocation_yield
        
        # Convert from annual to per-step (assuming daily steps)
        return total_yield / 365
    
    def _calculate_risk_penalty(self) -> float:
        """Calculate penalty for risk exposure."""
        penalty = 0.0
        
        for i, strategy in enumerate(self.strategies):
            # Higher penalty for higher risk
            risk_factor = (100 - strategy.risk_score) / 100
            penalty += risk_factor * self.current_allocations[i] * 0.1
        
        return penalty
    
    def _calculate_concentration_penalty(self) -> float:
        """Calculate penalty for concentrated allocations."""
        # Herfindahl index
        hhi = np.sum(self.current_allocations ** 2)
        
        # Penalty increases with concentration
        return hhi * 0.05


class AllocationOptimizer:
    """
    RL-based allocation optimizer using PPO.
    
    Learns optimal capital allocation strategies through
    interaction with the DeFi environment simulation.
    """
    
    MODEL_VERSION = "1.0.0"
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize the allocation optimizer.
        
        Args:
            model_path: Path to saved model
            config: Configuration dictionary
        """
        self.config = config or load_config()
        self.logger = setup_logging("AllocationOptimizer")
        
        # Get configuration
        self.agent_config = self.config.get("allocation_optimizer", {}).get("agent", {})
        self.constraints = self.config.get("allocation_optimizer", {}).get("constraints", {})
        self.reward_config = self.config.get("allocation_optimizer", {}).get("reward", {})
        
        # Initialize model (lazy loading)
        self._model = None
        self._model_path = model_path
    
    def _load_model(self):
        """Lazy load the RL model."""
        if self._model is not None:
            return
        
        try:
            from stable_baselines3 import PPO
            from stable_baselines3.common.vec_env import DummyVecEnv
            
            if self._model_path:
                self._model = PPO.load(self._model_path)
                self.logger.info(f"Loaded PPO model from {self._model_path}")
            else:
                self.logger.warning("No pre-trained model found. Using rule-based optimization.")
                self._model = None
        
        except ImportError:
            self.logger.warning("stable-baselines3 not available. Using rule-based optimization.")
            self._model = None
    
    def optimize(
        self,
        strategies: List[Strategy],
        total_tvl: float,
        current_allocations: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> AllocationDecision:
        """
        Compute optimal allocation.
        
        Args:
            strategies: List of available strategies
            total_tvl: Total TVL to allocate
            current_allocations: Current allocation weights
            constraints: Additional constraints
            
        Returns:
            AllocationDecision with optimal weights
        """
        # Load model if not already loaded
        self._load_model()
        
        # Merge constraints
        effective_constraints = {**self.constraints, **(constraints or {})}
        
        # Set current allocations
        if current_allocations:
            for strategy in strategies:
                strategy.current_allocation = current_allocations.get(strategy.id, 0.0)
        
        # Get optimal weights
        if self._model is not None:
            weights = self._rl_optimize(strategies, total_tvl, effective_constraints)
        else:
            weights = self._rule_based_optimize(strategies, total_tvl, effective_constraints)
        
        # Calculate expected metrics
        expected_apy = self._calculate_expected_apy(strategies, weights)
        expected_risk = self._calculate_expected_risk(strategies, weights)
        
        # Generate rebalance trades
        rebalance_trades = self._generate_rebalance_trades(
            strategies, weights, current_allocations or {}, total_tvl
        )
        
        # Estimate gas
        gas_estimate = len(rebalance_trades) * 5.0  # ~$5 per trade
        
        return AllocationDecision(
            weights=weights,
            expected_apy=expected_apy,
            expected_risk_score=expected_risk,
            rebalance_trades=rebalance_trades,
            gas_estimate=gas_estimate,
            confidence=0.85 if self._model else 0.65,
            timestamp=datetime.utcnow().isoformat(),
            model_version=self.MODEL_VERSION
        )
    
    def _rl_optimize(
        self,
        strategies: List[Strategy],
        total_tvl: float,
        constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """Use RL model to optimize allocation."""
        # Create environment
        env = AllocationEnvironment(
            strategies=strategies,
            initial_tvl=total_tvl,
            transaction_cost=constraints.get("transaction_cost", 0.001)
        )
        
        # Get observation
        obs = env.reset()
        
        # Get action from model
        action, _ = self._model.predict(obs, deterministic=True)
        
        # Normalize action
        weights = env._normalize_action(action)
        
        # Convert to dictionary
        return {
            strategy.id: float(weights[i])
            for i, strategy in enumerate(strategies)
        }
    
    def _rule_based_optimize(
        self,
        strategies: List[Strategy],
        total_tvl: float,
        constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Rule-based optimization using mean-variance approach.
        
        Maximizes: expected_yield - risk_penalty * variance
        Subject to: allocation constraints
        """
        max_single = constraints.get("max_single_allocation", 0.15)
        min_risk_score = constraints.get("min_risk_score", 50)
        max_chain = constraints.get("max_chain_allocation", 0.30)
        
        # Filter eligible strategies
        eligible = [s for s in strategies if s.risk_score >= min_risk_score]
        
        if not eligible:
            return {}
        
        # Calculate scores (yield adjusted for risk)
        scores = []
        for s in eligible:
            # Risk-adjusted score
            risk_factor = s.risk_score / 100.0
            yield_score = s.predicted_apy * risk_factor
            scores.append(yield_score)
        
        # Normalize scores
        total_score = sum(scores)
        if total_score == 0:
            # Equal weight if all scores are zero
            weights = {s.id: 1.0 / len(eligible) for s in eligible}
        else:
            weights = {}
            for i, s in enumerate(eligible):
                weights[s.id] = scores[i] / total_score
        
        # Apply constraints
        weights = self._apply_constraints(
            weights, eligible, max_single, max_chain
        )
        
        return weights
    
    def _apply_constraints(
        self,
        weights: Dict[str, float],
        strategies: List[Strategy],
        max_single: float,
        max_chain: float
    ) -> Dict[str, float]:
        """Apply allocation constraints."""
        # Create strategy lookup
        strategy_map = {s.id: s for s in strategies}
        
        # Apply single allocation cap
        for sid in weights:
            s = strategy_map.get(sid)
            if s:
                # Risk-based cap
                risk_cap = self._get_risk_cap(s.risk_score)
                weights[sid] = min(weights[sid], max_single, risk_cap)
        
        # Apply chain allocation cap
        chain_allocations = {}
        for sid, w in weights.items():
            s = strategy_map.get(sid)
            if s:
                chain = s.chain
                chain_allocations[chain] = chain_allocations.get(chain, 0) + w
        
        for chain, total in chain_allocations.items():
            if total > max_chain:
                # Scale down allocations on this chain
                scale = max_chain / total
                for sid, w in weights.items():
                    s = strategy_map.get(sid)
                    if s and s.chain == chain:
                        weights[sid] = w * scale
        
        # Re-normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def _get_risk_cap(self, risk_score: int) -> float:
        """Get maximum allocation based on risk score."""
        if risk_score >= 90:
            return 0.15
        elif risk_score >= 80:
            return 0.10
        elif risk_score >= 70:
            return 0.05
        elif risk_score >= 50:
            return 0.02
        else:
            return 0.0
    
    def _calculate_expected_apy(
        self,
        strategies: List[Strategy],
        weights: Dict[str, float]
    ) -> float:
        """Calculate expected APY from allocation."""
        total_apy = 0.0
        
        for strategy in strategies:
            weight = weights.get(strategy.id, 0.0)
            total_apy += strategy.predicted_apy * weight
        
        return total_apy
    
    def _calculate_expected_risk(
        self,
        strategies: List[Strategy],
        weights: Dict[str, float]
    ) -> float:
        """Calculate expected risk score from allocation."""
        total_risk = 0.0
        total_weight = 0.0
        
        for strategy in strategies:
            weight = weights.get(strategy.id, 0.0)
            total_risk += strategy.risk_score * weight
            total_weight += weight
        
        if total_weight > 0:
            return total_risk / total_weight
        return 0.0
    
    def _generate_rebalance_trades(
        self,
        strategies: List[Strategy],
        target_weights: Dict[str, float],
        current_allocations: Dict[str, float],
        total_tvl: float
    ) -> List[Dict[str, Any]]:
        """Generate list of trades needed to rebalance."""
        trades = []
        threshold = 0.005  # 0.5% threshold for rebalancing
        
        for strategy in strategies:
            target = target_weights.get(strategy.id, 0.0)
            current = current_allocations.get(strategy.id, 0.0)
            
            diff = target - current
            
            if abs(diff) > threshold:
                trades.append({
                    "strategy_id": strategy.id,
                    "protocol": strategy.protocol,
                    "chain": strategy.chain,
                    "asset": strategy.asset,
                    "action": "deposit" if diff > 0 else "withdraw",
                    "amount_usd": abs(diff) * total_tvl,
                    "current_weight": current,
                    "target_weight": target
                })
        
        # Sort by amount (largest first)
        trades.sort(key=lambda x: x["amount_usd"], reverse=True)
        
        return trades
    
    def to_dict(self, decision: AllocationDecision) -> Dict[str, Any]:
        """Convert allocation decision to dictionary for API response."""
        return {
            "weights": decision.weights,
            "expected_apy": decision.expected_apy,
            "expected_risk_score": decision.expected_risk_score,
            "rebalance_trades": decision.rebalance_trades,
            "gas_estimate": decision.gas_estimate,
            "confidence": decision.confidence,
            "timestamp": decision.timestamp,
            "model_version": decision.model_version
        }
    
    def train(
        self,
        strategies: List[Strategy],
        total_timesteps: int = 100000,
        save_path: Optional[str] = None
    ):
        """
        Train the RL agent.
        
        Args:
            strategies: List of strategies for training environment
            total_timesteps: Number of training steps
            save_path: Path to save trained model
        """
        try:
            from stable_baselines3 import PPO
            from stable_baselines3.common.vec_env import DummyVecEnv
            
            # Create environment
            env = AllocationEnvironment(strategies=strategies)
            
            # Wrap in vector environment
            vec_env = DummyVecEnv([lambda: env])
            
            # Create model
            self._model = PPO(
                "MlpPolicy",
                vec_env,
                learning_rate=self.agent_config.get("learning_rate", 0.0003),
                n_steps=self.agent_config.get("n_steps", 2048),
                batch_size=self.agent_config.get("batch_size", 64),
                n_epochs=self.agent_config.get("n_epochs", 10),
                gamma=self.agent_config.get("gamma", 0.99),
                verbose=1
            )
            
            # Train
            self.logger.info(f"Starting training for {total_timesteps} timesteps...")
            self._model.learn(total_timesteps=total_timesteps)
            
            # Save
            if save_path:
                self._model.save(save_path)
                self.logger.info(f"Model saved to {save_path}")
            
        except ImportError as e:
            self.logger.error(f"Cannot train: stable-baselines3 not available: {e}")
            raise