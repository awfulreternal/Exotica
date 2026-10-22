# EXOTICA

Exotica is a Telegram userbot powered by the vendored Heroku runtime, itself derived from Hikka. This distribution combines Heroku's actively maintained Hikka-compatible loader, security policy, built-in modules, and Heroku-TL client with Exotica installation, private data management, diagnostics, and backup tooling.

## Install

Requires Python 3.11 or newer. Python 3.14 has been tested in a clean Codespaces-style environment.

```sh
git clone <YOUR-EXOTICA-REPOSITORY-URL> Exotica
cd Exotica
./scripts/install.sh
. .venv/bin/activate
exotica doctor
```

The installer creates `.venv` and installs the single default Telegram client stack (`herokutl`). It does not install Telethon or Hikka's incompatible legacy client stack.

## First run

Create your Telegram API credentials at [my.telegram.org](https://my.telegram.org). Then start the interactive setup:

```sh
exotica login
```

The setup asks for the API ID/hash if they are not already configured, then offers phone or QR authorization. Enter the login code and, if enabled, your two-step verification password. To request QR login directly:

```sh
exotica login --qr-login
```

Credentials may instead be provided as `EXOTICA_API_ID` and `EXOTICA_API_HASH`. They are passed to the runtime through environment variables and are not placed in process arguments. The runtime saves its configuration under `EXOTICA_HOME` with private file permissions.

Start the userbot with:

```sh
exotica run
```

In Telegram:

- `.exotica` opens the Exotica inline control room with status, host, ping, and module views. Its navigation follows Hikka's inline form pattern; premium custom emoji are used when the account supports them, with Unicode fallback otherwise.
- `.info` shows measured provider/CPU/RAM data, Exotica version, uptime, and Telegram RTT.
- `.ping` measures RTT with one lightweight Telegram state RPC; it avoids an extra placeholder edit. Network distance and Telegram server latency cannot be optimized away locally.
- `.help` lists the commands provided by the built-in modules.

The runtime includes the Hikka-derived module loader, inline forms/lists/galleries, persistent module configuration/database, owner and group security rules, API flood protection, logging, translations, and backup/settings modules. Visible built-in module names use Exotica branding; upstream namespaces and copyright notices remain intact for compatibility and provenance.

Exotica creates its own inline bot profile image locally and does not auto-join Heroku support chats. Existing `heroku-userbot` asset channels and the legacy `heroku.*` database namespace remain readable for migration compatibility.

Host details are detected from the actual machine and container limits. Set `EXOTICA_CLOUD_PROVIDER=Oracle Cloud` only when needed, `EXOTICA_HOST_CPU_CORES` or `EXOTICA_HOST_MEMORY_GB` to override resource detection, and `EXOTICA_CLOUD_TIER` to display an explicitly supplied tier label. A configured label is not independently verified by Exotica.

CPU counts respect process affinity and Linux cgroup quotas; RAM respects cgroup limits. The dashboard reports measured Telegram RTT using one `updates.GetStateRequest`. It can avoid extra local API calls, but cannot reduce network distance or Telegram server response time.

Oracle's [official Always Free compute documentation](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) currently describes A1 usage equivalent to 2 OCPU and 12 GB RAM continuously (1,500 OCPU-hours and 9,000 GB-hours monthly). A measured 24 GB instance is displayed as hardware/container capacity, not automatically as an Always Free entitlement; verify the tenancy's quotas and billing in OCI.

## Modules and security

The upstream loader supports Hikka/Heroku module APIs and remaps common Hikka imports. This is not a guarantee that every third-party or fork-specific module works unchanged. The installed runtime can download modules when explicitly requested through its loader commands. Downloaded Python modules have the same operating-system and Telegram-account permissions as Exotica; they are not sandboxed. Review source before installing modules and restrict who can invoke commands through the security settings.

Built-in code-evaluation and terminal features are powerful and must only be used by the account owner. Do not expose an account session, API credentials, or writable module directory to other users.

## Data, backup, and restore

By default, Exotica stores data in `~/.local/share/exotica`; set `EXOTICA_HOME` to choose another directory. The runtime keeps configuration, module database, downloaded modules, and its session files under this private root.

`exotica backup` creates a local archive. Session files, `.env`, and legacy `api_token.txt` are excluded; sensitive keys such as API hashes and bot tokens are removed from archived JSON configuration. `exotica restore <archive>` validates archive paths and rejects links and special files.

The upstream Telegram backup modules are separate features and may send database/module backups through Telegram. Review their behavior and destination before enabling or using them.

## CLI

- `exotica doctor` — Python, platform, data-directory permissions, runtime availability.
- `exotica paths` — active data root.
- `exotica modules` — list downloaded runtime module source files without executing them; active modules are managed by the upstream loader in `loaded_modules`.
- `exotica backup` / `exotica restore <archive>` — local managed-data backup and restore.
- `exotica compat` — report the included Hikka-derived APIs and known compatibility caveats.
- `exotica run [Heroku options]` — run the active userbot; upstream options such as `--qr-login`, `--proxy-host`, and `--proxy-port` are forwarded.
- `exotica login [Heroku options]` — interactive first-run login with the upstream web flow disabled.

The retired Telethon implementation is available only through `exotica legacy-login` and `exotica legacy-run`. Install its optional dependency with `python -m pip install -e '.[legacy]'` only if you explicitly need that old implementation.

## Termux and Docker

Run the Termux installer inside Termux as an ordinary user:

```sh
sh scripts/install-termux.sh
. .venv/bin/activate
exotica login
```

Docker uses a non-root account and persistent `/data` volume. For interactive setup use `docker compose run --rm exotica login`; then run `docker compose run --rm exotica run`. Do not publish the data volume.

## Upstream sources

- [Heroku Userbot](https://github.com/Heroku-userbot/Heroku), pinned in `vendor/heroku` at commit `4d8a764087bd27e146c7834b720f3cd717abd0ec`. It is the selected runtime and contains Hikka-derived loader/UI/modules plus Heroku security and settings changes.
- [Hikka Userbot](https://github.com/hikariatama/hikka), pinned in `vendor/hikka` at commit `35bd52e24026bb6cb6e7a4ef2f85e9ca900b16aa`. Its upstream web UI is retained as source/reference, but its runtime is not installed because its pinned `aiohttp==3.8.3` fails to build on Python 3.14. Its supported Telegram inline/module functionality is supplied through the selected Heroku-derived runtime.
- [Heroku-TL](https://github.com/coddrago/heroku-tl), pinned as the `herokutl==2.2.1` dependency. This is a Telegram MTProto client library, not the Heroku Userbot.
- Hikka's README links to [`@lavhostbot`](https://t.me/lavhostbot?start=SGlra2E) for installation, and its source contains `LAVHOST`/`lavhost.ml` hosting hooks. Heroku's inspected current source does not contain those hooks. No official lavHost hosting source repository was verified. [`m3anly/lavmsgbot`](https://github.com/m3anly/lavmsgbot) describes itself as a remake for an instance of `@lavhost_bot`; it is not treated as official lavHost code. Exotica recognizes `LAVHOST` for its host display; it does not claim to provision or manage lavHost accounts.

## Licensing

Exotica, Hikka, and the checked-in Heroku license/source headers use AGPL-3.0 terms; full upstream license files and source copyright notices are retained under `vendor/`. GitHub's repository metadata currently labels Heroku GPL-3.0 while its checked-in LICENSE and source headers state AGPL-3.0; verify with the upstream maintainers before redistribution. Heroku-TL is MIT-licensed. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for exact provenance and obligations. Modified network-accessible versions must comply with AGPL-3.0 source-offer requirements.
