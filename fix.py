with open('tests/test_payments.py', 'r') as f:
    content = f.read()

test_code = """
class TestPaymentEventHandler:
    @pytest.fixture
    def mock_db(self):
        \"\"\"Mock SQLAlchemy database session.\"\"\"
        db = MagicMock()
        return db

    @patch("blank_business_builder.payments.datetime")
    def test_handle_subscription_deleted_success(self, mock_datetime, mock_db):
        \"\"\"Test successful handling of subscription.deleted event.\"\"\"
        from blank_business_builder.payments import PaymentEventHandler

        # Setup mock datetime
        mock_now = MagicMock()
        mock_datetime.utcnow.return_value = mock_now
        mock_timedelta = MagicMock()
        mock_datetime.timedelta.return_value = mock_timedelta

        # Setup test data
        event_data = {
            "object": {
                "id": "sub_123"
            }
        }

        # Mock database models
        mock_subscription = MagicMock()
        mock_subscription.user_id = "usr_123"
        mock_subscription.status = "active"

        mock_user = MagicMock()
        mock_user.subscription_tier = "pro"
        mock_user.license_status = "licensed"

        # Configure the db mock behavior
        # The function calls:
        # 1. db.query(Subscription).filter(...).first()
        # 2. db.query(User).filter(...).first()

        # Create mock query objects
        mock_sub_query = MagicMock()
        mock_sub_query.filter.return_value.first.return_value = mock_subscription

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = mock_user

        # Use side_effect to return different queries based on the model class passed
        def query_side_effect(model):
            if model.__name__ == 'Subscription':
                return mock_sub_query
            elif model.__name__ == 'User':
                return mock_user_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        # Execute
        PaymentEventHandler.handle_subscription_deleted(event_data, mock_db)

        # Assertions
        assert mock_subscription.status == "canceled"
        assert mock_user.subscription_tier == "free"
        assert mock_user.license_status == "trial"
        assert mock_user.trial_expires_at is not None

        # Verify db commit was called
        mock_db.commit.assert_called_once()

    def test_handle_subscription_deleted_not_found(self, mock_db):
        \"\"\"Test handling of subscription.deleted when subscription is not found.\"\"\"
        from blank_business_builder.payments import PaymentEventHandler

        event_data = {
            "object": {
                "id": "sub_not_found"
            }
        }

        # Mock db to return None for subscription query
        mock_sub_query = MagicMock()
        mock_sub_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model.__name__ == 'Subscription':
                return mock_sub_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        # Execute
        PaymentEventHandler.handle_subscription_deleted(event_data, mock_db)

        # Assertions - commit should not be called since we do not hit db.commit() in the if block
        mock_db.commit.assert_not_called()

    def test_handle_subscription_deleted_user_not_found(self, mock_db):
        \"\"\"Test handling of subscription.deleted when user is not found.\"\"\"
        from blank_business_builder.payments import PaymentEventHandler

        event_data = {
            "object": {
                "id": "sub_123"
            }
        }

        mock_subscription = MagicMock()
        mock_subscription.user_id = "usr_not_found"
        mock_subscription.status = "active"

        # Mock queries - subscription found, user not found
        mock_sub_query = MagicMock()
        mock_sub_query.filter.return_value.first.return_value = mock_subscription

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model.__name__ == 'Subscription':
                return mock_sub_query
            elif model.__name__ == 'User':
                return mock_user_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        # Execute
        PaymentEventHandler.handle_subscription_deleted(event_data, mock_db)

        # Assertions
        assert mock_subscription.status == "canceled"

        # Verify db commit was called
        mock_db.commit.assert_called_once()
"""
if "class TestPaymentEventHandler" not in content:
    with open('tests/test_payments.py', 'a') as f:
        f.write("\n" + test_code)

import re
# Remove the try import sqlalchemy because it breaks our test.
content = open('tests/test_payments.py').read()
content = re.sub(r"try:\n    import sqlalchemy\n    import sqlalchemy\.orm\nexcept ImportError:\n    mock_sqlalchemy = MagicMock\(\)\n    mock_sqlalchemy\.orm = MagicMock\(\)\n    sys\.modules\['sqlalchemy'\] = mock_sqlalchemy\n    sys\.modules\['sqlalchemy\.orm'\] = mock_sqlalchemy\.orm\n\n", "", content)

with open('tests/test_payments.py', 'w') as f:
    f.write(content)
