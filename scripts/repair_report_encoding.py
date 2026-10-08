from pathlib import Path
p=Path('scripts/build_report.py')
s=p.read_text(encoding='utf8')
if '\u00e2\u2020' in s:
    s=s.encode('cp1252').decode('utf8')
    p.write_text(s,encoding='utf8')
print('Report source encoding is UTF-8.')
