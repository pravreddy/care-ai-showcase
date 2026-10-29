from django.urls import path
from . import views

urlpatterns = [
    # Coupons
    path('coupons/', views.CouponListView.as_view(), name='coupon-list'),
    path('coupons/generate/', views.CouponGenerateView.as_view(), name='coupon-generate'),
    path('coupons/grant-free/', views.SuperuserGrantFreeView.as_view(), name='coupon-grant-free'),
    path('coupons/validate/<str:code>/', views.CouponValidateView.as_view(), name='coupon-validate'),
    path('coupons/redeem/', views.CouponRedeemView.as_view(), name='coupon-redeem'),
    path('coupons/<uuid:coupon_id>/deactivate/', views.CouponDeactivateView.as_view(), name='coupon-deactivate'),

    # Subscriptions
    path('subscriptions/my/', views.MySubscriptionView.as_view(), name='my-subscription'),
    path('subscriptions/plans/', views.PlansView.as_view(), name='plans'),
]
