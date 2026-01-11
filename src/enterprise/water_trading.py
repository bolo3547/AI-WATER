"""
AquaWatch Enterprise - Real-Time Water Trading Platform
=======================================================

"The NASDAQ for water."

Enterprise water trading features:
1. Water rights marketplace
2. Spot and futures trading
3. Cross-basin transfers
4. Price discovery algorithms
5. Regulatory compliance
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import random
import math

logger = logging.getLogger(__name__)


# =============================================================================
# WATER TRADING CONCEPTS
# =============================================================================

class TradeType(Enum):
    SPOT = "spot"             # Immediate delivery
    FORWARD = "forward"        # Future delivery
    OPTION = "option"          # Right to buy/sell
    SWAP = "swap"              # Exchange commitments


class OrderType(Enum):
    MARKET = "market"          # Execute at current price
    LIMIT = "limit"            # Execute at specific price
    STOP = "stop"              # Trigger at price point


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class WaterQuality(Enum):
    POTABLE = "potable"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"
    RECYCLED = "recycled"


# =============================================================================
# WATER BASINS & MARKETS
# =============================================================================

@dataclass
class WaterBasin:
    """Hydrological water basin."""
    basin_id: str
    name: str
    country: str
    
    # Capacity
    total_capacity_million_m3: float
    current_level_percent: float
    
    # Flow
    annual_inflow_million_m3: float
    annual_consumption_million_m3: float
    
    # Status
    stress_level: str  # low, medium, high, extremely_high
    trading_enabled: bool = True
    regulatory_authority: str = ""


@dataclass
class WaterMarket:
    """Regional water trading market."""
    market_id: str
    name: str
    basins: List[str]  # basin_ids
    currency: str
    
    # Trading hours
    trading_days: List[str]  # mon, tue, etc.
    trading_hours: Tuple[int, int]  # (start_hour, end_hour) UTC
    
    # Pricing
    reference_price_per_m3: float
    price_floor: float = None
    price_cap: float = None
    
    # Volume
    daily_volume_m3: float = 0
    
    # Status
    is_open: bool = False


# South African and Zambian markets
WATER_BASINS = {
    "SA_VAAL": WaterBasin(
        basin_id="SA_VAAL",
        name="Vaal River System",
        country="South Africa",
        total_capacity_million_m3=10500,
        current_level_percent=68,
        annual_inflow_million_m3=3200,
        annual_consumption_million_m3=2800,
        stress_level="high",
        regulatory_authority="DWS South Africa"
    ),
    "SA_ORANGE": WaterBasin(
        basin_id="SA_ORANGE",
        name="Orange River System",
        country="South Africa",
        total_capacity_million_m3=14500,
        current_level_percent=52,
        annual_inflow_million_m3=4100,
        annual_consumption_million_m3=3600,
        stress_level="extremely_high",
        regulatory_authority="DWS South Africa"
    ),
    "ZM_KAFUE": WaterBasin(
        basin_id="ZM_KAFUE",
        name="Kafue River Basin",
        country="Zambia",
        total_capacity_million_m3=8500,
        current_level_percent=75,
        annual_inflow_million_m3=4800,
        annual_consumption_million_m3=2200,
        stress_level="medium",
        regulatory_authority="WARMA Zambia"
    ),
    "ZM_ZAMBEZI": WaterBasin(
        basin_id="ZM_ZAMBEZI",
        name="Zambezi River Basin",
        country="Zambia",
        total_capacity_million_m3=45000,
        current_level_percent=62,
        annual_inflow_million_m3=12000,
        annual_consumption_million_m3=5500,
        stress_level="low",
        regulatory_authority="ZAMCOM"
    )
}

WATER_MARKETS = {
    "SAWX": WaterMarket(
        market_id="SAWX",
        name="South African Water Exchange",
        basins=["SA_VAAL", "SA_ORANGE"],
        currency="ZAR",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        trading_hours=(6, 16),
        reference_price_per_m3=15.50,
        price_floor=5.00,
        price_cap=100.00
    ),
    "ZAMWX": WaterMarket(
        market_id="ZAMWX",
        name="Zambia Water Exchange",
        basins=["ZM_KAFUE", "ZM_ZAMBEZI"],
        currency="ZMW",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        trading_hours=(6, 15),
        reference_price_per_m3=8.25,
        price_floor=2.00,
        price_cap=50.00
    )
}


# =============================================================================
# WATER RIGHTS
# =============================================================================

@dataclass
class WaterRight:
    """Tradeable water right/allocation."""
    right_id: str
    owner_id: str
    basin_id: str
    
    # Allocation
    annual_allocation_m3: float
    unused_balance_m3: float
    
    # Quality
    quality: WaterQuality
    
    # Validity
    valid_from: datetime
    valid_until: datetime
    
    # Trading
    tradeable_percent: float = 100.0  # % that can be traded
    encumbered: bool = False  # Pledged as collateral
    
    # History
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


# =============================================================================
# ORDER BOOK & MATCHING
# =============================================================================

@dataclass
class Order:
    """Trading order."""
    order_id: str
    trader_id: str
    market_id: str
    basin_id: str
    
    # Order details
    side: OrderSide
    order_type: OrderType
    trade_type: TradeType
    
    # Quantity
    quantity_m3: float
    filled_quantity_m3: float = 0
    
    # Price
    price_per_m3: float = None  # None for market orders
    
    # Quality
    quality: WaterQuality = WaterQuality.INDUSTRIAL
    
    # Timing
    delivery_date: datetime = None  # For forwards
    expiry: datetime = None
    
    # Status
    status: str = "open"  # open, partial, filled, cancelled
    
    # Timestamps
    submitted_at: datetime = None
    
    def __post_init__(self):
        if self.submitted_at is None:
            self.submitted_at = datetime.now(timezone.utc)
        if self.delivery_date is None:
            self.delivery_date = datetime.now(timezone.utc) + timedelta(days=3)


@dataclass
class Trade:
    """Executed trade."""
    trade_id: str
    market_id: str
    basin_id: str
    
    buy_order_id: str
    sell_order_id: str
    buyer_id: str
    seller_id: str
    
    # Execution
    quantity_m3: float
    price_per_m3: float
    total_value: float
    
    # Quality
    quality: WaterQuality
    
    # Timing
    delivery_date: datetime
    executed_at: datetime = None
    
    def __post_init__(self):
        if self.executed_at is None:
            self.executed_at = datetime.now(timezone.utc)
        self.total_value = self.quantity_m3 * self.price_per_m3


class OrderBook:
    """Order book for a basin."""
    
    def __init__(self, basin_id: str, market_id: str):
        self.basin_id = basin_id
        self.market_id = market_id
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.trades: List[Trade] = []
        self.last_price: float = None
    
    def add_order(self, order: Order) -> Dict:
        """Add order to book."""
        
        if order.side == OrderSide.BUY:
            self.buy_orders.append(order)
            self.buy_orders.sort(key=lambda o: o.price_per_m3 or float('inf'), reverse=True)
        else:
            self.sell_orders.append(order)
            self.sell_orders.sort(key=lambda o: o.price_per_m3 or 0)
        
        # Try to match
        matches = self._match_orders()
        
        return {
            "order_id": order.order_id,
            "status": order.status,
            "trades_executed": len(matches)
        }
    
    def _match_orders(self) -> List[Trade]:
        """Match buy and sell orders."""
        
        trades = []
        
        for buy in self.buy_orders[:]:
            if buy.status == "filled":
                continue
            
            for sell in self.sell_orders[:]:
                if sell.status == "filled":
                    continue
                
                # Check quality match
                if buy.quality != sell.quality:
                    continue
                
                # Check price match
                if buy.order_type == OrderType.LIMIT and sell.order_type == OrderType.LIMIT:
                    if buy.price_per_m3 < sell.price_per_m3:
                        continue
                
                # Determine execution price (midpoint for limit orders)
                if buy.price_per_m3 and sell.price_per_m3:
                    exec_price = (buy.price_per_m3 + sell.price_per_m3) / 2
                else:
                    exec_price = buy.price_per_m3 or sell.price_per_m3 or self.last_price
                
                # Determine quantity
                buy_remaining = buy.quantity_m3 - buy.filled_quantity_m3
                sell_remaining = sell.quantity_m3 - sell.filled_quantity_m3
                exec_quantity = min(buy_remaining, sell_remaining)
                
                # Create trade
                trade = Trade(
                    trade_id=f"TRD_{uuid.uuid4().hex[:8].upper()}",
                    market_id=self.market_id,
                    basin_id=self.basin_id,
                    buy_order_id=buy.order_id,
                    sell_order_id=sell.order_id,
                    buyer_id=buy.trader_id,
                    seller_id=sell.trader_id,
                    quantity_m3=exec_quantity,
                    price_per_m3=exec_price,
                    total_value=exec_quantity * exec_price,
                    quality=buy.quality,
                    delivery_date=min(buy.delivery_date, sell.delivery_date)
                )
                
                trades.append(trade)
                self.trades.append(trade)
                self.last_price = exec_price
                
                # Update orders
                buy.filled_quantity_m3 += exec_quantity
                sell.filled_quantity_m3 += exec_quantity
                
                if buy.filled_quantity_m3 >= buy.quantity_m3:
                    buy.status = "filled"
                else:
                    buy.status = "partial"
                
                if sell.filled_quantity_m3 >= sell.quantity_m3:
                    sell.status = "filled"
                else:
                    sell.status = "partial"
                
                logger.info(f"Trade executed: {exec_quantity} m³ @ {exec_price}")
        
        return trades
    
    def get_book_depth(self, levels: int = 5) -> Dict:
        """Get order book depth."""
        
        bids = []
        asks = []
        
        for order in self.buy_orders[:levels]:
            if order.status not in ["filled", "cancelled"]:
                bids.append({
                    "price": order.price_per_m3,
                    "quantity": order.quantity_m3 - order.filled_quantity_m3
                })
        
        for order in self.sell_orders[:levels]:
            if order.status not in ["filled", "cancelled"]:
                asks.append({
                    "price": order.price_per_m3,
                    "quantity": order.quantity_m3 - order.filled_quantity_m3
                })
        
        return {
            "basin": self.basin_id,
            "last_price": self.last_price,
            "bids": bids,
            "asks": asks,
            "spread": (asks[0]["price"] - bids[0]["price"]) if bids and asks else None
        }


# =============================================================================
# PRICE DISCOVERY
# =============================================================================

class PriceEngine:
    """
    Water price discovery engine.
    
    Factors:
    - Supply/demand
    - Scarcity (basin levels)
    - Seasonality
    - Weather forecasts
    - Economic conditions
    """
    
    def __init__(self):
        self.price_history: Dict[str, List[Dict]] = {}
    
    def calculate_reference_price(self, 
                                   basin_id: str,
                                   base_price: float) -> Dict:
        """Calculate reference price for basin."""
        
        basin = WATER_BASINS.get(basin_id)
        if not basin:
            return {"error": "Basin not found"}
        
        # Scarcity adjustment
        level = basin.current_level_percent
        if level < 30:
            scarcity_mult = 2.0
        elif level < 50:
            scarcity_mult = 1.5
        elif level < 70:
            scarcity_mult = 1.2
        else:
            scarcity_mult = 1.0
        
        # Stress adjustment
        stress_mult = {
            "low": 0.9,
            "medium": 1.0,
            "high": 1.3,
            "extremely_high": 1.8
        }.get(basin.stress_level, 1.0)
        
        # Seasonal adjustment (simulate summer premium)
        month = datetime.now().month
        if month in [10, 11, 12, 1, 2]:  # Southern hemisphere summer
            seasonal_mult = 1.15
        elif month in [6, 7, 8]:  # Winter
            seasonal_mult = 0.90
        else:
            seasonal_mult = 1.0
        
        # Balance adjustment
        balance_ratio = basin.annual_inflow_million_m3 / basin.annual_consumption_million_m3
        if balance_ratio < 1.0:
            balance_mult = 1 + (1 - balance_ratio)
        else:
            balance_mult = 1.0
        
        # Calculate final price
        final_price = base_price * scarcity_mult * stress_mult * seasonal_mult * balance_mult
        
        return {
            "basin_id": basin_id,
            "basin_name": basin.name,
            "base_price": base_price,
            "adjustments": {
                "scarcity": f"{scarcity_mult:.2f}x (level: {level}%)",
                "stress": f"{stress_mult:.2f}x ({basin.stress_level})",
                "seasonal": f"{seasonal_mult:.2f}x",
                "balance": f"{balance_mult:.2f}x"
            },
            "reference_price": round(final_price, 2),
            "currency_per_m3": final_price
        }
    
    def get_price_forecast(self, basin_id: str, days: int = 30) -> List[Dict]:
        """Forecast future prices."""
        
        basin = WATER_BASINS.get(basin_id)
        if not basin:
            return []
        
        current = self.calculate_reference_price(basin_id, 10.0)["reference_price"]
        
        forecast = []
        price = current
        
        for day in range(1, days + 1):
            # Random walk with trend
            trend = -0.001 if basin.current_level_percent > 60 else 0.002
            volatility = 0.02
            
            change = trend + random.gauss(0, volatility)
            price = price * (1 + change)
            
            forecast.append({
                "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                "forecast_price": round(price, 2),
                "confidence_low": round(price * 0.9, 2),
                "confidence_high": round(price * 1.1, 2)
            })
        
        return forecast


# =============================================================================
# TRADING PLATFORM
# =============================================================================

class WaterTradingPlatform:
    """
    Complete water trading platform.
    
    "Trade water like any other commodity."
    """
    
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = {}
        self.price_engine = PriceEngine()
        self.water_rights: Dict[str, WaterRight] = {}
        self.trader_positions: Dict[str, List[Dict]] = {}
        
        # Initialize order books
        for basin_id in WATER_BASINS:
            market_id = self._get_market_for_basin(basin_id)
            self.order_books[basin_id] = OrderBook(basin_id, market_id)
    
    def _get_market_for_basin(self, basin_id: str) -> str:
        """Get market ID for basin."""
        for market_id, market in WATER_MARKETS.items():
            if basin_id in market.basins:
                return market_id
        return None
    
    def register_water_right(self, right: WaterRight) -> Dict:
        """Register tradeable water right."""
        
        self.water_rights[right.right_id] = right
        
        return {
            "success": True,
            "right_id": right.right_id,
            "tradeable_quantity": right.annual_allocation_m3 * (right.tradeable_percent / 100)
        }
    
    def submit_order(self, order: Order) -> Dict:
        """Submit trading order."""
        
        # Validate
        if order.basin_id not in self.order_books:
            return {"error": f"Invalid basin: {order.basin_id}"}
        
        # Check market hours
        market = WATER_MARKETS.get(order.market_id)
        if market:
            now = datetime.now(timezone.utc)
            day_name = now.strftime("%a").lower()
            hour = now.hour
            
            if day_name not in market.trading_days:
                return {"error": "Market closed on this day"}
            
            if hour < market.trading_hours[0] or hour >= market.trading_hours[1]:
                return {"error": f"Market hours: {market.trading_hours[0]}:00-{market.trading_hours[1]}:00 UTC"}
        
        # Add to order book
        result = self.order_books[order.basin_id].add_order(order)
        
        return result
    
    def get_market_data(self, market_id: str) -> Dict:
        """Get market data."""
        
        market = WATER_MARKETS.get(market_id)
        if not market:
            return {"error": "Market not found"}
        
        basin_data = []
        total_volume = 0
        
        for basin_id in market.basins:
            basin = WATER_BASINS[basin_id]
            book = self.order_books[basin_id]
            
            # Get reference price
            ref_price = self.price_engine.calculate_reference_price(
                basin_id, 
                market.reference_price_per_m3
            )
            
            # Calculate daily volume
            today_trades = [t for t in book.trades 
                          if t.executed_at.date() == datetime.now().date()]
            volume = sum(t.quantity_m3 for t in today_trades)
            total_volume += volume
            
            basin_data.append({
                "basin_id": basin_id,
                "basin_name": basin.name,
                "level_percent": basin.current_level_percent,
                "stress": basin.stress_level,
                "last_price": book.last_price,
                "reference_price": ref_price["reference_price"],
                "daily_volume_m3": volume,
                "order_book": book.get_book_depth(3)
            })
        
        return {
            "market_id": market_id,
            "market_name": market.name,
            "currency": market.currency,
            "is_open": True,  # Simplified
            "total_daily_volume_m3": total_volume,
            "basins": basin_data
        }
    
    def get_trader_positions(self, trader_id: str) -> Dict:
        """Get trader's positions."""
        
        positions = []
        total_value = 0
        
        for basin_id, book in self.order_books.items():
            # Find trader's trades
            buys = sum(t.quantity_m3 for t in book.trades if t.buyer_id == trader_id)
            sells = sum(t.quantity_m3 for t in book.trades if t.seller_id == trader_id)
            
            net = buys - sells
            
            if net != 0:
                price = book.last_price or 10.0
                value = net * price
                total_value += value
                
                positions.append({
                    "basin_id": basin_id,
                    "basin_name": WATER_BASINS[basin_id].name,
                    "net_position_m3": net,
                    "current_price": price,
                    "position_value": value
                })
        
        return {
            "trader_id": trader_id,
            "positions": positions,
            "total_value": total_value
        }


# =============================================================================
# DEMO
# =============================================================================

def demo_trading():
    """Demo water trading platform."""
    
    print("=" * 70)
    print("📈 AQUAWATCH ENTERPRISE - WATER TRADING PLATFORM")
    print("=" * 70)
    
    platform = WaterTradingPlatform()
    
    # Market overview
    print("\n🌍 WATER MARKETS:")
    print("-" * 50)
    
    for market_id, market in WATER_MARKETS.items():
        print(f"\n{market.name} ({market_id})")
        print(f"  Currency: {market.currency}")
        print(f"  Reference price: {market.reference_price_per_m3} per m³")
        print(f"  Basins: {', '.join(market.basins)}")
    
    # Basin data
    print("\n\n💧 BASIN STATUS:")
    print("-" * 50)
    
    for basin_id, basin in WATER_BASINS.items():
        print(f"\n{basin.name}")
        print(f"  Level: {basin.current_level_percent}%")
        print(f"  Stress: {basin.stress_level}")
        print(f"  Balance: {basin.annual_inflow_million_m3}M inflow / {basin.annual_consumption_million_m3}M consumption")
    
    # Price discovery
    print("\n\n💰 PRICE DISCOVERY:")
    print("-" * 50)
    
    for basin_id in ["SA_VAAL", "ZM_KAFUE"]:
        price = platform.price_engine.calculate_reference_price(basin_id, 10.0)
        print(f"\n{price['basin_name']}")
        print(f"  Base: R{price['base_price']}")
        print(f"  Scarcity: {price['adjustments']['scarcity']}")
        print(f"  Stress: {price['adjustments']['stress']}")
        print(f"  Reference: R{price['reference_price']}/m³")
    
    # Simulate trading
    print("\n\n📊 TRADING SIMULATION:")
    print("-" * 50)
    
    # Create some orders
    sell_order = Order(
        order_id="ORD_001",
        trader_id="MINING_CO",
        market_id="SAWX",
        basin_id="SA_VAAL",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        trade_type=TradeType.SPOT,
        quantity_m3=50000,
        price_per_m3=14.50,
        quality=WaterQuality.INDUSTRIAL
    )
    
    buy_order = Order(
        order_id="ORD_002",
        trader_id="BEVERAGE_CO",
        market_id="SAWX",
        basin_id="SA_VAAL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        trade_type=TradeType.SPOT,
        quantity_m3=30000,
        price_per_m3=15.00,
        quality=WaterQuality.INDUSTRIAL
    )
    
    # Submit orders (bypassing market hours check for demo)
    platform.order_books["SA_VAAL"].add_order(sell_order)
    result = platform.order_books["SA_VAAL"].add_order(buy_order)
    
    print(f"Sell Order: {sell_order.quantity_m3} m³ @ R{sell_order.price_per_m3}")
    print(f"Buy Order: {buy_order.quantity_m3} m³ @ R{buy_order.price_per_m3}")
    print(f"Trades Executed: {result['trades_executed']}")
    
    if result['trades_executed'] > 0:
        trade = platform.order_books["SA_VAAL"].trades[-1]
        print(f"\n✅ TRADE EXECUTED:")
        print(f"  Quantity: {trade.quantity_m3} m³")
        print(f"  Price: R{trade.price_per_m3}/m³")
        print(f"  Total: R{trade.total_value:,.0f}")
    
    # Order book depth
    print("\n\n📚 ORDER BOOK (SA_VAAL):")
    print("-" * 50)
    
    depth = platform.order_books["SA_VAAL"].get_book_depth()
    print(f"Last Price: R{depth['last_price']}")
    print(f"\nBids (Buy):")
    for bid in depth['bids']:
        print(f"  {bid['quantity']:,} m³ @ R{bid['price']}")
    print(f"\nAsks (Sell):")
    for ask in depth['asks']:
        print(f"  {ask['quantity']:,} m³ @ R{ask['price']}")
    
    # Price forecast
    print("\n\n🔮 30-DAY PRICE FORECAST (SA_VAAL):")
    print("-" * 50)
    
    forecast = platform.price_engine.get_price_forecast("SA_VAAL", 7)
    for f in forecast:
        print(f"  {f['date']}: R{f['forecast_price']} (R{f['confidence_low']}-R{f['confidence_high']})")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_trading()
