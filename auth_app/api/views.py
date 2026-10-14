from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .serializers import RegisterSerializer

from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        user.is_active = False
        user.save()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_path = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
        activation_link = request.build_absolute_uri(activation_path)

        send_mail(subject = "Activate your Videoflix account",
                  message = f"Welcome to Videoflix! Please activate your account by clicking the following link {activation_link}" ,
                  from_email = "noreply@videoflix.de",
                  recipient_list = [user.email])
        

        return Response (
            {'user': {
                'id': user.id,
                'email': user.email
            },
                'token': token
            },
            status=status.HTTP_201_CREATED
        )

class ActivateView(generics.GenericAPIView):
    
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try: 
            uidb64 = urlsafe_base64_decode(uidb64)
            user_id = force_str(uidb64)
            user = User.objects.get(pk = user_id)

        except (User.DoesNotExist, ValueError):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()

            return Response({'message': 'Account successfully activated.'},status=status.HTTP_200_OK)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)
