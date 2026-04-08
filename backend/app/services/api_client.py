"""Simple API client for EX Venture Platform."""

import axios
from typing import Optional, Dict, Any

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.headers = {}
    
    def _update_headers(self):
        """Update request headers with auth token."""
        self.headers = {"Content-Type": "application/json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    async def register(self, email: str, password: str, name: str = "") -> Dict[str, Any]:
        """Register new user."""
        self._update_headers()
        response = await axios.post(
            f"{self.base_url}/api/auth/register",
            {"email": email, "password": password, "name": name},
            headers=self.headers,
        )
        data = response.json()
        if "access_token" in data:
            self.token = data["access_token"]
        return data
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user."""
        self._update_headers()
        response = await axios.post(
            f"{self.base_url}/api/auth/login",
            {"email": email, "password": password},
            headers=self.headers,
        )
        data = response.json()
        if "access_token" in data:
            self.token = data["access_token"]
        return data
    
    async def get_companies(self) -> list:
        """Get all companies."""
        self._update_headers()
        response = await axios.get(
            f"{self.base_url}/api/companies",
            headers=self.headers,
        )
        return response.json()
    
    async def create_company(self, name: str, url: str, industry_tags: list = None) -> Dict[str, Any]:
        """Create company."""
        self._update_headers()
        response = await axios.post(
            f"{self.base_url}/api/companies",
            {"name": name, "url": url, "industry_tags": industry_tags or []},
            headers=self.headers,
        )
        return response.json()
    
    async def get_content(self, company_id: str = None) -> list:
        """Get content items."""
        self._update_headers()
        params = {"company_id": company_id} if company_id else {}
        response = await axios.get(
            f"{self.base_url}/api/content",
            headers=self.headers,
            params=params,
        )
        return response.json()
    
    async def generate_content(
        self,
        company_id: str,
        platform: str,
        tone: str,
        topic: str,
        target_length: int = 500,
        image_style: str = "photorealistic",
    ) -> Dict[str, Any]:
        """Generate content item."""
        self._update_headers()
        response = await axios.post(
            f"{self.base_url}/api/content",
            {
                "platform": platform,
                "tone": tone,
                "topic": topic,
                "target_length": target_length,
                "image_style": image_style,
            },
            headers=self.headers,
            params={"company_id": company_id},
        )
        return response.json()
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        self._update_headers()
        response = await axios.get(
            f"{self.base_url}/api/scans/dashboard-stats",
            headers=self.headers,
        )
        return response.json()


# Example usage:
if __name__ == "__main__":
    print("EX Venture Platform API Client")
    print("See documentation at http://localhost:8000/docs")
