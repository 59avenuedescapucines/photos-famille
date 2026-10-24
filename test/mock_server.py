# Serveur de maquette : sert /site et simule l'API Apps Script (mêmes messages JSON), photos de test synthétiques.
import json, base64, io, uuid, datetime, http.server, socketserver, os, sys
from PIL import Image, ImageDraw
ROOT = os.path.join(os.path.dirname(__file__), '..', 'site')
MEMBERS = {'CODE-MATHIEU':dict(id='mathieu',nom_affiche='Mathieu Cadet',tag_fichier='Mathieu-Cadet',role='admin'),
           'CODE-FRANCK':dict(id='franck',nom_affiche='Franck Cadet',tag_fichier='Franck-Cadet',role='membre'),
           'CODE-NINI':dict(id='nini',nom_affiche='Nini Cadet',tag_fichier='Nini-Cadet',role='membre')}
NAMES = ['2003_Loic-Anot_Emilie-Cadet_Mathieu-Cadet_Franck-Cadet_Julian-Anot_Sylvie_Nini-Cadet_Marguerite-Cadet_Henri-Cadet.jpg',
 '2000s_Mathieu-Cadet_Nini-Cadet_Loic-Anot_Emilie-Cadet_Corse.jpg','1943_Henri-Cadet_Marguerite-Cadet_Pecquencourt.jpg','1960s_Franck-Cadet_Didier-Cadet.jpg','1980s_inconnu-a-identifier.jpg']
PHOTOS = [dict(id='p%d'%i, nom=n) for i,n in enumerate(NAMES)]
COMMENTS, SYNTH, AUDIO = [], {}, {}
SYNTH.update({'p%d'%i:dict(texte='Résumé de la photo %d. Une belle journée en famille, racontée par plusieurs voix.'%i,maj='2026-10-24T10:00:00Z',base=2) for i in range(5)})
DEPOTS=[]
BANS={}
MSGS=[]
def parse(n):
    b=n.rsplit('.',1)[0].split('_'); return b[0], [t for t in b[1:]]
def img(i,w,h):
    im=Image.new('RGB',(w,h),(180-i*20,140+i*10,100+i*15)); d=ImageDraw.Draw(im); d.rectangle([w//8,h//8,7*w//8,7*h//8],outline=(250,245,236),width=6); d.text((w//2-20,h//2),'Photo %d'%i,fill=(255,255,255))
    b=io.BytesIO(); im.save(b,'JPEG',quality=70); return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
def call(fn,args):
    code=args[0]; me=MEMBERS.get(code)
    if not me: raise Exception('Lien personnel inconnu ou désactivé.')
    if fn=='hello': return dict(me=dict(id=me['id'],nom=me['nom_affiche'],role=me['role'],tag=me['tag_fichier']),membres=[dict(id=m['id'],nom=m['nom_affiche'],tag=m['tag_fichier']) for m in MEMBERS.values()])
    if fn=='listPhotos':
        out=[]
        for p in PHOTOS:
            w,t=parse(p['nom']); n=len([c for c in COMMENTS if c['photo_id']==p['id'] and c['statut']!='supprime'])
            out.append(dict(id=p['id'],nom=p['nom'],when=w,tags=t,nbComm=n,hasSynth=p['id'] in SYNTH))
        return out
    if fn=='messages': return sorted(MSGS,key=lambda x:x['date'],reverse=True)[:10]
    if fn=='postMessage':
        if me['role']!='admin': raise Exception("Réservé à l'administrateur.")
        MSGS.append(dict(id=str(uuid.uuid4()),date=datetime.datetime.now(datetime.timezone.utc).isoformat(),texte=args[1])); return 'ok'
    if fn=='deleteMessage':
        if me['role']!='admin': raise Exception("Réservé à l'administrateur.")
        MSGS[:]=[x for x in MSGS if x['id']!=args[1]]; return True
    if fn=='updates':
        n=len([d for d in DEPOTS if d['statut']=='valide'])
        return dict(now=datetime.datetime.now(datetime.timezone.utc).isoformat(),newPhotos=n,message=(sorted(MSGS,key=lambda x:x['date'])[-1] if MSGS else None),app=dict(versionCode=2,url='https://exemple.fr/photos-famille.apk',notes='Nouveautés'))
    if fn=='synths': return {k:v['texte'] for k,v in SYNTH.items()}
    if fn=='bans': return sorted(BANS.get(me['id'],set()))
    if fn=='setBan':
        b=BANS.setdefault(me['id'],set()); (b.add if args[2] else b.discard)(args[1]); return True
    if fn=='upload':
        ph=args[1]
        if not ph.get('b64'): raise Exception('Photo manquante.')
        d=dict(id=str(uuid.uuid4()),file_id='d%d'%len(DEPOTS),deposant_id=me['id'],deposant=me['nom_affiche'],date=datetime.datetime.now(datetime.timezone.utc).isoformat(),description=ph.get('description',''),statut='en_attente',b64=ph['b64']); DEPOTS.append(d); return d['id']
    if fn=='listDepots':
        return [dict(id=d['file_id'],depotId=d['id'],deposant_id=d['deposant_id'],deposant=d['deposant'],date=d['date'],description=d['description'],statut=d['statut'],nbComm=0,mine=d['deposant_id']==me['id']) for d in DEPOTS if d['statut']!='supprime' and (d['statut']=='valide' or me['role']=='admin' or d['deposant_id']==me['id'])]
    if fn=='depotDecide':
        if me['role']!='admin': raise Exception("Réservé à l'administrateur.")
        [d for d in DEPOTS if d['id']==args[1]][0]['statut']=args[2]; return True
    if fn=='depotDelete':
        d=[d for d in DEPOTS if d['id']==args[1]][0]
        if me['role']!='admin' and not (d['deposant_id']==me['id'] and d['statut']!='valide'): raise Exception('Vous ne pouvez pas retirer ce dépôt.')
        d['statut']='supprime'; return True
    if fn=='image' and args[1].startswith('d'):
        d=[d for d in DEPOTS if d['file_id']==args[1]][0]
        if not (d['statut']=='valide' or me['role']=='admin' or d['deposant_id']==me['id']): raise Exception('Photo non autorisée.')
        return 'data:image/jpeg;base64,'+d['b64']
    if fn=='image':
        i=int(args[1][1:]); return img(i,320,240) if args[2]=='thumb' else img(i,1400,1000)
    if fn=='photo':
        cs=[dict(id=c['id'],photo_id=c['photo_id'],auteur_id=c['auteur_id'],auteur_nom=c['auteur_nom'],date=c['date'],texte=c['texte'],transcription=c['transcription'],hasAudio=bool(c['audio']),maj=c['date'],mine=c['auteur_id']==me['id'],canEdit=c['auteur_id']==me['id'] or me['role']=='admin') for c in COMMENTS if c['photo_id']==args[1] and c['statut']!='supprime']
        return dict(comments=cs,synth=SYNTH.get(args[1]))
    if fn=='audio':
        c=[c for c in COMMENTS if c['id']==args[1]][0]; return 'data:%s;base64,%s'%(c['audio']['mime'],c['audio']['b64'])
    if fn=='add':
        _,pid,texte,audio,tr=args
        if not texte.strip() and not audio: raise Exception('Commentaire vide.')
        COMMENTS.append(dict(id=str(uuid.uuid4()),photo_id=pid,auteur_id=me['id'],auteur_nom=me['nom_affiche'],date=datetime.datetime.utcnow().isoformat()+'Z',texte=texte,transcription=tr or '',audio=audio,statut='ok')); return 'ok'
    if fn in('edit','delete'):
        c=[c for c in COMMENTS if c['id']==args[1] and c['statut']!='supprime'][0]
        if c['auteur_id']!=me['id'] and me['role']!='admin': raise Exception('Vous ne pouvez modifier que vos propres contributions.')
        if fn=='edit':
            c['texte']=args[2]
            if args[3] is not None: c['transcription']=args[3]
        else: c['statut']='supprime'
        return True
    raise Exception('Fonction inconnue.')
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=ROOT,**k)
    def do_POST(s):
        body=json.loads(s.rfile.read(int(s.headers['Content-Length'])))
        try: r=dict(ok=True,data=call(body['fn'],body['args']))
        except Exception as e: r=dict(ok=False,error=str(e))
        o=json.dumps(r).encode(); s.send_response(200); s.send_header('Content-Type','application/json'); s.send_header('Access-Control-Allow-Origin','*'); s.send_header('Content-Length',str(len(o))); s.end_headers(); s.wfile.write(o)
    def log_message(s,*a): pass
if __name__=='__main__':
    socketserver.TCPServer.allow_reuse_address=True
    with socketserver.ThreadingTCPServer(('127.0.0.1',8765),H) as srv: srv.serve_forever()
