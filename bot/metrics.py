# Created: 2026-01-16
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from loguru import logger

class ArbMetrics:
    """Prometheus metrics for Flash-Arb Sentinel."""
    
    def __init__(self, port: int = 9090):
        # Counters
        self.arbs_discovered = Counter(
            'kerne_arb_discovered_total',
            'Total arbitrage opportunities discovered',
            ['base_token', 'hop_count']
        )
        self.arbs_executed = Counter(
            'kerne_arb_executed_total',
            'Total arbitrage executions attempted',
            ['status', 'lender']
        )
        self.arbs_blocked = Counter(
            'kerne_arb_blocked_total',
            'Arbitrages blocked by risk gate',
            ['reason']
        )
        
        # Gauges
        self.profit_usd = Gauge(
            'kerne_arb_profit_usd',
            'Last successful arb profit in USD'
        )
        self.gas_cost_usd = Gauge(
            'kerne_arb_gas_cost_usd',
            'Last arb gas cost in USD'
        )
        self.health_score = Gauge(
            'kerne_sentinel_health_score',
            'Current vault health score'
        )
        self.net_delta = Gauge(
            'kerne_sentinel_net_delta',
            'Current net delta exposure'
        )
        self.volatility_24h = Gauge(
            'kerne_market_volatility_24h',
            'Current 24h market volatility'
        )
        
        # Histograms
        self.discovery_latency = Histogram(
            'kerne_arb_discovery_latency_seconds',
            'Time to discover arbitrage opportunities',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        self.execution_latency = Histogram(
            'kerne_arb_execution_latency_seconds',
            'Time from discovery to execution completion',
            buckets=[1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics exporter started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus exporter: {e}")
    
    def record_discovery(self, base_token: str, hop_count: int, latency: float):
        self.arbs_discovered.labels(base_token=base_token, hop_count=str(hop_count)).inc()
        self.discovery_latency.observe(latency)
    
    def record_execution(self, success: bool, lender: str, profit_usd: float, gas_usd: float, latency: float):
        status = "success" if success else "failed"
        self.arbs_executed.labels(status=status, lender=lender).inc()
        if success:
            self.profit_usd.set(profit_usd)
            self.gas_cost_usd.set(gas_usd)
        self.execution_latency.observe(latency)
    
    def record_blocked(self, reason: str):
        self.arbs_blocked.labels(reason=reason).inc()
    
    def update_risk_metrics(self, health_score: float, net_delta: float, volatility: float):
        self.health_score.set(health_score)
        self.net_delta.set(net_delta)
        self.volatility_24h.set(volatility)
