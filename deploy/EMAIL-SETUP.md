# Email & Password-Reset Setup — end to end

How the password-reset emails work, **where every credential goes**, which
backend files read them, and how the frontend triggers the flow. Follow this and
password reset works for real (a real code lands in a real inbox).

---

## 0. The reset paths (A, B, D send email)

| # | Who resets whom | Trigger (frontend) | Endpoint(s) | Email? |
|---|---|---|---|---|
| **A** | A **tenant user** resets **their own** password | `tenant/login.html` → **"Forgot password?"** | `POST /api/v1/auth/forgot-password` + `/reset-password` | ✅ 6-digit OTP |
| **B** | A platform admin triggers recovery for a **tenant owner** | `platform/tenant-detail.html` → **Account Recovery** | `POST /api/platform/tenants/{id}/account-recovery` | ✅ 6-digit OTP |
| **C** | A platform admin **directly sets** any password | `platform/tenant-detail.html` → user row → **Set password**; `platform/platform_users.html` → **Set Password** | `POST /api/platform/tenants/{id}/users/{uid}/reset-password` · `POST /api/platform/admins/{id}/reset-password` | ❌ no email — admin types it and hands it over |
| **D** | A **platform admin** resets **their own** password | `platform/login.html` → **"Forgot Password?"** | `POST /api/platform/auth/forgot-password` + `/reset-password` | ✅ 6-digit OTP |

Path **C** needs **no SMTP** and always works. Paths **A**, **B** and **D** need working
SMTP credentials — that is what the rest of this doc is about. There is also a plain
**change-password** (must know the current one) for a signed-in user
(`POST /api/v1/auth/change-password`) or admin (`POST /api/platform/auth/change-password`).

---

## 1. Where the credentials go

There are **two** places, checked in this order for **every** email the app sends
(reset codes, recovery, the test button):

1. **`platform_settings` DB rows** — Platform dashboard → **Settings → Email (SMTP)**
2. **`apps/backend_fastfood/.env`** — the fallback, per field, whenever the DB value is blank

### `.env` — the baseline (always fill this in)

Copy `.env.example` → `.env`:

```dotenv
# ── SMTP / Email ─────────────────────────────────────────────
SMTP_HOST=smtp-relay.brevo.com          # your provider's SMTP host
SMTP_PORT=587                           # 587 = STARTTLS (what the code uses)
SMTP_USERNAME=xxxxxxxx@smtp-brevo.com   # provider SMTP *Login* (the "Login" on Brevo's SMTP page)
SMTP_PASSWORD=xsmtpsib-................  # provider **SMTP key** (NOT an API key, NOT your dashboard password)
SMTP_FROM_EMAIL=noreply@yourdomain.com  # the "From" address — must be a VERIFIED sender
SMTP_FROM_NAME=Your Company             # display name in the "From" header
```
One line per key, **no quotes, no spaces around `=`**, and never define a key twice.
Restart the backend after editing (`python run.py` locally, `sudo systemctl restart
multi-saas` in prod). `.env` is git-ignored — never commit it.

> Key names are case-sensitive and must match `core/config.py` exactly
> (`ENVIRONMENT` not `APP_ENV`, `CORS_ORIGINS` not `BACKEND_CORS_ORIGINS`). `.env.example` is correct.

### Platform → Settings → Email — the runtime override (use after deploy)

`platform/settings.html` → **Email (SMTP)** writes the same six values into the
`platform_settings` table. **Any value you set there wins over `.env`, immediately,
with no restart** (each email reads it fresh). A field left blank on that page
falls back to `.env`. This is how you **rotate the SMTP key after deployment** —
see §8.

Recommended: put working values in `.env` at deploy time; use the Settings page
only when you need to change them later.

---

## 2. What reads each key — the backend wiring

```
apps/backend_fastfood/
├── .env                          ← baseline SMTP values → core/config.py `settings.*`
│
├── core/email.py                 ← builds + sends the MIME message (aiosmtplib, STARTTLS)
│     resolve_smtp(smtp_cfg)             = merge: DB row value  OR  settings.<ENV>  per field
│     send_password_reset_otp(to, otp, smtp_cfg)     → paths A & D  (logs+swallows errors)
│     send_platform_recovery_email(..., smtp_cfg)    → path B       (logs+swallows errors)
│     send_test_email(to, smtp_cfg)                  → the test button (RAISES the real error)
│     ↑ every one takes the same optional `smtp_cfg` dict, resolved the same way
│
├── services/platform_setting_service.py  ← the DB override
│     get_all()  → { key: value }   (reads the platform_settings rows)
│     update()   → upsert of the six smtp_* keys (created on first Save; DB value wins over .env)
│
├── services/auth_service.py           → path A  forgot_password()
│     smtp_cfg = PlatformSettingService(db).get_all(); send_password_reset_otp(email, otp, smtp_cfg)
├── services/platform_auth_service.py  → path D  forgot_password()  (same, for platform admins)
├── api/platform/tenants.py            → path B  account_recovery()  (same, for tenant owners)
└── api/platform/settings.py           → POST /settings/test-email   (same; surfaces the error)
```

**Data stored (never the raw code):** `users.password_reset_token` holds the
**SHA-256 hash** of the OTP; `users.password_reset_expires_at` the expiry. The raw
6-digit code exists only in the email. Reusing or expiring a code fails the reset.

---

## 3. The frontend → backend flow

### Path A — tenant self-service (`tenant/login.html`)

```
[Forgot password?]  ─────────────────────────────────────────────────────────────
  Step 1  tenant_code + email
      └─ fetch POST /api/v1/auth/forgot-password  {tenant_code, email}
            → AuthService.forgot_password() → core/email.send_password_reset_otp()
            → 6-digit code emailed;  response is ALWAYS 200 "if the account exists…"
  Step 2  6-digit code + new password
      └─ fetch POST /api/v1/auth/reset-password  {tenant_code, token, new_password}
            → AuthService.reset_password()  → 200 "Password reset successfully."
            → user signs in with the new password
```

Requirements for path A to work:
- the tenant **user must have an email** on their account (`users.email`) — set it
  in the tenant dashboard → Users, or the platform tenant-detail Users tab;
- `.env` SMTP keys filled in and the backend restarted.

### Path B — platform-initiated (`platform/tenant-detail.html`)

```
[Account Recovery]  ────────────────────────────────────────────────────────────
  └─ fetch POST /api/platform/tenants/{id}/account-recovery
        → reads platform_settings (smtp_*), falls back to .env per field
        → OTP emailed to the tenant OWNER's address (30-min expiry)
  The owner then completes it from tenant/login.html → "Forgot password?" → Step 2
  (same /api/v1/auth/reset-password endpoint).
```

### Path C — direct set (no email)

`platform/tenant-detail.html` user row → **Set password**, or
`platform/platform_users.html` → **Set Password**:
```
  └─ POST /api/platform/tenants/{id}/users/{uid}/reset-password   (tenant user)
     POST /api/platform/admins/{id}/reset-password                (platform admin, super only)
        → password_hash overwritten immediately; hand the temp password over out-of-band.
```

### Path D — platform admin self-service (`platform/login.html`)

```
[Forgot Password?]  ───────────────────────────────────────────────────────────
  Step 1  email
      └─ fetch POST /api/platform/auth/forgot-password  {email}
            → PlatformAuthService.forgot_password() → core/email.send_password_reset_otp()
            → 6-digit code emailed; response ALWAYS 200 "if that account exists…"
              (stores SHA-256(otp) + 15-min expiry on platform_admins; single-use)
  Step 2  6-digit code + new password (min 8)
      └─ fetch POST /api/platform/auth/reset-password  {token, new_password}
            → verifies hash + expiry, sets the new password, clears the token
```
Uses the **same `.env` SMTP** config as Path A (no DB override). Requires the
`platform_admins.password_reset_token` columns (migration `ecea27ac0d3f`).

> The web pages call the API with **relative** URLs (`/api/v1/...`,
> `/api/platform/...`), so nothing in the frontend changes between local and
> production — same origin behind nginx. See `deploy/DEPLOYMENT-RUNBOOK.md`.

---

## 4. Getting real SMTP credentials

You need an SMTP relay that lets you send from a verified address. Any of these:

### Brevo (Sendinblue) — the project default
1. Create a free account at brevo.com (300 emails/day free).
2. **Senders & IP → Senders**: add and verify `noreply@yourdomain.com` (or use a
   Brevo subdomain sender they give you).
3. **SMTP & API → SMTP**: copy the **SMTP server** (`smtp-relay.brevo.com`),
   **port** (`587`), **Login** (`xxxxxxxx@smtp-brevo.com`) and generate an
   **SMTP key** (this is `SMTP_PASSWORD`, not your Brevo account password).
4. Fill `.env`:
   ```dotenv
   SMTP_HOST=smtp-relay.brevo.com
   SMTP_PORT=587
   SMTP_USERNAME=xxxxxxxx@smtp-brevo.com
   SMTP_PASSWORD=<the SMTP key>
   SMTP_FROM_EMAIL=noreply@yourdomain.com   # must be a verified sender
   SMTP_FROM_NAME=Your Company
   ```

### Gmail / Google Workspace
1. The account needs **2-Step Verification ON**.
2. Google Account → Security → **App passwords** → generate one for "Mail".
3. `.env`:
   ```dotenv
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=youraddress@gmail.com
   SMTP_PASSWORD=<16-char app password, no spaces>
   SMTP_FROM_EMAIL=youraddress@gmail.com
   SMTP_FROM_NAME=Your Company
   ```
   Personal Gmail is rate-limited (~500/day) — fine for low volume, not for scale.

### Anything else (Mailgun, SES, Postmark, Zoho…)
Use their **SMTP** credentials (host / 587 / username / password) and a verified
`SMTP_FROM_EMAIL`. The code only speaks STARTTLS on the configured port — port
`465` (implicit TLS) is **not** used, so pick the provider's STARTTLS/submission
port (usually 587).

---

## 5. Testing

> **The email contains a 6-digit CODE, not a clickable link.** You type that code
> into the "Forgot password?" panel on the login page. There is no reset URL by design.

### Fastest check — the "Send test email" button
Platform dashboard → **Settings → Email (SMTP)** → **Send test email** (`POST /api/platform/settings/test-email`, super-admin).
It sends a real message to your admin address and shows the **exact SMTP error** on
failure (e.g. `SMTP send failed: (535, '5.7.8 Authentication failed')`). Green toast = the
reset emails will send too.

### From the terminal (bypasses the app)
```
apps\backend_fastfood> .venv\Scripts\python.exe -c "import smtplib,ssl; from core.config import settings; s=smtplib.SMTP(settings.SMTP_HOST,settings.SMTP_PORT); s.starttls(context=ssl.create_default_context()); s.login(settings.SMTP_USERNAME,settings.SMTP_PASSWORD); print('LOGIN OK'); s.quit()"
```
`LOGIN OK` → creds are valid. `535` → the login/key pair is rejected by the provider
(regenerate the SMTP key, copy the exact Login string, verify the sender).

### Full flow (local)
1. Put real SMTP creds in `apps/backend_fastfood/.env` (see §7 below), restart `python run.py`.
2. Give a tenant user an email address (tenant dashboard → Users).
3. `tenant/login.html` → **Forgot password?** → enter tenant code + that email →
   **Send reset code**. Check the inbox (and spam).
4. Enter the 6-digit **code** + a new password → **Set new password** → sign in.

No SMTP configured (or wrong)? `forgot-password` still returns **200** (by design — it
never reveals whether an account exists). The send failure is **logged**, not shown:
```
python run.py           # watch the console
# → ERROR core.email  Failed to send password reset email to <addr>: (535, '5.7.8 Authentication failed')
```

### Production
```bash
sudo systemctl restart multi-saas
journalctl -u multi-saas -f          # watch while you trigger a reset
```
Look for `Password reset OTP sent to …` (success) or `Failed to send …` (check
host/port/credentials/verified-sender).

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| "No reset **link**" in the email | There is no link — the email carries a **6-digit code**. Enter it in the login page's "Forgot password?" panel. |
| Request returns 200 but no email arrives | SMTP is not configured or the creds are rejected. Use **Settings → Send test email** — it shows the exact error. |
| `535 5.7.8 Authentication failed` (test email or app log) | The `SMTP_USERNAME` + `SMTP_PASSWORD` pair is rejected by the provider. **Brevo:** SMTP & API → SMTP tab → copy the **Login** exactly + **Generate a new SMTP key** (an `xsmtpsib-…` key, not an `xkeysib-…` API key). **Gmail:** use a 16-char **App password** with 2FA on. Also make sure the account is fully activated. Put it as **one** `SMTP_PASSWORD=` line — no quotes, no spaces around `=`, and not defined twice. |
| `SMTPAuthenticationError` in the log | Same as 535 above. |
| `SMTP_FROM_EMAIL` rejected / mail bounces | The From address isn't a **verified sender** with your provider. Verify it (or use the provider-supplied sender). |
| Connection times out | Wrong `SMTP_HOST`/`SMTP_PORT`, or the VPS firewall blocks outbound 587. `sudo ufw allow out 587/tcp` if egress filtering is on; some hosts block SMTP ports by default — ask support or use an API-based relay. |
| Email lands in spam | Add SPF + DKIM DNS records for your domain at the provider; use a real domain in `SMTP_FROM_EMAIL`, not a free-mail address. |
| "Invalid or expired reset token" | OTP is single-use and expires (15 min path A, 30 min path B). Request a new one. Also confirm the tenant user actually has an email set — the OTP is stored against that user. |
| Saved new SMTP in Settings but email still uses the old sender | The override is **per field** — a field left blank falls back to `.env`. Fill the ones you want to change; use **Send test email** to confirm. No restart needed. |
| Want to go back to the `.env` SMTP values | Clear the DB rows: `DELETE FROM platform_settings WHERE key LIKE 'smtp_%';` (the UI can't clear the write-only password field). |
| Changed `.env` but nothing changed | The backend reads `.env` at startup only — restart it. |

---

## 7. Checklist to make it work for real

- [ ] Real SMTP account created; sender address **verified** with the provider.
- [ ] `apps/backend_fastfood/.env` has `SMTP_HOST`, `SMTP_PORT=587`,
      `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`.
- [ ] Backend restarted after editing `.env`.
- [ ] Tenant users who need self-service reset have an **email** on their account.
- [ ] Outbound port 587 open from the server.
- [ ] Test path A end-to-end (code arrives, reset succeeds, login works).
- [ ] (Prod) SPF + DKIM DNS records added so mail isn't spam-filtered.
- [ ] `.env` is `chmod 600`, owned by `www-data`, and **not** in git.

---

## 8. Rotating the SMTP key after deployment (Brevo keys expire every 90 days)

**You never touch the server or `.env` again.** Do it from the dashboard:

1. Brevo → **SMTP & API → SMTP** → **Generate a new SMTP key**, copy it
   (`xsmtpsib-…`; the `Login` almost never changes).
2. Platform dashboard → **Settings → Email (SMTP)** → paste the new key into
   **SMTP Password** (leave the other fields as-is) → **Save Email Settings**.
3. Same page → **Send test email** → wait for the green toast.

That's it. The new key is stored in `platform_settings` and every email
(reset codes, recovery, test) picks it up **on the next send** — no restart, no
redeploy. `.env` stays as the fallback for a fresh install or if the DB row is
cleared.

Notes:
- The **SMTP Password** field is write-only in the UI (never shown). Typing a new
  value replaces it; leaving it blank on Save keeps the current one. To go back to
  the `.env` value, an owner can clear the row directly:
  `DELETE FROM platform_settings WHERE key='smtp_password';`
- The value is stored in the DB the same way it lives in `.env` — as plaintext
  the app can read. Protect DB backups accordingly.
- A `viewer`/`manager` platform admin can't save Settings (super-admin only), but
  can still see the **Send test email** result.
