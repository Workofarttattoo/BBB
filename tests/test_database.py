import os
import unittest
from unittest.mock import patch, MagicMock

from src.blank_business_builder.database import get_db_engine

class TestDatabase(unittest.TestCase):

    @patch('src.blank_business_builder.database.create_engine')
    def test_get_db_engine_explicit_url(self, mock_create_engine):
        """Test get_db_engine with an explicit database_url passed."""
        test_url = "postgresql://user:pass@localhost/testdb"

        # Call the function
        engine = get_db_engine(database_url=test_url)

        # Verify create_engine was called correctly
        mock_create_engine.assert_called_once_with(
            test_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        self.assertEqual(engine, mock_create_engine.return_value)

    @patch('src.blank_business_builder.database.create_engine')
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://envuser:envpass@localhost/envdb"})
    def test_get_db_engine_env_url(self, mock_create_engine):
        """Test get_db_engine reads from DATABASE_URL environment variable."""
        # Call the function without explicit URL
        engine = get_db_engine()

        # Verify create_engine was called with the env var URL
        mock_create_engine.assert_called_once_with(
            "postgresql://envuser:envpass@localhost/envdb",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        self.assertEqual(engine, mock_create_engine.return_value)

    @patch('src.blank_business_builder.database.create_engine')
    def test_get_db_engine_default_url(self, mock_create_engine):
        """Test get_db_engine falls back to default URL when env var is missing."""
        # Setup mock to simulate missing env var using patch.dict with clear=True
        # or deleting from os.environ
        with patch.dict(os.environ, {}, clear=True):
            # Also ensure DATABASE_URL is truly removed if patch.dict clear=True doesn't cover all
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

            # Call the function
            engine = get_db_engine()

            # Verify create_engine was called with the fallback URL defined in the source
            mock_create_engine.assert_called_once_with(
                "postgresql://bbbuser:password@localhost:5432/bbb_production",
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False
            )
            self.assertEqual(engine, mock_create_engine.return_value)

if __name__ == '__main__':
    unittest.main()
