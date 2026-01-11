"""
AquaWatch NRW - Weather Integration for Predictive Analytics
============================================================

Weather-based predictive maintenance for Zambia/South Africa water utilities.

Features:
- Real-time weather data from OpenWeatherMap / WeatherAPI
- Pipe burst prediction during temperature extremes
- Rainfall correlation with NRW
- Drought monitoring for water stress
- Seasonal NRW forecasting

Regional Considerations:
- Zambia: Rainy season (Nov-Apr), Cold season (May-Aug), Hot season (Sep-Oct)
- South Africa: Winter (Jun-Aug), Summer rains (Oct-Mar)
"""

import os
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import math

logger = logging.getLogger(__name__)


# =============================================================================
# WEATHER DATA STRUCTURES
# =============================================================================

class WeatherCondition(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    DRIZZLE = "drizzle"
    FOG = "fog"
    DUST = "dust"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WeatherData:
    """Current weather data."""
    location: str
    timestamp: datetime
    
    # Temperature
    temperature_c: float
    feels_like_c: float
    temp_min_c: float
    temp_max_c: float
    
    # Precipitation
    humidity_percent: float
    rainfall_mm: float = 0.0
    rainfall_1h_mm: float = 0.0
    rainfall_3h_mm: float = 0.0
    
    # Conditions
    condition: WeatherCondition = WeatherCondition.CLEAR
    description: str = ""
    
    # Wind
    wind_speed_ms: float = 0.0
    wind_direction: int = 0
    
    # Pressure
    pressure_hpa: float = 1013.0
    
    # Visibility
    visibility_m: float = 10000.0
    
    # UV Index
    uv_index: float = 0.0


@dataclass
class WeatherForecast:
    """Weather forecast for a specific time."""
    forecast_time: datetime
    temperature_c: float
    rainfall_mm: float
    humidity_percent: float
    condition: WeatherCondition
    pop: float = 0.0  # Probability of precipitation (0-1)


@dataclass
class PipeRiskAssessment:
    """Risk assessment for pipe infrastructure."""
    zone_id: str
    timestamp: datetime
    
    # Risk scores (0-100)
    burst_risk: float
    leak_risk: float
    freeze_risk: float  # Not common in Zambia, but relevant for SA highlands
    ground_movement_risk: float
    
    # Overall
    overall_risk: RiskLevel
    risk_factors: List[str]
    recommended_actions: List[str]


# =============================================================================
# ZAMBIA/SOUTH AFRICA SEASONAL PATTERNS
# =============================================================================

ZAMBIA_SEASONS = {
    "rainy": {
        "months": [11, 12, 1, 2, 3, 4],
        "characteristics": "Heavy rainfall, ground saturation, increased NRW from runoff",
        "nrw_multiplier": 1.15,  # 15% higher NRW during rainy season
        "risk_factors": ["ground_movement", "runoff_contamination", "meter_flooding"]
    },
    "cold": {
        "months": [5, 6, 7, 8],
        "characteristics": "Dry, cool nights, temperature variation",
        "nrw_multiplier": 0.95,  # Slightly lower NRW
        "risk_factors": ["thermal_stress", "joint_contraction"]
    },
    "hot": {
        "months": [9, 10],
        "characteristics": "Hot and dry, peak demand",
        "nrw_multiplier": 1.10,  # Higher demand, more stress
        "risk_factors": ["high_demand", "pressure_spikes", "thermal_expansion"]
    }
}

SOUTH_AFRICA_SEASONS = {
    "summer": {
        "months": [10, 11, 12, 1, 2, 3],
        "characteristics": "Hot, afternoon thunderstorms in inland areas",
        "nrw_multiplier": 1.12,
        "risk_factors": ["thunderstorm_damage", "high_demand", "ground_movement"]
    },
    "autumn": {
        "months": [4, 5],
        "characteristics": "Cooling, reduced rainfall",
        "nrw_multiplier": 1.0,
        "risk_factors": []
    },
    "winter": {
        "months": [6, 7, 8],
        "characteristics": "Cold, dry, frost in highlands",
        "nrw_multiplier": 1.08,  # Freeze-related issues in highlands
        "risk_factors": ["frost_damage", "thermal_stress", "joint_leaks"]
    },
    "spring": {
        "months": [9],
        "characteristics": "Warming, unpredictable weather",
        "nrw_multiplier": 1.05,
        "risk_factors": ["temperature_variation"]
    }
}


def get_current_season(country: str, month: int = None) -> Dict:
    """Get current season information for the country."""
    if month is None:
        month = datetime.now().month
    
    seasons = ZAMBIA_SEASONS if country.lower() == "zambia" else SOUTH_AFRICA_SEASONS
    
    for season_name, season_data in seasons.items():
        if month in season_data["months"]:
            return {"name": season_name, **season_data}
    
    return {"name": "unknown", "nrw_multiplier": 1.0, "risk_factors": []}


# =============================================================================
# WEATHER API PROVIDERS
# =============================================================================

class OpenWeatherMapProvider:
    """
    OpenWeatherMap API provider.
    https://openweathermap.org/api
    
    Free tier: 1000 calls/day
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
    
    def get_current_weather(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Get current weather for coordinates."""
        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_current_weather(data)
            
            logger.error(f"Weather API error: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return None
    
    def get_forecast(self, lat: float, lon: float, days: int = 5) -> List[WeatherForecast]:
        """Get weather forecast."""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_forecast(data)
            
            return []
            
        except Exception as e:
            logger.error(f"Forecast fetch error: {e}")
            return []
    
    def _parse_current_weather(self, data: Dict) -> WeatherData:
        """Parse OpenWeatherMap current weather response."""
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        rain = data.get("rain", {})
        
        condition = self._map_condition(weather.get("id", 800))
        
        return WeatherData(
            location=data.get("name", "Unknown"),
            timestamp=datetime.fromtimestamp(data.get("dt", 0), timezone.utc),
            temperature_c=main.get("temp", 0),
            feels_like_c=main.get("feels_like", 0),
            temp_min_c=main.get("temp_min", 0),
            temp_max_c=main.get("temp_max", 0),
            humidity_percent=main.get("humidity", 0),
            rainfall_1h_mm=rain.get("1h", 0),
            rainfall_3h_mm=rain.get("3h", 0),
            condition=condition,
            description=weather.get("description", ""),
            wind_speed_ms=wind.get("speed", 0),
            wind_direction=wind.get("deg", 0),
            pressure_hpa=main.get("pressure", 1013),
            visibility_m=data.get("visibility", 10000)
        )
    
    def _parse_forecast(self, data: Dict) -> List[WeatherForecast]:
        """Parse OpenWeatherMap forecast response."""
        forecasts = []
        
        for item in data.get("list", []):
            weather = item.get("weather", [{}])[0]
            main = item.get("main", {})
            rain = item.get("rain", {})
            
            forecasts.append(WeatherForecast(
                forecast_time=datetime.fromtimestamp(item.get("dt", 0), timezone.utc),
                temperature_c=main.get("temp", 0),
                rainfall_mm=rain.get("3h", 0),
                humidity_percent=main.get("humidity", 0),
                condition=self._map_condition(weather.get("id", 800)),
                pop=item.get("pop", 0)
            ))
        
        return forecasts
    
    def _map_condition(self, code: int) -> WeatherCondition:
        """Map OpenWeatherMap condition code to enum."""
        if code >= 200 and code < 300:
            return WeatherCondition.THUNDERSTORM
        elif code >= 300 and code < 400:
            return WeatherCondition.DRIZZLE
        elif code >= 500 and code < 502:
            return WeatherCondition.RAIN
        elif code >= 502 and code < 600:
            return WeatherCondition.HEAVY_RAIN
        elif code >= 700 and code < 800:
            return WeatherCondition.FOG
        elif code == 800:
            return WeatherCondition.CLEAR
        else:
            return WeatherCondition.CLOUDY


# =============================================================================
# PREDICTIVE ANALYTICS ENGINE
# =============================================================================

class WeatherPredictiveAnalytics:
    """
    Weather-based predictive analytics for water infrastructure.
    
    Predicts:
    - Pipe burst probability based on temperature/pressure
    - Ground movement risk from rainfall
    - NRW increase during specific weather conditions
    - Optimal maintenance windows
    """
    
    def __init__(self, country: str = "zambia"):
        self.weather_provider = OpenWeatherMapProvider()
        self.country = country
        
        # Historical correlation data (simplified)
        self.burst_temp_correlation = -0.3  # Bursts increase when temp drops
        self.burst_rain_correlation = 0.4   # Bursts increase with heavy rain
        self.nrw_rain_correlation = 0.25    # NRW increases in rain
        
        # Thresholds
        self.heavy_rain_threshold = 20.0    # mm/hour
        self.temp_drop_threshold = 10.0     # °C drop in 24h
        self.frost_threshold = 2.0          # °C
        
        logger.info(f"Weather analytics initialized for {country}")
    
    def assess_pipe_risk(
        self, 
        zone_id: str, 
        lat: float, 
        lon: float,
        pipe_age_years: float = 20,
        pipe_material: str = "pvc"
    ) -> PipeRiskAssessment:
        """
        Assess pipe infrastructure risk based on current and forecast weather.
        """
        # Get current weather
        current = self.weather_provider.get_current_weather(lat, lon)
        forecast = self.weather_provider.get_forecast(lat, lon, days=3)
        
        if not current:
            return self._default_risk_assessment(zone_id)
        
        # Get seasonal factors
        season = get_current_season(self.country)
        
        # Calculate risk scores
        burst_risk = self._calculate_burst_risk(current, forecast, pipe_age_years, pipe_material)
        leak_risk = self._calculate_leak_risk(current, forecast, pipe_age_years)
        freeze_risk = self._calculate_freeze_risk(current, forecast)
        ground_risk = self._calculate_ground_movement_risk(current, forecast)
        
        # Apply seasonal multipliers
        burst_risk *= season.get("nrw_multiplier", 1.0)
        
        # Determine overall risk level
        max_risk = max(burst_risk, leak_risk, freeze_risk, ground_risk)
        if max_risk > 80:
            overall_risk = RiskLevel.CRITICAL
        elif max_risk > 60:
            overall_risk = RiskLevel.HIGH
        elif max_risk > 40:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        # Compile risk factors
        risk_factors = season.get("risk_factors", [])
        if current.rainfall_1h_mm > self.heavy_rain_threshold:
            risk_factors.append("heavy_rainfall")
        if current.temperature_c < self.frost_threshold:
            risk_factors.append("frost_conditions")
        if pipe_age_years > 30:
            risk_factors.append("aging_infrastructure")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            burst_risk, leak_risk, freeze_risk, ground_risk, 
            current, risk_factors
        )
        
        return PipeRiskAssessment(
            zone_id=zone_id,
            timestamp=datetime.now(timezone.utc),
            burst_risk=round(burst_risk, 1),
            leak_risk=round(leak_risk, 1),
            freeze_risk=round(freeze_risk, 1),
            ground_movement_risk=round(ground_risk, 1),
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            recommended_actions=recommendations
        )
    
    def _calculate_burst_risk(
        self, 
        current: WeatherData, 
        forecast: List[WeatherForecast],
        pipe_age: float,
        material: str
    ) -> float:
        """Calculate pipe burst risk score (0-100)."""
        base_risk = 10.0
        
        # Age factor (older pipes = higher risk)
        age_factor = min(pipe_age / 50 * 30, 30)  # Max 30 points from age
        
        # Material factor
        material_factors = {
            "pvc": 0.8,
            "hdpe": 0.7,
            "steel": 1.0,
            "cast_iron": 1.3,
            "asbestos_cement": 1.5,
            "concrete": 1.1
        }
        material_mult = material_factors.get(material.lower(), 1.0)
        
        # Temperature stress (rapid changes)
        if forecast:
            temp_range = max(f.temperature_c for f in forecast) - min(f.temperature_c for f in forecast)
            temp_factor = min(temp_range / self.temp_drop_threshold * 15, 15)
        else:
            temp_factor = 0
        
        # Rainfall factor (ground saturation)
        rain_factor = 0
        if current.rainfall_1h_mm > 5:
            rain_factor = min(current.rainfall_1h_mm / self.heavy_rain_threshold * 20, 20)
        
        # Pressure fluctuations (approximated from weather pressure)
        pressure_factor = abs(current.pressure_hpa - 1013) / 50 * 5
        
        risk = (base_risk + age_factor + temp_factor + rain_factor + pressure_factor) * material_mult
        return min(risk, 100)
    
    def _calculate_leak_risk(
        self, 
        current: WeatherData, 
        forecast: List[WeatherForecast],
        pipe_age: float
    ) -> float:
        """Calculate leak risk score (0-100)."""
        base_risk = 15.0
        
        # Age contributes to joint deterioration
        age_factor = min(pipe_age / 40 * 25, 25)
        
        # Temperature cycling causes joint expansion/contraction
        if forecast:
            daily_temp_range = current.temp_max_c - current.temp_min_c
            temp_factor = min(daily_temp_range / 15 * 15, 15)
        else:
            temp_factor = 0
        
        # Ground moisture affects joint seals
        moisture_factor = min(current.humidity_percent / 100 * 10, 10)
        
        risk = base_risk + age_factor + temp_factor + moisture_factor
        return min(risk, 100)
    
    def _calculate_freeze_risk(
        self, 
        current: WeatherData, 
        forecast: List[WeatherForecast]
    ) -> float:
        """Calculate freeze risk (relevant for SA highlands)."""
        if self.country.lower() == "zambia":
            return 0.0  # Frost extremely rare in Zambia
        
        # Check for near-freezing temperatures
        min_forecast_temp = current.temperature_c
        if forecast:
            min_forecast_temp = min(min_forecast_temp, min(f.temperature_c for f in forecast))
        
        if min_forecast_temp > 5:
            return 0.0
        
        if min_forecast_temp <= 0:
            return 80.0 + (0 - min_forecast_temp) * 5
        
        return max(0, (5 - min_forecast_temp) / 5 * 50)
    
    def _calculate_ground_movement_risk(
        self, 
        current: WeatherData, 
        forecast: List[WeatherForecast]
    ) -> float:
        """Calculate ground movement risk from rainfall."""
        base_risk = 5.0
        
        # Current rainfall
        if current.rainfall_1h_mm > self.heavy_rain_threshold:
            base_risk += 40
        elif current.rainfall_1h_mm > 10:
            base_risk += 20
        elif current.rainfall_1h_mm > 5:
            base_risk += 10
        
        # Forecast rainfall (sustained rain = saturated ground)
        if forecast:
            total_forecast_rain = sum(f.rainfall_mm for f in forecast[:24])  # Next 24h
            if total_forecast_rain > 50:
                base_risk += 30
            elif total_forecast_rain > 20:
                base_risk += 15
        
        return min(base_risk, 100)
    
    def _generate_recommendations(
        self,
        burst_risk: float,
        leak_risk: float,
        freeze_risk: float,
        ground_risk: float,
        current: WeatherData,
        risk_factors: List[str]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if burst_risk > 60:
            recommendations.append("Increase pressure monitoring frequency in high-risk zones")
            recommendations.append("Pre-position repair crews for rapid response")
        
        if leak_risk > 50:
            recommendations.append("Schedule joint inspection for aging pipe segments")
        
        if freeze_risk > 30:
            recommendations.append("Insulate exposed pipes in elevated areas")
            recommendations.append("Maintain minimum flow to prevent freezing")
        
        if ground_risk > 50:
            recommendations.append("Delay non-essential excavation work")
            recommendations.append("Monitor areas with previous ground movement issues")
        
        if "heavy_rainfall" in risk_factors:
            recommendations.append("Check valve chamber drainage")
            recommendations.append("Monitor for contamination from runoff")
        
        if not recommendations:
            recommendations.append("Normal operations - continue routine monitoring")
        
        return recommendations
    
    def _default_risk_assessment(self, zone_id: str) -> PipeRiskAssessment:
        """Return default risk assessment when weather data unavailable."""
        return PipeRiskAssessment(
            zone_id=zone_id,
            timestamp=datetime.now(timezone.utc),
            burst_risk=20.0,
            leak_risk=20.0,
            freeze_risk=0.0,
            ground_movement_risk=10.0,
            overall_risk=RiskLevel.LOW,
            risk_factors=["weather_data_unavailable"],
            recommended_actions=["Weather data unavailable - using baseline risk"]
        )
    
    def get_optimal_maintenance_window(
        self, 
        lat: float, 
        lon: float, 
        days_ahead: int = 7
    ) -> List[Dict]:
        """Find optimal days for maintenance based on weather forecast."""
        forecast = self.weather_provider.get_forecast(lat, lon, days=days_ahead)
        
        if not forecast:
            return []
        
        # Group forecast by day
        daily_forecast = {}
        for f in forecast:
            day = f.forecast_time.date()
            if day not in daily_forecast:
                daily_forecast[day] = []
            daily_forecast[day].append(f)
        
        # Score each day
        maintenance_windows = []
        for day, forecasts in daily_forecast.items():
            # Calculate daily scores
            max_rain = max(f.rainfall_mm for f in forecasts)
            avg_pop = sum(f.pop for f in forecasts) / len(forecasts)
            avg_temp = sum(f.temperature_c for f in forecasts) / len(forecasts)
            
            # Score (higher = better for maintenance)
            score = 100
            score -= max_rain * 2      # Penalize rain
            score -= avg_pop * 30      # Penalize rain probability
            
            # Temperature comfort (ideal: 15-25°C)
            if avg_temp < 10 or avg_temp > 35:
                score -= 20
            elif avg_temp < 15 or avg_temp > 30:
                score -= 10
            
            score = max(0, min(100, score))
            
            # Determine suitability
            if score > 70:
                suitability = "excellent"
            elif score > 50:
                suitability = "good"
            elif score > 30:
                suitability = "fair"
            else:
                suitability = "poor"
            
            maintenance_windows.append({
                "date": day.isoformat(),
                "score": round(score, 1),
                "suitability": suitability,
                "expected_rain_mm": round(max_rain, 1),
                "rain_probability": round(avg_pop * 100, 0),
                "avg_temperature_c": round(avg_temp, 1)
            })
        
        # Sort by score
        maintenance_windows.sort(key=lambda x: x["score"], reverse=True)
        
        return maintenance_windows
    
    def forecast_nrw_impact(
        self, 
        lat: float, 
        lon: float,
        baseline_nrw_percent: float = 30.0
    ) -> Dict:
        """Forecast NRW impact based on weather predictions."""
        current = self.weather_provider.get_current_weather(lat, lon)
        forecast = self.weather_provider.get_forecast(lat, lon, days=5)
        
        if not current or not forecast:
            return {
                "baseline_nrw": baseline_nrw_percent,
                "forecast_nrw": baseline_nrw_percent,
                "impact_factors": ["No weather data available"]
            }
        
        # Get seasonal adjustment
        season = get_current_season(self.country)
        seasonal_adjustment = (season.get("nrw_multiplier", 1.0) - 1) * 100
        
        # Calculate weather-based adjustment
        weather_adjustment = 0
        impact_factors = []
        
        # Rainfall impact
        total_forecast_rain = sum(f.rainfall_mm for f in forecast)
        if total_forecast_rain > 50:
            weather_adjustment += 3
            impact_factors.append(f"Heavy rain expected ({total_forecast_rain:.0f}mm)")
        
        # Temperature extremes
        temps = [f.temperature_c for f in forecast]
        if max(temps) > 35:
            weather_adjustment += 2
            impact_factors.append("High temperatures increase demand")
        
        # Calculate forecast NRW
        forecast_nrw = baseline_nrw_percent * (1 + seasonal_adjustment/100 + weather_adjustment/100)
        
        if not impact_factors:
            impact_factors.append("Normal conditions expected")
        
        return {
            "baseline_nrw": baseline_nrw_percent,
            "seasonal_adjustment_percent": round(seasonal_adjustment, 1),
            "weather_adjustment_percent": round(weather_adjustment, 1),
            "forecast_nrw": round(forecast_nrw, 1),
            "season": season.get("name", "unknown"),
            "impact_factors": impact_factors,
            "forecast_period_days": len(set(f.forecast_time.date() for f in forecast))
        }


# =============================================================================
# ZAMBIA/SOUTH AFRICA CITY COORDINATES
# =============================================================================

CITY_COORDINATES = {
    # Zambia
    "lusaka": {"lat": -15.3875, "lon": 28.3228, "country": "zambia"},
    "kitwe": {"lat": -12.8024, "lon": 28.2132, "country": "zambia"},
    "ndola": {"lat": -12.9587, "lon": 28.6366, "country": "zambia"},
    "kabwe": {"lat": -14.4469, "lon": 28.4464, "country": "zambia"},
    "chingola": {"lat": -12.5297, "lon": 27.8533, "country": "zambia"},
    "livingstone": {"lat": -17.8419, "lon": 25.8601, "country": "zambia"},
    
    # South Africa
    "johannesburg": {"lat": -26.2041, "lon": 28.0473, "country": "south_africa"},
    "cape_town": {"lat": -33.9249, "lon": 18.4241, "country": "south_africa"},
    "durban": {"lat": -29.8587, "lon": 31.0218, "country": "south_africa"},
    "pretoria": {"lat": -25.7479, "lon": 28.2293, "country": "south_africa"},
    "port_elizabeth": {"lat": -33.9608, "lon": 25.6022, "country": "south_africa"},
    "bloemfontein": {"lat": -29.0852, "lon": 26.1596, "country": "south_africa"},
    
    # Zimbabwe (neighboring)
    "harare": {"lat": -17.8252, "lon": 31.0335, "country": "zimbabwe"},
    "bulawayo": {"lat": -20.1325, "lon": 28.5851, "country": "zimbabwe"},
}


def get_city_coordinates(city: str) -> Optional[Dict]:
    """Get coordinates for a city."""
    return CITY_COORDINATES.get(city.lower())


# =============================================================================
# WEATHER SERVICE - MAIN CLASS
# =============================================================================

class WeatherService:
    """
    Main weather service for AquaWatch NRW.
    
    Provides:
    - Current weather for utility zones
    - Forecasts for planning
    - Risk assessments
    - Maintenance scheduling
    """
    
    def __init__(self, default_country: str = "zambia"):
        self.analytics = WeatherPredictiveAnalytics(country=default_country)
        self.provider = OpenWeatherMapProvider()
        self.default_country = default_country
        
        # Cache for weather data
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cache_ttl = timedelta(minutes=15)
        
        logger.info(f"WeatherService initialized for {default_country}")
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if still valid."""
        if key in self._cache:
            cached_time, data = self._cache[key]
            if datetime.now() - cached_time < self._cache_ttl:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Cache data."""
        self._cache[key] = (datetime.now(), data)
    
    def get_weather_for_zone(self, zone_id: str, lat: float, lon: float) -> Optional[WeatherData]:
        """Get current weather for a zone."""
        cache_key = f"weather_{zone_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        weather = self.provider.get_current_weather(lat, lon)
        if weather:
            self._set_cache(cache_key, weather)
        
        return weather
    
    def get_risk_assessment(
        self, 
        zone_id: str, 
        lat: float, 
        lon: float,
        pipe_age: float = 20,
        pipe_material: str = "pvc"
    ) -> PipeRiskAssessment:
        """Get risk assessment for a zone."""
        return self.analytics.assess_pipe_risk(
            zone_id, lat, lon, pipe_age, pipe_material
        )
    
    def get_maintenance_schedule(self, city: str) -> List[Dict]:
        """Get optimal maintenance windows for a city."""
        coords = get_city_coordinates(city)
        if not coords:
            return []
        
        return self.analytics.get_optimal_maintenance_window(
            coords["lat"], coords["lon"]
        )
    
    def get_nrw_forecast(
        self, 
        city: str, 
        baseline_nrw: float = 30.0
    ) -> Dict:
        """Get NRW impact forecast for a city."""
        coords = get_city_coordinates(city)
        if not coords:
            return {"error": "City not found"}
        
        return self.analytics.forecast_nrw_impact(
            coords["lat"], coords["lon"], baseline_nrw
        )
    
    def get_weather_summary(self, city: str) -> Dict:
        """Get comprehensive weather summary for dashboard."""
        coords = get_city_coordinates(city)
        if not coords:
            return {"error": "City not found"}
        
        weather = self.provider.get_current_weather(coords["lat"], coords["lon"])
        forecast = self.provider.get_forecast(coords["lat"], coords["lon"])
        season = get_current_season(coords["country"])
        
        if not weather:
            return {"error": "Weather data unavailable"}
        
        # Get next 24h forecast summary
        next_24h = [f for f in forecast if f.forecast_time < datetime.now(timezone.utc) + timedelta(hours=24)]
        
        return {
            "city": city.title(),
            "country": coords["country"].title().replace("_", " "),
            "current": {
                "temperature_c": weather.temperature_c,
                "feels_like_c": weather.feels_like_c,
                "humidity_percent": weather.humidity_percent,
                "condition": weather.condition.value,
                "description": weather.description,
                "rainfall_mm": weather.rainfall_1h_mm,
                "wind_speed_ms": weather.wind_speed_ms
            },
            "season": {
                "name": season.get("name", "unknown"),
                "nrw_impact": f"{(season.get('nrw_multiplier', 1.0) - 1) * 100:+.0f}%",
                "risk_factors": season.get("risk_factors", [])
            },
            "next_24h": {
                "min_temp_c": min(f.temperature_c for f in next_24h) if next_24h else None,
                "max_temp_c": max(f.temperature_c for f in next_24h) if next_24h else None,
                "total_rain_mm": sum(f.rainfall_mm for f in next_24h) if next_24h else 0,
                "max_rain_probability": max(f.pop for f in next_24h) * 100 if next_24h else 0
            },
            "timestamp": weather.timestamp.isoformat()
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Initialize service for Zambia
    service = WeatherService(default_country="zambia")
    
    # Get weather summary for Lusaka
    print("Weather Summary for Lusaka:")
    summary = service.get_weather_summary("lusaka")
    print(json.dumps(summary, indent=2, default=str))
    
    print("\n" + "="*50 + "\n")
    
    # Get risk assessment
    print("Risk Assessment for Zone A (Lusaka):")
    coords = get_city_coordinates("lusaka")
    risk = service.get_risk_assessment(
        "ZONE_A",
        coords["lat"],
        coords["lon"],
        pipe_age=25,
        pipe_material="pvc"
    )
    print(f"  Burst Risk: {risk.burst_risk}%")
    print(f"  Leak Risk: {risk.leak_risk}%")
    print(f"  Overall: {risk.overall_risk.value}")
    print(f"  Factors: {', '.join(risk.risk_factors)}")
    print(f"  Actions: {'; '.join(risk.recommended_actions)}")
    
    print("\n" + "="*50 + "\n")
    
    # Get maintenance windows
    print("Optimal Maintenance Windows (Lusaka):")
    windows = service.get_maintenance_schedule("lusaka")
    for w in windows[:3]:
        print(f"  {w['date']}: {w['suitability']} (score: {w['score']})")
    
    print("\n" + "="*50 + "\n")
    
    # Get NRW forecast
    print("NRW Impact Forecast (Lusaka):")
    nrw = service.get_nrw_forecast("lusaka", baseline_nrw=32.0)
    print(json.dumps(nrw, indent=2))
