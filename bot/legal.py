"""Static legal pages (served at /privacy, /terms). Plain self-contained HTML so
they render without any assets and can be linked from the app + Play Console.

NOTE: review with counsel before launch and set a real CONTACT_EMAIL.
"""

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
