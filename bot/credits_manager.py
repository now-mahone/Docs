# Created: 2025-12-29
import os
import json
from loguru import logger

class CreditsManager:
    """
    Manages the Kerne Credits (Points Program) and Referral Commissions.
    Points are awarded based on TVL contribution and time.
    Commissions are real ETH-based rewards from performance fees.
    """
    
    def __init__(self, db_path: str = "bot/data/credits.json", referral_db_path: str = "bot/data/referrals.json"):
        self.db_path = db_path
        self.referral_db_path = referral_db_path
        self._ensure_db_exists()
        self.credits_data = self._load_db()
        self.referral_data = self._load_referral_db()

    def _ensure_db_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({}, f)
        if not os.path.exists(self.referral_db_path):
            with open(self.referral_db_path, "w") as f:
                json.dump({}, f)

    def _load_db(self):
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _load_referral_db(self):
        try:
            with open(self.referral_db_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_db(self):
        with open(self.db_path, "w") as f:
            json.dump(self.credits_data, f, indent=4)
        with open(self.referral_db_path, "w") as f:
            json.dump(self.referral_data, f, indent=4)

    def update_credits(self, address: str, balance_eth: float, referred_by: str = None):
        """
        Updates credits for a specific address.
        Called periodically by the main loop.
        Implements Tiered Referrals: 10% for direct, 5% for secondary.
        """
        address = address.lower()
        if address not in self.credits_data:
            self.credits_data[address] = {
                "total_credits": 0.0,
                "last_update": 0,
                "multiplier": 1.0,
                "referred_by": referred_by.lower() if referred_by else None,
                "referral_count": 0
            }
            # If this user was referred, update the referrer's count and multiplier
            if referred_by:
                ref_addr = referred_by.lower()
                if ref_addr in self.credits_data:
                    self.credits_data[ref_addr]["referral_count"] += 1
                    # Each referral adds 0.1 to multiplier, max 3.0 (Viral Expansion)
                    self.credits_data[ref_addr]["multiplier"] = min(3.0, 1.0 + (self.credits_data[ref_addr]["referral_count"] * 0.1))
                    logger.info(f"Referrer {ref_addr} multiplier updated to {self.credits_data[ref_addr]['multiplier']:.2f}")
        
        # Simple accrual logic: 1 credit per ETH per hour
        accrual = balance_eth * self.credits_data[address]["multiplier"]
        self.credits_data[address]["total_credits"] += accrual
        
        # Tier 1 Referral bonus: Direct referrer gets 10%
        ref_addr = self.credits_data[address].get("referred_by")
        if ref_addr and ref_addr in self.credits_data:
            ref_bonus = accrual * 0.10
            self.credits_data[ref_addr]["total_credits"] += ref_bonus
            logger.info(f"Tier 1 Referral bonus of {ref_bonus:.4f} awarded to {ref_addr}")

            # Tier 2 Referral bonus: Secondary referrer gets 5%
            secondary_ref_addr = self.credits_data[ref_addr].get("referred_by")
            if secondary_ref_addr and secondary_ref_addr in self.credits_data:
                sec_bonus = accrual * 0.05
                self.credits_data[secondary_ref_addr]["total_credits"] += sec_bonus
                logger.info(f"Tier 2 Referral bonus of {sec_bonus:.4f} awarded to {secondary_ref_addr}")

        logger.info(f"Accrued {accrual:.4f} credits for {address}. Total: {self.credits_data[address]['total_credits']:.4f}")
        self._save_db()

    def calculate_referral_commissions(self, address: str, harvested_yield_eth: float):
        """
        Calculates and attributes real ETH commissions to referrers.
        harvested_yield_eth: The total yield harvested for this user in this period.
        """
        address = address.lower()
        if address not in self.credits_data:
            return

        # Tier 1 Referral bonus: Direct referrer gets 10% of performance fee
        # Assuming performance fee is 20% of yield
        performance_fee = harvested_yield_eth * 0.20
        
        ref_addr = self.credits_data[address].get("referred_by")
        if ref_addr:
            ref_addr = ref_addr.lower()
            if ref_addr not in self.referral_data:
                self.referral_data[ref_addr] = {
                    "pending_commissions": 0.0,
                    "total_earned": 0.0,
                    "total_volume_referred": 0.0,
                    "referral_count": 0,
                    "wealth_velocity": 0.0
                }
            
            tier1_bonus = performance_fee * 0.10
            self.referral_data[ref_addr]["pending_commissions"] += tier1_bonus
            self.referral_data[ref_addr]["total_earned"] += tier1_bonus
            logger.info(f"Tier 1 ETH Commission of {tier1_bonus:.6f} awarded to {ref_addr}")

            # Tier 2 Referral bonus: Secondary referrer gets 5% of performance fee
            secondary_ref_addr = self.credits_data.get(ref_addr, {}).get("referred_by")
            if secondary_ref_addr:
                secondary_ref_addr = secondary_ref_addr.lower()
                if secondary_ref_addr not in self.referral_data:
                    self.referral_data[secondary_ref_addr] = {
                        "pending_commissions": 0.0,
                        "total_earned": 0.0,
                        "total_volume_referred": 0.0,
                        "referral_count": 0,
                        "wealth_velocity": 0.0
                    }
                
                tier2_bonus = performance_fee * 0.05
                self.referral_data[secondary_ref_addr]["pending_commissions"] += tier2_bonus
                self.referral_data[secondary_ref_addr]["total_earned"] += tier2_bonus
                logger.info(f"Tier 2 ETH Commission of {tier2_bonus:.6f} awarded to {secondary_ref_addr}")

        self._save_db()

    def get_credits(self, address: str) -> float:
        return self.credits_data.get(address.lower(), {}).get("total_credits", 0.0)

if __name__ == "__main__":
    manager = CreditsManager()
    manager.update_credits("0x1234567890123456789012345678901234567890", 10.5)
    print(f"Credits: {manager.get_credits('0x1234567890123456789012345678901234567890')}")
