# Exotica upstream source layout

This repository combines the upstream Hikka project as its root source tree with the complete vendored Heroku Userbot source under `vendor/heroku`.

- Hikka core and built-in modules: https://github.com/hikariatama/Hikka, pinned to `35bd52e24026bb6cb6e7a4ef2f85e9ca900b16aa`.
- Heroku Userbot source and modules: https://github.com/Heroku-userbot/Heroku, pinned in the existing vendored checkout at `4d8a764087bd27e146c7834b720f3cd717abd0ec`.

The Heroku source is preserved intact as a separate upstream tree. Its modules target Heroku's runtime and dependencies; they are not copied over Hikka's same-named modules or represented as drop-in Hikka modules.

Both upstream projects are distributed under AGPL-3.0; retain their notices and license files when redistributing modifications.
