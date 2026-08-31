"""Static legal pages (served at /privacy, /terms). Plain self-contained HTML so
they render without any assets and can be linked from the app + Play Console.

NOTE: review with counsel before launch and set a real CONTACT_EMAIL.
"""

import json

CONTACT_EMAIL = "ryzagidev@gmail.com"

PRIVACY_HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PandaSolve — Privacy Policy</title>
<style>
  :root {{ --paper:#FDF6ED; --ink:#4B4138; --soft:#9B9081; --mint:#2F7D5B; --card:#fff; --line:#EFE3D2; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; line-height:1.6; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:32px 20px 64px; }}
  .badge {{ font-size:40px; }}
  h1 {{ font-size:28px; margin:8px 0 2px; }}
  .upd {{ color:var(--soft); font-size:14px; margin-bottom:28px; }}
  h2 {{ font-size:18px; margin:28px 0 6px; color:var(--mint); }}
  .card {{ background:var(--card); border:2px solid var(--line); border-radius:20px; padding:18px 20px; }}
  a {{ color:var(--mint); }}
  ul {{ padding-left:20px; }}
  code {{ background:var(--line); padding:1px 6px; border-radius:6px; }}
  footer {{ margin-top:36px; color:var(--soft); font-size:13px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="badge">🐼</div>
  <h1>PandaSolve — Privacy Policy</h1>
  <div class="upd">Last updated: 9 June 2026</div>

  <div class="card">
    <p>PandaSolve ("the app", "we") helps students solve and understand homework
    problems from a photo or text. This policy explains what we collect, why, and
    your choices. By using the app you agree to this policy.</p>

    <h2>What we collect</h2>
    <ul>
      <li><b>Account</b> — your email address, via Google Sign-In or email/password
        (authentication handled by Supabase).</li>
      <li><b>Your content</b> — the problems you submit: photos, typed text, follow-up
        chat messages, and any images you attach in chat.</li>
      <li><b>Solutions &amp; history</b> — the generated solutions, your folders, and a
        record of solved tasks tied to your account.</li>
      <li><b>Balance &amp; purchases</b> — your daily/purchased solution balance and a
        record of in-app purchases (processed by Google Play; we do not receive your
        card details).</li>
      <li><b>Diagnostics</b> — crash and error reports to keep the app stable.</li>
    </ul>

    <h2>How we use it</h2>
    <ul>
      <li>To produce step-by-step solutions, your problem content is sent to our AI
        providers — <b>OpenAI</b> and <b>Google (Gemini)</b> — for processing.</li>
      <li>To maintain your account, balance, history and folders.</li>
      <li>To process and verify in-app purchases.</li>
      <li>To diagnose crashes and improve reliability.</li>
    </ul>
    <p>We do <b>not</b> sell your personal data or use it for third-party advertising.</p>

    <h2>Service providers</h2>
    <ul>
      <li><b>Supabase</b> — authentication, database and file storage.</li>
      <li><b>OpenAI</b> and <b>Google Gemini</b> — AI that generates solutions.</li>
      <li><b>Google</b> — Sign-In and Google Play Billing.</li>
      <li><b>Sentry</b> — crash reporting (when enabled).</li>
    </ul>
    <p>Each processes data under its own terms and security practices.</p>

    <h2>Retention &amp; deletion</h2>
    <p>We keep your content and history while your account is active. You can request
    deletion of your account and associated data by emailing us; we will delete it
    within a reasonable period, except where retention is required by law.</p>

    <h2>Children</h2>
    <p>The app is intended for students. If you are below the age of digital consent in
    your country, please use the app with a parent or guardian.</p>

    <h2>Your rights</h2>
    <p>You may request access to, correction of, or deletion of your personal data.
    Contact us at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>

    <h2>Changes</h2>
    <p>We may update this policy; the "last updated" date above will change. Continued
    use after an update means you accept the revised policy.</p>

    <h2>Contact</h2>
    <p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
  </div>

  <footer>© 2026 PandaSolve · <a href="/terms">Terms of Use</a></footer>
</div>
</body>
</html>"""

TERMS_HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PandaSolve — Terms of Use</title>
<style>
  body {{ margin:0; background:#FDF6ED; color:#4B4138;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; line-height:1.6; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:32px 20px 64px; }}
  h1 {{ font-size:28px; }} h2 {{ font-size:18px; color:#2F7D5B; margin-top:24px; }}
  .card {{ background:#fff; border:2px solid #EFE3D2; border-radius:20px; padding:18px 20px; }}
  a {{ color:#2F7D5B; }} .upd {{ color:#9B9081; font-size:14px; }}
</style>
</head>
<body>
<div class="wrap">
  <div style="font-size:40px">🐼</div>
  <h1>PandaSolve — Terms of Use</h1>
  <div class="upd">Last updated: 9 June 2026</div>
  <div class="card">
    <h2>Using the app</h2>
    <p>PandaSolve provides AI-generated explanations of homework problems for learning
    purposes. Solutions may contain errors — verify important results yourself. Don't use
    the app to cheat where prohibited by your school or exam rules.</p>
    <h2>Accounts &amp; balance</h2>
    <p>You get a number of free solutions each day. Additional solutions can be bought as
    consumable packs through Google Play. Purchases are final except where required by law
    or Google Play policy.</p>
    <h2>Acceptable use</h2>
    <p>Don't upload unlawful content or attempt to disrupt the service.</p>
    <h2>Disclaimer</h2>
    <p>The app is provided "as is", without warranties. To the extent permitted by law we
    are not liable for indirect or incidental damages.</p>
    <h2>Contact</h2>
    <p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
  </div>
  <footer style="margin-top:36px;color:#9B9081;font-size:13px">© 2026 PandaSolve · <a href="/privacy">Privacy Policy</a></footer>
</div>
</body>
</html>"""

# Landing page after a user clicks the email-confirmation link. Supabase verifies
# the token, then redirects here (set this URL as the Site URL / a Redirect URL in
# the Supabase Auth settings). We just tell them to return to the app and sign in.
CONFIRMED_HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PandaSolve — почта подтверждена</title>
<style>
  body { margin:0; background:#FDF6ED; color:#4B4138;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; line-height:1.6;
    min-height:100vh; display:flex; align-items:center; justify-content:center; }
  .card { max-width:420px; margin:20px; background:#fff; border:2px solid #EFE3D2;
    border-radius:24px; padding:34px 28px; text-align:center; }
  .badge { font-size:56px; }
  h1 { font-size:22px; margin:10px 0 6px; color:#2F7D5B; }
  p { font-size:15px; margin:6px 0; }
  .sub { color:#9B9081; font-size:13px; margin-top:14px; }
</style>
</head>
<body>
  <div class="card">
    <div class="badge">🐼✅</div>
    <h1>Почта подтверждена!</h1>
    <p>Вернись в приложение PandaSolve и войди со своей почтой и паролем.</p>
    <p class="sub">Email confirmed — open the PandaSolve app and sign in with your email and password.</p>
  </div>
</body>
</html>"""

# Account-deletion instructions, required by Google Play (Data safety → account
# deletion). Must name the app, give clear steps, and state what's deleted/kept.
DELETE_ACCOUNT_HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PandaSolve — Delete your account</title>
<style>
  body {{ margin:0; background:#FDF6ED; color:#4B4138;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; line-height:1.6; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:32px 20px 64px; }}
  .badge {{ font-size:40px; }}
  h1 {{ font-size:26px; margin:8px 0 2px; }}
  h2 {{ font-size:18px; margin:26px 0 6px; color:#2F7D5B; }}
  .card {{ background:#fff; border:2px solid #EFE3D2; border-radius:20px; padding:18px 20px; }}
  a {{ color:#2F7D5B; }}
  ol, ul {{ padding-left:22px; }}
  li {{ margin:6px 0; }}
  footer {{ margin-top:36px; color:#9B9081; font-size:13px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="badge">🐼</div>
  <h1>Delete your PandaSolve account</h1>
  <div class="card">
    <p>You can delete your <b>PandaSolve</b> account and its associated data at any time.</p>

    <h2>How to request deletion</h2>
    <ol>
      <li>Email <a href="mailto:{CONTACT_EMAIL}?subject=Delete%20my%20account">{CONTACT_EMAIL}</a>
        from the email address you use to sign in (or include it in the message).</li>
      <li>Use the subject line <b>"Delete my account"</b>.</li>
      <li>We verify the request and delete your account within <b>30 days</b>, and email you to confirm.</li>
    </ol>

    <h2>What gets deleted</h2>
    <ul>
      <li>Your account and sign-in details (email / auth identity)</li>
      <li>The problems you submitted — photos and typed text</li>
      <li>Your chat messages and attachments</li>
      <li>Your solution history and folders</li>
      <li>Your solution balance</li>
    </ul>

    <h2>What may be kept</h2>
    <p>We retain a minimal record of in-app purchases / transactions where required for
    legal, tax, accounting and fraud-prevention purposes, for the period required by law,
    after which it is deleted. These records are not used to identify you inside the app.</p>

    <h2>Deleting only some data</h2>
    <p>You can also ask us to delete <b>specific data</b> (for example, your solution history)
    without deleting your whole account — just say so in the same email.</p>

    <h2>Contact</h2>
    <p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
  </div>
  <footer>© 2026 PandaSolve · <a href="/privacy">Privacy Policy</a> · <a href="/terms">Terms of Use</a></footer>
</div>
</body>
</html>"""


# Where the Supabase password-recovery email lands (GET /auth/reset).
#
# Unlike the other pages here this one is a function, not a constant: it has to
# bake in the project URL and anon key so the browser can call Supabase directly.
# Both are public values (the Android app ships the same anon key), but they are
# environment-specific, so they arrive as arguments and keep this module free of
# env reads.
#
# The token arrives in the URL *fragment* (Supabase implicit flow), which never
# reaches the server — so the exchange has to happen in the page. SupabaseAuth.kt
# pins `flowType = IMPLICIT` for exactly this reason; PKCE would put a `?code=`
# here whose verifier only exists on the phone that asked, breaking the common
# "open the email on my laptop" case.
_RESET_PASSWORD_TEMPLATE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PandaSolve — новый пароль</title>
<style>
  :root { --paper:#FDF6ED; --ink:#4B4138; --soft:#9B9081; --mint:#2F7D5B;
          --card:#fff; --line:#EFE3D2; --coral:#BF5A41; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--paper); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; line-height:1.6;
    min-height:100vh; display:flex; align-items:center; justify-content:center; }
  .card { width:100%; max-width:420px; margin:20px; background:var(--card);
    border:2px solid var(--line); border-radius:24px; padding:34px 28px; text-align:center; }
  .badge { font-size:56px; }
  h1 { font-size:22px; margin:10px 0 6px; color:var(--mint); }
  p { font-size:15px; margin:6px 0; }
  .sub { color:var(--soft); font-size:13px; margin-top:14px; }
  label { display:block; text-align:left; font-size:13px; color:var(--soft); margin:14px 0 4px; }
  input { width:100%; padding:12px 14px; font-size:16px; color:var(--ink);
    background:var(--paper); border:2px solid var(--line); border-radius:14px; }
  input:focus { outline:none; border-color:var(--mint); }
  button { width:100%; margin-top:18px; padding:14px; font-size:16px; font-weight:700;
    color:#fff; background:var(--mint); border:none; border-radius:16px; cursor:pointer; }
  button[disabled] { opacity:.55; cursor:default; }
  .err { color:var(--coral); font-size:13px; margin-top:12px; min-height:18px; }
  .hidden { display:none; }
</style>
</head>
<body>
  <div class="card">

    <div id="form-view">
      <div class="badge">🐼🔑</div>
      <h1>Новый пароль</h1>
      <p>Придумай новый пароль для входа в PandaSolve.</p>
      <p class="sub">New password — choose a new password for your PandaSolve account.</p>

      <label for="pw">Новый пароль / New password</label>
      <input id="pw" type="password" autocomplete="new-password" minlength="6">
      <label for="pw2">Повтори пароль / Repeat password</label>
      <input id="pw2" type="password" autocomplete="new-password" minlength="6">

      <button id="go">Сохранить / Save</button>
      <div class="err" id="err"></div>
    </div>

    <div id="done-view" class="hidden">
      <div class="badge">🐼✅</div>
      <h1>Пароль сохранён!</h1>
      <p>Вернись в приложение PandaSolve и войди с новым паролем.</p>
      <p class="sub">Password updated — open the PandaSolve app and sign in with your new password.</p>
    </div>

    <div id="dead-view" class="hidden">
      <div class="badge">🐼⏳</div>
      <h1>Ссылка не действует</h1>
      <p>Ссылка для сброса пароля устарела или уже использована.
         Запроси новую в приложении.</p>
      <p class="sub">This reset link is expired or already used — request a new one from the app.</p>
    </div>

  </div>
<script>
  var SUPABASE_URL = __SUPABASE_URL__;
  var ANON_KEY = __ANON_KEY__;

  // Supabase redirects here with #access_token=...&type=recovery. Read it, then
  // strip the fragment so the token isn't left sitting in the URL bar or history.
  var token = new URLSearchParams(location.hash.replace(/^#/, "")).get("access_token");
  history.replaceState(null, "", location.pathname);

  var show = function (id) {
    ["form-view", "done-view", "dead-view"].forEach(function (v) {
      document.getElementById(v).classList.toggle("hidden", v !== id);
    });
  };

  if (!token) show("dead-view");

  document.getElementById("go").addEventListener("click", function () {
    var pw = document.getElementById("pw").value;
    var pw2 = document.getElementById("pw2").value;
    var err = document.getElementById("err");
    var btn = document.getElementById("go");

    if (pw.length < 6) {
      err.textContent = "Минимум 6 символов / at least 6 characters";
      return;
    }
    if (pw !== pw2) {
      err.textContent = "Пароли не совпадают / passwords don't match";
      return;
    }

    err.textContent = "";
    btn.disabled = true;
    fetch(SUPABASE_URL + "/auth/v1/user", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "apikey": ANON_KEY,
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({ password: pw })
    }).then(function (res) {
      if (res.ok) { show("done-view"); return; }
      return res.json().catch(function () { return {}; }).then(function (body) {
        btn.disabled = false;
        // 401/403 means the recovery token is spent or expired — that is a dead
        // link, not a bad password, so send the user back to the app for a new one.
        if (res.status === 401 || res.status === 403) { show("dead-view"); return; }
        err.textContent = body.msg || body.error_description || ("Ошибка / error " + res.status);
      });
    }).catch(function () {
      btn.disabled = false;
      err.textContent = "Нет соединения / no connection";
    });
  });
</script>
</body>
</html>"""


def reset_password_html(supabase_url: str, anon_key: str) -> str:
    """Render the password-recovery page for a given Supabase project.

    `supabase_url` / `anon_key` are JSON-encoded rather than pasted in, so a
    stray quote in the environment can't break out of the JS string literal and
    leave a page that throws on load.
    """
    return _RESET_PASSWORD_TEMPLATE.replace(
        "__SUPABASE_URL__", json.dumps(supabase_url)
    ).replace("__ANON_KEY__", json.dumps(anon_key))
