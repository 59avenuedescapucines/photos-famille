import subprocess,sys,time
from playwright.sync_api import sync_playwright
cfg=open('../site/config.js').read(); open('../site/config.js','w').write("window.PF_API_URL='http://127.0.0.1:8765/api';\n")
srv=subprocess.Popen([sys.executable,'mock_server.py']); time.sleep(1.2)
SS='''window.__spoken=[];window.SpeechSynthesisUtterance=function(t){this.text=t};
Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{lang:'fr-FR'}],cancel(){},speak(u){window.__spoken.push(u.text);setTimeout(()=>u.onend&&u.onend(),300)}}});'''
try:
  with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':390,'height':844}).new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.add_init_script(SS)
    pg.goto('http://127.0.0.1:8765/index.html?c=CODE-FRANCK'); pg.wait_for_selector('.tile'); time.sleep(1)
    print('synths:',pg.evaluate("Object.keys(S.synths)"), 'speech in window:',pg.evaluate("'speechSynthesis' in window"))
    pg.click('text=Lancer le diaporama'); pg.wait_for_selector('.range'); print('spk checked/disabled:',pg.evaluate("[document.getElementById('o-spk').checked,document.getElementById('o-spk').disabled]"))
    pg.evaluate("document.querySelector('.range').value=4;document.querySelector('.range').dispatchEvent(new Event('input'))")
    pg.click('text=Démarrer'); pg.wait_for_selector('.ss-stage img'); t=[pg.inner_text('.ss-cap h2')]
    for i in range(4):
        time.sleep(5.5); t.append(pg.inner_text('.ss-cap h2'))
    print('titres successifs:',[x[:18] for x in t]); print('spoken:',pg.evaluate('window.__spoken'),'sous-titre:',pg.inner_text('.ss-text')[:50]); print('errs',errs)
    b.close()
finally:
  srv.terminate(); open('../site/config.js','w').write(cfg)
