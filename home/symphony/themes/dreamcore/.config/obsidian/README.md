# Obsidian · Dreamcore

Самостоятельная тема Obsidian для учебных заметок. Источник цветов —
`../../palette.json`, читаемые производные — `../../derived.json`.
Прежние темы Obsidian и Symphony Zen не изменены.

## Файлы

- `build.py` — собирает `theme.css` и `manifest.json` из общей палитры.
- `chrome.css` — панели, вкладки, меню, кнопки и выделения.
- `editor.css` — текст, код, ссылки, таблицы и подсветка важных слов.
- `focus.css` — режим одной заметки и команда существующего Style Settings.
- `theme.css`, `manifest.json` — готовые файлы для Obsidian.

Тема использует синий `#194B66`, кремовый `#FAEEBA`, голубые ссылки,
светлый лавандовый акцент и зелёное выделение с тёмным текстом.
Фон блоков кода затемнён из основного синего для читаемости оранжевых токенов.
Текст заметки — Noto Sans 18 px, интерфейс — Noto Sans, код —
JetBrainsMono Nerd Font. Ширина обычной строки ограничена 780 px.

## Фокусировка

`Ctrl+Alt+F` переключает **Style Settings: Toggle Dreamcore Focus**.
Та же команда доступна в палитре Obsidian (`Ctrl+P`, поиск `Dreamcore Focus`)
и в Settings → Style Settings → Dreamcore.

В режиме фокуса скрыты боковые панели, вкладки, заголовки интерфейса, статус,
свойства, встроенные обратные ссылки и другие открытые рядом заметки.
Остаётся активная Markdown-заметка. Повторное нажатие возвращает интерфейс:
панели и заметки не закрываются, их раскладка не переписывается.
Граф и Canvas не включают скрытие интерфейса. Диалоги и палитра команд доступны.

Для скрытия также внешних панелей рабочего стола используется уже существующий
Hyprland `Super+F` (полный экран окна); затем `Ctrl+Alt+F` убирает интерфейс Obsidian.

Новых плагинов нет: используется установленный `obsidian-style-settings`.
Фокусировка — CSS-класс, без таймеров, обработчиков текста, blur и анимации фона.
При смене темы команда Dreamcore исчезает; прежние команды Willemstad сохранены.

## Сборка и применение

```sh
python3 ~/symphony/themes/dreamcore/.config/obsidian/build.py
cp ~/symphony/themes/dreamcore/.config/obsidian/{theme.css,manifest.json} \
  ~/Documents/MyVault/MyVault/.obsidian/themes/Dreamcore/
```

Файлы в хранилище являются обычными копиями: абсолютных CSS-импортов и ссылок
на локальную машину нет. Общий `dreamcore/build.py` не изменён; после смены
палитры нужно отдельно запустить приведённую команду.

Для смены оформления: Settings → Appearance → Themes → Dreamcore или прежняя
Willemstad. Для полного отката закрыть Obsidian и восстановить `appearance.json`,
`hotkeys.json` и данные Style Settings из резервной копии, путь к которой записан
в `~/.local/state/obsidian-dreamcore/backup-path`.
