from urllib.parse import parse_qs
from django.db import close_old_connections
from jwt import DecodeError, ExpiredSignatureError, InvalidSignatureError
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.auth import AuthMiddlewareStack 

from jwt import decode as jwt_decode 


from main import settings
from users.models import User


class JWTAuthMiddleware :

    def __init__(self, app):
        self.app = app

    
    async def __call__(self, scope, receive, send):
        close_old_connections()

        try:
            token = parse_qs(scope['query_string'].decode('utf8')).get('token', None)[ 0 ]
            data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            scope['user'] = await self.get_user(data['user_id'])
        except (TypeError, KeyError, InvalidSignatureError, ExpiredSignatureError, DecodeError):
            scope['user'] = AnonymousUser
            
        return await self.app(scope, receive, send)
    
    @database_sync_to_async
    def get_user ( self, user_id ):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
        
    
def JWTAuthMIddlewareStack (app):
    return JWTAuthMiddleware(AuthMiddlewareStack(app))