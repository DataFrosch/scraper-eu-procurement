"""
Monetary value parsers.

Each parser handles exactly ONE specific format.
"""

from .float_dot_decimal import parse_float_dot_decimal

__all__ = ["parse_float_dot_decimal"]
