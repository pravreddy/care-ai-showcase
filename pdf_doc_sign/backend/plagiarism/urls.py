from django.urls import path
from . import views

urlpatterns = [
    path('scan/', views.PlagiarismScanFileView.as_view(), name='plagiarism-scan-file'),
    path('scan-text/', views.PlagiarismScanTextView.as_view(), name='plagiarism-scan-text'),
    path('history/', views.PlagiarismHistoryView.as_view(), name='plagiarism-history'),
    path('scans/<uuid:scan_id>/', views.PlagiarismScanDeleteView.as_view(), name='plagiarism-delete'),
    path('providers/', views.PlagiarismProvidersView.as_view(), name='plagiarism-providers'),
]
