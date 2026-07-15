"""
 ============================================================================
 Application Configuration
 ============================================================================
 Description: Centralized configuration management using Pydantic Settings
 Loads environment variables and provides type-safe configuration access
 ============================================================================
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Provides type-safe configuration access with defaults.
    """
    
    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "gis_engine"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Google Geocoding API
    GOOGLE_MAPS_API_KEY: str = ""
    
    # KGIS API
    KGIS_API_URL: str = "https://kgis.karnataka.gov.in/api/survey-number"
    
    # KGIS ArcGIS REST LULC Service
    KGIS_LULC_URL: str = "https://kgis.ksrsac.in/kgismaps1/rest/services/NR_V2/LULC_10K/MapServer/0/query"
    
    # KGIS Admin Hierarchy Service
    KGIS_ADMIN_URL: str = "https://kgis.ksrsac.in:9000/genericwebservices/ws/nearbyadminhierarchy"
    
    # Airport Reference Coordinates (for AAI zone calculation)
    KIAL_LAT: float = 13.1986
    KIAL_LNG: float = 77.7066
    KIAL_NAME: str = "Kempegowda International Airport (BIAL)"
    HAL_LAT: float = 12.9499
    HAL_LNG: float = 77.6681
    HAL_NAME: str = "HAL Airport (Bengaluru)"
    
    # Application Configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # Cache Configuration
    CACHE_TTL_SECONDS: int = 172800  # 48 hours
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
