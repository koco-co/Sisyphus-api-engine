"""Extractor Factory for Sisyphus API Engine.

This module provides a factory for creating extractors.
Following Google Python Style Guide.
"""


from apirun.extractor.cookie_extractor import CookieExtractor
from apirun.extractor.header_extractor import HeaderExtractor
from apirun.extractor.jsonpath_extractor import JSONPathExtractor
from apirun.extractor.regex_extractor import RegexExtractor


class ExtractorFactory:
    """Factory for creating extractor instances.

    Supported extractor types:
    - jsonpath: Extract using JSONPath expressions
    - regex: Extract using regular expressions
    - header: Extract from HTTP headers
    - cookie: Extract from cookies
    """

    def __init__(self):
        """Initialize ExtractorFactory."""
        self._extractors: dict[str, type] = {
            'jsonpath': JSONPathExtractor,
            'regex': RegexExtractor,
            'header': HeaderExtractor,
            'cookie': CookieExtractor,
        }

    def create_extractor(self, extractor_type: str):
        """Create extractor instance by type.

        Args:
            extractor_type: Type of extractor to create

        Returns:
            Extractor instance

        Raises:
            ValueError: If extractor type is not supported
        """
        extractor_class = self._extractors.get(extractor_type.lower())

        if extractor_class is None:
            raise ValueError(f'Unsupported extractor type: {extractor_type}')

        return extractor_class()

    def register_extractor(self, name: str, extractor_class: type) -> None:
        """Register a custom extractor.

        Args:
            name: Extractor name
            extractor_class: Extractor class
        """
        self._extractors[name.lower()] = extractor_class
