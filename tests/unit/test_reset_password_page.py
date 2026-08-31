"""The /auth/reset page — where the Supabase password-recovery link lands.

The page is the only path a user has back into a forgotten account (the app has
no in-app recovery screen), so the things asserted here are the things that make
it work at all: it must know which Supabase project to talk to, it must read the
recovery token the redirect hands it, and it must be readable by both RU and EN
users.

bot/legal.py stays import-safe (no env reads, no Supabase client), so these run
without the stubs in tests/conftest.py doing any work.

The GET /auth/reset route itself is deliberately NOT covered here: importing
bot.app.main performs the Supabase service login at module load, which is why
test_import_main.py builds a router-only app instead. The route is the same
three-line pattern as /auth/confirmed, /privacy and /terms — none of which are
route-tested either. It was verified by running the app and fetching the path.
"""

from __future__ import annotations

import json

from bot.legal import reset_password_html

URL = "https://agjegzjxrshobnicmrxb.supabase.co"
ANON = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdHViIn0.stub"


def test_page_embeds_the_project_it_must_call() -> None:
    """Without the project URL and anon key the page cannot reach Supabase."""
    page = reset_password_html(URL, ANON)
    assert URL in page
    assert ANON in page


def test_page_updates_the_password_via_the_supabase_user_endpoint() -> None:
    """Setting a new password is a PATCH of the authenticated user."""
    page = reset_password_html(URL, ANON)
    assert "/auth/v1/user" in page
    assert "PATCH" in page


def test_page_reads_the_recovery_token_from_the_url_fragment() -> None:
    """Supabase's implicit-flow redirect carries the token in the #fragment,
    which never reaches the server — the page has to parse it client-side."""
    page = reset_password_html(URL, ANON)
    assert "location.hash" in page
    assert "access_token" in page


def test_page_is_bilingual() -> None:
    """Russian-first copy with an English counterpart, per the app's convention."""
    page = reset_password_html(URL, ANON)
    assert "Новый пароль" in page
    assert "New password" in page


def test_interpolated_values_are_json_encoded() -> None:
    """A stray quote in an env var must not break out of the JS string literal
    and silently produce a page that throws on load."""
    page = reset_password_html('https://x.co/"+alert(1)+"', 'a"b')
    assert json.dumps('https://x.co/"+alert(1)+"') in page
    assert json.dumps('a"b') in page
