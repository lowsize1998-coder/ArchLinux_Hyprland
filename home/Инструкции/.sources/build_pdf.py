"""Create editable ODT documents; export them with the installed LibreOffice."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import subprocess
import zipfile

ROOT = Path('/home/rozetta/Инструкции')
SOURCE = ROOT / '.sources'
GUIDES = json.loads((SOURCE / 'guides.json').read_text())
NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
      'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
      'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
      'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
      'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
      'xmlns:xlink="http://www.w3.org/1999/xlink" '
      'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"')

STYLES = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles {NS} office:version="1.3">
<office:font-face-decls><style:font-face style:name="Noto Sans" svg:font-family="'Noto Sans'"/>
<style:font-face style:name="Noto Sans Mono" svg:font-family="'Noto Sans Mono'"/></office:font-face-decls>
<office:styles>
<style:default-style style:family="paragraph"><style:paragraph-properties fo:line-height="125%" fo:margin-bottom="0.12cm" fo:orphans="2" fo:widows="2"/><style:text-properties style:font-name="Noto Sans" fo:font-size="10.5pt" fo:color="#243F4D" fo:language="ru" fo:country="RU"/></style:default-style>
<style:style style:name="Title" style:family="paragraph"><style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0.35cm" fo:keep-with-next="always"/><style:text-properties fo:font-size="24pt" fo:font-weight="bold" fo:color="#194B66"/></style:style>
<style:style style:name="Subtitle" style:family="paragraph"><style:paragraph-properties fo:margin-bottom="0.55cm"/><style:text-properties fo:font-size="9pt" fo:color="#64767E"/></style:style>
<style:style style:name="Heading" style:family="paragraph"><style:paragraph-properties fo:margin-top="0.45cm" fo:margin-bottom="0.2cm" fo:keep-with-next="always"/><style:text-properties fo:font-size="13pt" fo:font-weight="bold" fo:color="#194B66"/></style:style>
<style:style style:name="Cell" style:family="paragraph"><style:paragraph-properties fo:margin-bottom="0cm" fo:line-height="120%"/><style:text-properties fo:font-size="10pt"/></style:style>
<style:style style:name="Key" style:family="paragraph" style:parent-style-name="Cell"><style:text-properties fo:font-weight="bold" fo:color="#194B66"/></style:style>
<style:style style:name="HeaderCell" style:family="paragraph" style:parent-style-name="Cell"><style:text-properties fo:font-weight="bold" fo:color="#FAEEBA"/></style:style>
<style:style style:name="Source" style:family="paragraph"><style:paragraph-properties fo:margin-bottom="0.16cm"/><style:text-properties fo:font-size="8pt" fo:color="#526D7A"/></style:style>
<style:style style:name="Footer" style:family="paragraph"><style:paragraph-properties fo:text-align="end"/><style:text-properties fo:font-size="8pt" fo:color="#526D7A"/></style:style>
</office:styles>
<office:automatic-styles><style:page-layout style:name="Page"><style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" style:print-orientation="portrait" fo:margin-top="1.6cm" fo:margin-bottom="1.6cm" fo:margin-left="1.6cm" fo:margin-right="1.6cm"/>
<style:footer-style><style:header-footer-properties fo:min-height="0.5cm" fo:margin-top="0.4cm"/></style:footer-style></style:page-layout></office:automatic-styles>
<office:master-styles><style:master-page style:name="Standard" style:page-layout-name="Page"><style:footer><text:p text:style-name="Footer">DREAMCORE · 14.10.2026 · <text:page-number/> / <text:page-count/></text:p></style:footer></style:master-page></office:master-styles>
</office:document-styles>'''

def p(value, style='Cell'):
    return f'<text:p text:style-name="{style}">{escape(value)}</text:p>'

def table(rows, number):
    def row(values, header=False, alternate=False):
        result='<table:table-row table:style-name="Row">'
        for i,value in enumerate(values):
            cell_style='HeaderBG' if header else 'Alternate' if alternate else 'Normal'
            para_style='HeaderCell' if header else 'Key' if i==0 else 'Cell'
            result+=f'<table:table-cell table:style-name="{cell_style}" office:value-type="string">{p(value,para_style)}</table:table-cell>'
        return result+'</table:table-row>'
    result=f'<table:table table:name="Table{number}" table:style-name="Table"><table:table-column table:style-name="KeyCol"/><table:table-column table:style-name="DescCol"/>'
    result+='<table:table-header-rows>'+row(['Клавиши / действие','Что происходит'],header=True)+'</table:table-header-rows>'
    result+=''.join(row(values,alternate=i%2==0) for i,values in enumerate(rows))
    return result+'</table:table>'

def write_odt(guide):
    body=f'<text:h text:style-name="Title" text:outline-level="1">{escape(guide["title"])}</text:h>'
    body+=p('Arch Linux · Hyprland · Личные настройки и подтверждённые штатные клавиши','Subtitle')
    for i,section in enumerate(guide['sections']):
        body+=f'<text:h text:style-name="Heading" text:outline-level="2">{escape(section["title"])}</text:h>'
        body+=table(section['rows'],i)
    if guide['notes']:
        body+='<text:h text:style-name="Heading" text:outline-level="2">Особенности твоей настройки</text:h>'
        body+=''.join(p(note) for note in guide['notes'])
    body+='<text:h text:style-name="Heading" text:outline-level="2">Источники и актуальность</text:h>'
    body+=p('Настройки зафиксированы 14.10.2026. После обновлений приложение может изменить стандартные назначения.','Source')
    body+=''.join(p(source,'Source') for source in guide['sources'])
    content=f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {NS} office:version="1.3"><office:automatic-styles>
<style:style style:name="Table" style:family="table"><style:table-properties style:width="17.8cm" table:align="margins" fo:margin-top="0.04cm" fo:margin-bottom="0.1cm"/></style:style>
<style:style style:name="KeyCol" style:family="table-column"><style:table-column-properties style:column-width="5.6cm"/></style:style>
<style:style style:name="DescCol" style:family="table-column"><style:table-column-properties style:column-width="12.2cm"/></style:style>
<style:style style:name="Row" style:family="table-row"><style:table-row-properties fo:keep-together="always"/></style:style>
<style:style style:name="Normal" style:family="table-cell"><style:table-cell-properties fo:padding="0.15cm" fo:border-bottom="0.4pt solid #DCE3E7" style:vertical-align="middle"/></style:style>
<style:style style:name="Alternate" style:family="table-cell" style:parent-style-name="Normal"><style:table-cell-properties fo:padding="0.15cm" fo:border-bottom="0.4pt solid #DCE3E7" fo:background-color="#F0F5F7" style:vertical-align="middle"/></style:style>
<style:style style:name="HeaderBG" style:family="table-cell"><style:table-cell-properties fo:padding="0.17cm" fo:background-color="#194B66" style:vertical-align="middle"/></style:style>
</office:automatic-styles><office:body><office:text>{body}</office:text></office:body></office:document-content>'''
    target=SOURCE/Path(guide['file']).with_suffix('.odt')
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','application/vnd.oasis.opendocument.text',compress_type=zipfile.ZIP_STORED)
        z.writestr('content.xml',content)
        styles = STYLES
        if guide.get('high_contrast_keys'):
            styles = styles.replace(
                'style:parent-style-name="Cell"><style:text-properties fo:font-weight="bold" fo:color="#194B66"',
                'style:parent-style-name="Cell"><style:text-properties fo:font-weight="bold" fo:color="#000000"')
        z.writestr('styles.xml',styles)
        z.writestr('META-INF/manifest.xml','''<?xml version="1.0" encoding="UTF-8"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/><manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/><manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/></manifest:manifest>''')
    return target

if __name__=='__main__':
    import sys
    chosen=GUIDES[:1] if '--sample' in sys.argv else GUIDES
    groups={}
    for guide in chosen:
        odt=write_odt(guide)
        groups.setdefault(str((ROOT/guide['file']).parent),[]).append(str(odt))
    for folder,files in groups.items():
        Path(folder).mkdir(parents=True,exist_ok=True)
        result=subprocess.run(['libreoffice','-env:UserInstallation=file:///home/rozetta/.local/state/shortcut-guides/libreoffice-profile','--headless','--convert-to','pdf:writer_pdf_Export','--outdir',folder,*files],text=True,capture_output=True,timeout=300)
        if result.returncode:raise RuntimeError(result.stderr)
        print(Path(folder).name, len(files),'PDF files',flush=True)
    print('Finished',len(chosen),'guides')
