# Application Android « Photos famille » (APK)

L'application affiche le site dans une coque Android et ajoute :
- le **micro** et le **choix de photos** (dépôts) ;
- des **notifications**, contrôlées toutes les ~30 minutes quand le téléphone a du réseau :
  - **nouvelles photos** (galerie principale ou dépôts validés) : **au plus une notification par heure** ;
  - **message de l'administrateur** : une notification par nouveau message ;
  - **mise à jour de l'application** : une notification par nouvelle version, avec le lien de téléchargement.
  Trois canaux distincts : chacun peut les couper séparément dans les réglages du téléphone.

⚠️ Ce code n'a PAS pu être compilé ni essayé sur un téléphone par Claude (pas d'outils Android disponibles
dans son environnement). Il est écrit avec soin, mais la première construction peut révéler une erreur à corriger.

## Construire l'APK sans rien installer (GitHub Actions)
Prérequis : le projet est dans un dépôt GitHub (le dépôt peut être privé).
1. Dépôt GitHub > Settings > Secrets and variables > Actions > onglet **Variables** > New repository variable :
   `SITE_URL` = adresse du site, avec `/` final (ex. `https://photos-famille.netlify.app/`).
2. **Clé de signature** (à faire une seule fois, à conserver précieusement : sans elle, les mises à jour de
   l'application seront refusées par Android). Sur un PC avec Java :
   `keytool -genkeypair -v -keystore famille.jks -alias famille -keyalg RSA -keysize 2048 -validity 10000`
   Puis encoder le fichier : PowerShell `[Convert]::ToBase64String([IO.File]::ReadAllBytes("famille.jks"))`
   (Linux/Mac : `base64 -w0 famille.jks`). Dans l'onglet **Secrets**, créer :
   `KEYSTORE_BASE64` (le texte encodé), `KEYSTORE_PASSWORD`, `KEY_ALIAS` (= famille), `KEY_PASSWORD`.
   (Sans ces secrets, l'APK est quand même construit mais signé avec une clé jetable.)
3. Onglet **Actions** > « Construire l'APK Android » > Run workflow > saisir le numéro de version (1 la première fois).
4. À la fin, télécharger l'archive « photos-famille-apk » : elle contient `app-release.apk`.

## Installer sur un téléphone
Envoyer l'APK (Drive, message…), l'ouvrir, autoriser « installer des applis de cette source », installer.
Ouvrir ensuite **son lien personnel** (ou l'application, puis le lien) : l'application mémorise le lien et active
les notifications. Autoriser les notifications et le micro quand Android le demande.

## Publier une mise à jour
1. Modifier le code, puis relancer la construction avec un numéro de version **plus grand**.
2. Mettre l'APK à disposition (par exemple dans le Drive de la famille, partage « toute personne avec le lien »).
3. Dans la feuille `Base-appli-famille`, onglet **Config** : `apk_version_code` = nouveau numéro, `apk_url` = lien de
   téléchargement, `apk_notes` = nouveautés (une phrase). Les téléphones équipés d'une version plus ancienne reçoivent
   la notification dans la demi-heure. (Les changements du **site** n'exigent pas de nouvelle APK : ils s'appliquent seuls.)

## Limites à connaître
- Les notifications ne sont pas instantanées (contrôle ~toutes les 30 minutes ; Android peut les retarder en mode économie d'énergie).
- Android seulement. Sur iPhone, le site fonctionne mais sans ces notifications.
