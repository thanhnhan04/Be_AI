"""
TMDB (The Movie Database) Integration
Fetch movie data from TMDB API
"""

import httpx
from typing import List, Optional, Dict
from config import settings
import logging

logger = logging.getLogger(__name__)


class TMDBClient:
    """Client for The Movie Database API"""
    
    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = "https://image.tmdb.org/t/p/"
        
    async def search_movies(self, query: str, page: int = 1) -> Dict:
        """Search for movies by title"""
        if not self.api_key:
            raise ValueError("TMDB API key not configured")
        
        url = f"{self.base_url}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": query,
            "page": page,
            "language": "en-US"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_movie_details(self, tmdb_id: int) -> Dict:
        """Get detailed information about a movie"""
        if not self.api_key:
            raise ValueError("TMDB API key not configured")
        
        url = f"{self.base_url}/movie/{tmdb_id}"
        params = {
            "api_key": self.api_key,
            "language": "en-US"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Transform genres
            data['genres'] = [g['name'] for g in data.get('genres', [])]
            
            return data
    
    async def get_popular_movies(self, page: int = 1) -> Dict:
        """Get popular movies"""
        if not self.api_key:
            raise ValueError("TMDB API key not configured")
        
        url = f"{self.base_url}/movie/popular"
        params = {
            "api_key": self.api_key,
            "page": page,
            "language": "en-US"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_trending_movies(self, time_window: str = "week") -> Dict:
        """Get trending movies (day or week)"""
        if not self.api_key:
            raise ValueError("TMDB API key not configured")
        
        url = f"{self.base_url}/trending/movie/{time_window}"
        params = {
            "api_key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def discover_movies(
        self,
        genre_ids: Optional[List[int]] = None,
        sort_by: str = "popularity.desc",
        page: int = 1
    ) -> Dict:
        """Discover movies by filters"""
        if not self.api_key:
            raise ValueError("TMDB API key not configured")
        
        url = f"{self.base_url}/discover/movie"
        params = {
            "api_key": self.api_key,
            "sort_by": sort_by,
            "page": page,
            "language": "en-US"
        }
        
        if genre_ids:
            params["with_genres"] = ",".join(map(str, genre_ids))
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    def get_image_url(self, path: str, size: str = "w500") -> str:
        """
        Get full image URL
        
        Sizes: w92, w154, w185, w342, w500, w780, original
        """
        if not path:
            return None
        return f"{self.image_base_url}{size}{path}"
    
    def transform_movie_data(self, tmdb_movie: Dict) -> Dict:
        """Transform TMDB movie data to our schema"""
        return {
            "tmdb_id": tmdb_movie['id'],
            "title": tmdb_movie['title'],
            "original_title": tmdb_movie.get('original_title'),
            "overview": tmdb_movie.get('overview'),
            "release_date": tmdb_movie.get('release_date'),
            "poster_path": tmdb_movie.get('poster_path'),
            "backdrop_path": tmdb_movie.get('backdrop_path'),
            "genres": [g['name'] for g in tmdb_movie.get('genres', [])] if isinstance(tmdb_movie.get('genres', [{}])[0] if tmdb_movie.get('genres') else {}, dict) else tmdb_movie.get('genre_ids', []),
            "vote_average": tmdb_movie.get('vote_average', 0.0),
            "vote_count": tmdb_movie.get('vote_count', 0),
            "popularity": tmdb_movie.get('popularity', 0.0),
            "runtime": tmdb_movie.get('runtime'),
            "original_language": tmdb_movie.get('original_language'),
            "adult": tmdb_movie.get('adult', False)
        }


tmdb_client = TMDBClient()
