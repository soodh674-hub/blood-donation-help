"""
Custom WhiteNoise storage backend that ignores missing source map files.

This fixes the MissingFileError for leaflet.js.map and other missing source maps.
"""
from whitenoise.storage import CompressedStaticFilesStorage
import logging
import os

logger = logging.getLogger(__name__)


class WhiteNoiseStaticFilesStorage(CompressedStaticFilesStorage):
    """
    Custom WhiteNoise storage WITHOUT manifest hashing.
    
    Uses CompressedStaticFilesStorage instead of CompressedManifestStaticFilesStorage
    to avoid manifest errors with missing files like favicon.ico and .map files.
    
    This is more forgiving and production-safe.
    """
    
    def post_process(self, paths, dry_run=False, **options):
        """
        Override post_process to skip files that reference missing source maps.
        """
        processed_paths = []
        for name, hashed_name, processed in super().post_process(paths, dry_run, **options):
            # Skip processing for .map files and files that might reference them
            if name.endswith('.map'):
                logger.info(f"Skipping source map file: {name}")
                continue
            processed_paths.append((name, hashed_name, processed))
        return processed_paths
    
    def url(self, name, force=False):
        """
        Override url method to handle missing files gracefully.
        """
        try:
            # FileSystemStorage.url() only takes name parameter
            return super().url(name)
        except ValueError as e:
            # If the file is missing from manifest, try to return a direct URL
            if 'Missing staticfiles manifest entry' in str(e):
                logger.warning(f"Missing manifest entry for '{name}', using direct URL")
                return f"{self.base_url}{name}"
            raise
