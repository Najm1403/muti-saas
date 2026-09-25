# STORIXX web client

The web client is a static site. Deploy the contents of this directory behind HTTPS at:

`https://shop.apkaysoftware.com`

The pages use same-origin `/api/...` requests by default. When the API is hosted separately, define `window.API_BASE_URL` before the page scripts, for example:

```html
<script>window.API_BASE_URL = 'https://api.example.com';</script>
```

For the supported same-domain deployment, proxy `/api/` from the web server to the
FastAPI service. Follow the canonical
[production deployment runbook](../../deploy/DEPLOYMENT-RUNBOOK.md).

## CSS

Tailwind is compiled into `shared/tailwind.css` and served locally; browser pages
must not load the Tailwind CDN. The compiled file is committed so production
deployments do not require Node.js or a CSS build step.

After adding or changing utility classes, rebuild from PowerShell with the
Tailwind CLI (version 3.4.17):

```powershell
powershell -ExecutionPolicy Bypass -File ./build-css.ps1 `
  -TailwindExecutable C:\path\to\tailwindcss.exe
```

Run `python tests/local_css_smoke.py` before deployment to detect a missing or
stale bundle and any reintroduced CDN reference.

After deployment, verify:

- `/platform/login.html` loads over HTTPS.
- Platform templates can be created and edited; assignment is performed from **Platform → Tenants → open tenant → Modules**.
- Applying or switching a template displays a confirmation dialog.
- The selected tenant changes while another tenant remains unchanged.
