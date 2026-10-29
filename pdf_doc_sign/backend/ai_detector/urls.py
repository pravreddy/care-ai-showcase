from django.urls import path
from . import views

urlpatterns = [
    path('scan/', views.AIDetectView.as_view(), name='ai-detect-scan'),
    path('scan-text/', views.AIDetectTextView.as_view(), name='ai-detect-scan-text'),
    path('history/', views.AIDetectHistoryView.as_view(), name='ai-detect-history'),
    path('scans/<uuid:scan_id>/', views.AIDetectScanDetailView.as_view(), name='ai-detect-detail'),
    path('scans/<uuid:scan_id>/deep/', views.AIDeepScanView.as_view(), name='ai-detect-deep'),
    path('providers/', views.AIDetectorProvidersView.as_view(), name='ai-detect-providers'),
    path('usage/', views.AIDetectorUsageView.as_view(), name='ai-detect-usage'),
]
