"""
AquaWatch NRW - Gamification & Public Transparency
=================================================

"Make it a game, and people will play."

Features:
1. Utility Leaderboard - Compete on NRW reduction
2. Technician Performance Scoring
3. Public Dashboard - Citizens see their utility's performance
4. Water Savings Achievements
5. Community Challenges
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


# =============================================================================
# ACHIEVEMENT SYSTEM
# =============================================================================

class AchievementCategory(Enum):
    LEAK_DETECTION = "leak_detection"
    RESPONSE_TIME = "response_time"
    WATER_SAVED = "water_saved"
    UPTIME = "uptime"
    EFFICIENCY = "efficiency"
    STREAK = "streak"


@dataclass
class Achievement:
    """Unlockable achievement."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    icon: str  # Emoji or icon name
    
    # Requirements
    target_value: float
    unit: str
    
    # Rewards
    xp_reward: int = 100
    badge_tier: str = "bronze"  # bronze, silver, gold, platinum, diamond
    
    # Tracking
    is_hidden: bool = False
    is_repeatable: bool = False


# Predefined achievements
ACHIEVEMENTS = [
    # Leak Detection
    Achievement("first_leak", "First Catch", "Detect your first leak", 
               AchievementCategory.LEAK_DETECTION, "🎣", 1, "leaks", 50, "bronze"),
    Achievement("leak_hunter", "Leak Hunter", "Detect 10 leaks", 
               AchievementCategory.LEAK_DETECTION, "🔍", 10, "leaks", 200, "silver"),
    Achievement("leak_master", "Leak Master", "Detect 100 leaks", 
               AchievementCategory.LEAK_DETECTION, "🏆", 100, "leaks", 1000, "gold"),
    Achievement("leak_legend", "Leak Legend", "Detect 1000 leaks", 
               AchievementCategory.LEAK_DETECTION, "👑", 1000, "leaks", 5000, "diamond"),
    
    # Response Time
    Achievement("quick_response", "Quick Response", "Respond within 30 minutes", 
               AchievementCategory.RESPONSE_TIME, "⚡", 30, "minutes", 100, "bronze"),
    Achievement("flash", "The Flash", "Respond within 10 minutes", 
               AchievementCategory.RESPONSE_TIME, "💨", 10, "minutes", 300, "gold"),
    
    # Water Saved
    Achievement("drop_saver", "Drop Saver", "Save 1,000 m³ of water", 
               AchievementCategory.WATER_SAVED, "💧", 1000, "m³", 150, "bronze"),
    Achievement("river_keeper", "River Keeper", "Save 100,000 m³ of water", 
               AchievementCategory.WATER_SAVED, "🌊", 100000, "m³", 2000, "gold"),
    Achievement("ocean_guardian", "Ocean Guardian", "Save 1,000,000 m³ of water", 
               AchievementCategory.WATER_SAVED, "🌍", 1000000, "m³", 10000, "diamond"),
    
    # Uptime
    Achievement("always_on", "Always On", "99% sensor uptime for a month", 
               AchievementCategory.UPTIME, "📡", 99, "%", 500, "gold"),
    Achievement("ironclad", "Ironclad", "99.9% uptime for a year", 
               AchievementCategory.UPTIME, "🛡️", 99.9, "%", 5000, "diamond"),
    
    # Streaks
    Achievement("week_warrior", "Week Warrior", "7-day zero-incident streak", 
               AchievementCategory.STREAK, "🔥", 7, "days", 200, "silver"),
    Achievement("month_master", "Month Master", "30-day zero-incident streak", 
               AchievementCategory.STREAK, "⭐", 30, "days", 1000, "gold"),
]


@dataclass
class UserProgress:
    """User's gamification progress."""
    user_id: str
    username: str
    
    # XP & Level
    total_xp: int = 0
    level: int = 1
    
    # Stats
    leaks_detected: int = 0
    water_saved_m3: float = 0.0
    avg_response_minutes: float = 60.0
    current_streak_days: int = 0
    longest_streak_days: int = 0
    
    # Achievements
    unlocked_achievements: List[str] = field(default_factory=list)
    
    # Rankings
    global_rank: int = 0
    utility_rank: int = 0
    
    def calculate_level(self):
        """Calculate level from XP (exponential curve)."""
        # Level = sqrt(XP / 100)
        import math
        self.level = max(1, int(math.sqrt(self.total_xp / 100)))
    
    def add_xp(self, amount: int, reason: str = ""):
        """Add XP and check for level up."""
        old_level = self.level
        self.total_xp += amount
        self.calculate_level()
        
        if self.level > old_level:
            logger.info(f"🎉 {self.username} leveled up to {self.level}!")
            return {"level_up": True, "new_level": self.level}
        return {"level_up": False}


# =============================================================================
# LEADERBOARD SYSTEM
# =============================================================================

@dataclass
class UtilityScore:
    """Utility's performance score."""
    utility_id: str
    utility_name: str
    country: str
    
    # KPIs
    nrw_percentage: float = 40.0
    nrw_reduction_ytd: float = 0.0  # Percentage points reduced this year
    response_time_avg_min: float = 60.0
    sensor_uptime_pct: float = 95.0
    leaks_fixed_ytd: int = 0
    water_saved_m3_ytd: float = 0.0
    
    # Calculated score (0-100)
    total_score: float = 0.0
    
    # Ranking
    global_rank: int = 0
    regional_rank: int = 0
    
    def calculate_score(self):
        """Calculate composite performance score."""
        # Lower NRW = better
        nrw_score = max(0, 100 - self.nrw_percentage * 2)
        
        # NRW reduction bonus
        reduction_score = min(30, self.nrw_reduction_ytd * 3)
        
        # Response time (target: 30 min)
        response_score = max(0, 100 - (self.response_time_avg_min - 30) * 2)
        
        # Uptime
        uptime_score = self.sensor_uptime_pct
        
        # Weighted average
        self.total_score = (
            nrw_score * 0.4 +
            reduction_score * 0.2 +
            response_score * 0.2 +
            uptime_score * 0.2
        )


class Leaderboard:
    """
    Global and regional leaderboards.
    
    Public transparency - citizens can see how their utility compares.
    """
    
    def __init__(self):
        self.utilities: Dict[str, UtilityScore] = {}
        self.technicians: Dict[str, UserProgress] = {}
        
        # Sample data
        self._load_sample_data()
    
    def _load_sample_data(self):
        """Load sample utilities for demo."""
        sample_utilities = [
            ("LWSC", "Lusaka Water & Sewerage", "Zambia", 35.0, 5.0),
            ("NWSC", "Nkana Water & Sewerage", "Zambia", 42.0, 3.0),
            ("SWSC", "Southern Water & Sewerage", "Zambia", 48.0, 2.0),
            ("JHB_WATER", "Johannesburg Water", "South Africa", 38.0, 4.0),
            ("CAPE_TOWN", "Cape Town Water", "South Africa", 28.0, 8.0),
            ("ETHEKWINI", "eThekwini Water", "South Africa", 36.0, 3.5),
            ("RAND_WATER", "Rand Water", "South Africa", 15.0, 2.0),
            ("NAIROBI", "Nairobi Water", "Kenya", 42.0, 4.0),
            ("DAR_ES_SALAAM", "DAWASCO", "Tanzania", 55.0, 1.0),
            ("KAMPALA", "NWSC Uganda", "Uganda", 33.0, 6.0),
        ]
        
        for uid, name, country, nrw, reduction in sample_utilities:
            score = UtilityScore(
                utility_id=uid,
                utility_name=name,
                country=country,
                nrw_percentage=nrw,
                nrw_reduction_ytd=reduction,
                response_time_avg_min=random.randint(20, 90),
                sensor_uptime_pct=random.uniform(90, 99.9),
                leaks_fixed_ytd=random.randint(50, 500),
                water_saved_m3_ytd=random.randint(10000, 500000)
            )
            score.calculate_score()
            self.utilities[uid] = score
        
        self._update_rankings()
    
    def _update_rankings(self):
        """Update global and regional rankings."""
        # Sort by score
        sorted_utilities = sorted(
            self.utilities.values(),
            key=lambda x: x.total_score,
            reverse=True
        )
        
        for i, utility in enumerate(sorted_utilities):
            utility.global_rank = i + 1
        
        # Regional rankings
        regions = {}
        for utility in self.utilities.values():
            if utility.country not in regions:
                regions[utility.country] = []
            regions[utility.country].append(utility)
        
        for country, utilities in regions.items():
            sorted_regional = sorted(utilities, key=lambda x: x.total_score, reverse=True)
            for i, utility in enumerate(sorted_regional):
                utility.regional_rank = i + 1
    
    def get_global_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get global utility leaderboard."""
        sorted_utilities = sorted(
            self.utilities.values(),
            key=lambda x: x.total_score,
            reverse=True
        )[:limit]
        
        return [
            {
                "rank": u.global_rank,
                "utility": u.utility_name,
                "country": u.country,
                "score": round(u.total_score, 1),
                "nrw_pct": u.nrw_percentage,
                "nrw_reduction": u.nrw_reduction_ytd,
                "water_saved_m3": u.water_saved_m3_ytd
            }
            for u in sorted_utilities
        ]
    
    def get_country_leaderboard(self, country: str) -> List[Dict]:
        """Get country-specific leaderboard."""
        country_utilities = [
            u for u in self.utilities.values()
            if u.country.lower() == country.lower()
        ]
        
        sorted_utilities = sorted(
            country_utilities,
            key=lambda x: x.total_score,
            reverse=True
        )
        
        return [
            {
                "rank": u.regional_rank,
                "utility": u.utility_name,
                "score": round(u.total_score, 1),
                "nrw_pct": u.nrw_percentage,
                "trend": "↓" if u.nrw_reduction_ytd > 0 else "→"
            }
            for u in sorted_utilities
        ]
    
    def get_utility_details(self, utility_id: str) -> Dict:
        """Get detailed utility performance."""
        u = self.utilities.get(utility_id)
        if not u:
            return {}
        
        return {
            "utility_id": u.utility_id,
            "name": u.utility_name,
            "country": u.country,
            "global_rank": u.global_rank,
            "regional_rank": u.regional_rank,
            "score": round(u.total_score, 1),
            "metrics": {
                "nrw_percentage": u.nrw_percentage,
                "nrw_reduction_ytd": u.nrw_reduction_ytd,
                "response_time_avg": u.response_time_avg_min,
                "sensor_uptime": u.sensor_uptime_pct,
                "leaks_fixed": u.leaks_fixed_ytd,
                "water_saved_m3": u.water_saved_m3_ytd
            },
            "badges": self._get_utility_badges(u)
        }
    
    def _get_utility_badges(self, u: UtilityScore) -> List[Dict]:
        """Get badges earned by utility."""
        badges = []
        
        if u.nrw_percentage < 20:
            badges.append({"name": "Elite Performer", "icon": "🏆", "tier": "gold"})
        elif u.nrw_percentage < 30:
            badges.append({"name": "Top Performer", "icon": "⭐", "tier": "silver"})
        
        if u.nrw_reduction_ytd > 5:
            badges.append({"name": "Rapid Improver", "icon": "📈", "tier": "gold"})
        
        if u.sensor_uptime_pct > 99:
            badges.append({"name": "Always On", "icon": "📡", "tier": "gold"})
        
        if u.water_saved_m3_ytd > 100000:
            badges.append({"name": "Water Guardian", "icon": "💧", "tier": "silver"})
        
        return badges


# =============================================================================
# PUBLIC TRANSPARENCY DASHBOARD
# =============================================================================

class PublicDashboard:
    """
    Citizen-facing transparency dashboard.
    
    "Sunlight is the best disinfectant."
    
    Shows:
    - How their utility is performing
    - Water quality
    - Incident reports
    - Comparison with other utilities
    """
    
    def __init__(self, leaderboard: Leaderboard):
        self.leaderboard = leaderboard
    
    def get_citizen_view(self, utility_id: str) -> Dict:
        """Get citizen-friendly view of utility performance."""
        utility = self.leaderboard.utilities.get(utility_id)
        if not utility:
            return {"error": "Utility not found"}
        
        # Calculate letter grade
        score = utility.total_score
        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "utility_name": utility.utility_name,
            "performance_grade": grade,
            "performance_score": round(score, 1),
            "ranking": {
                "global": f"#{utility.global_rank} worldwide",
                "regional": f"#{utility.regional_rank} in {utility.country}"
            },
            "water_loss": {
                "percentage": utility.nrw_percentage,
                "status": "Good" if utility.nrw_percentage < 25 else 
                         "Average" if utility.nrw_percentage < 40 else "Needs Improvement",
                "trend": f"↓ {utility.nrw_reduction_ytd}% this year" if utility.nrw_reduction_ytd > 0 else "→ Stable"
            },
            "response_time": {
                "average_minutes": utility.response_time_avg_min,
                "rating": "Fast" if utility.response_time_avg_min < 30 else 
                         "Normal" if utility.response_time_avg_min < 60 else "Slow"
            },
            "recent_improvements": [
                f"Fixed {utility.leaks_fixed_ytd} leaks this year",
                f"Saved {utility.water_saved_m3_ytd:,.0f} m³ of water",
                f"Sensor network {utility.sensor_uptime_pct:.1f}% uptime"
            ],
            "how_you_can_help": [
                "Report leaks: Call 123 or use our app",
                "Fix dripping taps - saves 20L/day",
                "Water garden early morning or evening"
            ]
        }
    
    def get_incident_feed(self, utility_id: str, limit: int = 10) -> List[Dict]:
        """Get recent incidents (anonymized for public)."""
        # In production, fetch from database
        sample_incidents = [
            {
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "area": "Kabulonga",
                "type": "Pipe repair",
                "status": "Resolved",
                "duration": "4 hours"
            },
            {
                "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "area": "Chelstone",
                "type": "Planned maintenance",
                "status": "Completed",
                "duration": "8 hours"
            },
            {
                "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "area": "Matero",
                "type": "Emergency repair",
                "status": "Resolved",
                "duration": "2 hours"
            }
        ]
        return sample_incidents[:limit]
    
    def get_comparison(self, utility_id: str) -> Dict:
        """Compare utility with peers."""
        utility = self.leaderboard.utilities.get(utility_id)
        if not utility:
            return {}
        
        # Get country peers
        peers = [
            u for u in self.leaderboard.utilities.values()
            if u.country == utility.country and u.utility_id != utility_id
        ]
        
        if not peers:
            return {}
        
        avg_nrw = sum(p.nrw_percentage for p in peers) / len(peers)
        avg_response = sum(p.response_time_avg_min for p in peers) / len(peers)
        
        return {
            "utility": utility.utility_name,
            "comparison_group": f"Other utilities in {utility.country}",
            "metrics": {
                "nrw_percentage": {
                    "you": utility.nrw_percentage,
                    "average": round(avg_nrw, 1),
                    "better_than_average": utility.nrw_percentage < avg_nrw
                },
                "response_time": {
                    "you": utility.response_time_avg_min,
                    "average": round(avg_response, 1),
                    "better_than_average": utility.response_time_avg_min < avg_response
                }
            }
        }


# =============================================================================
# COMMUNITY CHALLENGES
# =============================================================================

@dataclass
class Challenge:
    """Community challenge."""
    id: str
    name: str
    description: str
    
    # Target
    target_value: float
    current_value: float = 0.0
    unit: str = "m³"
    
    # Timing
    start_date: datetime = None
    end_date: datetime = None
    
    # Rewards
    prize_description: str = ""
    xp_reward: int = 500
    
    # Participants
    participating_utilities: List[str] = field(default_factory=list)
    
    @property
    def progress_pct(self) -> float:
        return min(100, (self.current_value / self.target_value) * 100) if self.target_value > 0 else 0


class ChallengeSystem:
    """
    Community challenges for utilities.
    
    Examples:
    - "Save 1 million m³ across all Zambian utilities"
    - "Reduce NRW by 5% in Q1"
    - "Zero critical incidents for a week"
    """
    
    def __init__(self):
        self.active_challenges: Dict[str, Challenge] = {}
        self.completed_challenges: List[Challenge] = []
        
        # Create sample challenges
        self._create_sample_challenges()
    
    def _create_sample_challenges(self):
        """Create sample challenges."""
        now = datetime.now(timezone.utc)
        
        self.active_challenges["million_liters"] = Challenge(
            id="million_liters",
            name="Million Liter Challenge",
            description="Together, let's save 1 million cubic meters of water this quarter!",
            target_value=1000000,
            current_value=650000,
            unit="m³",
            start_date=now - timedelta(days=60),
            end_date=now + timedelta(days=30),
            prize_description="Top contributing utility wins IoT sensor kit",
            xp_reward=1000,
            participating_utilities=["LWSC", "NWSC", "SWSC", "JHB_WATER"]
        )
        
        self.active_challenges["response_time"] = Challenge(
            id="response_time",
            name="Lightning Response",
            description="Average response time under 30 minutes for one month",
            target_value=30,
            current_value=35,
            unit="minutes",
            start_date=now - timedelta(days=20),
            end_date=now + timedelta(days=10),
            prize_description="Featured in AquaWatch spotlight",
            xp_reward=500
        )
    
    def get_active_challenges(self) -> List[Dict]:
        """Get all active challenges."""
        return [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "progress": round(c.progress_pct, 1),
                "target": f"{c.target_value:,.0f} {c.unit}",
                "current": f"{c.current_value:,.0f} {c.unit}",
                "days_remaining": max(0, (c.end_date - datetime.now(timezone.utc)).days) if c.end_date else 0,
                "participants": len(c.participating_utilities),
                "prize": c.prize_description
            }
            for c in self.active_challenges.values()
        ]
    
    def contribute(self, challenge_id: str, utility_id: str, value: float):
        """Record contribution to challenge."""
        challenge = self.active_challenges.get(challenge_id)
        if challenge:
            challenge.current_value += value
            if utility_id not in challenge.participating_utilities:
                challenge.participating_utilities.append(utility_id)
            
            # Check if completed
            if challenge.current_value >= challenge.target_value:
                self._complete_challenge(challenge)
    
    def _complete_challenge(self, challenge: Challenge):
        """Mark challenge as completed."""
        logger.info(f"🎉 Challenge completed: {challenge.name}")
        self.completed_challenges.append(challenge)
        del self.active_challenges[challenge.id]


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

leaderboard = Leaderboard()
public_dashboard = PublicDashboard(leaderboard)
challenge_system = ChallengeSystem()


# =============================================================================
# DEMO
# =============================================================================

def demo_gamification():
    """Demonstrate gamification features."""
    
    print("=" * 60)
    print("🏆 AQUAWATCH GAMIFICATION SYSTEM")
    print("=" * 60)
    
    # Global Leaderboard
    print("\n📊 GLOBAL UTILITY LEADERBOARD:")
    print("-" * 50)
    for entry in leaderboard.get_global_leaderboard(5):
        trend = "↓" if entry["nrw_reduction"] > 0 else "→"
        print(f"  #{entry['rank']} {entry['utility'][:25]:<25} "
              f"Score: {entry['score']:>5.1f} | NRW: {entry['nrw_pct']}% {trend}")
    
    # Citizen View
    print("\n👤 CITIZEN VIEW (Lusaka Water):")
    print("-" * 50)
    citizen = public_dashboard.get_citizen_view("LWSC")
    print(f"  Performance Grade: {citizen['performance_grade']}")
    print(f"  Water Loss: {citizen['water_loss']['percentage']}% ({citizen['water_loss']['status']})")
    print(f"  Ranking: {citizen['ranking']['global']}")
    
    # Active Challenges
    print("\n🎯 ACTIVE CHALLENGES:")
    print("-" * 50)
    for challenge in challenge_system.get_active_challenges():
        print(f"  {challenge['name']}")
        print(f"    Progress: {challenge['progress']}% ({challenge['current']} / {challenge['target']})")
        print(f"    Days remaining: {challenge['days_remaining']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_gamification()
