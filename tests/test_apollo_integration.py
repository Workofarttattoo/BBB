from src.blank_business_builder.integrations.apollo import ApolloService


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.posts = []

    def post(self, url, json, headers, timeout):
        self.posts.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if url.endswith("/v1/mixed_people/search"):
            return _FakeResponse({"people": [{"id": "p_1", "first_name": "Alex"}]})
        return _FakeResponse({"person": {"id": "p_1", "email": "alex@example.com"}})


def test_apollo_search_then_enrich():
    session = _FakeSession()
    service = ApolloService(api_key="apollo-key", session=session)

    search = service.search_people(q_keywords="AI CTO", q_organization_name="Acme", per_page=5)
    assert search["people"][0]["id"] == "p_1"

    enrich = service.enrich_person(email="alex@example.com", first_name="Alex", last_name="Rivera")
    assert enrich["person"]["email"] == "alex@example.com"

    assert len(session.posts) == 2
    assert session.posts[0]["url"].endswith("/v1/mixed_people/search")
    assert session.posts[0]["json"]["q_keywords"] == "AI CTO"
    assert session.posts[0]["headers"]["X-Api-Key"] == "apollo-key"
    assert session.posts[1]["url"].endswith("/v1/people/match")
    assert session.posts[1]["json"]["email"] == "alex@example.com"
