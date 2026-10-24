# Photos de famille — mise en route

## 1. Serveur (Apps Script) — compte le compte Google de la famille
1. Aller sur script.google.com > Nouveau projet, le nommer « Photos famille ».
2. Remplacer tout le contenu de Code.gs par le fichier Code.gs fourni, puis enregistrer.
3. Déployer > Nouveau déploiement > type « Application Web » ; Exécuter en tant que : **Moi** ; Qui a accès : **Tout le monde**.
4. Autoriser l'accès quand Google le demande (« Paramètres avancés » > « Accéder à Photos famille » : c'est normal, le script est le vôtre).
5. Copier l'URL de l'application web (finit par /exec) et la transmettre à Claude.

## 2. Site (dossier `site`)
Hébergement statique gratuit (GitHub Pages, Netlify ou Cloudflare Pages) : à choisir.
Mettre l'URL /exec dans `site/config.js`.

## 3. Liens personnels
Chaque membre a un code (onglet Membres de la feuille privée). Son lien : `https://<site>/?c=<code>`.
Désactiver quelqu'un : mettre « non » dans la colonne actif.

## Tests
`python3 test/run_test.py` : test automatique avec un serveur de maquette (aucun accès au Drive).

## Mise à jour du serveur (important après chaque nouvelle version de Code.gs)
Dans le projet Apps Script : Déployer > Gérer les déploiements > (crayon) > Version : « Nouvelle version » > Déployer.
L'adresse /exec reste la même, rien à changer dans le site.

## Dépôts de photos par les membres
- Les photos arrivent dans `Appli-famille-PRIVE\Depots-famille`, statut « en_attente » (onglet Depots de la feuille).
- L'administrateur les valide ou les refuse depuis l'onglet « À valider » de l'appli.

## Nouveautés de cette version (à redéployer côté serveur)
- Diaporama (durée réglable, aléatoire, lecture à voix haute du résumé, photos masquées par personne : onglet `Exclusions`).
- Messages de l'administrateur (onglet `Messages`) et paramètres de l'application (onglet `Config`).
- Application Android : voir `android/LISEZ-MOI-APK.md`.
