import subprocess, time, sys, os, datetime, json
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__)); site=os.path.join(here,'..','site')
cfg=open(os.path.join(site,'config.js')).read()
open(os.path.join(site,'config.js'),'w').write("window.PF_API_URL='http://127.0.0.1:8765/api';\n")
# images d'exemple plus parlantes (sépia + vignette)
import mock_server as M
from PIL import Image, ImageDraw, ImageFilter
import base64, io, random
def sepia(i,w,h):
    random.seed(i); im=Image.new('RGB',(w,h)); d=ImageDraw.Draw(im)
    for y in range(h):
        t=y/h; d.line([(0,y),(w,y)],fill=(int(196-40*t),int(168-45*t),int(128-40*t)))
    for k in range(3+i%3):
        x=random.randint(w//6,5*w//6); y0=h//3; hh=random.randint(h//3,h//2)
        d.ellipse([x-w//14,y0-w//14,x+w//14,y0+w//14],fill=(90,70,55)); d.rounded_rectangle([x-w//11,y0+w//14,x+w//11,y0+hh],radius=w//30,fill=(70+k*12,55+k*8,45))
    v=Image.new('L',(w,h),0); ImageDraw.Draw(v).ellipse([-w//5,-h//5,w+w//5,h+h//5],fill=255); v=v.filter(ImageFilter.GaussianBlur(w//8))
    dark=Image.new('RGB',(w,h),(40,28,20)); im=Image.composite(im,dark,v)
    b=io.BytesIO(); im.save(b,'JPEG',quality=80); return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
M.img=sepia
M.NAMES[:]=['1943_Henri-Cadet_Marguerite-Cadet_Pecquencourt.jpg','1950s_Marguerite-Cadet_Didier-Cadet_Bernard-Cadet_Douai.jpg','1960s_Franck-Cadet_Didier-Cadet.jpg','1975_Henri-Cadet_Marguerite-Cadet_Douai.jpg','1993_Henri-Cadet_Marguerite-Cadet_Noces-d-or.jpg','2003_Loic-Anot_Emilie-Cadet_Mathieu-Cadet_Franck-Cadet_Nini-Cadet_Marguerite-Cadet_Henri-Cadet.jpg']
M.PHOTOS[:]=[dict(id='p%d'%i,nom=n) for i,n in enumerate(M.NAMES)]
now=datetime.datetime.now(datetime.timezone.utc)
def C(pid,aid,anom,txt,days,tr='',audio=False):
    M.COMMENTS.append(dict(id=str(random.random()),photo_id=pid,auteur_id=aid,auteur_nom=anom,date=(now-datetime.timedelta(days=days)).isoformat(),texte=txt,transcription=tr,audio={'mime':'audio/webm','b64':''} if audio else None,statut='ok'))
C('p3','didier','Didier Cadet','Photo prise devant la maison de Douai, juste après la tonte de la haie. Pépé était fier de son jardin.',3)
C('p3','franck','Franck Cadet','',2,'Moi je me souviens que Mémé avait fait un gâteau ce jour-là, c’était pour l’anniversaire de Bernard.',True)
C('p3','emilie','Emilie Cadet','Je crois que c’est l’été 1975, la voiture derrière est la Simca de Pépé.',1)
M.SYNTH['p3']=dict(texte="Photo prise à Douai, probablement l'été 1975, devant la maison familiale. Didier se souvient que Pépé était fier de son jardin ; Franck évoque un gâteau de Mémé pour l'anniversaire de Bernard ; Emilie reconnaît la Simca de Pépé à l'arrière-plan.",maj=now.isoformat(),base=3)
C('p0','didier','Didier Cadet','Le mariage de Pépé et Mémé, le 8 mai 1943 à Pecquencourt.',5)
C('p5','nini','Nini Cadet','Les 60 ans de mariage, cérémonie en mairie.',4)
M.DEPOTS.append(dict(id='dep1',file_id='d0',deposant_id='franck',deposant='Franck Cadet',date=now.isoformat(),description='Pépé et sa péniche miniature, vers 1985.',statut='en_attente',b64=sepia(2,900,675).split(',')[1]))
M.DEPOTS.append(dict(id='dep2',file_id='d1',deposant_id='emilie',deposant='Emilie Cadet',date=now.isoformat(),description='Repas de famille chez Mémé, Noël 1998.',statut='valide',b64=sepia(4,900,675).split(',')[1]))
srv=subprocess.Popen([sys.executable,'-c','import sys;sys.path.insert(0,r"%s");import mock_server as M,socketserver\nM_=None'%here]) if False else None
import threading, socketserver
socketserver.TCPServer.allow_reuse_address=True
httpd=socketserver.ThreadingTCPServer(('127.0.0.1',8765),M.H); threading.Thread(target=httpd.serve_forever,daemon=True).start(); time.sleep(.5)
out=os.path.join(here,'demo'); os.makedirs(out,exist_ok=True)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
    ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,permissions=['microphone'])
    pg=ctx.new_page(); pg.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); pg.wait_for_selector('.tile img'); time.sleep(.8); pg.screenshot(path=out+'/1-galerie.png')
    pg.click('.tile:nth-child(4)'); pg.wait_for_selector('.comment'); pg.wait_for_selector('.photo-frame img'); time.sleep(.5); pg.screenshot(path=out+'/2-fiche-haut.png')
    pg.evaluate("window.scrollTo(0, 560)"); time.sleep(.3); pg.screenshot(path=out+'/3-fiche-commentaires.png')
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.click('text=Raconter à voix haute'); pg.wait_for_selector('.dot'); time.sleep(2.5); pg.screenshot(path=out+'/4-enregistrement.png')
    pg.click('nav >> text=Ajouter des photos'); time.sleep(.4); pg.screenshot(path=out+'/5-ajout.png')
    pa=ctx.new_page(); pa.goto('http://127.0.0.1:8765/index.html?c=CODE-MATHIEU'); pa.wait_for_selector('nav >> text=À valider'); pa.click('nav >> text=À valider'); pa.wait_for_selector('.review .ph img'); time.sleep(.5); pa.screenshot(path=out+'/6-validation.png')
    d=b.new_context(viewport={'width':1180,'height':760},device_scale_factor=1.5).new_page(); d.goto('http://127.0.0.1:8765/index.html?c=CODE-MATHIEU'); d.wait_for_selector('.tile img'); time.sleep(.8); d.screenshot(path=out+'/7-ordinateur.png')
    # diaporama + bandeau de message
    M.MSGS.append(dict(id='m1',date=now.isoformat(),texte='Rendez-vous dimanche chez Mémé pour trier les photos du grenier !'))
    q=ctx.new_page(); q.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); q.wait_for_selector('.banner'); q.wait_for_selector('.tile img'); time.sleep(.6); q.screenshot(path=out+'/8-message.png')
    q.click('text=Lancer le diaporama'); q.wait_for_selector('.range'); q.evaluate("document.querySelector('.range').value=10;document.querySelector('.range').dispatchEvent(new Event('input'))"); time.sleep(.3); q.screenshot(path=out+'/9-diaporama-reglages.png')
    q.click('text=Démarrer'); q.wait_for_selector('.ss-stage img'); time.sleep(1.2); q.screenshot(path=out+'/10-diaporama.png')
    b.close()
finally:
  httpd.shutdown(); open(os.path.join(site,'config.js'),'w').write(cfg)
