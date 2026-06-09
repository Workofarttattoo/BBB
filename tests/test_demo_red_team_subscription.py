import sys
import unittest
from unittest.mock import patch

class TestDemoRedTeamSubscription(unittest.TestCase):
    def test_import_error_handling(self):
        """Test that ImportError is handled correctly by sys.exit(1)"""
        # Save original modules
        orig_modules = sys.modules.copy()

        # Ensure the script is not already imported
        if 'scripts.demos.demo_red_team_subscription' in sys.modules:
            del sys.modules['scripts.demos.demo_red_team_subscription']

        with patch.dict('sys.modules', {'blank_business_builder.red_team_subscription_system': None}):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    try:
                        import scripts.demos.demo_red_team_subscription
                    except Exception:
                        # Catch any other exceptions that might happen during import,
                        # though the sys.exit should raise SystemExit, which we mocked
                        pass

                    mock_exit.assert_called_once_with(1)
                    # Check if print was called with the error message
                    print_args = mock_print.call_args[0][0]
                    self.assertIn("Error importing RedTeamLicenseManager", print_args)

        # Clean up
        sys.modules = orig_modules
        if 'scripts.demos.demo_red_team_subscription' in sys.modules:
            del sys.modules['scripts.demos.demo_red_team_subscription']

if __name__ == '__main__':
    unittest.main()
