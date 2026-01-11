"""
AquaWatch NRW - Blockchain Water Credits
========================================

"Carbon credits but for water."

Features:
1. Tokenized water savings
2. Immutable audit trail
3. Water trading marketplace
4. ESG reporting integration
5. Smart contracts for automatic incentives
"""

import logging
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


# =============================================================================
# BLOCKCHAIN PRIMITIVES
# =============================================================================

@dataclass
class Block:
    """A block in the water credit blockchain."""
    index: int
    timestamp: datetime
    transactions: List[Dict]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    
    def calculate_hash(self) -> str:
        """Calculate block hash."""
        block_data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()
    
    def mine(self, difficulty: int = 2):
        """Mine the block (proof of work)."""
        prefix = "0" * difficulty
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.calculate_hash()


class TransactionType(Enum):
    WATER_CREDIT_MINT = "water_credit_mint"       # Create new credits from verified savings
    WATER_CREDIT_TRANSFER = "water_credit_transfer"  # Transfer between parties
    WATER_CREDIT_RETIRE = "water_credit_retire"   # Use/retire credits
    LEAK_VERIFIED = "leak_verified"               # Immutable leak record
    REPAIR_COMPLETED = "repair_completed"         # Repair verification
    AUDIT = "audit"                               # External audit record


@dataclass
class Transaction:
    """A blockchain transaction."""
    tx_id: str
    tx_type: TransactionType
    timestamp: datetime
    
    # Parties
    from_address: str
    to_address: str
    
    # Data
    data: Dict = field(default_factory=dict)
    
    # Credits (if applicable)
    credit_amount: float = 0.0  # In liters equivalent
    
    # Verification
    verified: bool = False
    verifier: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "tx_id": self.tx_id,
            "tx_type": self.tx_type.value,
            "timestamp": self.timestamp.isoformat(),
            "from": self.from_address,
            "to": self.to_address,
            "data": self.data,
            "credit_amount": self.credit_amount,
            "verified": self.verified,
            "verifier": self.verifier
        }


# =============================================================================
# WATER CREDIT SYSTEM
# =============================================================================

@dataclass
class WaterCredit:
    """Tokenized water savings."""
    credit_id: str
    owner: str
    
    # Value
    liters_saved: float
    co2_equivalent_kg: float  # Water savings also save energy
    
    # Origin
    origin_utility: str
    origin_dma: str
    leak_id: str
    
    # Metadata
    created_at: datetime
    expires_at: datetime = None
    
    # Status
    is_retired: bool = False
    retired_at: Optional[datetime] = None
    retired_by: str = ""
    
    @property
    def value_usd(self) -> float:
        """Calculate credit value in USD."""
        # Example pricing: $0.01 per 1000 liters saved
        water_value = self.liters_saved / 1000 * 0.01
        # Plus carbon credit value: ~$50/ton CO2
        carbon_value = self.co2_equivalent_kg / 1000 * 50
        return water_value + carbon_value


class WaterCreditBlockchain:
    """
    Blockchain for water savings verification.
    
    "Trust, but verify. Or just verify."
    """
    
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.credits: Dict[str, WaterCredit] = {}
        self.balances: Dict[str, float] = {}  # Address -> total credits
        
        # Difficulty for mining
        self.difficulty = 2
        
        # Create genesis block
        self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the first block."""
        genesis = Block(
            index=0,
            timestamp=datetime.now(timezone.utc),
            transactions=[],
            previous_hash="0" * 64
        )
        genesis.hash = genesis.calculate_hash()
        self.chain.append(genesis)
        logger.info("🔗 Genesis block created")
    
    def get_latest_block(self) -> Block:
        """Get the most recent block."""
        return self.chain[-1]
    
    def add_transaction(self, tx: Transaction) -> str:
        """Add a transaction to pending pool."""
        self.pending_transactions.append(tx)
        logger.info(f"📝 Transaction added: {tx.tx_id}")
        return tx.tx_id
    
    def mine_pending_transactions(self, miner_address: str) -> Block:
        """Mine all pending transactions into a new block."""
        if not self.pending_transactions:
            return None
        
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now(timezone.utc),
            transactions=[tx.to_dict() for tx in self.pending_transactions],
            previous_hash=self.get_latest_block().hash
        )
        
        new_block.mine(self.difficulty)
        self.chain.append(new_block)
        
        # Process transactions
        for tx in self.pending_transactions:
            self._process_transaction(tx)
        
        self.pending_transactions = []
        
        logger.info(f"⛏️ Block #{new_block.index} mined with {len(new_block.transactions)} transactions")
        return new_block
    
    def _process_transaction(self, tx: Transaction):
        """Process a mined transaction."""
        if tx.tx_type == TransactionType.WATER_CREDIT_MINT:
            # Create new credits
            credit = WaterCredit(
                credit_id=tx.tx_id,
                owner=tx.to_address,
                liters_saved=tx.credit_amount,
                co2_equivalent_kg=tx.credit_amount * 0.001,  # Rough estimate
                origin_utility=tx.data.get("utility", ""),
                origin_dma=tx.data.get("dma", ""),
                leak_id=tx.data.get("leak_id", ""),
                created_at=tx.timestamp
            )
            self.credits[credit.credit_id] = credit
            self.balances[tx.to_address] = self.balances.get(tx.to_address, 0) + tx.credit_amount
        
        elif tx.tx_type == TransactionType.WATER_CREDIT_TRANSFER:
            # Transfer credits
            self.balances[tx.from_address] = self.balances.get(tx.from_address, 0) - tx.credit_amount
            self.balances[tx.to_address] = self.balances.get(tx.to_address, 0) + tx.credit_amount
        
        elif tx.tx_type == TransactionType.WATER_CREDIT_RETIRE:
            # Retire credits
            credit_id = tx.data.get("credit_id")
            if credit_id in self.credits:
                credit = self.credits[credit_id]
                credit.is_retired = True
                credit.retired_at = tx.timestamp
                credit.retired_by = tx.from_address
    
    def verify_chain(self) -> bool:
        """Verify blockchain integrity."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # Check hash
            if current.hash != current.calculate_hash():
                return False
            
            # Check chain linkage
            if current.previous_hash != previous.hash:
                return False
        
        return True
    
    def get_balance(self, address: str) -> float:
        """Get credit balance for address."""
        return self.balances.get(address, 0)
    
    def get_credit_history(self, address: str) -> List[Dict]:
        """Get transaction history for address."""
        history = []
        for block in self.chain:
            for tx_data in block.transactions:
                if tx_data.get("from") == address or tx_data.get("to") == address:
                    history.append({
                        "block": block.index,
                        "timestamp": tx_data["timestamp"],
                        "type": tx_data["tx_type"],
                        "amount": tx_data["credit_amount"],
                        "from": tx_data["from"],
                        "to": tx_data["to"]
                    })
        return history


# =============================================================================
# WATER SAVINGS VERIFIER
# =============================================================================

class WaterSavingsVerifier:
    """
    Verifies water savings for credit minting.
    
    Uses multiple data sources:
    - Flow meter readings
    - Repair records
    - Before/after comparisons
    """
    
    def __init__(self, blockchain: WaterCreditBlockchain):
        self.blockchain = blockchain
        self.verification_threshold = 0.95  # 95% confidence required
    
    def verify_leak_repair(self, 
                          leak_id: str,
                          utility_id: str,
                          dma_id: str,
                          pre_repair_flow: float,  # L/hour
                          post_repair_flow: float,  # L/hour
                          hours_monitored: int = 24) -> Dict:
        """Verify water savings from a leak repair."""
        
        # Calculate savings
        hourly_savings = pre_repair_flow - post_repair_flow
        
        if hourly_savings <= 0:
            return {
                "verified": False,
                "reason": "No savings detected"
            }
        
        # Annualize savings
        annual_savings_liters = hourly_savings * 24 * 365
        
        # Calculate confidence
        # Higher monitoring time = higher confidence
        confidence = min(0.99, 0.7 + (hours_monitored / 168) * 0.29)  # 168 = 1 week
        
        if confidence < self.verification_threshold:
            return {
                "verified": False,
                "reason": f"Confidence too low: {confidence:.0%}"
            }
        
        # Create mint transaction
        tx = Transaction(
            tx_id=f"MINT_{leak_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            tx_type=TransactionType.WATER_CREDIT_MINT,
            timestamp=datetime.now(timezone.utc),
            from_address="AQUAWATCH_SYSTEM",
            to_address=utility_id,
            credit_amount=annual_savings_liters,
            data={
                "leak_id": leak_id,
                "utility": utility_id,
                "dma": dma_id,
                "pre_repair_flow": pre_repair_flow,
                "post_repair_flow": post_repair_flow,
                "hours_monitored": hours_monitored,
                "confidence": confidence
            },
            verified=True,
            verifier="AQUAWATCH_VERIFIER"
        )
        
        self.blockchain.add_transaction(tx)
        
        # Also record leak as immutable record
        leak_tx = Transaction(
            tx_id=f"LEAK_{leak_id}",
            tx_type=TransactionType.LEAK_VERIFIED,
            timestamp=datetime.now(timezone.utc),
            from_address="AQUAWATCH_SYSTEM",
            to_address=utility_id,
            data={
                "leak_id": leak_id,
                "location_dma": dma_id,
                "leak_rate": pre_repair_flow,
                "verification_method": "flow_comparison"
            }
        )
        self.blockchain.add_transaction(leak_tx)
        
        return {
            "verified": True,
            "annual_savings_liters": annual_savings_liters,
            "credits_minted": annual_savings_liters,
            "confidence": confidence,
            "tx_id": tx.tx_id
        }


# =============================================================================
# WATER CREDIT MARKETPLACE
# =============================================================================

@dataclass
class CreditListing:
    """A listing in the marketplace."""
    listing_id: str
    seller: str
    credit_amount: float
    price_usd_per_1000l: float
    created_at: datetime
    status: str = "active"  # active, sold, cancelled


class WaterCreditMarketplace:
    """
    Marketplace for trading water credits.
    
    Connects water utilities, ESG investors, and companies
    seeking to offset water usage.
    """
    
    def __init__(self, blockchain: WaterCreditBlockchain):
        self.blockchain = blockchain
        self.listings: Dict[str, CreditListing] = {}
        self.trade_history: List[Dict] = []
    
    def create_listing(self, 
                       seller: str,
                       credit_amount: float,
                       price_usd_per_1000l: float) -> CreditListing:
        """Create a new credit listing."""
        
        # Verify seller has enough credits
        balance = self.blockchain.get_balance(seller)
        if balance < credit_amount:
            raise ValueError(f"Insufficient credits: {balance} < {credit_amount}")
        
        listing_id = f"LIST_{len(self.listings)+1:06d}"
        listing = CreditListing(
            listing_id=listing_id,
            seller=seller,
            credit_amount=credit_amount,
            price_usd_per_1000l=price_usd_per_1000l,
            created_at=datetime.now(timezone.utc)
        )
        
        self.listings[listing_id] = listing
        logger.info(f"📋 Listing created: {listing_id} - {credit_amount:.0f}L @ ${price_usd_per_1000l}/1000L")
        
        return listing
    
    def buy_credits(self, 
                    listing_id: str,
                    buyer: str,
                    amount: float = None) -> Dict:
        """Buy credits from a listing."""
        
        listing = self.listings.get(listing_id)
        if not listing or listing.status != "active":
            raise ValueError("Invalid or inactive listing")
        
        buy_amount = amount or listing.credit_amount
        if buy_amount > listing.credit_amount:
            raise ValueError("Insufficient credits in listing")
        
        total_price = (buy_amount / 1000) * listing.price_usd_per_1000l
        
        # Create transfer transaction
        tx = Transaction(
            tx_id=f"TRANSFER_{listing_id}_{datetime.now().strftime('%H%M%S')}",
            tx_type=TransactionType.WATER_CREDIT_TRANSFER,
            timestamp=datetime.now(timezone.utc),
            from_address=listing.seller,
            to_address=buyer,
            credit_amount=buy_amount,
            data={
                "listing_id": listing_id,
                "price_usd": total_price,
                "price_per_1000l": listing.price_usd_per_1000l
            }
        )
        
        self.blockchain.add_transaction(tx)
        
        # Update listing
        listing.credit_amount -= buy_amount
        if listing.credit_amount <= 0:
            listing.status = "sold"
        
        # Record trade
        self.trade_history.append({
            "listing_id": listing_id,
            "buyer": buyer,
            "seller": listing.seller,
            "amount": buy_amount,
            "price_usd": total_price,
            "timestamp": datetime.now(timezone.utc)
        })
        
        logger.info(f"💰 Trade executed: {buy_amount:.0f}L for ${total_price:.2f}")
        
        return {
            "success": True,
            "amount_purchased": buy_amount,
            "total_price_usd": total_price,
            "tx_id": tx.tx_id
        }
    
    def get_active_listings(self) -> List[Dict]:
        """Get all active listings."""
        return [
            {
                "listing_id": l.listing_id,
                "seller": l.seller,
                "available": l.credit_amount,
                "price_per_1000l": l.price_usd_per_1000l,
                "total_value_usd": (l.credit_amount / 1000) * l.price_usd_per_1000l,
                "created_at": l.created_at.isoformat()
            }
            for l in self.listings.values()
            if l.status == "active"
        ]
    
    def get_market_stats(self) -> Dict:
        """Get marketplace statistics."""
        active = [l for l in self.listings.values() if l.status == "active"]
        
        total_volume = sum(l.credit_amount for l in active)
        avg_price = sum(l.price_usd_per_1000l for l in active) / len(active) if active else 0
        
        # Recent trades
        recent_trades = self.trade_history[-10:] if self.trade_history else []
        trade_volume = sum(t["amount"] for t in recent_trades)
        trade_value = sum(t["price_usd"] for t in recent_trades)
        
        return {
            "active_listings": len(active),
            "total_volume_liters": total_volume,
            "average_price_per_1000l": avg_price,
            "recent_trade_volume": trade_volume,
            "recent_trade_value_usd": trade_value,
            "total_trades": len(self.trade_history)
        }


# =============================================================================
# ESG REPORTING
# =============================================================================

class ESGReporter:
    """
    Generate ESG reports from blockchain data.
    
    Provides auditable proof of water savings for:
    - Annual reports
    - Sustainability disclosures
    - Carbon credit verification
    """
    
    def __init__(self, blockchain: WaterCreditBlockchain):
        self.blockchain = blockchain
    
    def generate_report(self, 
                        entity: str,
                        start_date: datetime,
                        end_date: datetime) -> Dict:
        """Generate ESG report for an entity."""
        
        # Get all transactions for entity
        history = self.blockchain.get_credit_history(entity)
        
        # Filter by date
        relevant = [
            tx for tx in history
            if start_date.isoformat() <= tx["timestamp"] <= end_date.isoformat()
        ]
        
        # Calculate metrics
        minted = sum(tx["amount"] for tx in relevant if tx["type"] == "water_credit_mint")
        transferred_in = sum(tx["amount"] for tx in relevant 
                           if tx["type"] == "water_credit_transfer" and tx["to"] == entity)
        transferred_out = sum(tx["amount"] for tx in relevant 
                             if tx["type"] == "water_credit_transfer" and tx["from"] == entity)
        retired = sum(tx["amount"] for tx in relevant if tx["type"] == "water_credit_retire")
        
        # Environmental impact
        water_saved_m3 = minted / 1000
        co2_saved_kg = water_saved_m3 * 0.001 * 1000  # Rough estimate
        
        return {
            "entity": entity,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "water_metrics": {
                "credits_minted": minted,
                "credits_purchased": transferred_in,
                "credits_sold": transferred_out,
                "credits_retired": retired,
                "net_credits": minted + transferred_in - transferred_out - retired,
                "water_saved_cubic_meters": water_saved_m3
            },
            "environmental_impact": {
                "co2_equivalent_kg": co2_saved_kg,
                "equivalent_households_yearly_usage": water_saved_m3 / 150,  # ~150m³/year/household
                "equivalent_olympic_pools": water_saved_m3 / 2500
            },
            "blockchain_proof": {
                "chain_verified": self.blockchain.verify_chain(),
                "transactions_count": len(relevant),
                "latest_block": self.blockchain.get_latest_block().index
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

water_blockchain = WaterCreditBlockchain()
verifier = WaterSavingsVerifier(water_blockchain)
marketplace = WaterCreditMarketplace(water_blockchain)
esg_reporter = ESGReporter(water_blockchain)


# =============================================================================
# DEMO
# =============================================================================

def demo_blockchain():
    """Demonstrate blockchain water credits."""
    
    print("=" * 60)
    print("🔗 AQUAWATCH WATER CREDIT BLOCKCHAIN")
    print("=" * 60)
    
    # Verify some leak repairs
    print("\n🔍 VERIFYING LEAK REPAIRS...")
    
    repairs = [
        ("LEAK_001", "LWSC", "DMA_KABULONGA", 500, 50, 72),
        ("LEAK_002", "LWSC", "DMA_CHELSTONE", 1200, 100, 48),
        ("LEAK_003", "NWSC", "DMA_INDUSTRIAL", 2000, 200, 96),
    ]
    
    for leak_id, utility, dma, pre, post, hours in repairs:
        result = verifier.verify_leak_repair(
            leak_id=leak_id,
            utility_id=utility,
            dma_id=dma,
            pre_repair_flow=pre,
            post_repair_flow=post,
            hours_monitored=hours
        )
        if result["verified"]:
            print(f"  ✅ {leak_id}: {result['annual_savings_liters']:,.0f}L/year credits minted")
    
    # Mine the block
    print("\n⛏️ MINING PENDING TRANSACTIONS...")
    block = water_blockchain.mine_pending_transactions("AQUAWATCH_MINER")
    print(f"  Block #{block.index} mined with {len(block.transactions)} transactions")
    
    # Check balances
    print("\n💰 CREDIT BALANCES:")
    for utility in ["LWSC", "NWSC"]:
        balance = water_blockchain.get_balance(utility)
        print(f"  {utility}: {balance:,.0f} liters equivalent")
    
    # Create marketplace listing
    print("\n📋 MARKETPLACE:")
    listing = marketplace.create_listing(
        seller="LWSC",
        credit_amount=5000000,  # 5 million liters
        price_usd_per_1000l=0.015
    )
    print(f"  Listing: {listing.credit_amount:,.0f}L @ ${listing.price_usd_per_1000l}/1000L")
    
    # Simulate a purchase
    print("\n🛒 SIMULATING PURCHASE...")
    purchase = marketplace.buy_credits(
        listing_id=listing.listing_id,
        buyer="ESG_INVESTOR_1",
        amount=1000000
    )
    print(f"  Purchased: {purchase['amount_purchased']:,.0f}L for ${purchase['total_price_usd']:.2f}")
    
    # Mine transfer
    water_blockchain.mine_pending_transactions("AQUAWATCH_MINER")
    
    # Market stats
    print("\n📊 MARKET STATISTICS:")
    stats = marketplace.get_market_stats()
    print(f"  Active Listings: {stats['active_listings']}")
    print(f"  Total Volume: {stats['total_volume_liters']:,.0f} liters")
    print(f"  Average Price: ${stats['average_price_per_1000l']:.3f}/1000L")
    
    # ESG Report
    print("\n📄 ESG REPORT (LWSC):")
    report = esg_reporter.generate_report(
        entity="LWSC",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    print(f"  Water Saved: {report['water_metrics']['water_saved_cubic_meters']:,.0f} m³")
    print(f"  CO₂ Equivalent: {report['environmental_impact']['co2_equivalent_kg']:,.0f} kg")
    print(f"  Blockchain Verified: {'✅' if report['blockchain_proof']['chain_verified'] else '❌'}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_blockchain()
