class TestHealth:
    async def test_health_check(self, client):
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


class TestCreateLink:
    async def test_create_link_201(self, client):
        res = await client.post("/api/links", json={"url": "https://python.org"})
        assert res.status_code == 201
        data = res.json()
        assert "code" in data
        assert data["visit_count"] == 0
        assert data["url"] == "https://python.org/"  # pydantic normalises trailing slash

    async def test_create_link_duplicate_code_400(self, client):
        await client.post("/api/links", json={"url": "https://example.com", "custom_code": "dup123"})
        res = await client.post("/api/links", json={"url": "https://other.com", "custom_code": "dup123"})
        assert res.status_code == 400


class TestListLinks:
    async def test_list_links_200(self, client):
        await client.post("/api/links", json={"url": "https://example.com"})
        res = await client.get("/api/links")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) >= 1


class TestRedirect:
    async def test_redirect_302(self, client):
        create_res = await client.post("/api/links", json={"url": "https://python.org"})
        code = create_res.json()["code"]
        res = await client.get(f"/r/{code}", follow_redirects=False)
        assert res.status_code == 302
        assert "python.org" in res.headers["location"]

    async def test_redirect_unknown_404(self, client):
        res = await client.get("/r/doesnotexist", follow_redirects=False)
        assert res.status_code == 404


class TestDeleteLink:
    async def test_delete_link_204(self, client):
        create_res = await client.post("/api/links", json={"url": "https://example.com"})
        code = create_res.json()["code"]
        res = await client.delete(f"/api/links/{code}")
        assert res.status_code == 204

    async def test_delete_unknown_404(self, client):
        res = await client.delete("/api/links/badcode")
        assert res.status_code == 404


class TestVisitCount:
    async def test_visit_count_increments(self, client):
        create_res = await client.post("/api/links", json={"url": "https://example.com"})
        code = create_res.json()["code"]
        # Two redirects
        await client.get(f"/r/{code}", follow_redirects=False)
        await client.get(f"/r/{code}", follow_redirects=False)
        # Check visit count
        links = await client.get("/api/links")
        link = next(item for item in links.json() if item["code"] == code)
        assert link["visit_count"] == 2
