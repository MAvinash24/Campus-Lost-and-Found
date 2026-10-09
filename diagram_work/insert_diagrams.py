from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
from copy import deepcopy
from PIL import Image
import hashlib,json
base=Path(r'D:\sse\deliverables');out=base/'updated_reports';out.mkdir(exist_ok=True)
source=Path(r'C:\Users\NAANI\Downloads\College_Lost_and_Found_Report.docx')
imgs=base/'detailed_diagrams'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','pic':'http://schemas.openxmlformats.org/drawingml/2006/picture'}
def q(prefix,name):return '{'+ns[prefix]+'}'+name
with ZipFile(source) as z:parts={n:z.read(n) for n in z.namelist()}
root=etree.fromstring(parts['word/document.xml']);orig=deepcopy(root);body=root.find('w:body',ns)
rel=etree.fromstring(parts['word/_rels/document.xml.rels']);relmap={e.get('Id'):e.get('Target') for e in rel}
replacements={'rId10':'01_use_cases_campus','rId11':'03_analysis_sequence','rId12':'04_entity_relationship','rId13':'05_dfd_level_0','rId14':'06_dfd_level_1','rId15':'08_application_architecture','rId23':'09_sensitive_information_flow','rId24':'10_attack_tree','rId25':'11_security_refined_architecture'}
changes=[]
def pprop(p,key,val=None):
 pr=p.find('w:pPr',ns)
 if pr is None:pr=etree.Element(q('w','pPr'));p.insert(0,pr)
 el=pr.find('w:'+key,ns)
 if el is None:el=etree.SubElement(pr,q('w',key))
 if val is not None:el.set(q('w','val'),str(val))
def dimensions(p,path):
 w,h=Image.open(path).size;extent=p.find('.//wp:extent',ns);cx=int(extent.get('cx'));cy=round(cx*h/w)
 extent.set('cy',str(cy))
 for e in p.findall('.//a:xfrm/a:ext',ns):e.set('cx',str(cx));e.set('cy',str(cy))
 for e in p.findall('.//a:srcRect',ns):e.getparent().remove(e)
 pprop(p,'keepNext');pprop(p,'keepLines')
for p in list(body):
 blip=p.find('.//a:blip',ns)
 if blip is None:continue
 rid=blip.get(q('r','embed'))
 if rid not in replacements:continue
 name=replacements[rid];path=imgs/(name+'.png');target='word/'+relmap[rid]
 parts[target]=path.read_bytes();dimensions(p,path)
 for e in p.findall('.//wp:docPr',ns):e.set('descr',name.replace('_',' '))
 changes.append({'operation':'replace','old_media':target,'new_image':name+'.png'})
insertions=[('Figure 1  Use cases with include and conditional extend relationships','02_use_cases_administration','Figure 1A  Administration and operations use cases'),('Figure 5  Level 1 DFD with stores and authorization flows','07_dfd_level_2_recovery','Figure 5A  Detailed Level 2 DFD for creator-only recovery'),('Figure 16  Architecture refined around the highest-risk flows','12_report_lifecycle','Figure 16A  Report moderation and recovery lifecycle')]
nextid=max(int(e.get('id')) for e in root.findall('.//wp:docPr',ns))+1
for idx,(anchor,name,cap) in enumerate(insertions):
 caption=next(p for p in body if ''.join(p.xpath('.//w:t/text()',namespaces=ns))==anchor)
 template=caption.getprevious();p=deepcopy(template);rid='rId'+str(50+idx);bl=p.find('.//a:blip',ns);bl.set(q('r','embed'),rid)
 for e in p.findall('.//wp:docPr',ns):e.set('id',str(nextid));e.set('name',name);e.set('descr',name.replace('_',' '));nextid+=1
 for e in p.findall('.//pic:cNvPr',ns):e.set('id',str(nextid));e.set('name',name+'.png');nextid+=1
 for k in ['wp14:anchorId','wp14:editId']:
  pass
 path=imgs/(name+'.png');dimensions(p,path);pprop(p,'pageBreakBefore')
 fn='word/media/detailed_'+name+'.png';parts[fn]=path.read_bytes()
 etree.SubElement(rel,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',Id=rid,Type=ns['r']+'/image',Target='media/detailed_'+name+'.png')
 cp=deepcopy(caption)
 for e in cp.findall('w:r',ns):cp.remove(e)
 rr=etree.SubElement(cp,q('w','r'));etree.SubElement(rr,q('w','t')).text=cap
 caption.addnext(p);p.addnext(cp);changes.append({'operation':'insert','caption':cap,'new_image':name+'.png'})
parts['word/document.xml']=etree.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
parts['word/_rels/document.xml.rels']=etree.tostring(rel,encoding='UTF-8',xml_declaration=True,standalone=True)
output=out/'College_Lost_and_Found_Report_Updated_Diagrams.docx'
with ZipFile(output,'w',ZIP_DEFLATED) as z:
 for n,data in parts.items():z.writestr(n,data)
original_text=orig.xpath('//w:t/text()',namespaces=ns);final_text=root.xpath('//w:t/text()',namespaces=ns)
added=[i[2] for i in insertions]
remaining=[t for t in final_text if t not in added]
assert remaining==original_text,'Original text changed'
with ZipFile(output) as z:
 for rid,name in replacements.items():assert z.read('word/'+relmap[rid])==(imgs/(name+'.png')).read_bytes()
 assert len(root.findall('.//a:blip',ns))==25
qa={'original_text_nodes':len(original_text),'preserved_original_text_nodes':len(remaining),'original_text_unchanged':True,'old_diagrams_replaced':9,'new_diagrams_added':3,'total_new_diagrams':12,'original_tables':len(orig.findall('.//w:tbl',ns)),'updated_tables':len(root.findall('.//w:tbl',ns)),'original_images':22,'updated_images':25,'changes':changes,'original_docx_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(out/'preservation_check.json').write_text(json.dumps(qa,indent=2),encoding='utf8');print(json.dumps(qa,indent=2))
