# DEPLOY RUNBOOK — Posting Autopilot on a $6–12/mo VPS

This app is a 6-service Docker stack (web + worker + scheduler + bot + postgres + redis)
and **cannot run on Vercel/Netlify**. A small VPS is the right home. ~30–60 min end to end.

## 0. What you need first
- A VPS: Hetzner CX22 (~€4.5/mo) or DigitalOcean/Vultr ($6–12/mo), Ubuntu 22.04+.
- A domain (or subdomain) you control, e.g. `app.postingautopilot.com`.
- A dedicated Telegram bot token from @BotFather.
- An OpenAI API key.
- (For payments) a Stripe account — see `STRIPE_RUNBOOK.md`.

## 1. Point the domain at the server
Create a DNS **A record**: `app.postingautopilot.com → <server IP>`. Wait for it to resolve
(`dig +short app.postingautopilot.com`). Caddy needs this to issue the HTTPS cert.

## 2. Install Docker on the VPS
```bash
ssh root@<server-ip>
curl -fsSL https://get.docker.com | sh
```

## 3. Get the code + secrets
```bash
git clone https://github.com/chernushoov/posting-autopilot.git
cd posting-autopilot
cp .env.production.example .env
nano .env            # fill EVERY value (DOMAIN, POSTGRES_PASSWORD + matching DATABASE_URL,
                     # FLASK_SECRET_KEY=$(openssl rand -hex 32), ADMIN_PASSWORD, bot token,
                     # AI_API_KEY, and the Stripe block when ready)
touch .env.runtime   # optional secrets overlay; can stay empty
```

## 4. Launch (production overlay)
```bash
./deploy.sh
# == docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec web python -m scripts.seed   # first run only: init DB
```

## 5. Verify
```bash
curl -s https://$DOMAIN/health        # expect ok
docker compose ps                      # all services Up; caddy has 80/443
```
Open `https://<domain>/login` → log in with ADMIN_LOGIN / ADMIN_PASSWORD.

## 6. Updating later
```bash
git pull && ./deploy.sh               # rebuild + restart changed services
```

## Notes / gotchas
- HTTPS is automatic via Caddy + Let's Encrypt once DNS resolves. First request may take ~10s.
- `FORCE_HTTPS=1` must be set (it is in the template) so session cookies are Secure behind the proxy.
- Postgres is **not** exposed publicly in prod (overlay drops the port). Back up `ra_pg` volume.
- The DM bot has `restart: unless-stopped` — it self-heals; check `docker compose logs bot` if screening stops.
- Do NOT enable the Facebook browser auto-poster (it risks the account). Manual FB path is safe.
- Real public posting to live Telegram groups starts only when YOU connect a Telegram account and run a campaign — nothing posts on its own.
