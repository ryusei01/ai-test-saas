import pytest
from fastapi import HTTPException
from app.analyzer import inspect_files, parse_github_url

def test_valid_repo():
    assert parse_github_url("https://github.com/acme/shop") == ("acme", "shop")

@pytest.mark.parametrize("url", ["http://github.com/a/b", "https://evil.com/a/b", "https://github.com/a/b/extra", "https://github.com@evil.com/a/b"])
def test_invalid_repo(url):
    with pytest.raises(HTTPException):
        parse_github_url(url)

def test_route_and_form():
    result = inspect_files([("src/app/login/page.tsx", "export default function Login(){return <form><input /></form>}")], "a/b")
    assert "/login" in result.routes
    assert {c.kind for c in result.cases} == {"page", "form"}
