# thepopwinegdrives/urls.py

from django.urls import path
from .views import BookListCreate, BookDetail, AggregatedContentView, ScrapeWebpageView
 
urlpatterns = [
    path('books/', BookListCreate.as_view(), name='book-list'),
    path('books/<int:pk>/', BookDetail.as_view(), name='book-detail'),
    path('scrape-webpage/', ScrapeWebpageView.as_view(), name='scrape-webpage'),
    path('aggregated-content/', AggregatedContentView.as_view(), name='aggregated-content'),
]
