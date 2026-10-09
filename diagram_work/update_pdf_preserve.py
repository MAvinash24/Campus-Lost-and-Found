from pathlib import Path
import pymupdf as fitz,json,hashlib
from PIL import Image
root=Path(r'D:\sse');imgs=root/'deliverables/detailed_diagrams';out=root/'deliverables/updated_reports';qa=root/'diagram_work/updated_pdf_qa';qa.mkdir(exist_ok=True)
source=Path(r'C:\Users\NAANI\Downloads\College_Lost_and_Found_Report.pdf');doc=fitz.open(source);texts=[p.get_text() for p in doc]
changes={7:'01_use_cases_campus',9:'03_analysis_sequence',10:'04_entity_relationship',11:'05_dfd_level_0',12:'06_dfd_level_1',13:'08_application_architecture',25:'09_sensitive_information_flow',27:'10_attack_tree',28:'11_security_refined_architecture'}
for num,name in changes.items():
 page=doc[num];info=page.get_image_info(xrefs=True);assert len(info)==1
 box=fitz.Rect(info[0]['bbox']);page.delete_image(info[0]['xref']);page.insert_image(box,filename=str(imgs/(name+'.png')),keep_proportion=True)
 assert page.get_text()==texts[num]
insertions={7:('02_use_cases_administration','Figure 1A  Administration and operations use cases'),12:('07_dfd_level_2_recovery','Figure 5A  Detailed Level 2 DFD for creator-only recovery'),28:('12_report_lifecycle','Figure 16A  Report moderation and recovery lifecycle')}
final=fitz.open();mapping={};newpages=[]
for num in range(len(doc)):
 mapping[num]=len(final);final.insert_pdf(doc,from_page=num,to_page=num)
 if num in insertions:
  name,caption=insertions[num];page=final.new_page(width=doc[num].rect.width,height=doc[num].rect.height)
  page.insert_text((59.5,66),'College Lost and Found',fontname='hebo',fontsize=15,color=(.086,.196,.31))
  pic=imgs/(name+'.png');w,h=Image.open(pic).size;width=page.rect.width-119;top=110;height=width*h/w
  page.insert_image(fitz.Rect(59.5,top,59.5+width,top+height),filename=str(pic))
  page.insert_textbox(fitz.Rect(59.5,top+height+18,page.rect.width-59.5,top+height+70),caption,fontname='helv',fontsize=10,color=(.13,.21,.29))
  page.insert_text((59.5,page.rect.height-43),'20CYS401  Secure Software Engineering',fontname='helv',fontsize=9,color=(.34,.44,.52));newpages.append(len(final))
final.set_metadata(doc.metadata)
dest=out/'College_Lost_and_Found_Report_Updated_Diagrams.pdf';final.save(dest,garbage=4,deflate=True);final.close()
final=fitz.open(dest)
for old,new in mapping.items():assert final[new].get_text()==texts[old],f'Original PDF text changed on page {old+1}'
result={'original_pdf_pages':len(doc),'updated_pdf_pages':len(final),'all_original_page_text_preserved_exactly':True,'original_page_to_updated_page':{str(k+1):v+1 for k,v in mapping.items()},'added_diagram_pages':newpages,'old_diagrams_replaced':9,'new_diagrams_added':3,'original_pdf_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
check=json.loads((out/'preservation_check.json').read_text());check['pdf']=result;(out/'preservation_check.json').write_text(json.dumps(check,indent=2),encoding='utf8')
for i,p in enumerate(final):p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(qa/f'page-{i+1:02d}.png')
print(json.dumps({k:v for k,v in result.items() if k!='original_page_to_updated_page'},indent=2))
# Full-size pages remain available; grouped sheets provide an overview for inspection.
from PIL import ImageDraw,ImageFont
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
for start in range(0,len(final),4):
 sheet=Image.new('RGB',(1840,2680),'#dddddd');draw=ImageDraw.Draw(sheet)
 for j in range(min(4,len(final)-start)):
  p=qa/f'page-{start+j+1:02d}.png';im=Image.open(p);im.thumbnail((900,1280));x=(j%2)*920+10;y=(j//2)*1340+40;sheet.paste(im,(x,y));draw.text((x,y-30),f'Page {start+j+1}',font=font,fill='black')
 sheet.save(qa/f'sheet-{start//4+1:02d}.jpg')
