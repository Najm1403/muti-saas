# core/email.py
#
# Async email dispatch via SMTP (Brevo by default).
#
# SMTP config resolution — every sender uses the SAME order:
#   1. the `platform_settings` rows passed in as `smtp_cfg`  (Platform → Settings → Email)
#   2. the `.env` values from core/config.py                 (fallback / first-run)
# So the SaaS owner can rotate the SMTP key from the dashboard after deploy,
# without editing .env or restarting — just paste the new key and Save.

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from core.config import settings

logger = logging.getLogger(__name__)


def resolve_smtp(smtp_cfg: dict[str, str | None] | None = None) -> dict:
    """Merge the DB override (`smtp_cfg`) over the `.env` defaults.

    A blank / missing DB value falls back to `.env` per-field.
    """
    cfg = smtp_cfg or {}

    def pick(db_key: str, env_val):
        v = cfg.get(db_key)
        return v if (v is not None and str(v).strip() != "") else env_val

    port_raw = pick("smtp_port", settings.SMTP_PORT)
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 587

    return {
        "host":       pick("smtp_host", settings.SMTP_HOST),
        "port":       port,
        "username":   pick("smtp_username", settings.SMTP_USERNAME),
        "password":   pick("smtp_password", settings.SMTP_PASSWORD),
        "from_email": pick("smtp_from_email", settings.SMTP_FROM_EMAIL),
        "from_name":  pick("smtp_from_name", settings.SMTP_FROM_NAME),
        "app_name":   pick("platform_name", settings.APP_NAME),
    }


async def _send(message: MIMEMultipart, s: dict) -> None:
    """Low-level send. Raises on failure — callers decide whether to swallow."""
    await aiosmtplib.send(
        message,
        hostname=s["host"],
        port=s["port"],
        username=s["username"] or None,
        password=s["password"] or None,
        start_tls=True,
    )


def _build(subject: str, to_email: str, s: dict, plain: str, html: str | None = None) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f'{s["from_name"]} <{s["from_email"]}>'
    msg["To"] = to_email
    msg.attach(MIMEText(plain, "plain"))
    if html:
        msg.attach(MIMEText(html, "html"))
    return msg


# ─────────────────────────────────────────────────────────────
# Public senders
# ─────────────────────────────────────────────────────────────

async def send_password_reset_otp(
    to_email: str, otp: str, smtp_cfg: dict[str, str | None] | None = None
) -> None:
    """6-digit password-reset OTP (tenant self-service + platform self-service).

    Any SMTP error is logged but NOT re-raised — the caller always returns a
    generic success so it never leaks whether the address exists.
    """
    s = resolve_smtp(smtp_cfg)
    app_name = s["app_name"]
    mins = settings.PASSWORD_RESET_EXPIRE_MINUTES

    plain = (
        f"Your password reset code is: {otp}\n\n"
        f"It expires in {mins} minutes.\n"
        f"Enter it on the sign-in page. If you did not request this, ignore this email."
    )
    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:520px;margin:40px auto">
      <h2 style="color:#e63946;">{app_name}</h2>
      <p>Your password reset code is:</p>
      <div style="font-size:32px;font-weight:bold;letter-spacing:10px;color:#e63946;
                  background:#fef2f2;border-radius:8px;padding:16px 24px;display:inline-block;margin:8px 0">{otp}</div>
      <p>This code expires in <strong>{mins} minutes</strong>. Enter it on the sign-in page.</p>
      <p style="color:#888;font-size:12px;">If you did not request a password reset, ignore this email.</p>
    </body></html>
    """
    msg = _build(f"[{app_name}] Password reset code", to_email, s, plain, html)
    try:
        await _send(msg, s)
        logger.info("Password reset OTP sent to %s", to_email)
    except (aiosmtplib.SMTPException, OSError) as exc:
        logger.error("Failed to send password reset email to %s: %s", to_email, exc)


async def send_platform_recovery_email(
    to_email: str,
    to_name: str,
    tenant_code: str,
    otp: str,
    smtp_cfg: dict[str, str | None] | None = None,
) -> None:
    """Account-recovery OTP for a tenant owner, triggered by a platform admin.

    Errors are logged and swallowed — never raised to the caller.
    """
    s = resolve_smtp(smtp_cfg)
    app_name = s["app_name"]
    if not s["host"] or not s["from_email"]:
        logger.warning("SMTP not configured — recovery email not sent to %s", to_email)
        return

    plain = (
        f"Hello {to_name},\n\n"
        f"A platform administrator has initiated an account recovery for your account.\n\n"
        f"Your one-time password (OTP) is: {otp}\n\n"
        f"This code expires in 30 minutes.\n"
        f"Enter it in the '{tenant_code}' tenant panel to reset your password.\n\n"
        f"If you did not expect this, contact your platform administrator."
    )
    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:520px;margin:40px auto">
      <h2 style="color:#2563eb">{app_name}</h2>
      <p>Hello <strong>{to_name}</strong>,</p>
      <p>A platform administrator has initiated an <strong>account recovery</strong> for your tenant
         <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px">{tenant_code}</code>.</p>
      <p>Your one-time password is:</p>
      <div style="font-size:32px;font-weight:bold;letter-spacing:10px;color:#2563eb;
                  background:#eff6ff;border-radius:8px;padding:16px 24px;display:inline-block;margin:8px 0">{otp}</div>
      <p>This code expires in <strong>30 minutes</strong>.<br>
         Enter it in the <strong>{tenant_code}</strong> panel to reset your password.</p>
      <p style="color:#888;font-size:12px">If you did not expect this, contact your platform administrator.</p>
    </body></html>
    """
    msg = _build(f"[{app_name}] Account Recovery — Tenant {tenant_code}", to_email, s, plain, html)
    try:
        await _send(msg, s)
        logger.info("Account recovery OTP sent to %s (tenant: %s)", to_email, tenant_code)
    except (aiosmtplib.SMTPException, OSError) as exc:
        logger.error("Failed to send recovery email to %s: %s", to_email, exc)


async def send_test_email(
    to_email: str, smtp_cfg: dict[str, str | None] | None = None
) -> None:
    """Diagnostic email. Unlike the OTP senders this RAISES on failure so the
    'Send test email' button can show the real SMTP error."""
    s = resolve_smtp(smtp_cfg)
    missing = [k for k in ("host", "username", "password", "from_email") if not s[k]]
    if missing:
        raise ValueError(
            "SMTP is not configured. Fill it in Platform → Settings → Email, "
            f"or in .env. Missing: {', '.join(missing)}"
        )
    msg = _build(
        f"[{s['app_name']}] SMTP test — it works", to_email, s,
        "This is a test email from your platform dashboard.\n"
        "If you received it, password-reset code emails will send too.",
    )
    await _send(msg, s)   # SMTPException / OSError propagate to the route
    logger.info("SMTP test email sent to %s", to_email)
