# Third-Party Notices

## Heroku Userbot

- Repository: https://github.com/Heroku-userbot/Heroku (the requested `coddrago/Heroku` URL redirects here)
- Vendored commit: `4d8a764087bd27e146c7834b720f3cd717abd0ec`
- Included under `vendor/heroku/`; upstream source headers and `vendor/heroku/LICENSE` are retained.
- The repository API reports `GPL-3.0`, while the checked-in LICENSE and source file headers state GNU AGPL-3.0. This metadata discrepancy remains unresolved; confirm with maintainers before redistribution beyond AGPL terms.
- Heroku's README acknowledges Hikka as its project foundation and Heroku-TL as its Telegram client backbone.

## Hikka Userbot

- Repository: https://github.com/hikariatama/hikka
- Vendored commit: `35bd52e24026bb6cb6e7a4ef2f85e9ca900b16aa`
- Included under `vendor/hikka/`; upstream copyright notices and `vendor/hikka/LICENSE` are retained.
- License: GNU AGPL-3.0.
- The separately vendored Hikka runtime is retained as a source snapshot/reference. Its pinned `aiohttp==3.8.3` does not build on Python 3.14; the supported runtime is Heroku's Hikka-derived implementation.

## Heroku-TL

- Repository: https://github.com/coddrago/heroku-tl
- Inspected commit: `6a0c7283e5c560845d754b3624aa7010ce0d7461`
- Installed as the single default client dependency `herokutl==2.2.1`, not vendored into this repository.
- Repository license: MIT. The client is a Telethon-derived MTProto library, not the Heroku Userbot.

```text
Copyright (c) 2026 - 2030 Codrago

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

## lavHost

- Hikka's upstream README links to https://t.me/lavhostbot?start=SGlra2E for installation. The inspected Hikka code also contains `LAVHOST` environment handling and constructs `lavhost.ml` URLs.
- The inspected current Heroku source has no lavHost provisioning client or host account management implementation.
- No official lavHost hosting source repository could be verified in public GitHub results. `https://github.com/m3anly/lavmsgbot` explicitly describes itself as a remake for an instance of `@lavhost_bot`; it is not treated as official lavHost code and is not included.

## Distribution

Exotica is distributed under GNU AGPL-3.0-or-later. This combined distribution retains the upstream AGPL code and notices above. Operators who make a modified version available over a network must comply with the applicable AGPL source-offer requirements. Review the licenses of installed Python dependencies when redistributing a built artifact.
