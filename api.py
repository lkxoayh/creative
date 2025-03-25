import requests
import re
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class EpicConfig:
    CLIENT_ID: str = 'cf92d8822f0448f68da3558e1815d806'
    DEVICE_ID: str = '9f2ac2d5f13c4ebd98430953c7b5c67c'
    ACCOUNT_ID: str = 'cf92d8822f0448f68da3558e1815d806'
    SECRET: str = 'LJW7YYZ74EYUL5CCYHM2RND63TQMERPM'
    BASE_URL: str = 'https://account-public-service-prod.ol.epicgames.com'
    CONTENT_URL: str = 'https://content-service.bfda.live.use1a.on.epicgames.com'
        
class EpicAPI:
    token: str = ''
    token_eg1: str = ''
    public_token: str = ''
    version: str = ''
    digits: str = ''
    user_agent: str = ''
    
    def __init__(self):
        self.session = requests.Session()
        self.config = EpicConfig()

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'user-agent': f'Fortnite/++Fortnite+Release-{version}-CL-{digits} Windows/10.0.19045.1.256.64bit'
        }

    def login(self) -> str:
        global token_eg1
        """Authenticate and get access token"""
        auth_response = self.session.post(
            url=f'{self.config.BASE_URL}/account/api/oauth/token',
            headers={
                "Authorization": "Basic M2Y2OWU1NmM3NjQ5NDkyYzhjYzI5ZjFhZjA4YThhMTI6YjUxZWU5Y2IxMjIzNGY1MGE2OWVmYTY3ZWY1MzgxMmU="
            },
            data={
                "grant_type": "device_auth",
                "device_id": self.config.DEVICE_ID,
                "account_id": self.config.ACCOUNT_ID,
                "secret": self.config.SECRET,
                "token_type": "eg1"
            }
        ).json()
        
        token_eg1 = auth_response['access_token']
        token = auth_response['access_token']
        return token

    def get_exchange_code(self) -> str:
        """Get exchange code for EGS login"""
        response = self.session.get(
            url=f'{self.config.BASE_URL}/account/api/oauth/exchange',
            headers={"Authorization": f"Bearer {token_eg1}"}
        ).json()
        return response['code']

    def get_login_egs(self, code: str) -> Dict[str, Any]:
        """Get EGS login token"""
        response = self.session.post(
            url=f'{self.config.BASE_URL}/account/api/oauth/token',
            headers={
                "Authorization": "Basic MzRhMDJjZjhmNDQxNGUyOWIxNTkyMTg3NmRhMzZmOWE6ZGFhZmJjY2M3Mzc3NDUwMzlkZmZlNTNkOTRmYzc2Y2Y="
            },
            data={
                "grant_type": "exchange_code",
                "exchange_code": code,
                "token_type": "eg1"
            }
        ).json()
        return response

    def get_island(self, link: str) -> str:
        """Get project ID from island link"""
        response = self.session.get(
            f'{self.config.CONTENT_URL}/admin/api/content/link/{link}',
            headers={'cookie': f'content-service:access_token={token};'}
        )
        return response.json()['projectId']

    def get_island_team(self, project: str) -> str:
        """Get team ID from project"""
        response = self.session.get(
            f'{self.config.CONTENT_URL}/api/content/v2/project/{project}',
            headers={'cookie': f'content-service:access_token={token};'}
        )
        error_message = response.json()['errorMessage']
        match = re.search(r'team_id=([a-f0-9\-]+)', error_message)
        return match.group(1) if match else 'no_team'
    
    def get_team_info(self, teamid: str) -> Dict[str, Any]:
        """Get team information by team ID
        
        Args:
            teamid: The ID of the team to look up
            
        Returns:
            Dict containing team information
        """
        response = self.session.get(
            url=f'{self.config.CONTENT_URL}/admin/api/content/my-teams/{teamid}',
            headers={'cookie': f'content-service:access_token={token};'}
        )
        return response.json()

    async def update_tokens(self):
        global token, version, digits, user_agent, public_token
        """Background task to refresh tokens"""
        while True:
            try:
                print('Connected Content Service !')
                token = self.login()
                public_token = self.get_public_token()
                
                version_response = self.session.get('http://192.168.1.34:8000/version').json()
                user_agent = version_response['version']
                
                version_str = user_agent[user_agent.index("Release-") + 8:]
                version = version_str[:version_str.index("-CL-")]
                digits = version_str[version_str.index("CL-") + 3:version_str.index(" W")]
                
                await asyncio.sleep(3600)
            except Exception as e:
                print(f"Token refresh error: {e}")
                await asyncio.sleep(60)

    def get_public_token(self) -> str:
        """Get public access token"""
        response = self.session.post(
            url='https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token',
            data="grant_type=client_credentials&token_type=eg1",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic M2Y2OWU1NmM3NjQ5NDkyYzhjYzI5ZjFhZjA4YThhMTI6YjUxZWU5Y2IxMjIzNGY1MGE2OWVmYTY3ZWY1MzgxMmU="
            }
        ).json()
        return response['access_token']

    def slug(self, slug: str) -> Dict[str, Any]:
        """Get affiliate information by slug
        
        Args:
            slug: The affiliate slug to look up
            
        Returns:
            Response from the affiliate API
        """
        response = self.session.get(
            url=f"https://affiliate-public-service-prod.ol.epicgames.com/affiliate/api/public/affiliates/slug/{slug}",
            headers={"Authorization": f"Bearer {public_token}"}
        )
        return response

# Initialize API instance
epic_api = EpicAPI()

def start_background_tasks():
    """Start background token refresh task"""
    loop = asyncio.get_event_loop()
    loop.create_task(epic_api.update_tokens())