# Publier un projet sur GitHub — mémo et prompt

Mémo de poste à poste. Ce qui suit vient de pièges réels, pas d'une liste de
bonnes pratiques générales.

---

## Un poste, une clé

**Une clé privée ne voyage pas.** Copiée sur une clé USB ou envoyée par
messagerie, elle devient une copie qu'on ne contrôle plus, et on perd la
capacité de révoquer un seul poste sans casser les autres.

GitHub accepte autant de clés de compte que l'on veut. Sur un nouveau poste :

```bash
ssh-keygen -t ed25519 -C "contact@nicolasboyer.fr" -f ~/.ssh/github_<poste>
cat ~/.ssh/github_<poste>.pub        # à coller sur github.com/settings/keys
```

Puis dans `~/.ssh/config` :

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_<poste>
    IdentitiesOnly yes
```

**Vérification qui compte** : `ssh -T git@github.com` doit répondre
`Hi Nicolboy!`. S'il répond un **nom de dépôt**, c'est une clé de
*déploiement* — limitée à ce dépôt, et inutilisable ailleurs. Une clé de
déploiement survit d'ailleurs quelque temps à la suppression de son dépôt, et
bloque alors sa propre réutilisation avec un « key already in use » déroutant.

**Piège associé** : un `core.sshCommand` dans le `.git/config` d'un dépôt
court-circuite `~/.ssh/config` et impose une autre clé. Symptôme : `ssh -T`
réussit, `git push` échoue avec « denied to deploy key ».

```bash
git config --local --unset core.sshCommand
```

---

## Prompt de migration

À coller dans Claude Code sur le poste concerné.

```
Je veux publier mes projets de ce poste sur GitHub, compte Nicolboy.
Procède projet par projet, dans cet ordre, et arrête-toi à chaque décision.

1. INVENTAIRE
   Liste les dossiers de projet, leur taille, s'ils sont déjà sous git,
   et ce qu'ils contiennent. Ne touche à rien pour l'instant.
   Dis-moi lesquels te semblent publiables et lesquels ne le sont pas.

2. CE QUI BLOQUE UNE PUBLICATION — vérifie-le avant tout le reste
   - Datasheets et documents constructeur : SOUS COPYRIGHT, jamais
     redistribuables. Cherche tous les PDF, y compris dans l'historique git.
     S'ils sont déjà commités, un `git rm` ne suffit pas : un clone les
     rapatrierait. Il faut purger l'historique.
     À la place, écris un docs/references.md avec les références exactes
     et où les télécharger chez le fabricant.
   - Secrets : clés, jetons, mots de passe, SSID. Cherche aussi dans
     l'historique.
   - Code tiers : SDK, bibliothèques fabricant. Ne les réécris pas et ne
     retire jamais leurs en-têtes de copyright — c'est la condition qui rend
     leur redistribution légale. Dis-moi sous quelle licence ils sont.

3. PRÉPARATION
   - .gitignore : binaires, dossiers de build, config locale d'IDE,
     outillage d'agent (.claude/, .codex/), *.pdf
   - README : ce que fait le projet, son architecture, son ÉTAT RÉEL —
     y compris ce qui ne marche pas encore. Pas de liste de fonctionnalités.
   - LICENSE : demande-moi laquelle. CERN-OHL-S pour du matériel,
     MIT ou Apache-2.0 pour du logiciel.
   - Vérifie que la branche par défaut porte bien le travail à jour.
     Une branche `main` abandonnée pendant que tout vit ailleurs est un
     piège classique : GitHub affiche `main`.

4. AVANT DE POUSSER
   - Commite d'abord tout ce qui traîne non sauvegardé, avec de vrais
     messages qui disent POURQUOI, pas quoi.
   - Fais une sauvegarde : git bundle create ../<nom>.bundle --all
   - Propose-moi un nom de dépôt et attends ma validation.
   - Ne pousse jamais sans me demander.

Règles générales : commite avant toute modification. Si tu trouves une
incohérence entre la documentation et le code, signale-la, ne la corrige
pas d'office.
```

---

## D'où viennent ces points

| Point | Ce qui s'est passé |
|---|---|
| PDF dans l'historique | 13 Mo de documents TI, **95 % du poids** du dépôt firmware. Purgés : 12 Mo → 579 Ko |
| Branche par défaut | `main` figée depuis six semaines pendant que 51 commits vivaient sur `bringup`. GitHub aurait affiché la vieille |
| Commiter d'abord | une modification substantielle non sauvegardée a failli disparaître dans la réécriture d'historique |
| Clé de déploiement | authentifiait, mais refusait de pousser vers un autre dépôt que le sien |
| Licence du code tiers | les fichiers C2000Ware sont sous BSD 3 clauses : redistribuables, **à condition** de garder les en-têtes |

---

## Conventions de nommage

Les dépôts publiés suivent `<OUTIL>-<CIBLE>-<sujet>` :

- `KICAD-C2000-devkit`
- `CCS-C2000-hv-boost`

Un visiteur du profil voit la paire et comprend que l'un est le matériel et
l'autre ce qui tourne dessus. La partie descriptive reste en minuscules avec
des tirets.

**Un nom n'est pas un engagement** : un renommage GitHub conserve l'historique,
les issues et les étoiles, et installe une redirection permanente depuis
l'ancienne URL.
