/**
 * Photos de famille — backend (Google Apps Script)
 * À déployer depuis le compte le compte Google de la famille
 *   Déployer > Nouveau déploiement > Application Web
 *   Exécuter en tant que : Moi    |    Qui a accès : Tous les utilisateurs
 * L'identité de chaque personne vient de son lien personnel (colonne "code" de l'onglet Membres).
 * Pas de page ici : l'interface est un site statique qui appelle ce script (doPost).
 */
const CFG = {
  PHOTOS_FOLDER_ID: '1t5RoMjoXH_7QYCkDvxhUXS6gMPBGquBe',   // Photos\Claude
  AUDIO_FOLDER_ID: '1AOCCaPx7sxpbROF41Y3OMDPnkxO5ZiOs',    // Appli-famille-PRIVE\Temoignages-audio
  DEPOTS_FOLDER_ID: '1fVencWbfKOSxk7o4hKGX8EXOdyjU_Kc1',   // Appli-famille-PRIVE\Depots-famille
  SHEET_ID: '11Zb6o1K0MduA5W9BqEWcvxMuo1S8oezQMJ3Slxb-8pI' // Base-appli-famille
};
const COMMENT_COLS = ['id', 'photo_id', 'photo_nom', 'auteur_id', 'auteur_nom', 'date', 'texte', 'audio_id', 'audio_mime', 'transcription', 'statut', 'maj'];

/* ---------- Point d'entrée API (JSON) ---------- */
// La page web est hébergée à part (site statique) ; elle appelle ce script en POST (text/plain, sans pré-vérification CORS).
const API = { hello: api_hello, listPhotos: api_listPhotos, image: api_image, photo: api_photo, audio: api_audio, add: api_add, edit: api_edit, delete: api_delete,
  updates: api_updates, messages: api_messages, postMessage: api_postMessage, deleteMessage: api_deleteMessage,
  synths: api_synths, bans: api_bans, setBan: api_setBan,
  upload: api_upload, listDepots: api_listDepots, depotDecide: api_depotDecide, depotDelete: api_depotDelete };

function doGet() { return json_({ ok: true, service: 'photos-famille' }); }

function doPost(e) {
  try {
    const req = JSON.parse(e.postData.contents);
    if (!Object.prototype.hasOwnProperty.call(API, req.fn)) throw new Error('Fonction inconnue.');
    const result = API[req.fn].apply(null, req.args || []);
    return json_({ ok: true, data: result });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  }
}

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

/* ---------- Utilitaires ---------- */
function sheet_(name) { return SpreadsheetApp.openById(CFG.SHEET_ID).getSheetByName(name); }

function members_() {
  const cache = CacheService.getScriptCache();
  const hit = cache.get('members');
  if (hit) return JSON.parse(hit);
  const v = sheet_('Membres').getDataRange().getValues();
  const h = v.shift();
  const list = v.filter(r => r[0]).map(r => { const o = {}; h.forEach((k, i) => o[k] = String(r[i])); return o; });
  cache.put('members', JSON.stringify(list), 300);
  return list;
}

function auth_(code) {
  if (!code) throw new Error('Lien personnel manquant.');
  const m = members_().find(x => x.code === String(code) && x.actif === 'oui');
  if (!m) throw new Error('Lien personnel inconnu ou désactivé.');
  return m;
}

function readComments_() {
  const v = sheet_('Commentaires').getDataRange().getValues();
  v.shift();
  return v.filter(r => r[0]).map((r, i) => {
    const o = { _row: i + 2 };
    COMMENT_COLS.forEach((k, j) => o[k] = (r[j] instanceof Date) ? r[j].toISOString() : String(r[j]));
    return o;
  });
}

function publicComment_(c, me) {
  return {
    id: c.id, photo_id: c.photo_id, auteur_id: c.auteur_id, auteur_nom: c.auteur_nom,
    date: c.date, texte: c.texte, transcription: c.transcription,
    hasAudio: !!c.audio_id, maj: c.maj,
    mine: c.auteur_id === me.id, canEdit: c.auteur_id === me.id || me.role === 'admin'
  };
}

function inFolder_(file, folderId) {
  const it = file.getParents();
  while (it.hasNext()) if (it.next().getId() === folderId) return true;
  return false;
}
function inPhotosFolder_(file) { return inFolder_(file, CFG.PHOTOS_FOLDER_ID); }

function readDepots_() {
  const v = sheet_('Depots').getDataRange().getValues(); v.shift();
  return v.filter(r => r[0]).map((r, i) => ({ _row: i + 2, id: String(r[0]), file_id: String(r[1]), nom_fichier: String(r[2]), deposant_id: String(r[3]),
    deposant_nom: String(r[4]), date: r[5] instanceof Date ? r[5].toISOString() : String(r[5]), description: String(r[6]), statut: String(r[7]) }));
}
/** Une photo est utilisable (voir / commenter) si elle est dans le dossier principal, ou si c'est un dépôt validé
 *  (ou un dépôt en attente vu par son déposant ou par l'administrateur). */
function photoAllowed_(me, photoId) {
  const f = DriveApp.getFileById(photoId);
  if (inPhotosFolder_(f)) return f;
  if (inFolder_(f, CFG.DEPOTS_FOLDER_ID)) {
    const d = readDepots_().find(x => x.file_id === photoId);
    if (d && (d.statut === 'valide' || me.role === 'admin' || (d.deposant_id === me.id && d.statut !== 'refuse'))) return f;
  }
  throw new Error('Photo non autorisée.');
}

/* Nom de fichier : AAAA(ou 2000s)_Prenom-Nom_Prenom-Nom_Lieu.jpg */
function parseName_(name) {
  const base = name.replace(/\.[^.]+$/, '');
  const parts = base.split('_');
  const when = parts.shift() || '';
  const tags = parts.map(p => p.replace(/-\d+$/, ''));
  return { when: when, tags: tags };
}

/* ---------- API (appelée par google.script.run) ---------- */
function api_hello(code) {
  const me = auth_(code);
  return {
    me: { id: me.id, nom: me.nom_affiche, role: me.role, tag: me.tag_fichier },
    membres: members_().filter(m => m.actif === 'oui').map(m => ({ id: m.id, nom: m.nom_affiche, tag: m.tag_fichier }))
  };
}

function api_listPhotos(code) {
  auth_(code);
  const cache = CacheService.getScriptCache();
  let photos;
  const hit = cache.get('photos');
  if (hit) photos = JSON.parse(hit);
  else {
    photos = [];
    const it = DriveApp.getFolderById(CFG.PHOTOS_FOLDER_ID).getFiles();
    while (it.hasNext()) {
      const f = it.next();
      if (f.getMimeType().indexOf('image/') !== 0) continue;
      const p = parseName_(f.getName());
      photos.push({ id: f.getId(), nom: f.getName(), when: p.when, tags: p.tags });
    }
    photos.sort((a, b) => a.when.localeCompare(b.when) || a.nom.localeCompare(b.nom));
    try { cache.put('photos', JSON.stringify(photos), 600); } catch (e) { /* trop gros : pas grave */ }
  }
  const count = {};
  readComments_().forEach(c => { if (c.statut !== 'supprime') count[c.photo_id] = (count[c.photo_id] || 0) + 1; });
  const syn = {};
  const sv = sheet_('Syntheses').getDataRange().getValues(); sv.shift();
  sv.forEach(r => { if (r[0] && r[3]) syn[r[0]] = true; });
  return photos.map(p => Object.assign({}, p, { nbComm: count[p.id] || 0, hasSynth: !!syn[p.id] }));
}

/** Image d'une photo. size = 'thumb' (petite) ou 'big' (affichage). Renvoie une data-URL. */
function api_image(code, photoId, size) {
  const meImg = auth_(code);
  const f = photoAllowed_(meImg, photoId);
  let blob = null;
  try {
    const w = size === 'thumb' ? 'w320' : 'w1400';
    const r = UrlFetchApp.fetch('https://drive.google.com/thumbnail?id=' + photoId + '&sz=' + w,
      { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true });
    if (r.getResponseCode() === 200 && r.getBlob().getContentType().indexOf('image/') === 0) blob = r.getBlob();
  } catch (e) { /* repli ci-dessous */ }
  if (!blob) blob = size === 'thumb' ? f.getThumbnail() : f.getBlob();
  return 'data:' + blob.getContentType() + ';base64,' + Utilities.base64Encode(blob.getBytes());
}

function api_photo(code, photoId) {
  const me = auth_(code);
  const comments = readComments_()
    .filter(c => c.photo_id === photoId && c.statut !== 'supprime')
    .sort((a, b) => a.date.localeCompare(b.date))
    .map(c => publicComment_(c, me));
  let synth = null;
  const sv = sheet_('Syntheses').getDataRange().getValues(); sv.shift();
  const row = sv.find(r => r[0] === photoId);
  if (row && row[3]) synth = { texte: String(row[3]), maj: row[4] instanceof Date ? row[4].toISOString() : String(row[4]), base: Number(row[5]) || 0 };
  return { comments: comments, synth: synth };
}

function api_audio(code, commentId) {
  auth_(code);
  const c = readComments_().find(x => x.id === commentId && x.statut !== 'supprime');
  if (!c || !c.audio_id) throw new Error('Audio introuvable.');
  const blob = DriveApp.getFileById(c.audio_id).getBlob();
  return 'data:' + (c.audio_mime || blob.getContentType()) + ';base64,' + Utilities.base64Encode(blob.getBytes());
}

/** audio = { b64: '...', mime: 'audio/webm' } ou null */
function api_add(code, photoId, texte, audio, transcription) {
  const me = auth_(code);
  texte = String(texte || '').trim();
  if (!texte && !audio) throw new Error('Commentaire vide.');
  const f = photoAllowed_(me, photoId);
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const id = Utilities.getUuid();
    const now = new Date().toISOString();
    let audioId = '', mime = '';
    if (audio && audio.b64) {
      mime = audio.mime || 'audio/webm';
      const ext = mime.indexOf('mp4') >= 0 ? 'm4a' : mime.indexOf('ogg') >= 0 ? 'ogg' : 'webm';
      const blob = Utilities.newBlob(Utilities.base64Decode(audio.b64), mime.split(';')[0], me.id + '_' + now.replace(/[:.]/g, '-') + '.' + ext);
      audioId = DriveApp.getFolderById(CFG.AUDIO_FOLDER_ID).createFile(blob).getId();
    }
    sheet_('Commentaires').appendRow([id, photoId, f.getName(), me.id, me.nom_affiche, now, texte, audioId, mime, String(transcription || ''), 'ok', now]);
    return id;
  } finally { lock.releaseLock(); }
}

function findRow_(id) {
  const c = readComments_().find(x => x.id === id && x.statut !== 'supprime');
  if (!c) throw new Error('Commentaire introuvable.');
  return c;
}

function api_edit(code, id, texte, transcription) {
  const me = auth_(code);
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const c = findRow_(id);
    if (c.auteur_id !== me.id && me.role !== 'admin') throw new Error('Vous ne pouvez modifier que vos propres contributions.');
    const sh = sheet_('Commentaires');
    sh.getRange(c._row, 7).setValue(String(texte || ''));
    if (transcription !== undefined && transcription !== null) sh.getRange(c._row, 10).setValue(String(transcription));
    sh.getRange(c._row, 12).setValue(new Date().toISOString());
    return true;
  } finally { lock.releaseLock(); }
}

/** Suppression "douce" : la ligne reste dans la feuille (statut = supprime), l'audio part à la corbeille. */
function api_delete(code, id) {
  const me = auth_(code);
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const c = findRow_(id);
    if (c.auteur_id !== me.id && me.role !== 'admin') throw new Error('Vous ne pouvez supprimer que vos propres contributions.');
    const sh = sheet_('Commentaires');
    sh.getRange(c._row, 11).setValue('supprime');
    sh.getRange(c._row, 12).setValue(new Date().toISOString());
    if (c.audio_id) { try { DriveApp.getFileById(c.audio_id).setTrashed(true); } catch (e) {} }
    return true;
  } finally { lock.releaseLock(); }
}

/* ---------- Dépôts de photos par les membres ---------- */
const MAX_DEPOT_B64 = 9 * 1024 * 1024; // ~6,5 Mo d'image : la page réduit les photos avant l'envoi

/** photo = { name, mime, b64, description } — enregistrée "en_attente" jusqu'à validation par l'administrateur. */
function api_upload(code, photo) {
  const me = auth_(code);
  if (!photo || !photo.b64) throw new Error('Photo manquante.');
  if (photo.b64.length > MAX_DEPOT_B64) throw new Error('Photo trop volumineuse.');
  const mime = String(photo.mime || 'image/jpeg');
  if (mime.indexOf('image/') !== 0) throw new Error('Seules les images sont acceptées.');
  const ext = mime.indexOf('png') >= 0 ? 'png' : 'jpg';
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const now = new Date().toISOString();
    const clean = String(photo.description || '').trim().slice(0, 500);
    const fname = now.slice(0, 10) + '_' + me.id + '_' + Utilities.getUuid().slice(0, 6) + '.' + ext;
    const file = DriveApp.getFolderById(CFG.DEPOTS_FOLDER_ID).createFile(Utilities.newBlob(Utilities.base64Decode(photo.b64), mime, fname));
    const id = Utilities.getUuid();
    sheet_('Depots').appendRow([id, file.getId(), fname, me.id, me.nom_affiche, now, clean, 'en_attente', now]);
    return id;
  } finally { lock.releaseLock(); }
}

/** Dépôts visibles : validés (tous) + les siens (tous statuts) ; l'administrateur voit tout. */
function api_listDepots(code) {
  const me = auth_(code);
  const count = {};
  readComments_().forEach(c => { if (c.statut !== 'supprime') count[c.photo_id] = (count[c.photo_id] || 0) + 1; });
  return readDepots_()
    .filter(d => d.statut === 'valide' || me.role === 'admin' || d.deposant_id === me.id)
    .sort((a, b) => b.date.localeCompare(a.date))
    .map(d => ({ id: d.file_id, depotId: d.id, deposant_id: d.deposant_id, deposant: d.deposant_nom, date: d.date,
                 description: d.description, statut: d.statut, nbComm: count[d.file_id] || 0, mine: d.deposant_id === me.id }));
}

/** Administrateur uniquement : decision = 'valide' | 'refuse' */
function api_depotDecide(code, depotId, decision) {
  const me = auth_(code);
  if (me.role !== 'admin') throw new Error('Réservé à l\'administrateur.');
  if (['valide', 'refuse'].indexOf(decision) < 0) throw new Error('Décision inconnue.');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const d = readDepots_().find(x => x.id === depotId);
    if (!d) throw new Error('Dépôt introuvable.');
    const sh = sheet_('Depots');
    sh.getRange(d._row, 8).setValue(decision);
    sh.getRange(d._row, 9).setValue(new Date().toISOString());
    return true;
  } finally { lock.releaseLock(); }
}

/** Le déposant peut retirer son dépôt tant qu'il n'est pas validé ; l'administrateur peut retirer n'importe lequel. */
function api_depotDelete(code, depotId) {
  const me = auth_(code);
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const d = readDepots_().find(x => x.id === depotId && x.statut !== 'supprime');
    if (!d) throw new Error('Dépôt introuvable.');
    if (me.role !== 'admin' && !(d.deposant_id === me.id && d.statut !== 'valide')) throw new Error('Vous ne pouvez pas retirer ce dépôt.');
    const sh = sheet_('Depots');
    sh.getRange(d._row, 8).setValue('supprime');
    sh.getRange(d._row, 9).setValue(new Date().toISOString());
    try { DriveApp.getFileById(d.file_id).setTrashed(true); } catch (e) {}
    return true;
  } finally { lock.releaseLock(); }
}

/* ---------- Diaporama : résumés et photos masquées par personne ---------- */
/** Tous les résumés : { photo_id: texte } (pour la lecture à voix haute). */
function api_synths(code) {
  auth_(code);
  const v = sheet_('Syntheses').getDataRange().getValues(); v.shift();
  const o = {};
  v.forEach(r => { if (r[0] && r[3]) o[String(r[0])] = String(r[3]); });
  return o;
}

/** Photos masquées du diaporama par la personne connectée. */
function api_bans(code) {
  const me = auth_(code);
  const v = sheet_('Exclusions').getDataRange().getValues(); v.shift();
  return v.filter(r => String(r[0]) === me.id).map(r => String(r[1]));
}

function api_setBan(code, photoId, banned) {
  const me = auth_(code);
  photoId = String(photoId || '');
  if (!photoId) throw new Error('Photo manquante.');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const sh = sheet_('Exclusions');
    const v = sh.getDataRange().getValues();
    let found = false;
    for (let i = v.length - 1; i >= 1; i--) {
      if (String(v[i][0]) === me.id && String(v[i][1]) === photoId) {
        if (banned && !found) found = true; else sh.deleteRow(i + 1);   // doublons éventuels supprimés
      }
    }
    if (banned && !found) sh.appendRow([me.id, photoId, new Date().toISOString()]);
    return true;
  } finally { lock.releaseLock(); }
}

/* ---------- Notifications (APK) et messages de l'administrateur ---------- */
function readMessages_() {
  const v = sheet_('Messages').getDataRange().getValues(); v.shift();
  return v.filter(r => r[0]).map((r, i) => ({ _row: i + 2, id: String(r[0]), date: r[1] instanceof Date ? r[1].toISOString() : String(r[1]), texte: String(r[2]), auteur_id: String(r[3]) }));
}
function config_() {
  const v = sheet_('Config').getDataRange().getValues(); v.shift();
  const o = {}; v.forEach(r => { if (r[0]) o[String(r[0])] = String(r[1]); });
  return o;
}

/** Dernier message de l'administrateur (ou null). */
function lastMessage_() {
  const m = readMessages_();
  if (!m.length) return null;
  m.sort((a, b) => a.date.localeCompare(b.date));
  const x = m[m.length - 1];
  return { id: x.id, date: x.date, texte: x.texte };
}

/**
 * Interrogé par l'APK (toutes les heures) et par le site.
 * sincePhotos : date ISO du dernier contrôle des photos (vide au premier appel -> 0 photo, la date renvoyée sert de point de départ)
 * Renvoie : { now, newPhotos, message:{id,date,texte}|null, app:{versionCode,url,notes} }
 */
function api_updates(code, sincePhotos) {
  auth_(code);
  const now = new Date().toISOString();
  let n = 0;
  if (sincePhotos && /^\d{4}-\d{2}-\d{2}T/.test(String(sincePhotos))) {
    const since = String(sincePhotos).replace(/\.\d+Z$/, 'Z');
    const it = DriveApp.getFolderById(CFG.PHOTOS_FOLDER_ID).searchFiles("createdDate > '" + since + "' and mimeType contains 'image/'");
    while (it.hasNext()) { it.next(); n++; }
    readDepots_().forEach(d => { if (d.statut === 'valide' && d.date > String(sincePhotos)) n++; });
  }
  const cfg = config_();
  return {
    now: now, newPhotos: n, message: lastMessage_(),
    app: { versionCode: parseInt(cfg.apk_version_code, 10) || 0, url: cfg.apk_url || '', notes: cfg.apk_notes || '' }
  };
}

/** Les 10 derniers messages (le plus récent d'abord). */
function api_messages(code) {
  auth_(code);
  return readMessages_().sort((a, b) => b.date.localeCompare(a.date)).slice(0, 10).map(m => ({ id: m.id, date: m.date, texte: m.texte }));
}

function api_postMessage(code, texte) {
  const me = auth_(code);
  if (me.role !== 'admin') throw new Error('Réservé à l\'administrateur.');
  texte = String(texte || '').trim().slice(0, 500);
  if (!texte) throw new Error('Message vide.');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const id = Utilities.getUuid();
    sheet_('Messages').appendRow([id, new Date().toISOString(), texte, me.id]);
    return id;
  } finally { lock.releaseLock(); }
}

function api_deleteMessage(code, id) {
  const me = auth_(code);
  if (me.role !== 'admin') throw new Error('Réservé à l\'administrateur.');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const m = readMessages_().find(x => x.id === String(id));
    if (!m) throw new Error('Message introuvable.');
    sheet_('Messages').deleteRow(m._row);
    return true;
  } finally { lock.releaseLock(); }
}
