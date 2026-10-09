# Décisions de conception

Ce document rassemble les choix qui ont l'air d'inefficacités et n'en sont pas.
Chacun a coûté quelque chose — une broche, une piste, un composant — en échange
d'une propriété qu'on ne voulait pas perdre.

Il existe parce que ces choix sont exactement ceux qu'on « optimise » six mois
plus tard, faute de se rappeler ce qu'ils protégeaient. Chaque entrée dit donc
trois choses : la décision, sa raison, et ce qui casse si on la défait.

Ce fichier fait autorité sur les décisions. Le brochage, lui, est décrit dans
[`spec-devkit.md`](spec-devkit.md), les nappes dans
[`nappes-shield.md`](nappes-shield.md).

---

## 1. Le connecteur est identique sur les deux MCU, et ça se paie

**Décision.** Les deux devkits, F280037 et F28P551, exposent le même connecteur
— 56 positions sur 56. Pour y parvenir, les LED sont posées sur les
entrées/sorties **non communes** aux deux boîtiers.

**Pourquoi.** Poser une LED est le besoin le plus trivial de la carte ; c'est
donc lui qu'on sacrifie. En le reléguant sur les broches qui divergent, on
libère toutes les broches communes pour ce qui traverse le connecteur. Le shield
devient indifférent au MCU monté dessus.

**Ce qui casse.** Déplacer une LED sur une broche commune la retire du domaine
partagé et rompt l'interchangeabilité. Il faudrait alors deux shields.

Les quatre divergences, toutes locales à la carte devkit :

| Broche | F280037 | F28P551 |
|---|---|---|
| 27 | VDD 1,2 V, découplage | LED bleue (GPIO20) |
| 28 | VDDIO 3,3 V | LED rouge (GPIO21) |
| 40 | LED rouge (GPIO32) | pastille de test |
| 46 | LED bleue (GPIO39) | VREGENZ à VSS |

La cause profonde est le régulateur 1,2 V : le F28P551 a le sien en interne,
activé par VREGENZ à VSS ; le F280037 en 64 PM non-Q n'a pas cette broche et
demande un LDO supplémentaire. **Toute divergence hors de cette liste est une
erreur.**

---

## 2. PWM3 et PWM4 restent en réserve, et restent des PWM

**Décision.** Les positions B10 à B13 portent `PWM3_A/B` et `PWM4_A/B`, câblées
de bout en bout sur la nappe PWM alors que rien ne s'en sert encore.

**Pourquoi.** Ce sont les deux seules paires complémentaires HRPWM avec temps
mort matériel encore disponibles. La nappe PWM est aussi la seule à alternance
signal/masse pensée pour des fronts rapides — un PWM posé ailleurs n'aurait pas
le même environnement.

**Ce qui casse.** Les réaffecter à une commande lente sous prétexte qu'elles
sont libres consomme une ressource rare pour un besoin que n'importe quel GPIO
satisfait. Les commandes lentes du shield — `Stage1_EN`, `Stage2_EN`, `HV_EN`,
`Discharge` — ont leur propre nappe GPIO, faite pour elles.

---

## 3. Alternance signal / masse stricte 1:1 sur les quatre nappes

**Décision.** Un conducteur sur deux est une masse, sur les quatre nappes. Aucune
ligne d'alimentation ne circule dedans.

**Pourquoi.** C'est de la mesure de courant. Le retour de chaque signal longe le
signal lui-même, la boucle reste petite, la diaphonie s'effondre.

**Ce qui casse.** Récupérer une masse pour y passer un signal de plus donne un
conducteur gratuit et une mesure qui dérive sans qu'on sache pourquoi.

**Exception, voulue.** `VREF_ADC` et `VREFLO_SENSE` sont **adjacents** — A27/A28
au connecteur, positions 6 et 7 de la nappe ADC-2. C'est une paire de référence,
pas deux signaux indépendants : la conversion est ramenée à
(VIN − VREFLO) / (VREFHI − VREFLO). Les séparer par une masse rendrait la mesure
différentielle fausse au lieu de la protéger.

C'est aussi la raison pour laquelle le **+5 V a son propre connecteur**. Les
500 mA de la commande n'ont pas à partager leur retour avec les masses de
référence des voies ADC : c'était précisément le mécanisme d'erreur à éviter.

---

## 4. Chaque shunt sort deux fois : `_MES` filtré, `_CMP` direct

**Décision.** La sortie de chaque AMC0300R est reprise deux fois sur le shield.
Un chemin filtré vers la voie de mesure, un chemin direct vers le comparateur.

**Pourquoi.** Le chemin `_CMP` attaque le CMPSS sans filtre anti-repliement : la
Trip Zone se déclenche sans le retard qu'introduirait le filtre. Et les deux
chemins étant indépendants, un défaut sur le filtre ne désarme pas la
protection.

**Ce qui casse.** Fusionner les deux chemins, ou insérer un filtre sur `_CMP`,
remet le retard dans la boucle de protection et recrée le point de défaillance
unique. Contrainte à respecter : Rs ≤ 50 Ω sur le chemin comparateur.

| Voie | Broche | CMPSS | Rôle |
|---|---|---|---|
| `I_SHUNT1_CMP` | 9 | CMP1_HP0 | seuil DAC interne → Trip Zone, sans filtre |
| `I_SHUNT1_MES` | 13 | — | mesure ADC, filtrée |
| `I_SHUNT2_CMP` | 25 | CMP2_HP3 | chemin direct |
| `I_SHUNT2_MES` | 24 | — | mesure ADC, filtrée |

---

## 5. Les 16 voies ADC sortent toutes, pour 9 nécessaires

**Décision.** Toutes les voies ADC du boîtier sont exportées. Les cinq libres —
A12, A14, A15, A17, A18 — sont câblées jusqu'aux cinq réserves de la nappe
ADC-2, dans le même ordre.

**Pourquoi.** Une voie de mesure ajoutée plus tard se raccorde de bout en bout
sans retoucher une seule carte. La marge est volontaire et son coût est nul :
ces broches ne servaient à rien d'autre.

**Ce qui casse.** « Récupérer » ces positions pour autre chose économise cinq
pistes et transforme le moindre ajout de mesure en nouvelle révision des trois
cartes.

---

## 6. nRESET en drain ouvert uniquement

**Décision.** La ligne `nRESET` (B3) n'est jamais attaquée en push-pull depuis
le shield.

**Pourquoi.** Le MCU tire lui-même cette ligne à zéro sur watchdog et sur
brownout. C'est une ligne à plusieurs maîtres.

**Ce qui casse.** Une sortie push-pull côté shield met en conflit deux étages
lorsque le MCU se réinitialise — courant de court-circuit, et un reset qui
n'aboutit pas.

---

## 7. Point de jonction VSS/VSSA unique

**Décision.** Les masses numérique et analogique se rejoignent en **un seul
point**, près du boîtier, et une seule masse remonte au connecteur.

**Pourquoi.** Deux jonctions créent une boucle, et la boucle capte.

---

## 8. `GND` et `+5V` en `power_in`, avec un `PWR_FLAG` par net

**Décision.** Les broches d'alimentation du connecteur gardent le type
électrique `power_in`, et chaque net porte un `PWR_FLAG`.

**Pourquoi.** Le connecteur alimente bien la carte, mais c'est le brochage qui
fait autorité et il les décrit en entrée. Un net composé uniquement de
`power_in` fait lever `power_pin_not_driven` à l'ERC, même avec un symbole de
masse dessus : le `PWR_FLAG` répond à ça sans toucher au type électrique.

**Ce qui casse.** Passer les broches en `power_out` fait taire l'ERC en mentant
sur la nature du connecteur. C'est la documentation qu'on dégrade pour obtenir
un rapport propre.

---

## 9. Le shield s'édite à la main, les devkits se régénèrent

**Décision.** Les trois schémas n'ont pas le même statut, et il faut le savoir
avant d'ouvrir KiCad :

| Schéma | Édition |
|---|---|
| `devkit_A_F280037.kicad_sch` | **jetable** — reconstruit par `gen_devkit.py` |
| `devkit_B_F28P551.kicad_sch` | **jetable** — idem |
| `shield.kicad_sch` | **édité à la main**, c'est le fichier de travail |

**Pourquoi.** Le générateur du shield amenait à la ligne de départ — connecteurs
posés, alimentations câblées, un `PWR_FLAG` par net — puis s'arrêtait : le
routage des signaux demande des choix de conception qui n'appartiennent pas à un
script. Ce travail commence maintenant, et il se fait dans KiCad.

`gen_shield.py` a donc été **retiré du dépôt**. Il écrivait `shield.kicad_sch`
en entier et l'aurait écrasé au premier `--force`, sans avertissement. Un
amorçage à usage unique qui traîne dans l'arborescence est un piège, pas un
outil. Il reste dans l'historique git (commit `31ecd50`) si l'on veut repartir
d'une feuille blanche.

**Ce qui casse.** Retoucher un schéma de devkit à la main : la modification
disparaît au prochain `gen_devkit.py --force`. Ce qui doit survivre se modifie
dans `src/` ou dans le générateur.

---

## 10. Les schémas source des devkits sont versionnés dans `src/`

**Décision.** `src/devkit_c2000_A_F280037.kicad_sch` et son homologue B sont
suivis par git. `imports/` reste la boîte de réception, ignorée.

**Pourquoi.** `gen_devkit.py` ne fabrique pas ces schémas : il les recopie et
les retouche — nom de projet, symbole MCU carré, recalage sur la grille de
1,27 mm. La vraie source, c'était donc un dossier non versionné. Un dépôt dont
l'argument est que tout se régénère depuis une source ne peut pas laisser cette
source hors de lui-même.

**Ce qui casse.** Remettre `PROJECTS` sur `imports/` : le jour où ce dossier
disparaît, les deux devkits ne sont plus régénérables et rien ne le signale
avant qu'on essaie.

---

## 11. Deux rangées égales de 28, et une clé mécanique obligatoire

**Décision.** Le connecteur fait 28 + 28, pas 24 + 32. Quatre signaux ont été
retirés pour que les deux rangées tiennent : `CMP_OUT2`, `CLB_OUT2`, `GPIO_2` et
`GPIO_3`. Les broches MCU correspondantes — 62, 54, 53 et 55 — deviennent des
pastilles de test. `CMP_OUT1` et `CLB_OUT1` perdent leur indice.

**Pourquoi.** Deux rangées identiques, c'est un seul type de support, une seule
référence à approvisionner, et un dessin de carte symétrique.

**Ce qui casse — et c'est le point à ne pas oublier.** L'asymétrie 24/32
assurait le détrompage toute seule : une rangée de 24 n'entre pas dans un
support de 32. Ce n'est plus le cas. **Il faut une clé mécanique explicite** —
position obturée aux extrémités, ou ergot sur le support. Sans elle, une carte
branchée à l'envers met le +5 V de B2 sur une entrée analogique.

C'est la contrainte la plus facile à oublier et la plus coûteuse à découvrir
après fabrication.

**Trace.** Le basculement date du 2026-08-30, vers 15 h 25. `doc/spec-devkit.md`
a été recalé depuis `lib/C2000_Devkit_Connectors.kicad_sym` — qui faisait
seule autorité pendant l'intervalle — et vérifié position par position, 56 sur
56.

---

## 12. Deux versions de PCB : 2 couches maison, 4 couches externes

**Décision.** Chaque carte est dessinée en deux variantes de fabrication :

| | 2 couches | 4 couches |
|---|---|---|
| Fabrication | maison | externe |
| Pistes mini | 1 mm | au choix du fabricant |
| Vias | 2 mm, perçage 0,8 mm | standard |
| Plan de masse | fragmenté, au mieux | **continu en couche 2** |
| Statut | prototype, mise au point | version de référence |

**Pourquoi.** La version maison permet d'itérer en quelques heures au lieu de
quelques semaines, et de valider la mécanique — encombrements, entraxes,
détrompage — avant d'engager un tirage externe.

**Ce qui ne change pas d'une version à l'autre.** Le schéma, le brochage, le
connecteur. Les deux variantes sortent du **même `.kicad_sch`** : seule la
géométrie du PCB diffère. Dès qu'un signal change d'une version à l'autre, ce
ne sont plus deux variantes mais deux cartes, et la comparaison des mesures ne
veut plus rien dire.

**Ce qu'il faut savoir de la version 2 couches.** Sans plan de masse continu
sous la zone analogique, les retours de courant partagent des chemins et la
mesure en pâtit — c'est l'objet même de la décision §3. Attendre d'elle une
validation fonctionnelle et mécanique, **pas** une caractérisation en bruit ni
un chiffre de précision : ils ne se transposeraient pas à la version 4 couches.

**Conséquence sur l'outillage.** Les règles de conception écrites par
`kicad_gen.py` — piste 1 mm, via 2 mm, perçage 0,8 mm — sont celles de la
fabrication maison. Le projet 4 couches demandera son propre jeu de règles, bien
plus fin. Ne pas appliquer les contraintes maison à la version externe : ce
serait payer un fabricant pour des pistes de 1 mm.

---

## 13. La conversion isolée migre sur le shield, deux NCM3S1205MC séparés, masses secondaires reliées en un point

**Décision.** La carte de puissance séparée (qui portait toute la
conversion et toute l'isolation dans `shield-c2000`) disparaît. Le shield
reçoit directement le 11-25V externe et produit ses propres rails isolés.
Chaque carte DC/DC enfichable porte désormais l'isolation que *sa* fonction
exige — plus de point central qui isole pour tout le monde.

**Pourquoi.** Décision de conception de l'utilisateur, pas une optimisation
de ma part : la carte de puissance figée ne convenait qu'à une seule
fonction de conversion ; des cartes DC/DC enfichables, chacune avec son
isolation propre, couvrent plusieurs fonctions sans redessiner le shield à
chaque fois.

**Composant retenu : NCM3S1205MC-R7** (Murata NCM3 series,
`composants-datasheets/datasheets/isolation/KDC_NCM3.pdf` p.1) — entrée
9-36V (couvre 11-25V), sortie 5V/600mA max (3W), isolation 5000VAC
renforcée. Écarté avant lui : l'OKI-78SR (titre du datasheet : *"Non-Isolated
Switching Regulator DC-DC"*, masses Vin/Vout communes) — ne fait pas ce
qu'on lui demandait.

**Deux exemplaires, pas un seul partagé.** Un NCM3S1205MC pour le domaine
"numérique" (les deux devkits + l'OLED), un second dédié au domaine
"isolation E/S" (LDO 3,3V vers les nappes). Objectif : ne pas coupler le
bruit du CPU/de la radio Wi-Fi de l'ESP32 sur l'alimentation de
l'isolation, et donner à chaque domaine son propre budget de 600mA plutôt
qu'un budget unique partagé entre tout le monde.

**Coupure par destination — trois cavaliers, pas un.** Cavalier C2000,
cavalier ESP32, cavalier E/S — chacun 2 points 2,54mm, côté régulé (5V ou
3,3V), en aval de leur module. Le 11-25V brut reste toujours présent aux
deux NCM3S1205MC, non coupé : avec le module #1 partagé entre les deux
devkits, une coupure individuelle n'a de sens que côté régulé.

**Masses secondaires des deux NCM3S1205MC : reliées, en un point unique —
pas laissées séparées.** Premier réflexe (le mien), corrigé par
l'utilisateur : séparer les deux masses semblait cohérent avec la
séparation de bruit visée par les deux modules, mais le 3V3_ISO alimente le
côté **commande/non-isolé** des isolateurs des cartes DC/DC — c'est ce
côté-là que le C2000 doit pouvoir lire avec une référence commune, sinon le
signal de sortie de l'isolateur n'a plus de référence valable une fois relu
côté numérique. L'isolation galvanique réelle se fait à l'intérieur de
chaque puce isolatrice (AMC03xx etc.), pas entre les deux domaines du
shield. Un point unique (étoile), pas deux jonctions séparées : même
principe que le point de jonction VSS/VSSA unique déjà utilisé sur les
devkits — deux jonctions créeraient une boucle de masse.

**3V3_ISO reste un LDO fixe simple, pas asservi à VDDA/VREF.** Idée
soulevée puis écartée : faire porter la précision ADC des cartes DC/DC par
l'alimentation de l'isolateur plutôt que par sa référence. Un LDO (±1-2%
typique) n'a pas la stabilité d'une vraie référence — ce n'est pas le bon
outil. La vraie solution, déjà disponible sans rien ajouter : les
isolateurs ratiométriques (suffixe "R", type AMC0311R/AMC0302R) ont une
broche REFIN dédiée, à raccorder sur VREF_ADC (déjà présent sur la nappe
ADC-2) — pas sur 3V3_ISO. Protection de sortie prévue malgré tout : une
zener entre 3V3_ISO et masse, en crowbar contre une panne du LDO
(pass-transistor qui lâche et laisse passer le 5V d'entrée vers la sortie —
mode de panne déjà vécu), pas de l'ESD générique.

**2×10 IDC, pas 2×8 breakaway.** Les quatre nappes doivent désormais porter
GND + 3V3_ISO en plus de leurs 16 positions existantes (inchangées). Les
embases IDC à sertir avec détrompeur existent en tailles standard de nappe
(10/14/16/20/26/34 voies) ; 2×9 (18 voies, le minimum strict) n'en est pas
une, 2×10 l'est — et laisse une réserve gratuite, cohérent avec la décision
#5 déjà actée (marge ADC gratuite).

**Ce qui casse.** Relier les masses des deux NCM3S1205MC en plusieurs
points (pas un seul) réintroduit une boucle de masse — c'est précisément
ce que la décision #7 (point de jonction unique) existe pour éviter, ici
appliqué au même problème à un autre endroit du schéma. Asservir 3V3_ISO à
VDDA/VREF pour « résoudre » la précision ADC masque le vrai problème
(REFIN mal câblé sur la carte DC/DC) sans le résoudre, et dégrade la
stabilité du rail d'alimentation de l'isolation pour tout le monde.

## 14. GND/3V3_ISO des nappes en positions 1/2 (pas 17/18), et correction d'un bug de signe Y sur les labels de connecteur

**Décision.** Sur les 4 nappes, `3V3_ISO` passe en position 1 et `GND` en
position 2 (au lieu de 17/18, ajoutées en fin par la décision #13). Les 16
positions signal/masse existantes, inchangées de nom, se décalent
mécaniquement de 2 crans (ancienne position *n* → nouvelle position *n+2*).
Les anciennes positions 17/18 disparaissent, leur rôle repris par les
nouvelles 1/2.

**Pourquoi.** Décision explicite de l'utilisateur, pas une optimisation de
ma part : il a fourni l'image d'un connecteur de référence (`CpuOut1` /
`CTRL_C2000_OUT`, dans `alim-flyback-filament/isolation.kicad_sch` — projet
routé, prêt pour production, lu mais jamais édité) où les deux broches
d'alimentation (`3V3_CTRL`, `GND_CTRL`) occupent les positions 1 et 2,
avant tout signal. Convention à reprendre pour les nappes du shield plutôt
que l'ajout en fin de connecteur retenu dans la décision #13.

**Bug de signe Y trouvé en vérifiant la connexion des labels.** En
positionnant les labels des broches BAT54S ajoutées aujourd'hui, l'ERC a
révélé qu'aucun label de connecteur posé plus tôt dans la session
(nappes, rangées A/B devkit C2000, J1/J3 ESP32) ne touchait réellement sa
broche. KiCad inverse l'axe Y entre les coordonnées locales d'un symbole
(bibliothèque, Y vers le haut) et son placement sur le schéma (Y vers le
bas) : la formule correcte est `monde_y = instance_y − local_y` (le signe
d'addition que j'utilisais était faux), `monde_x = instance_x + local_x`
reste correct. Confirmé en comparant mes positions aux coordonnées réelles
que `kicad-cli sch erc` rapporte pour chaque broche (ex. BAT54S D11 Pin 3,
réellement à (250.00, 11.11) contre (250.00, 28.89) avant correction).
Labels régénérés sur `connecteurs_nappe.kicad_sch` et
`connecteur_devkit.kicad_sch` avec la formule corrigée et le style du
connecteur de référence (`shape bidirectional`, `rotation 180`,
`justify right`), uniformément.

**Ce qui casse.** Toute nouvelle génération de labels sur un connecteur
dans ce dépôt doit utiliser `monde_y = instance_y − local_y`, pas l'inverse
— le bug est facile à reproduire car `kicad-cli sch erc` ne le signale
que comme `label_dangling`/`pin_not_connected` (pas une erreur explicite
de coordonnées), à vérifier systématiquement en croisant quelques broches
avec les coordonnées réelles du rapport ERC avant de considérer un lot de
labels comme posé.

---

## Points ouverts — ne pas combler par une estimation

Ces valeurs manquent. Elles demandent une lecture de datasheet ou une mesure,
pas une approximation plausible.

- Broches de mode de démarrage des deux MCU : à lire dans le manuel technique.
- `VREFHI` en mode externe : plage, impédance de source, courant. Et le choix
  2,5 V ou 3,0 V, selon la pleine échelle des AMC.
- Courant de sortie GPIO : le mode 20 mA du F28P551 n'est pas confirmé dans
  SPRSPC5. Considérer 4 mA — les DPC817 à 5 mA imposeraient alors un buffer
  côté shield.
- État au reset de GPIO39 (LED, PCB F280037).
- Caractéristiques de sortie des AMC0311S et AMC0300R : impédance, pleine
  échelle, bande passante — pour dimensionner les filtres sous Rs ≤ 50 Ω.
- Courant d'entrée du REFIN des AMC0300R, pour le suiveur.
- Nombre de banques Flash des deux MCU, pour le FOTA.
- Débit SCI maximal accepté par l'autobaud du bootloader : il fixe la durée
  d'indisponibilité pendant une mise à jour.
- Matériel LFU dédié sur le F28P551 : documenté pour le F28003x, à confirmer.
- Répartition exacte des plans sur la version 4 couches : masse pleine en
  couche 2 est acquis, la couche 3 reste à décider (alimentation, ou seconde
  masse sous la zone analogique).
- Budget de courant des deux rails 5V des NCM3S1205MC (600mA dispo chacun) —
  #1 face à 2 devkits + OLED, #2 face au LDO 3,3V + la consommation réelle
  des cartes DC/DC côté isolation, inconnue tant qu'aucune carte fille n'est
  spécifiée (§13).
- Modèle de LDO 3,3V exact et valeur de la zener de protection — dépend du
  courant réel tiré par les cartes DC/DC connectées, et du courant de
  court-circuit du LDO en panne une fois choisi (§13).
- Référence exacte du connecteur d'alimentation 11-25V (type, tenue en
  courant) — pas encore choisie.
