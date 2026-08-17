from django.urls import path
from .views import (
    CVAnalysisView,
    AIExtractionConfirmView,
    AIExtractionListView
)

urlpatterns = [
    path('cv-analyze/', CVAnalysisView.as_view(), name='cv-analyze'),
    path('extractions/', AIExtractionListView.as_view(), name='ai-extractions'),
    path('extractions/<str:extraction_id>/confirm/', AIExtractionConfirmView.as_view(), name='ai-extraction-confirm'),
]