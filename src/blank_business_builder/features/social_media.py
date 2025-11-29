"""
Social media integration for automated posting.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    tweepy = None
    TWEEPY_AVAILABLE = False

from ..ech0_service import ECH0Service

class SocialMedia:
    """
    Social media agent for posting to Twitter.
    """

    def __init__(self, consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)
        self.ech0_service = ECH0Service()

    async def post_tweet(self, text: str) -> bool:
        """
        Post a tweet to Twitter.
        """
        try:
            # Try posting with ECH0 first
            return await self.ech0_service.post_to_social_media("Twitter", text)
        except Exception:
            # Fallback to Tweepy
            try:
                self.api.update_status(text)
                return True
            except Exception as e:
                print(f"Error posting tweet: {e}")
                return False
