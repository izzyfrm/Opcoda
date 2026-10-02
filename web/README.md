# opcoda.cc — website + accounts

The Cloudflare Worker `opcoda` serves the site and the account API. Code generation runs on your PC. By default, `start-coda.ps1` uses a local Ollama coding model; the from-scratch Coda checkpoints remain available with `-Backend coda`.

```
browser ──► opcoda.cc (Worker "opcoda")
              ├─ public/            static site (HTML/CSS/JS, no build step)
              ├─ /api/*             src/index.ts: accounts, sessions, chats, avatars
              ├─ D1 "opcoda-db"     users, sessions, conversations, messages, avatars, usage
              └─ env.CODA_MODEL ──► Workers VPC service "coda-model"
                                    ──► Cloudflare Tunnel "opcoda-model" (private, no public hostname)
                                    ──► server.py on your PC at 127.0.0.1:8000
                                        └─► Ollama at 127.0.0.1:11434 (default)
                                        Authorization: Bearer MODEL_TOKEN
```

When your PC or `server.py` is off, the site still works (sign in, history, settings). Chat shows **Offline**,
and failed messages don't use up the daily limit.

## Security model

- **Passwords**: PBKDF2-SHA256 with 100k iterations (the Workers maximum) and a per-user random salt,
  compared in constant time. Unknown usernames take the same time as wrong passwords.
- **Sessions**: a random 256-bit token in an `HttpOnly; Secure; SameSite=Lax` `__Host-` cookie. Only its
  SHA-256 is stored. Sessions slide over 30 days. Changing your password signs out other devices.
- **CSRF**: SameSite cookies, plus every non-GET API call must carry a same-origin `Origin` header.
- **Rate limits** (D1 fixed windows): 10 accounts per hour per IP; 20 logins per 15 minutes per IP and 8 per
  username; 10 messages per minute; a daily message limit (`DAILY_MESSAGE_LIMIT`).
- **Sign-ups** are open by default. Set the `INVITE_CODE` secret to make them invite-only.
- **Avatars**: resized to 256×256 in the browser. The server checks the file signature (PNG/JPEG/WebP) and a
  300 KB limit. Avatars are only served to their owner.
- **Headers**: a strict CSP (no inline scripts or styles), frame denial, nosniff, and HSTS (`public/_headers`).
- **Model link**: the model API has no public URL. Only the Worker can reach it, through Workers VPC.
  `server.py` also refuses `/api/generate` without the shared token.
- **CPU limits**: on the Workers Free plan, CPU time is capped at 10 ms per request. Sign-in and sign-up
  use more than that for password hashing. Cloudflare tolerates occasional overruns, but if sign-ins start
  failing with "exceeded CPU", that's the cause. The Workers Paid plan removes the limit.

## Local development

```powershell
cd web
npm install
copy .dev.vars.example .dev.vars      # then set MODEL_TOKEN to any random string
npm run db:migrate:local
npx wrangler dev                      # http://127.0.0.1:8787
```

In a second terminal at the repo root, run the model with the same token:

```powershell
$env:CODA_MODEL_TOKEN = "<same value as MODEL_TOKEN in web/.dev.vars>"
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Checks:

```powershell
npm run check                          # TypeScript
node test/api-smoke.mjs                # 33 API checks against the running wrangler dev
```

## Deploy

**Already done on 2026-10-02.** Day to day you only need two things:

```powershell
.\start-coda.ps1                     # from the repo root: local coding model + private tunnel
cd web; npx wrangler deploy          # after changing the website or Worker
```

What was set up, for reference or a rebuild:

| Resource | Name / ID |
|---|---|
| Worker | `opcoda`, custom domain `opcoda.cc` (workers.dev disabled) |
| D1 | `opcoda-db` (`f0d4ddcd-d744-439e-8f70-2276dd4aa9b5`), migrations in `migrations/` |
| Tunnel | `opcoda-model` (`fafd726f-2a72-4d2f-8718-2a3bb2dda275`), config `tunnel/opcoda-model.yml` |
| VPC service | `coda-model` (`01a0fa7a-719c-7010-a2b7-d80b9c105df1`) → `127.0.0.1:8000` through the tunnel |
| Secret | `MODEL_TOKEN` = contents of `.coda-model-token` (repo root, gitignored) |

Rebuild from scratch (run from `web/`):

```powershell
npx wrangler d1 create opcoda-db                          # put database_id in wrangler.jsonc
npm run db:migrate:remote
cloudflared tunnel create opcoda-model                    # copy tunnel/opcoda-model.example.yml -> .yml, fill in the ID
npx wrangler vpc service create coda-model --type http --tunnel-id <TUNNEL_ID> --ipv4 127.0.0.1 --http-port 8000
                                                          # put service_id in wrangler.jsonc
node -e "console.log(require('crypto').randomBytes(32).toString('base64url'))" > ..\.coda-model-token
Get-Content ..\.coda-model-token | npx wrangler secret put MODEL_TOKEN
npx wrangler deploy
```

Don't use `cloudflared tunnel route dns` for this tunnel. The model is deliberately private, and the
`cert.pem` in `~/.cloudflared` belongs to the `izzyy.me` zone.

## Settings you can change

| Where | What |
|---|---|
| `wrangler.jsonc` → `vars.DAILY_MESSAGE_LIMIT` | messages per user per UTC day |
| `.dev.vars` → `MODEL_URL` | local dev only: reach `server.py` directly instead of through Workers VPC |
| `npx wrangler secret put INVITE_CODE` | require an invite code to sign up (`wrangler secret delete INVITE_CODE` to reopen) |
| `CODA_CHECKPOINT` env / `start-coda.ps1 -Checkpoint` | which checkpoint `server.py` serves |
| `start-coda.ps1 -Backend coda` | serve the original from-scratch checkpoint instead of Ollama |
| `start-coda.ps1 -OllamaModel` | local Ollama model name (default `llama3.2:3b`) |
