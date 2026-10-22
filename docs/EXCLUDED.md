# Что исключено из GitHub-комплекта

Включение конфигов не означает включение личных данных приложений.

- Пароли, OAuth tokens, API keys и account credentials.
- Browser cookies, logins/key/certificate databases, history, sessions,
  bookmarks, extension storage и полный Zen/Chromium profile.
- Telegram tdata; Discord/Mattermost local storage и account databases.
- Spotify autologin, saved credentials, OAuth Spotify Qt, кеши музыки.
- Bitwarden vault, KDE Connect pairing keys, VPN profiles и клиентские сертификаты.
- SSH/GPG keys, cloud/kube/docker credentials, Wi-Fi credentials.
- Codex auth.json, session transcripts, history, plugin account connections.
- Рабочие проекты, Obsidian-заметки, личные календари и private calendar URLs.
- Steam userdata, игры, личные файлы, книги и сохранения.
- Кеши, логи, старые backup, .git history, зависимости node_modules и
  распакованные копии AppImage.
- Текущая таблица разделов, ключи шифрования, bootloader installation state,
  полный `/etc`, `/boot` и образ диска.

Полный исходный `~/.config`, browser profile и `/home` не обходились
рекурсивным копированием: использованы списки разрешённых каталогов и файлов.
Аккаунтные файлы исключены по назначению; для отдельных JSON экспортированы
только явно выбранные UI-ключи. Затем комплект проверяется на известные
форматы ключей и приватных данных. Автоматический поиск шаблонов не является
математической гарантией отсутствия любого мыслимого секрета.

Перед удалением Linux самостоятельно сохранить нужные личные данные на другой
носитель или в своё защищённое хранилище. В этот комплект они намеренно не
добавлялись. Особенно важно отдельно сохранить Obsidian vault и проекты,
поскольку восстановление `.obsidian` не возвращает содержимое заметок.
