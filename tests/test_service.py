import re
import pytest
from backend import service


class TestGenerateCode:
    def test_default_length(self):
        assert len(service.generate_code()) == 6

    def test_alphanumeric(self):
        code = service.generate_code(length=100)
        assert re.fullmatch(r"[A-Za-z0-9]+", code)

    def test_custom_length(self):
        assert len(service.generate_code(length=12)) == 12


class TestCreateLink:
    async def test_returns_response(self, db):
        result = await service.create_link(db, "https://example.com", "http://localhost:8000")
        assert result.url == "https://example.com"
        assert result.visit_count == 0

    async def test_auto_generates_code(self, db):
        result = await service.create_link(db, "https://example.com", "http://localhost:8000")
        assert len(result.code) == 6

    async def test_custom_code(self, db):
        result = await service.create_link(db, "https://example.com", "http://localhost:8000", custom_code="mylink")
        assert result.code == "mylink"

    async def test_duplicate_custom_code_raises(self, db):
        await service.create_link(db, "https://example.com", "http://localhost:8000", custom_code="dup")
        with pytest.raises(ValueError, match="code_taken"):
            await service.create_link(db, "https://other.com", "http://localhost:8000", custom_code="dup")


class TestGetLink:
    async def test_found(self, db):
        created = await service.create_link(db, "https://example.com", "http://localhost:8000")
        result = await service.get_link(db, created.code)
        assert result is not None
        assert result.code == created.code

    async def test_not_found(self, db):
        result = await service.get_link(db, "notexist")
        assert result is None


class TestDeleteLink:
    async def test_returns_true(self, db):
        created = await service.create_link(db, "https://example.com", "http://localhost:8000")
        assert await service.delete_link(db, created.code) is True

    async def test_not_found_returns_false(self, db):
        assert await service.delete_link(db, "notexist") is False


class TestIncrementVisit:
    async def test_increments(self, db):
        created = await service.create_link(db, "https://example.com", "http://localhost:8000")
        await service.increment_visit(db, created.code)
        result = await service.get_link(db, created.code)
        assert result is not None
        assert result.visit_count == 1
