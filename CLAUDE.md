# Projet PCB — KiCad 10, Windows

**Lire `../KICAD.md` d'abord** (édition manuelle, câblage labels-only,
pièges d'axe Y et de cache de symbole, réglages de projet, commit avant
modification, vérification kicad-cli) — ce fichier-ci ne couvre que ce
qui est spécifique à ce dépôt.

## Origine

Ce dépôt reprend le projet `shield` de `KICAD-C2000-devkit` (dossier
`KICAD-C2000-devkit` du workspace), au moment où son rôle a dépassé le simple
support mécanique des deux devkits : il reçoit maintenant le 11-25V externe
et produit lui-même les rails isolés (5V numérique, 5V/3,3V isolation E/S)
qu'une carte de puissance séparée portait jusque-là. D'où le changement de
nom et de dépôt plutôt qu'une extension sur place — `KICAD-C2000-devkit` reste
inchangé, c'est l'ancien état, pas un doublon à synchroniser.

`doc/spec-devkit.md`, `doc/decisions.md` (décisions #1 à #12) et
`doc/methode-kicad-claude.md` sont copiés tels quels depuis `KICAD-C2000-devkit` :
ils décrivent des choix encore valables (brochage des 64 broches du
connecteur devkit, alternance signal/masse des nappes, etc.). Les décisions
à partir de #13 sont propres à ce dépôt.

## Environnement
- venv à créer : `.venv\Scripts\python.exe`, avec `kicad-python` (kipy)
  installé — pas copié depuis `KICAD-C2000-devkit` (un venv contient des
  chemins absolus, voir `KICAD-EDITION-GROUPEE-KIPY.md`).
- Dépôt : https://github.com/Nicolboy/KICAD-C2000-powershield, branche
  `main`. Clés SSH et procédure de publication : `doc/publier-un-projet.md`.

## Ce qui fait autorité

`doc/spec-devkit.md` reste la référence pour le connecteur devkit 2×28
(brochage, alimentation, JTAG, mécanique) — copié depuis `KICAD-C2000-devkit`,
pas réédité ici. `doc/nappes-shield.md` décrit les quatre nappes **et**
désormais la chaîne d'alimentation du shield lui-même (ce qui a changé
par rapport à `KICAD-C2000-devkit` : plus de carte de puissance séparée).

- Ne jamais éditer `lib/C2000_Devkit_Connectors.kicad_sym` sans mettre à
  jour `doc/nappes-shield.md` dans la foulée (et vice versa) — ce fichier
  n'est **pas généré**, rien ne vérifie automatiquement qu'il suit le
  `.md`. Même piège que documenté dans `KICAD-C2000-devkit/CLAUDE.md`, toujours
  vrai ici.
- Pas de générateur dans ce dépôt (`gen_devkit.py` et consorts restent
  dans `KICAD-C2000-devkit`, ils génèrent les schémas devkit, hors sujet ici).
  `shield.kicad_sch` est édité à la main dès le départ.

## Vérification avant tout commit

Un seul projet dans ce dépôt : `shield` (commande dans `KICAD.md`).

## Décisions de conception et points ouverts

`doc/decisions.md` **fait autorité**. Décisions #1 à #12 héritées de
`KICAD-C2000-devkit` (toujours valables, pas recopiées ici). À partir de #13 :
propres à ce dépôt (migration de la conversion isolée sur le shield,
pourquoi deux NCM3S1205MC séparés, pourquoi les nappes passent en 2×10
IDC).

- Les lire avant de toucher au brochage, aux nappes ou aux types électriques.
- Ne jamais en « optimiser » une sans décision explicite de l'utilisateur.
- Ne pas recopier ces décisions ici : deux copies divergent, c'est
  exactement ce que ce dépôt cherche à éviter.
- Pour une valeur listée comme ouverte : demander, ne pas estimer.
