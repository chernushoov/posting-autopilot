# android-agent — подключение телефона (≈25 мин, один раз)

Роль: мобильный прокси для FB (закрывает O3), внешний watchdog прода, хост Claude-агента. Детали — `../DEVICES.md`.

## 0. Железо
- Отдельная SIM с данными ≥20 ГБ/мес. Wi-Fi **выключен** (FB должен видеть мобильный IP оператора).
- Телефон постоянно на зарядке. Включить ограничение заряда 80–85% (Samsung: «Защита батареи»).
- Не использовать как личный телефон.

## 1. Приложения
- **Tailscale** (Play Store) → войти в тот же аккаунт, что iMac/MacBook.
  Android: Настройки → Сеть → VPN → Tailscale → «Постоянная VPN» = ВКЛ.
  Админка Tailscale: переименовать устройство в `android-agent`, тег `tag:agent`, Disable key expiry. ACL — из `../DEVICES.md`.
- **Termux**, **Termux:API**, **Termux:Boot** — только из **F-Droid**, все три оттуда же.
- Открыть Termux:Boot один раз.
- Настройки → Приложения → Termux / Termux:API / Termux:Boot / Tailscale → Батарея → **Без ограничений**.

## 2. Termux
```
pkg install -y git gh
gh auth login
gh repo clone chernushoov/posting-autopilot -- --depth 1 -b ccr-6619f392-28owwd
bash ~/posting-autopilot/ops/fleet/android/bootstrap.sh
```
В конце скрипт печатает `FB_PROXY_*` — сохранить.

## 3. Алерты в Telegram
1. @BotFather → `/newbot` → токен. Написать боту `/start`.
2. `curl -s https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id`.
3. `nano ~/fleet/agent.env` → `TG_BOT_TOKEN`, `TG_CHAT_ID`.
4. Проверка: `echo report-now > ~/fleet/state/cmd` → отчёт придёт ≤5 мин.

## 4. Claude-агент
```
proot-distro login ubuntu --termux-home
cd ~/agent && claude        # войти, доверить папку, /exit
exit
~/fleet/start_bridge.sh --enable
```
Телефон появится в Claude app как новая среда (bridge).

## 5. Сообщить мне
Написать: «телефон в сети» + Tailscale IP телефона (`100.x.y.z`, видно в приложении Tailscale).
Дальше делаю я: ежедневный триаж-агент на телефоне + подключение прода к прокси (`../hetzner_join_tailnet.sh`, сначала dry-run).

## Проверка
| Что | Как |
|---|---|
| прокси | `curl -x http://fb:<PASS>@127.0.0.1:8888 https://ipinfo.io/json` → org = мобильный оператор |
| сервисы | `sv status fleet-proxy crond` → run |
| cron | `crontab -l` |
| агент | `tmux attach -t claude` (выход: Ctrl+B, D) |
| перезагрузка | после ребута всё стартует само (Termux:Boot) |
