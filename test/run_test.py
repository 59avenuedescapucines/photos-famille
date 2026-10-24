import subprocess, time, sys, os
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__))
cfg=open(os.path.join(here,'..','site','config.js')).read()
open(os.path.join(here,'..','site','config.js'),'w').write("window.PF_API_URL='http://127.0.0.1:8765/api';\n")
srv=subprocess.Popen([sys.executable,os.path.join(here,'mock_server.py')]); time.sleep(1.2)
out=os.path.join(here,'shots'); os.makedirs(out,exist_ok=True)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
    ctx=b.new_context(viewport={'width':390,'height':844},permissions=['microphone'],device_scale_factor=2)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m: m.type=='error' and errs.append(m.text))
    # lien invalide
    pg.goto('http://127.0.0.1:8765/index.html?c=FAUX'); pg.wait_for_selector('text=Bienvenue'); pg.screenshot(path=out+'/0-sans-lien.png')
    # Franck
    pg.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); pg.wait_for_selector('.tile'); pg.wait_for_selector('.tile img'); 
    assert 'Bonjour Franck' in pg.inner_text('#who'); print('tuiles',pg.locator('.tile').count())
    pg.screenshot(path=out+'/1-galerie.png')
    pg.click('.chip:has-text("Franck Cadet")'); n=pg.locator('.tile').count(); print('filtre Franck ->',n); assert n==2
    pg.fill('.search','corse'); time.sleep(.3); print('recherche corse ->',pg.locator('.tile').count())
    pg.fill('.search',''); pg.click('.chip:has-text("Tout le monde")')
    pg.locator('.tile').first.click(); pg.wait_for_selector('.photo-frame img'); pg.wait_for_selector('text=Personne n’a encore')
    pg.fill('textarea[aria-label="Votre commentaire"]','Photo prise chez Mémé, un dimanche de 2003.')
    pg.click('text=Publier mon commentaire'); pg.wait_for_selector('.comment'); print('commentaire texte OK')
    # audio
    pg.click('text=Raconter à voix haute'); pg.wait_for_selector('.dot'); pg.screenshot(path=out+'/2-enregistrement.png'); time.sleep(2.2)
    pg.click('text=Terminer l’enregistrement'); pg.wait_for_selector('audio'); 
    pg.fill('#trans','Transcription corrigée à la main.'); pg.click('text=Publier mon commentaire'); pg.wait_for_selector('text=Écouter le témoignage')
    pg.screenshot(path=out+'/3-fiche.png',full_page=True)
    pg.click('text=Écouter le témoignage'); pg.wait_for_selector('.comment audio'); print('lecture audio OK, 2 commentaires:',pg.locator('.comment').count())
    # modifier
    pg.locator('.comment').first.locator('text=Modifier').click(); pg.locator('.comment textarea').first.fill('Texte modifié.'); pg.click('text=Enregistrer'); pg.wait_for_selector('text=Texte modifié.')
    # Nini ne peut pas modifier celui de Franck ; admin oui
    pg2=ctx.new_page(); pg2.goto('http://127.0.0.1:8765/index.html?c=CODE-NINI'); pg2.wait_for_selector('.tile'); pg2.locator('.tile').first.click(); pg2.wait_for_selector('.comment')
    assert pg2.locator('.comment >> text=Modifier').count()==0; print('Nini: pas de bouton Modifier sur les contributions de Franck OK')
    pg3=ctx.new_page(); pg3.goto('http://127.0.0.1:8765/index.html?c=CODE-MATHIEU'); pg3.wait_for_selector('.tile'); pg3.locator('.tile').first.click(); pg3.wait_for_selector('.comment')
    assert pg3.locator('.comment >> text=Supprimer').count()==2; print('Admin: peut supprimer les 2 OK'); pg3.screenshot(path=out+'/4-admin.png',full_page=True)
    pg3.locator('text=Supprimer').first.click(); pg3.click('text=Oui, supprimer'); time.sleep(.6); print('après suppression admin:',pg3.locator('.comment').count())
    # --- dépôts de photos ---
    from PIL import Image as I
    I.new('RGB',(3000,2000),(120,160,200)).save(os.path.join(here,'depot1.jpg')); I.new('RGB',(900,1200),(200,120,90)).save(os.path.join(here,'depot2.jpg'))
    pf=ctx.new_page(); pf.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); pf.wait_for_selector('.tile'); pf.click('nav >> text=Ajouter des photos')
    pf.set_input_files('#file',[os.path.join(here,'depot1.jpg'),os.path.join(here,'depot2.jpg')]); pf.wait_for_selector('.previews img')
    pf.fill('textarea[aria-label="Description"]','Pépé et Mémé devant la maison de Douai, vers 1975.'); pf.screenshot(path=out+'/7-depot.png',full_page=True)
    pf.click('text=Envoyer 2 photos'); pf.wait_for_selector('text=photos reçues'); print('dépôt de 2 photos OK')
    # Nini ne voit pas le dépôt en attente ; l'admin si
    pn=ctx.new_page(); pn.goto('http://127.0.0.1:8765/index.html?c=CODE-NINI'); pn.wait_for_selector('.tile'); pn.click('nav >> text=Nouveautés'); time.sleep(.8)
    assert pn.locator('.tile .when:has-text("Par Franck")').count()==0 and pn.locator('nav >> text=À valider').count()==0; print('Nini: ne voit pas le dépôt en attente, pas de bouton À valider OK')
    pa=ctx.new_page(); pa.goto('http://127.0.0.1:8765/index.html?c=CODE-MATHIEU'); pa.wait_for_selector('nav >> text=À valider'); 
    assert pa.inner_text('nav').count('2')>=1; pa.click('nav >> text=À valider'); pa.wait_for_selector('.review .ph img'); pa.screenshot(path=out+'/8-validation.png',full_page=True)
    pa.locator('.review button:has-text("✔ Valider")').first.click(); time.sleep(.6); pa.locator('.review button:has-text("✖ Refuser")').first.click(); time.sleep(.6); print('admin: 1 validée, 1 refusée')
    pn.click('nav >> text=Photos'); pn.click('nav >> text=Nouveautés'); pn.wait_for_selector('.tile .when:has-text("Par Franck")'); print('Nini voit la photo validée OK, tuiles:',pn.locator('.tile .when:has-text("Par Franck")').count())
    pn.locator('.tile button').first.click(); pn.wait_for_selector('textarea[aria-label="Votre commentaire"]'); print('commentable OK'); pn.screenshot(path=out+'/9-depot-fiche.png')
    # --- diaporama ---
    SSJS = '''window.__spoken=[];window.SpeechSynthesisUtterance=function(t){this.text=t};
      Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{lang:'fr-FR'}],cancel(){},speak(u){window.__spoken.push(u.text);setTimeout(()=>u.onend&&u.onend(),300)}}});'''
    ds=ctx.new_page(); ds.add_init_script(SSJS); ds.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); ds.wait_for_selector('.tile')
    # un résumé sur la photo 0 et 1 pour tester la voix
    import mock_server
    ds.click('text=Lancer le diaporama'); ds.wait_for_selector('.range'); ds.evaluate("document.querySelector('.range').value=4; document.querySelector('.range').dispatchEvent(new Event('input'))")
    ds.check('#o-rnd'); ds.click('text=Démarrer le diaporama'); ds.wait_for_selector('.ss-stage img'); first=ds.inner_text('.ss-cap h2'); print('diaporama démarré, 1re photo:',first[:40])
    ds.screenshot(path=out+'/10-diaporama.png'); time.sleep(6.5); second=ds.inner_text('.ss-cap h2'); assert second!=first; print('avance automatique OK')
    jc=lambda w: ds.evaluate("w=>[...document.querySelectorAll('.ss-bar button')].find(b=>b.textContent.includes(w)).click()", w); jc('Pause'); t1=ds.inner_text('.ss-cap h2'); time.sleep(5); assert ds.inner_text('.ss-cap h2')==t1; print('pause OK')
    jc('Lecture'); jc('Ne plus afficher'); ds.wait_for_selector('.ss-toast'); print('bannir OK, toast:',ds.inner_text('.ss-toast')[:40])
    ds.keyboard.press('Escape'); ds.wait_for_selector('.tile'); ds.click('text=Lancer le diaporama'); ds.wait_for_selector('.banlist .it'); print('liste des masquées:',ds.locator('.banlist .it').count()); ds.click('.banlist .it button'); time.sleep(.5); print('rétablie, reste:',ds.locator('.banlist .it').count())
    print('voix appelée:',ds.evaluate('window.__spoken.length'),'fois')
    # --- message de l'administrateur ---
    pa.click('nav >> text=Message'); pa.fill('textarea[aria-label="Message"]','Rendez-vous dimanche chez Mémé pour trier les photos du grenier !'); pa.click('text=Envoyer à la famille'); pa.wait_for_selector('text=Message envoyé'); 
    pf2=ctx.new_page(); pf2.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); pf2.wait_for_selector('.banner'); print('bandeau pour Franck:',pf2.inner_text('.banner')[:60].replace(chr(10),' '))
    pf2.screenshot(path=out+'/11-bandeau.png'); pf2.click('.banner button'); assert pf2.locator('.banner').count()==0; pf2.reload(); pf2.wait_for_selector('.tile'); time.sleep(.6); assert pf2.locator('.banner').count()==0; print('bandeau masqué après lecture OK')
    assert pf2.locator('nav >> text=Message').count()==0; print('membre: pas d\'onglet Message OK')
    r=pf2.evaluate("fetch(window.PF_API_URL,{method:'POST',body:JSON.stringify({fn:'postMessage',args:['CODE-FRANCK','piratage']})}).then(r=>r.json())"); assert not r['ok']; print('membre ne peut pas poster:',r['error'])
    pg.screenshot(path=out+'/5-desktop.png'); 
    d=ctx.browser.new_context(viewport={'width':1200,'height':800}).new_page(); d.goto('http://127.0.0.1:8765/index.html?c=CODE-MATHIEU'); d.wait_for_selector('.tile img'); d.screenshot(path=out+'/6-desktop.png')
    print('erreurs JS:',errs); b.close()
finally:
  srv.terminate(); open(os.path.join(here,'..','site','config.js'),'w').write(cfg)
