from django.urls import path
from . import views

urlpatterns = [
    # Public (no auth — visitors aren't logged in)
    path('start/', views.ChatStartView.as_view(), name='chatbot-start'),
    path('<uuid:session_id>/message/', views.ChatMessageView.as_view(), name='chatbot-message'),
    path('<uuid:session_id>/', views.ChatSessionDetailView.as_view(), name='chatbot-session'),

    # Admin (platform admin only)
    path('leads/', views.LeadListView.as_view(), name='chatbot-leads'),
    path('sessions/', views.ChatSessionListView.as_view(), name='chatbot-sessions'),
]
