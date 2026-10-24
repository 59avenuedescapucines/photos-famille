import re, os, time, threading, socketserver
src=open('shots_demo.py').read()
setup=src.split("out=os.path.join(here,'demo')")[0]
exec(setup)
PAL={
 'A-Soleil':  dict(paper='#fffaf2',card='#ffffff',ink='#2a2230',muted='#6e6577',line='#f0e3d2',accent='#e4572e',ink2='#ffffff',soft='#ffe9c9',warn='#c4281c'),
 'B-Mediterranee': dict(paper='#f4f9fd',card='#ffffff',ink='#14263a',muted='#5a6f85',line='#d9e6f2',accent='#1f6fb5',ink2='#ffffff',soft='#ffe3bd',warn='#c4281c'),
 'C-Jardin':  dict(paper='#f6fbf4',card='#ffffff',ink='#1f2d24',muted='#5c7064',line='#dcebd9',accent='#2f8f5b',ink2='#ffffff',soft='#fde4d8',warn='#c4281c'),
}
os.makedirs('pal',exist_ok=True)
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    for name,c in PAL.items():
        css=":root{--paper:%(paper)s;--card:%(card)s;--ink:%(ink)s;--muted:%(muted)s;--line:%(line)s;--accent:%(accent)s;--accent-ink:%(ink2)s;--soft:%(soft)s;--warn:%(warn)s}"%c
        ctx=b.new_context(viewport={'width':390,'height':780},device_scale_factor=2,color_scheme='light')
        pg=ctx.new_page(); pg.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); pg.wait_for_selector('.tile img'); pg.add_style_tag(content=css); time.sleep(.6)
        pg.screenshot(path='pal/%s-galerie.png'%name)
        pg.click('.tile:nth-child(4)'); pg.wait_for_selector('.comment'); pg.wait_for_selector('.photo-frame img'); pg.evaluate("window.scrollTo(0,520)"); time.sleep(.4)
        pg.screenshot(path='pal/%s-fiche.png'%name)
    b.close()
finally:
  httpd.shutdown(); open(os.path.join(site,'config.js'),'w').write(cfg)
from PIL import Image, ImageDraw
names=list(PAL); ims=[[Image.open('pal/%s-%s.png'%(n,k)) for k in ('galerie','fiche')] for n in names]
w,h=ims[0][0].size; pad=30; W=len(names)*w+(len(names)+1)*pad; H=2*h+3*pad+50
out=Image.new('RGB',(W,H),(245,245,245)); d=ImageDraw.Draw(out)
for i,n in enumerate(names):
    x=pad+i*(w+pad); d.text((x,12),n,fill=(30,30,30))
    out.paste(ims[i][0],(x,50)); out.paste(ims[i][1],(x,50+h+pad))
out=out.resize((W//2,H//2)); out.save('pal/comparaison.png'); print(out.size)
