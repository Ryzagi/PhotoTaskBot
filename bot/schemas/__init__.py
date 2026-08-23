"""Pydantic models used across the API.

Split into modules per domain object. Mobile clients regenerate types from the
emitted openapi.json — any breaking change here cascades to mobile CI.
"""
