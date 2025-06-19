from authlib.integrations.httpx_client import AsyncOAuth2Client
from app.config.settings import get_settings
import httpx
from typing import Dict, Any, Optional

settings = get_settings()

class OAuthService:
    def __init__(self):
        self.providers = {
            'google': {
                'client_id': settings.google_client_id,
                'client_secret': settings.google_client_secret,
                'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scope': 'openid email profile'
            },
            'github': {
                'client_id': settings.github_client_id,
                'client_secret': settings.github_client_secret,
                'authorize_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'user_info_url': 'https://api.github.com/user',
                'scope': 'user:email'
            },
            'discord': {
                'client_id': settings.discord_client_id,
                'client_secret': settings.discord_client_secret,
                'authorize_url': 'https://discord.com/api/oauth2/authorize',
                'token_url': 'https://discord.com/api/oauth2/token',
                'user_info_url': 'https://discord.com/api/users/@me',
                'scope': 'identify email'
            }
        }
    
    def get_oauth_client(self, provider: str) -> AsyncOAuth2Client:
        """Crear cliente OAuth para el proveedor especificado"""
        if provider not in self.providers:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        config = self.providers[provider]
        return AsyncOAuth2Client(
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )
    
    def get_authorization_url(self, provider: str) -> str:
        """Generar URL de autorización para el proveedor"""
        if provider not in self.providers:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        config = self.providers[provider]
        client = self.get_oauth_client(provider)
        
        redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/oauth/{provider}/callback"
        
        authorization_url, state = client.create_authorization_url(
            config['authorize_url'],
            redirect_uri=redirect_uri,
            scope=config['scope']
        )
        
        return authorization_url
    
    async def exchange_code_for_token(self, provider: str, code: str) -> Dict[str, Any]:
        """Intercambiar código de autorización por token de acceso"""
        if provider not in self.providers:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        config = self.providers[provider]
        client = self.get_oauth_client(provider)
        
        redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/oauth/{provider}/callback"
        
        token = await client.fetch_token(
            config['token_url'],
            code=code,
            redirect_uri=redirect_uri
        )
        
        return token
    
    async def get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Obtener información del usuario usando el token de acceso"""
        if provider not in self.providers:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        config = self.providers[provider]
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(config['user_info_url'], headers=headers)
            response.raise_for_status()
            user_data = response.json()
        
        # Normalizar datos del usuario según el proveedor
        if provider == 'google':
            return {
                'id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name'],
                'avatar_url': user_data.get('picture', '')
            }
        elif provider == 'github':
            # Para GitHub, necesitamos obtener el email por separado si es privado
            email = user_data.get('email')
            if not email:
                email_response = await client.get(
                    'https://api.github.com/user/emails',
                    headers=headers
                )
                emails = email_response.json()
                primary_email = next((e for e in emails if e['primary']), None)
                email = primary_email['email'] if primary_email else ''
            
            return {
                'id': str(user_data['id']),
                'email': email,
                'name': user_data.get('name', user_data['login']),
                'avatar_url': user_data.get('avatar_url', '')
            }
        elif provider == 'discord':
            return {
                'id': user_data['id'],
                'email': user_data.get('email', ''),
                'name': user_data.get('global_name', user_data['username']),
                'avatar_url': f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data.get('avatar') else ''
            }
        
        return user_data

oauth_service = OAuthService()