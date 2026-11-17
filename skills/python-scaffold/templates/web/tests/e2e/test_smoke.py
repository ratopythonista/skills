import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_home_loads_in_the_browser(page: Page, server_url: str) -> None:
    page.goto(server_url)

    expect(page.get_by_role("heading", name="{{PROJECT}}")).to_be_visible()
    expect(page.get_by_text("Scaffolded with the pack-python web profile.")).to_be_visible()
