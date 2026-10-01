"""Experimental Google hotel review collector for Atlas.

This side project deliberately keeps navigation, parsing and persistence
separate so its output can become an Atlas data source later.
"""

from .parser import parse_reviews_html
from .schema import GoogleReview, GoogleReviewsResult

__all__ = ["GoogleReview", "GoogleReviewsResult", "parse_reviews_html"]
