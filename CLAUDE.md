# Projet PCB — KiCad 10, Windows

**Lire `../KICAD.md` d'abord** (conventions communes à tous les projets
KiCad de l'atelier : câblage labels-only, pièges d'axe Y et de cache de
symbole, réglages de projet par défaut) — ce fichier-ci ne couvre que ce
qui est spécifique à ce dépôt.

## Origine

Ce dépôt reprend le projet `shield` de `KICAD-C2000-shield` (dossier
`shield-c2000` du workspace), au moment où son rôle a dépassé le simple
support mécanique des deux devkits : il reçoit maintenant le 11-25V externe
et produit lui-même les rails isolés (5V numérique, 5V/3,3V isolation E/S)
qu'une carte de puissance séparée portait jusque-là. D'où le changement de
nom et de dépôt plutôt qu'une extension sur place — `shield-c2000` reste
inchangé, c'est l'ancien état, pas un doublon à synchroniser.

`doc/spec-devkit.md`, `doc/decisions.md` (décisions #1 à #12) et
`doc/methode-kicad-claude.md` sont copiés tels quels depuis `shield-c2000` :
ils décrivent des choix encore valables (brochage des 64 broches du
connecteur devkit, alternance signal/masse des nappes, etc.). Les décisions
à partir de #13 sont propres à ce dépôt.

## Environnement
- KiCad 10 doit être OUVERT avec le projet chargé pour l'API IPC (kipy) —
  elle ne marche pas en headless sur cette version.
- venv à créer : `.venv\Scripts\python.exe`, avec `kicad-python` (kipy)
  installé — pas copié depuis `shield-c2000` (chemins absolus, à refaire).
- kicad-cli est dans le PATH.
- Dépôt : à créer sur GitHub (compte Nicolboy) — nom `KICAD-C2000-power`.
  Clé SSH de compte `~/.ssh/github_nicolboy`, sélectionnée par
  `~/.ssh/config`. Ne jamais remettre de `core.sshCommand` dans le dépôt :
  ça contourne cette configuration et fait échouer le push avec
  « denied to deploy key ».

## Règles
- Committer avant toute modification (git).
- PCB: passer par kipy sur l'instance ouverte. Ne jamais éditer
  le `.kicad_pcb` à la main pendant que KiCad est ouvert.
- Schéma: éditer `shield.kicad_sch` directement, KiCad FERMÉ, puis relancer.
  C'est le seul projet du dépôt — pas de version jetable à régénérer.
- Exports et vérifs: kicad-cli uniquement (pas d'export via l'API en v10).
- Après chaque lot de modifs: `kicad-cli pcb drc` / `kicad-cli sch erc`,
  et rapporter les erreurs sans les corriger d'office.

## Ce qui fait autorité

`doc/spec-devkit.md` reste la référence pour le connecteur devkit 2×28
(brochage, alimentation, JTAG, mécanique) — copié depuis `shield-c2000`,
pas réédité ici. `doc/nappes-shield.md` décrit les quatre nappes **et**
désormais la chaîne d'alimentation du shield lui-même (ce qui a changé
par rapport à `shield-c2000` : plus de carte de puissance séparée).

- Ne jamais éditer `lib/C2000_Devkit_Connectors.kicad_sym` sans mettre à
  jour `doc/nappes-shield.md` dans la foulée (et vice versa) — ce fichier
  n'est **pas généré**, rien ne vérifie automatiquement qu'il suit le
  `.md`. Même piège que documenté dans `shield-c2000/CLAUDE.md`, toujours
  vrai ici.
- Pas de générateur dans ce dépôt (`gen_devkit.py` et consorts restent
  dans `shield-c2000`, ils génèrent les schémas devkit, hors sujet ici).
  `shield.kicad_sch` est édité à la main dès le départ.

## Vérification avant tout commit

```
kicad-cli sch erc --exit-code-violations shield.kicad_sch
kicad-cli pcb drc --exit-code-violations shield.kicad_pcb
```

## Décisions de conception et points ouverts

`doc/decisions.md` **fait autorité**. Décisions #1 à #12 héritées de
`shield-c2000` (toujours valables, pas recopiées ici). À partir de #13 :
propres à ce dépôt (migration de la conversion isolée sur le shield,
pourquoi deux NCM3S1205MC séparés, pourquoi les nappes passent en 2×10
IDC).

- Les lire avant de toucher au brochage, aux nappes ou aux types électriques.
- Ne jamais en « optimiser » une sans décision explicite de l'utilisateur.
- Ne pas recopier ces décisions ici : deux copies divergent, c'est
  exactement ce que ce dépôt cherche à éviter.
- Pour une valeur listée comme ouverte : demander, ne pas estimer.
