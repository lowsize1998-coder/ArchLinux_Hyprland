# Zaread · Dreamcore

Zaread 1.5.0 is installed in `~/.local/share/zaread/zaread`, linked from
`~/.local/bin/zaread`. Source: https://github.com/paoloap/zaread.
The pinned source revision and checksum are in
`~/.local/state/zaread-setup/source.json`.

DOCX files are converted locally to PDF by LibreOffice Still, without opening
its editor. The converted copy is stored in `~/.cache/zaread/`; the original
document is not edited. On subsequent opens, unchanged documents use the cache.

The reader is `zathura-rice launch`, so the existing Dreamcore colors and
Zathura shortcuts, including opacity controls, apply to these documents.
This is a read-only workflow; DOCX editing is not provided by Zaread.

Open a document from the Rofi launcher: `Super+Space` → `Zaread`.
Or from the terminal:

```bash
zaread "/path/to/document.docx"
zaread-open
```

Only DOCX is assigned to Zaread by default. PDF and EPUB keep their existing
Zathura associations. The previous MIME settings are backed up under
`~/.local/state/zaread-setup/backups/`.
