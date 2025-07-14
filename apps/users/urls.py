from django.urls import path
from .views import (
    RegisterView, LogoutView, CreateAdminView,
    MyProfileView, AllUsersAdminView, AllUserProfilesAdminView,
    LogoutAndBlacklistRefreshTokenForUserView
)
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('create-admin/', CreateAdminView.as_view(), name='create-admin'),
    path('profile/', MyProfileView.as_view(), name='my-profile'),
    path('admin/users/', AllUsersAdminView.as_view(), name='all-users-admin'),
    path('admin/userprofiles/', AllUserProfilesAdminView.as_view(), name='all-userprofiles-admin'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += [
    path('logout/', LogoutAndBlacklistRefreshTokenForUserView.as_view(), name='logout'),
] 