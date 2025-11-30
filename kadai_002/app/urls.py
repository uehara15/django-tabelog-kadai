from django.urls import path
from . import views
from .views import MemberProfileUpdateView,ReviewUpdateView, ReviewDeleteView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ショップ関連
    path('', views.ShopListView.as_view(), name='shop_list'),
    path('shop/<int:pk>/', views.ShopDetailView.as_view(), name='shop_detail'),
    path('shop/update/<int:pk>/', views.ShopUpdateView.as_view(), name='shop_update'),

    #レビュー関連
    path('review/<int:pk>/edit/', ReviewUpdateView.as_view(), name='review_edit'),
    path('review/<int:pk>/delete/', ReviewDeleteView.as_view(), name='review_delete'),

    # 認証関連
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # 会社説明
    path('company/', views.company_detail, name='company_detail'),  
   
    # サブスク
    path("subscription/", views.SubscriptionPageView.as_view(), name="subscription"),
    path("subscription/create/", views.create_subscription, name="create_subscription"),

    #会員情報編集
    path("member/edit/", MemberProfileUpdateView.as_view(), name="member_edit"),

    # 予約関連
    path('shop/<int:shop_id>/reservation/', views.make_reservation, name='make_reservation'),
    path('reservation/complete/<int:reservation_id>/', views.reservation_complete, name='reservation_complete'),
    path('my_reservations/', views.MyReservationListView.as_view(), name='my_reservations'),
    path('reservation/<int:pk>/cancel/', views.ReservationCancelView.as_view(), name='reservation_cancel'),

    # Stripe決済関連
    path('shop/<int:pk>/checkout/', views.CreateCheckoutSessionView.as_view(), name='checkout'),
    path('success/', views.SuccessPageView.as_view(), name='success'),
    path('cancel/', views.CancelPageView.as_view(), name='cancel'),
    path("billing/portal/", views.billing_portal, name="billing_portal"),

    # パスワードリセット
    path("password_reset/", 
         auth_views.PasswordResetView.as_view(
             template_name="app/password_reset.html"
         ), 
         name="password_reset"),

    path("password_reset_done/", 
         auth_views.PasswordResetDoneView.as_view(
             template_name="app/password_reset_done.html"
         ), 
         name="password_reset_done"),

    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="app/password_reset_confirm.html"
         ),
         name="password_reset_confirm"),

    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(
             template_name="app/password_reset_complete.html"
         ),
         name="password_reset_complete"),

    # urls.py
    path("favorite/add/<int:shop_id>/", views.add_favorite, name="add_favorite"),
    path("favorite/remove/<int:shop_id>/", views.remove_favorite, name="remove_favorite"),
    path("favorites/", views.my_favorite_list, name="my_favorite_list"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)