from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers.user_serializers import UserSerializer
from users.models import User
from main.utils.custom_api_errors import NotFoundRefreshToken, NotFoundToken, UserNotFound
from rest_framework.response import Response
from rest_framework.serializers import ReturnDict
from rest_framework import status


class JWTTokenService:

    @staticmethod
    def check_token(token):
        if not token:
            raise NotFoundToken()

        try:
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')
            
            user = User.objects.get(id=user_id)
            user_data = UserSerializer(user).data

            return Response(
                {"message": "Token is valid", "user": user_data},
                status=status.HTTP_200_OK,
            )
            
                    
        except TokenError as e:
            raise InvalidToken(e.args[0])
        except User.DoesNotExist:
            raise UserNotFound()

    @staticmethod
    def token_refresh(response):

        if 'refresh' in response.data:
            new_refresh_token = response.data['refresh']
        
            response.set_cookie(
                'refresh',
                new_refresh_token,
                max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                secure=settings.CSRF_COOKIE_SECURE,
                samesite=settings.CSRF_COOKIE_SAMESITE,
                httponly=True,
            )
        
            del response.data['refresh']
        
        return response

    @staticmethod
    def token_pair(request, response):
        new_response = Response({
            'access': response.data['access'],
            'user': {
            'id': request.user.id if hasattr(request, 'user') else None,
            'username': request.data.get('username', None)
            }
        }, status=status.HTTP_200_OK)
        
        new_response.set_cookie(
            'refresh',
            response.data['refresh'],
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            samesite=settings.CSRF_COOKIE_SAMESITE,
            secure=settings.CSRF_COOKIE_SECURE,
        )
        
        return new_response