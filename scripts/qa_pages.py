from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import pymupdf as fitz,json
q=Path('deliverables/qa');d=fitz.open(q/'College_Lost_and_Found_Report.pdf')
pages=[q/f'page-{n+1}.png' for n in range(len(d))]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
for start in range(0,len(pages),4):
    sheet=Image.new('RGB',(1600,2320),'#dddddd');draw=ImageDraw.Draw(sheet)
    for j,p in enumerate(pages[start:start+4]):
        im=Image.open(p).convert('RGB');im.thumbnail((780,1090))
        x=(j%2)*800+10;y=(j//2)*1160+40
        sheet.paste(im,(x,y));draw.text((x,y-32),p.stem,font=font,fill='black')
    sheet.save(q/f'sheet-{start//4+1}.png')
(q/'text-review.json').write_text(json.dumps([{'page':i+1,'characters':len(p.get_text()),'text':p.get_text()} for i,p in enumerate(d)],indent=2),encoding='utf8')
print('Prepared',len(pages),'rendered pages for visual inspection.')
