# Telegram · Symphony Zen

Статическая штатная тема Telegram Desktop 7.2.9, согласованная с Zen Browser
и общей палитрой Symphony Zen. Дополнительных процессов и зависимостей нет.

## Источник цветов

```text
~/.config/symphony/current/.config/gtk-3.0/colors.css
    ├── Zen Browser: build-colors.py → chrome/colors.css
    └── Telegram: build-theme.py → themes/symphony-zen.tdesktop-theme
```

Telegram копирует применённую тему во внутреннее хранилище. Он не перечитывает
ссылку на исходный файл при изменении GTK-палитры. Поэтому генерация и импорт —
отдельные действия; автоматического изменения Telegram при переключении
Symphony не добавлено.

## Файлы

- `scripts/build-theme.py` — чтение общей палитры, роли UI, проверка aliases,
  генерация сплошного PNG и ZIP. Только стандартная библиотека Python.
- `upstream/` — публичная базовая схема Telegram 7.2.9 с источником и лицензией.
- `themes/symphony-zen.tdesktop-palette` — итоговые 467 цветов.
- `themes/symphony-zen.tdesktop-theme` — тема с фоном; импортировать этот файл.
- `themes/palette.json` — семантические цвета для просмотра и дальнейшей правки.

## Обновить тему

```sh
python ~/.config/telegram-rice/scripts/build-theme.py
Telegram -- tg://settings/appearance/wallpapers/choose-photo
```

В Telegram нажать **Choose from file**, выбрать
`~/.config/telegram-rice/themes/symphony-zen.tdesktop-theme` и подтвердить
**Keep changes**. Перед заменой проверить актуальность схемы для новой версии
Telegram. Генератор предназначен прежде всего для текущей тёмной Symphony Zen;
при переходе на светлую палитру повторно проверить контраст и роли.

## Применённые параметры — 2026-10-06

- UI и сообщения: Noto Sans, через штатный Font family; emoji fallback штатный.
- Auto-night mode: Off, чтобы другая встроенная тема не подменяла собственную.
- Фон #0f0f0f, панели и входящие #1c1c1e, исходящие #2c2c2f.
- Цветовые состояния выделения #49494c, hover #343437, акцент #a8a8ac.
- Красные предупреждения и цвета идентичности аватаров сохранены.
- Штатные масштабы, геометрия сообщений, анимации и ускорение не менялись.
- Qt/GTK, Hyprland, NVIDIA и системные настройки не менялись.

Новых эффектов blur/прозрачности и анимаций тема не добавляет. Это не замер FPS;
она использует обычный механизм палитр Telegram без модов и фоновых демонов.

## Возврат

Backup до настройки:
`~/.local/state/telegram-rice/backups/20261006-150228/`.

Через **Choose from file** импортировать `previous-theme.tdesktop-theme` из
backup и подтвердить **Keep changes**. Он содержит прежнюю палитру и фон.
Затем вернуть **Font family → Default** (потребуется перезапуск) и
**Auto-night mode → System**, как было до настройки.

`settingss.before` — дополнительная непрозрачная копия локальных настроек с
правами 600; для обычного отката использовать импорт темы. Не копировать
настройки поверх файлов работающего Telegram. Backup не помещать в Git.

Здесь хранятся только воспроизводимые настройки и публичные исходные данные.
Файлы авторизации, переписки и внутренний `tdata` в этот каталог не входят.
