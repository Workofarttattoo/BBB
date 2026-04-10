import re

with open("src/blank_business_builder/level6_agent.py", "r") as f:
    content = f.read()

# We need to add func from sqlalchemy
if "from sqlalchemy import func" not in content:
    content = content.replace("from sqlalchemy.orm import Session", "from sqlalchemy.orm import Session\nfrom sqlalchemy import func")

# Replace manage_churn_prevention
old_manage_churn_prevention = """
    async def manage_churn_prevention(self, db: Session) -> List[AgentDecision]:
        \"\"\"
        Predictive churn prevention.
        - Identify at-risk customers
        - Automated retention campaigns
        - Personalized intervention
        \"\"\"
        decisions = []

        # Get paid subscribers
        subscriptions = db.query(Subscription).filter(
            Subscription.status == "active"
        ).all()

        for subscription in subscriptions:
            churn_risk = self._calculate_churn_risk(subscription, db)

            if churn_risk > 0.7:  # High risk
                user = db.query(User).filter(User.id == subscription.user_id).first()
                decision = await self._create_retention_campaign(user, churn_risk, db)
                decisions.append(decision)

        return decisions
"""

new_manage_churn_prevention = """
    async def manage_churn_prevention(self, db: Session) -> List[AgentDecision]:
        \"\"\"
        Predictive churn prevention.
        - Identify at-risk customers
        - Automated retention campaigns
        - Personalized intervention
        \"\"\"
        decisions = []

        # Get paid subscribers
        subscriptions = db.query(Subscription).filter(
            Subscription.status == "active"
        ).all()

        if not subscriptions:
            return decisions

        # Bulk fetch users
        user_ids = [sub.user_id for sub in subscriptions]
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_dict = {user.id: user for user in users}

        # Bulk fetch business counts
        business_counts = dict(
            db.query(Business.user_id, func.count(Business.id))
            .filter(Business.user_id.in_(user_ids))
            .group_by(Business.user_id)
            .all()
        )

        for subscription in subscriptions:
            user = user_dict.get(subscription.user_id)
            if not user:
                continue

            business_count = business_counts.get(subscription.user_id, 0)
            churn_risk = self._calculate_churn_risk(subscription, user, business_count)

            if churn_risk > 0.7:  # High risk
                decision = await self._create_retention_campaign(user, churn_risk, db)
                decisions.append(decision)

        return decisions
"""

content = content.replace(old_manage_churn_prevention.strip("\n"), new_manage_churn_prevention.strip("\n"))

# Replace _calculate_churn_risk
old_calculate_churn_risk = """
    def _calculate_churn_risk(self, subscription: Subscription, db: Session) -> float:
        \"\"\"Calculate churn probability for a subscription.\"\"\"
        risk_score = 0.0

        user = db.query(User).filter(User.id == subscription.user_id).first()

        # Factor 1: Login frequency
        if user.last_login:
            days_since_login = (datetime.utcnow() - user.last_login).days
            if days_since_login > 30:
                risk_score += 0.4
            elif days_since_login > 14:
                risk_score += 0.2

        # Factor 2: Usage (businesses created)
        business_count = db.query(Business).filter(Business.user_id == user.id).count()
        if business_count == 0:
            risk_score += 0.3
        elif business_count == 1:
            risk_score += 0.1

        # Factor 3: Cancel at period end flag
        if subscription.cancel_at_period_end:
            risk_score += 0.5

        return min(risk_score, 1.0)
"""

new_calculate_churn_risk = """
    def _calculate_churn_risk(self, subscription: Subscription, user: User, business_count: int) -> float:
        \"\"\"Calculate churn probability for a subscription.\"\"\"
        risk_score = 0.0

        # Factor 1: Login frequency
        if user.last_login:
            days_since_login = (datetime.utcnow() - user.last_login).days
            if days_since_login > 30:
                risk_score += 0.4
            elif days_since_login > 14:
                risk_score += 0.2

        # Factor 2: Usage (businesses created)
        if business_count == 0:
            risk_score += 0.3
        elif business_count == 1:
            risk_score += 0.1

        # Factor 3: Cancel at period end flag
        if subscription.cancel_at_period_end:
            risk_score += 0.5

        return min(risk_score, 1.0)
"""

content = content.replace(old_calculate_churn_risk.strip("\n"), new_calculate_churn_risk.strip("\n"))

with open("src/blank_business_builder/level6_agent.py", "w") as f:
    f.write(content)
