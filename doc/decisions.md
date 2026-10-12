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
conversion et toute l'isolation dans `KICAD-C2000-devkit`) disparaît. Le shield
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

## 15. Embase OLED en IDC 2 × 8 détrompée, empreintes assignées à tout le projet

**Décision.** Ajout du connecteur `OLED_SPI_2x8` (J10) sur
`connecteur_devkit.kicad_sch` : IDC 2 × 8 à sertir, détrompeur de série,
même famille que les nappes DC/DC mais une taille en dessous (16 broches
contre 20). Brochage repris tel quel du plan constructeur de l'écran
`ER-OLEDM032-1B` (voir `nappes-shield.md`) ; les labels `OLED_CS/RST/DC/
SCK/MOSI` existaient déjà sur les broches natives SPI de l'ESP32, seule
l'embase physique manquait. Broche 7 non étiquetée sur le plan constructeur
fourni : laissée en `NC` par prudence plutôt que supposée masse — à
reconfirmer si le datasheet complet devient disponible.

À la même occasion, assignation d'une empreinte à tous les composants du
projet qui n'en avaient pas (R/C en 0805, BAT54S en SOT-23, connecteurs
2 broches génériques — cavaliers et alimentation — en PinHeader 1×02,
zener de protection en SMC), et création de l'empreinte custom
`lib/NCM3S1205MC.kicad_mod` d'après les cotes du datasheet Murata
(page « Recommended Footprint Details »), ce module n'ayant pas
d'empreinte standard dans les bibliothèques KiCad.

**Pourquoi.** L'export vers le PCB échouait sur tous les composants
(« empreinte non assignée ») : aucune empreinte n'avait encore été choisie
pour ce premier passage PCB, en dehors des connecteurs devkit/ESP32/nappe
qui en portaient déjà une par défaut dans leur symbole.

**Ce qui casse.** Les cotes du NCM3S1205MC comportent une ambiguïté : les
deux sous-cotes horizontales (8,00 / 8,50 mm, barrière d'isolement) ne se
recoupent pas proprement avec la cote totale de 22,00 mm à partir de
l'image seule. Le placement des 4 pastilles utilise uniquement la largeur
totale et la largeur de pastille (valeurs non ambiguës) ; la barrière
d'isolement n'est qu'une zone de sérigraphie, sans effet électrique. À
vérifier visuellement dans l'éditeur d'empreinte PCB contre la page 10 du
datasheet avant fabrication.

---

## 16. Filtre EMC NCM3S1205MC : étage d'entrée posé, étage de sortie volontairement omis

**Décision.** Sur `dc.kicad_sch`, ajout de l'étage d'entrée du filtre EMC
recommandé par le datasheet (p.8, « EMC Filtering and Spectra ») pour
chaque instance : L1/L2 (22 µH, série sur VIN_PWR/retour) + C26/C27
(22 µF) + C28 (220 pF) pour U2, L3/L4 + C31/C32 + C33 pour U3 — composants
caractérisés dans `composants-datasheets/data/shield-power/ncm3s1205mc.yaml`
(`recommended_components`). L'étage de sortie (C4/C5, 470 pF, un par
instance soit C29/C30 et C34/C35) a été posé puis retiré : ni ces deux
paires de composants ni leurs labels ne figurent dans le schéma final.

**Pourquoi.** Le NCM3S1205MC est choisi spécifiquement pour sa faible
capacité d'entrée/sortie — paramètre déterminant pour une alimentation
isolée destinée à des lignes qui traversent la barrière. Rajouter 470 pF
en parallèle côté sortie va à l'encontre de ce choix, même si ces deux
condensateurs ne pontent pas la barrière primaire/secondaire (vérifié par
coordonnées : C29/C30 sont posés entre `5V_ISO` et `GND`, C34/C35 entre
`5V_NUM` et `GND`, tous deux cote secondaire uniquement — donc sans effet
sur la capacité primaire/secondaire proprement dite, mais la décision
porte sur le principe, pas seulement sur la topologie).

**Ce qui casse.** Le datasheet qualifie ces 470 pF comme faisant partie du
filtre EMC nécessaire pour la conformité EN 55032 Classe B — leur absence
n'a pas été compensée par une autre topologie. Si une non-conformité EMC
apparaît en essai, ce point est le premier candidat à rouvrir, en
réévaluant alors le compromis capacité/conformité plutôt qu'en les
rajoutant par défaut.

---

## 17. Routage des quatre nappes, reséquencement signal/masse, et deux nappes supplémentaires (GPIO-2, COM)

**Décision.** Les connecteurs J1-J4 (ADC-1, ADC-2, PWM, GPIO) n'avaient
jusqu'ici que leurs broches d'alimentation câblées (`3V3_ISO`/`GND` —
vérifié : exactement 40 `global_label` dans `connecteurs_nappe.kicad_sch`,
10 par connecteur, zéro signal réel). Cette décision couvre trois choses à
la fois : (a) le câblage des signaux restés en souffrance depuis la
decision #9, (b) un changement de convention de position qui gagne une
broche signal par connecteur sans changer sa taille, (c) l'ajout de deux
connecteurs pour couvrir les besoins génériques (logique de réserve, bus
de communication) annoncés par l'utilisateur mais absents des quatre
nappes d'origine.

**(a) Câblage.** Chaque broche signal de J1-J4 reçoit maintenant le
`global_label` que la documentation promettait depuis la decision #13
(`Vin`, `PWM1_A`, `Stage1_EN`, etc.) — toujours aucune ligne de wire,
uniquement des labels posés aux coordonnées réelles de chaque broche
(vérifié par `kicad-cli sch erc`, piège d'inversion d'axe Y de la decision
#14 surveillé).

**(b) Reséquencement signal (impair) / masse (pair), à partir de la
broche 3.** Avant : position 1 `3V3_ISO`, 2 `GND`, 3 `GND` (deuxième masse
consécutive), puis alternance à partir de 4 — 8 emplacements signal
exploitables sur 20 broches, les positions 19/20 jamais définies. Après :
position 1 `3V3_ISO`, 2 `GND`, puis strictement signal sur les impairs (3,
5, 7… 19) et masse sur les pairs (4, 6… 20) — 9 emplacements signal, les
20 broches toutes définies. Exception volontaire, déjà actée (decision
#3) : la paire de référence `VREF_ADC`/`VREFLO_SENSE` (ADC-2) reste
adjacente, en 7/8, la position 8 cédant sa masse pour cette seule paire.

**Pourquoi reséquencer plutôt qu'agrandir le connecteur.** Mon premier jet
proposait un connecteur 2×13 (26 voies, palier standard suivant) pour
donner de la marge à GPIO et à un nouveau connecteur de bus. Écarté par
l'utilisateur : pas de 2×13 en stock, tout doit rester en 2×10. Le
reséquencement donne la même marge (une broche signal de plus par
connecteur) sans changer de référence de connecteur.

**(c) Deux connecteurs de plus plutôt qu'un connecteur agrandi : GPIO-1 /
GPIO-2, et COM.** But générique annoncé par l'utilisateur : le devkit+
shield doit pouvoir piloter n'importe quelle carte fille future (PWM,
logique, ADC, bus I2C/SPI/UART/CAN/Modbus), pas seulement les deux cartes
connues aujourd'hui (convertisseur 0-500V, `alim-flyback-filament`). Deux
besoins non couverts par les quatre nappes d'origine :

- **Logique de réserve.** GPIO (renommé GPIO-1) est désormais plein — 8
  signaux d'origine + `CLB_OUT` (broche B27 du connecteur devkit,
  orpheline jusqu'ici, aucune nappe ne l'exportait) = 9 emplacements sur
  9. Une carte future dont le besoin en E/S logique ne ressemble à rien
  d'anticipé ici n'a nulle part où se brancher sans **GPIO-2**, un
  sixième connecteur 2×10 entièrement en réserve.
- **Bus de communication.** `UART_TX`/`RX`, `SPI_CLK`/`SIMO`/`SOMI`/`STE`,
  `CAN_TX`/`RX` existent déjà comme `global_label` sur le connecteur
  devkit (`connecteur_devkit.kicad_sch`) mais n'étaient câblés sur aucune
  nappe — **COM**, cinquième connecteur neuf, les expose en logique 3,3V
  brute (8 signaux, 1 réserve). Les transceivers CAN et RS-485/Modbus
  restent sur la carte fille qui en a besoin (décision de l'utilisateur,
  cohérente avec la decision #13 : chaque carte porte l'isolation que *sa*
  fonction exige) — le shield ne route jamais de différentiel.

**Une carte fille ne peuple que les connecteurs dont elle a besoin.**
Précision explicite de l'utilisateur : les six connecteurs ne sont pas un
paquet tout-ou-rien. Exemple immédiat : le convertisseur 0-500V utilise
ADC-1, ADC-2, PWM en entier et seulement GPIO-1 — ni GPIO-2, ni COM. Un
connecteur non peuplé côté carte fille ne coûte rien côté shield.

**Désignateurs J13/J14, pas J5/J6.** `used_designators` dans
`shield.kicad_pro` réservait déjà J1-J9 et J11-J12 (connecteurs devkit,
ESP32, OLED J10, alimentation) avant même de toucher à ce fichier —
confirmé par une recherche `property "Reference" "J\d+"` sur tous les
schémas du projet. GPIO-2 et COM prennent J13 et J14 pour ne pas entrer en
collision avec un composant existant ailleurs dans le projet.

**Bibliothèque externe synchronisée.** `lib/C2000_Devkit_Connectors.kicad_sym`
mis à jour en parallèle de la copie embarquée dans
`connecteurs_nappe.kicad_sch` (symboles `NAPPE_ADC1`/`ADC2`/`PWM` avec le
nouveau séquencement, `NAPPE_GPIO` renommé `NAPPE_GPIO1`, `NAPPE_GPIO2` et
`NAPPE_COM` ajoutés) — sinon `kicad-cli sch erc` lève `lib_symbol_issues`
(symbole introuvable en bibliothèque), et toute « Update Symbols from
Library » future écraserait silencieusement le travail de cette décision.

**Ce qui casse.** Reproduire le reséquencement sur un connecteur qui
n'existe pas encore sans relire cette décision referait l'erreur
d'origine (masse en double avant le premier signal). Ajouter un signal à
GPIO-1 ou à COM sans vérifier qu'une réserve existe déjà (`réserve
GPIO2-*`/`réserve COM-1`) revalide une nouvelle révision du connecteur au
lieu de consommer la marge déjà prévue.

**Point relevé, non résolu ici — hors périmètre.** `Stage1_EN`,
`Stage2_EN`, `HV_EN` et `Discharge` (GPIO-1) ne sont reliés à aucune
broche du connecteur devkit : ces noms viennent de l'ancien firmware
TMS320F28027 (GPIO16/17/32/5), et la nouvelle carte de conversion 0-500V
— nouveau MCU, projet séparé — n'a pas encore choisi ses broches. ERC :
`isolated_pin_label` sur les quatre, attendu, à lever quand ce choix sera
fait. De même, les réserves ADC (`ADC_8` à `ADC_12` côté connecteur
devkit) restent elles aussi isolées, un gap pré-existant à cette session.

---

## 18. Découplage 100 nF sur chacune des six nappes

**Décision.** Un condensateur 100 nF entre `3V3_ISO` et `GND`, posé au
plus près de chaque connecteur de nappe (`C29`/`C30`/`C34`/`C35`/`C42`/
`C43` pour J1/J2/J3/J4/J13/J14) — en plus du découplage par IC déjà en
place, pas à sa place.

**Pourquoi un découplage aux deux bouts.** Chaque carte fille découple
déjà ses propres IC (règle déjà en place dans cet atelier). Côté shield,
un bypass à chaque sortie de nappe — plutôt qu'un seul point au LDO —
limite qu'une carte bruyante sur une nappe (ex. un transceiver CAN sur
COM) ne remonte sur `3V3_ISO` et ne perturbe une carte sensible sur une
autre nappe (ADC-1/ADC-2) : même logique que la séparation déjà faite en
decision #13 entre les deux domaines d'alimentation (numérique vs
isolation E/S).

**Valeur.** 100 nF, pas 1 µF ni 10 µF : `3V3_ISO` n'alimente que le côté
commande/non-isolé des isolateurs des cartes filles (decision #13), pas
un étage de puissance — dizaines de mA par carte, pas d'ampères. Un bulk
plus généreux côté carte fille (hors périmètre du shield) reste
pertinent si une carte précise tire plus que ça ; pas justifié par
défaut ici.

**Ce qui casse.** Centraliser le découplage à un seul point (LDO
uniquement) réintroduit le risque de couplage inter-cartes que ce choix
évite. Monter à 1 µF ou plus sans carte fille connue identifiant un
besoin réel serait du surdimensionnement sans raison.

---

## 19. Correction du brochage ADC-2, et protection des 11 signaux nappe nouvellement câblés

**Décision.** Deux problèmes trouvés en relisant le travail de la
decision #17 après coup.

**(a) ADC-2 oubliait `I_SHUNT1_CMP`/`I_SHUNT2_CMP`.** Seule la voie
filtrée (`I_shunt1`/`I_shunt2`, chemin `_MES`) avait été câblée ; la
decision #4 impose pourtant que chaque shunt sorte **deux fois** — un
second chemin, direct et sans filtre, vers le comparateur CMPSS. Les deux
signaux manquants existaient déjà, isolés, au connecteur devkit (ERC :
`isolated_pin_label`). Corrigé en consommant 2 des 6 réserves d'ADC-2
(réserves : 6 → 4), sans les coller à `I_shunt1`/`I_shunt2` : les deux
chemins doivent rester électriquement indépendants, l'adjacence sur le
connecteur n'aide à rien et mélange visuellement ce qui ne doit pas se
confondre — contrairement à l'exception `VREF_ADC`/`VREFLO_SENSE`, qui
est une vraie paire de référence.

**(b) 11 signaux câblés en decision #17 n'avaient aucune protection**,
alors que tout le reste du connecteur devkit en a une. Vérifié en
comparant chaque signal de nappe à son équivalent `_MCU` dans les trois
feuilles de protection existantes (23 trios BAT54S + R + 100 pF, un par
signal, déjà en place avant la decision #17) : `CLB_OUT`, `UART_TX`,
`UART_RX`, `SPI_CLK`, `SPI_SIMO`, `SPI_SOMI`, `SPI_STE`, `CAN_TX`,
`CAN_RX` n'avaient aucun trio, et les deux signaux du point (a) non plus
une fois ajoutés.

**Nouvelle feuille `protection_nappe.kicad_sch`**, 11 trios, copiés
composant par composant et label par label depuis un trio réel
(`protection_devkit3.kicad_sch`, le plus petit des trois feuilles
existantes) plutôt que redessinés — même principe que
`KICAD-EDITION-GROUPEE-KIPY.md` §1 (extraire le gabarit, pas le
re-deviner). Topologie identique partout : BAT54S (clamp vers `GND`/
`3V3_PROT`) + R série + C 100 pF shunt vers `GND`, entre le nom brut
côté nappe et son équivalent `_MCU` côté connecteur devkit — **9 des 11
avec R = 100 Ω** (identique aux 23 trios déjà posés), **`I_SHUNT1_CMP`/
`I_SHUNT2_CMP` avec R = 22 Ω** : la decision #4 impose Rs ≤ 50 Ω sur ce
chemin, que 100 Ω dépasserait. Le condensateur est conservé malgré la
contrainte « sans filtre » de la decision #4 — décision explicite de
l'utilisateur, pas une optimisation de ma part : avec R = 22 Ω, le pôle
RC du 100 pF tombe à 2,2 ns (au lieu de 10 ns avec 100 Ω), soit ~7 % du
budget Trip Zone de 30 ns, jugé acceptable plutôt que de retirer le C.

**Chaque connecteur devkit protégé doit porter le nom `_MCU`, pas le nom
brut.** Conséquence directe de la convention déjà en place sur les 23
trios existants (`Vin` côté nappe → trio → `Vin_MCU` côté connecteur
devkit, jamais l'inverse) : avant d'ajouter un trio pour un signal,
son label au connecteur devkit (`connecteur_devkit.kicad_sch`) doit
d'abord passer du nom brut au nom `_MCU` — sinon le trio protège un
signal qui ne va nulle part. Fait pour les 9 signaux du point (b)
(`CLB_OUT_MCU`, `UART_TX_MCU`, etc.).

**Erratum (même session) : le renommage ci-dessus avait été oublié pour
`I_SHUNT1_CMP`/`I_SHUNT2_CMP`** — leur label isolé au connecteur devkit
était resté sous son nom brut après la création du trio. Conséquence :
le nom brut étant partagé par un `global_label` KiCad entre la feuille
nappe et la feuille connecteur devkit, les deux bouts du trio
(`I_SHUNT1_CMP` côté nappe, `I_SHUNT1_CMP_MCU` théorique côté MCU)
pointaient en fait vers le **même nœud électrique** que l'entrée brute —
le trio BAT54S/R/C existait sur le PCB mais était court-circuité par ce
doublon de nom, invisible à l'ERC (fusionner deux labels de même nom
n'est pas une erreur de connectivité, juste un mauvais choix de nom).
Corrigé en renommant les deux labels du connecteur devkit en
`I_SHUNT1_CMP_MCU`/`I_SHUNT2_CMP_MCU`. **Nécessite un nouveau "Update
PCB from Schematic"** : la mise à jour précédente du PCB a eu lieu
pendant que le bug était encore présent, donc le pad concerné du
connecteur devkit porte encore le mauvais nom de net sur le fichier
`.kicad_pcb` tant que la resynchronisation n'a pas été refaite.

**Second erratum (même session, corrigé deux fois) : l'exception
d'adjacence 7/8 elle-même était le problème, pas seulement la position
de `I_SHUNT1_CMP`.** Premier essai de correction (insuffisant) : garder
`VREF_ADC`/`VREFLO_SENSE` adjacents en 7/8 et seulement déplacer
`I_SHUNT1_CMP`/`I_SHUNT2_CMP` de 9/11 vers 11/13 pour les éloigner de
cette zone non blindée. L'utilisateur a corrigé : la position 8 ne doit
pas être une exception du tout, elle doit porter une masse comme
n'importe quelle position paire. Correction définitive : la paire de
référence `VREF_ADC`/`VREFLO_SENSE` est déplacée en positions **3/5**
(entourées de masse des deux côtés — leur lien électrique passe par le
suiveur rail-to-rail du shield, pas par leur proximité sur la nappe, donc
l'adjacence n'apportait rien) ; `I_shunt1`/`I_shunt2`, qui occupaient
3/5, reculent en **7/9** (toujours entourées de masse, toujours
adjacentes entre elles via la masse de la position 8) ; `I_SHUNT1_CMP`/
`I_SHUNT2_CMP` restent en **11/13**. Alternance stricte masse/signal sur
tout le connecteur, **zéro exception**. Réserves : 4 → **3** (la
position 9, ancien slot libre, porte maintenant `I_shunt2`) ;
renumérotées `RESERVE_ADC2_1`-`3` en positions 15/17/19. Table mise à
jour dans `doc/nappes-shield.md`, y compris le paragraphe général qui
décrivait l'exception 7/8 comme acceptée. Comme pour le premier erratum,
nécessite un nouveau "Update PCB from Schematic" — et cette fois les
tracés déjà routés de `I_shunt1`/`I_shunt2` sur le PCB devront être
repris physiquement : changer le net d'un pad existant ne déplace pas
la piste déjà posée vers le nouveau pad, KiCad va signaler un
désaccord de net sur la piste existante qu'il faudra re-router à la
main vers les nouvelles broches 7/9.

**Désignateurs** (balayage de tous les `.kicad_sch`, aucun trou en
dessous du max avant cette décision) : `D25`-`D35`, `R24`-`R34`,
`C44`-`C54`. `netclass_patterns` étendu : les 9 nets `_MCU` standards et
`CLB_OUT` (bare, oublié lors de la classification précédente) rejoignent
`Rapide` ; `I_SHUNT1_CMP_MCU`/`I_SHUNT2_CMP_MCU` rejoignent `Analogique`
(cohérent avec leurs homologues bruts, déjà classés).

**Ce qui casse.** Ajouter un trio pour un signal sans renommer le label
du connecteur devkit en `_MCU` laisse le trio protéger un nœud qui ne
va nulle part — invisible à l'œil, détecté seulement par
`kicad-cli sch erc` (`isolated_pin_label` qui persiste). Copier un trio
standard (R = 100 Ω) pour un futur chemin comparateur direct
reproduirait l'erreur que `I_SHUNT1_CMP`/`I_SHUNT2_CMP` viennent de
corriger — relire la decision #4 avant toute nouvelle protection sur un
chemin Trip Zone.

**Vérification.** `kicad-cli sch erc` par type de violation (méthode
`KICAD-EDITION-GROUPEE-KIPY.md` §6) : les 11 `isolated_pin_label`
corrigés par cette décision ont disparu (restent les 9 déjà connus,
hors périmètre — point (a) de la decision #17) ; `pin_not_connected`
baisse de 2 (réserves ADC-2 consommées) ; `endpoint_off_grid` augmente
de 33 (un par composant neuf), cohérent avec le même défaut déjà présent
sur les 23 trios existants, pas une régression propre à cette décision.

---

## 20. Bloc CLB du F28P551 utilisé comme mini-CPLD : 4 sorties neuves, nappe GPIO-2 renommée "logic", 5 entrées partagées

**Décision.** Le CLB (Configurable Logic Block) du F28P551 est utilisé comme
un bloc de logique programmable généraliste (mini CPLD), pas uniquement pour
le chemin `CLB_OUT` existant. Ça demande des broches MCU neuves, un devkit
déjà routé modifié en conséquence, et une nappe entièrement repensée.

**(a) Modification de `devkit_B_F28P551`** (carte figée, production-ready —
modifiée malgré la règle habituelle, décision explicite de l'utilisateur,
voir mémoire `kicad_frozen_production_boards`). Quatre masses du connecteur A
sacrifiées pour sortir quatre GPIO jusque-là non câblés sur le connecteur
56 broches : A4→`Stage2_EN` (GPIO20), A10→`HV_EN` (GPIO21), A13→`Stage1_EN`
(GPIO9), A16→`Discharge` (GPIO41). Choix des positions : les deux broches
pleinement isolées (masse des deux côtés, A13/A16) reçoivent les signaux
les plus sensibles côté vitesse — `Stage1_EN` (le seul des quatre pilotable
en matériel par le CLB, voir point (c)) et `Discharge` (coupure de sécurité) ;
`Stage2_EN`/`HV_EN` (commandes d'activation, bascule rare) héritent des
positions plus modestement blindées A4/A10, voisines de mesures ADC-1 lentes
plutôt que du cluster shunt/comparateur. Vérifié via `pin_map.h` : des 4
GPIO, un seul (GPIO9, `OUTPUTXBAR6`) a un chemin X-bar de sortie en
silicium — les trois autres (`GPIO20`, `GPIO21`, `GPIO41`) n'en ont
structurellement aucun, dans aucune configuration. Ce n'est pas un défaut :
les 4 signaux sont de simples sorties GPIO pilotées par le logiciel (le CLB
peut influencer la décision via le registre `CLB_GP_REG` et une bascule
matérielle sur `Stage1_EN` seulement, sans avoir besoin de driver les 3
autres). Report obligatoire sur `connecteur_devkit.kicad_sch` (symboles
ET labels réels, les deux copies — bibliothèque externe
`lib/C2000_Devkit_Connectors.kicad_sym` incluse) : même reséquencement que
le devkit, pour que les deux connecteurs mâle/femelle restent en accord.

**(b) Renommage en logique négative, `nRESET`→`~{RESET}`,
`GPIO_1`/`nFAULT_MCU`→`~{FAULT_MCU}`** (fait par l'utilisateur sur le devkit
et `connecteur_devkit.kicad_sch`). **Erratum découvert en vérifiant** :
`protection_devkit3.kicad_sch` gardait l'ancien nom `nFAULT_MCU` sur les 3
étiquettes du trio existant (D23/R22/C22) — le renommage du connecteur avait
silencieusement coupé ce trio du reste du circuit (`isolated_pin_label` sur
`~{FAULT_MCU}`, invisible autrement, même catégorie de bug que l'erratum
ADC-2 de la decision #19). Corrigé en renommant les 3 étiquettes du trio en
`~{FAULT_MCU}`.

**(c) Quatre trios de protection neufs**, `D36`/`R35`/`C55` (`Stage1_EN`),
`D37`/`R36`/`C56` (`Stage2_EN`), `D38`/`R37`/`C57` (`HV_EN`),
`D39`/`R38`/`C58` (`Discharge`) — gabarit identique aux 23+11 trios
existants (BAT54S + R + 100 pF), mais **R = 10 Ω** au lieu de 100 Ω : les
quatre signaux sont classés `Rapide`, décision explicite de l'utilisateur
plutôt qu'une optimisation de ma part. Pôle RC du 100 pF à 159 MHz (au lieu
de 15,9 MHz avec 100 Ω) — filtrage minimal, cohérent avec des commandes de
sécurité où le délai de la protection elle-même ne doit pas dominer le temps
de réponse.

**(d) Nappe GPIO-2 renommée nappe "logic"** (`NAPPE_GPIO2`→`NAPPE_LOGIC`,
symbole + bibliothèque externe + instance `J13`). Les 9 réserves
(`RESERVE_GPIO2_1`-`9`) devenues `CLB_Out_1`-`4` / `CLB_In_1`-`5` — noms
**cosmétiques sur le symbole connecteur uniquement**, même principe que
`GPIOxx/fonction` côté devkit : l'étiquette électrique réelle reste le vrai
nom de signal, pour qu'il fusionne avec les autres nappes qui le portent
déjà. Répartition : les 4 sorties neuves du point (c) sur `CLB_Out_1`-`4`
(déjà présentes aussi sur la nappe GPIO-1, positions 3/5/7/9, en attente
depuis la decision #17 — **un signal peut vivre sur deux nappes à la fois**,
un seul point d'accès réellement utilisé selon la carte fille branchée) ;
cinq signaux déjà protégés ailleurs tapés en entrée sur `CLB_In_1`-`5` :
`CAN_RX`/`CAN_TX` (nappe COM) et `PWM2_B`/`PWM3_B`/`PWM4_B` (nappe PWM) —
piqués côté nom brut (avant leur trio d'origine), donc le même trio protège
les deux nappes à la fois, sans sacrifice : CAN continue de fonctionner,
les trois canaux PWM gardent leur voie complémentaire intacte. `CMP_OUT`
(6e candidat identifié en cours de route) écarté pour tenir le compte à 5
entrées exactement.

**Désignateurs** : `D36`-`D39`, `R35`-`R38`, `C55`-`C58` (aucun trou en
dessous du max avant cette décision). `netclass_patterns` étendu : les 4
signaux neufs (bruts et `_MCU`) rejoignent `Rapide`. `used_designators`
mis à jour (`C42-58`, `R1-38`).

**Ce qui casse.** Oublier de reporter le reséquencement du devkit sur
`connecteur_devkit.kicad_sch` referait exactement l'erratum (b) : un nom de
label qui ne correspond plus des deux côtés du même connecteur, invisible
tant qu'on ne compare pas net par net. Ajouter une future sortie CLB sur
`GPIO20`/`GPIO21`/`GPIO41` est impossible en silicium — relire le point (a)
avant d'essayer.

**Vérification.** `kicad-cli sch erc` par type : `isolated_pin_label` 9 → 5
(disparition de `Stage1_EN`/`Stage2_EN`/`HV_EN`/`Discharge`, qui restaient
les 9 signaux déjà connus en pas encore reliés — 5 subsistent, les réserves
ADC libres `ADC_8`-`ADC_12`, hors périmètre) ; `pin_not_connected` baisse de
9 (les 9 broches de la nappe logic désormais câblées) ; aucune nouvelle
catégorie de violation.

---

## 21. Empreinte NCM3S1205MC remplacée par le modèle téléchargé SnapEDA (symbole + footprint), broches inchangées

**Décision.** L'utilisateur a téléchargé le modèle KiCad du Murata
NCM3S1205MC-R7 publié par SnapEDA
(`composants-datasheets/datasheets/NCM3S1205MC/`, symbole
`NCM3S1205MC-R7.kicad_sym` + empreinte `CONV_NCM3S1205MC-R7.kicad_mod`,
Murata via Mouser). Décision explicite (question posée, réponse
« remplacer symbole + footprint ») plutôt qu'une estimation : les deux
géométries disponibles pour ce composant divergent et aucune des deux
n'est vérifiée par une capture d'empreinte physique (R15 de
`composants-datasheets/.claude/rules/data-yaml.md`) — l'ambiguïté n'est
donc pas résolue, seulement déplacée vers une source différente.

**(a) Footprint** (`lib/NCM3S1205MC.kicad_mod`, et copie figée dans
`shield.kicad_pcb` pour U2 et U3, dual-copy comme pour les symboles de
connecteur). Géométrie remplacée par celle du modèle SnapEDA : pastilles
à `x=±11.0mm` (au lieu de `±9.9mm`), pas vertical de 6,75mm inchangé,
numérotation 1-4 préservée (même correspondance pin-fonction qu'avant :
1=`-VIN`, 2=`+VIN`, 3=`+VOUT`, 4=`-VOUT`). Contour sérigraphie à 8
segments (encoches au droit de chaque pastille, le style SnapEDA) plutôt
que l'ancien contour à une seule encoche coin. Nom de l'empreinte
conservé (`NCM3S1205MC`, pas `CONV_NCM3S1205MC-R7`) pour ne pas toucher
la propriété `Footprint` des instances U2/U3. Les deux zones de garde
(keepout anti-coulée) du modèle SnapEDA n'ont **pas** été reportées :
aucune zone n'existe ailleurs dans ce board, les reproduire à la main
sans exemple local à valider aurait été un risque de syntaxe gratuit pour
un gain cosmétique (anti-coulée de cuivre sous le boîtier). Vérifié : U2
et U3 sont posés mais **non routés** (zéro segment sur `U2_VINF`,
`U2_GNDF`, `U3_VINF`, `U3_GNDF`, `5V_ISO`, `5V_NUM` à proximité de ces
deux footprints) — le changement de position des pastilles ne casse donc
aucune piste existante. `kicad-cli pcb drc` : 412 violations avant et
après, catégories identiques.

**(b) Symbole** (`lib/Power_Parts.kicad_sym`, et copie embarquée dans
`dc.kicad_sch`). Seuls les **noms** de broches sont repris du modèle
téléchargé (`-Vin`→`-VIN`, `+Vin`→`+VIN`, `+Vout`→`+VOUT`,
`-Vout`→`-VOUT`) — **position, longueur et type électrique des broches
inchangés**. Deux raisons, vérifiées toutes les deux avant de trancher,
pas supposées :
- `dc.kicad_sch` n'est **pas** en labels-only comme les nappes : des
  fils réels relient U2/U3 au filtre EMC local (L1-4/C26-33/C40-41).
  Reprendre aussi les coordonnées de broches du modèle SnapEDA (qui
  élargit le symbole de 5,08mm de chaque côté) aurait désaligné ces fils
  de leur point de connexion sans qu'aucun outil ne le signale avant
  ouverture dans KiCad.
- Le modèle SnapEDA type ses broches d'alimentation en `input`/`output`
  simples plutôt qu'en `power_in`/`power_out`. Testé : adopter ce typage
  fait disparaître 3 `power_pin_not_driven` (U2/U3 broches 1/2, attendu)
  mais en fait apparaître un nouveau sur `J1 Pin 2 [GND]` — `+VOUT` (U2
  ET U3, broche 3) sert de driver implicite du net `GND` entier via son
  type `power_out` ; le repasser en `output` simple retire ce rôle de
  driver à l'échelle du projet. Ce n'est pas un artefact du modèle
  téléchargé, c'est un choix électrique déjà en place dans ce dépôt
  (sortie flottante, référence de masse choisie côté secondaire) —
  revert complet des 4 types de broche. `kicad-cli sch erc` : 200
  violations avant et après l'édition finale, catégories et comptes
  identiques (vérifié par diff).

**Vérification physique.** Cotes et pastilles du modèle SnapEDA confirmées
par l'utilisateur contre la page 10 du datasheet Murata (KDC_NCM3_A01) —
correspondance exacte. Le point ouvert hérité de la decision #15 est
clos : c'est désormais ce footprint, vérifié, qui fait référence pour
NCM3S1205MC dans ce dépôt.

**(c) Modèle 3D.** Absent du téléchargement SnapEDA (ni fichier `.step`
dans `composants-datasheets/datasheets/NCM3S1205MC/`, ni nœud `(model ...)`
dans `CONV_NCM3S1205MC-R7.kicad_mod`). Récupéré directement chez Murata :
page officielle `murata.com/en-us/products/power/3d`, fichier
`mps_dcdc_nmc3s_mc_a.step` (SolidWorks 2023, STEP AP214, ~16,6 Mo) — un
seul modèle couvrant toute la famille de boîtier NCM3S-MC (cohérent avec
le datasheet, qui ne publie qu'un seul plan d'empreinte pour toute la
série). Stocké dans `lib/NCM3S1205MC.step`, référencé depuis
`lib/NCM3S1205MC.kicad_mod` et les deux copies figées U2/U3 dans
`shield.kicad_pcb` via `${KIPRJMOD}/lib/NCM3S1205MC.step`, offset/scale/
rotate à l'identité. Alignement visuel dans l'éditeur 3D de KiCad non
vérifié par Claude (pas de rendu 3D disponible en CLI) — à confirmer par
l'utilisateur à l'ouverture. Taille notable pour un dépôt git (16,6 Mo,
premier modèle 3D custom de ce projet) : signalé, pas d'action prise sans
demande explicite.

**(d) Bug trouvé en cherchant pourquoi certains trios n'avaient pas de
rendu 3D** (signalé par l'utilisateur : groupe D4/R3/C3 visible, groupe
D9/R7/C7 absent). Vérifié sur les 158 empreintes de `shield.kicad_pcb` :
**97 en manquaient**, toutes issues des générations en masse par script de
ce projet (23 trios `protections_devkit*`, 11 trios `protection_nappe`
decision #19, et même `R35`-`R38` de la decision #20 alors que leurs
`D36`-`D39`/`C55`-`C58` jumeaux en avaient) — les seules rescapées : `R1`-
`R3`/`C1`-`C2`/`C24`-`C43`/`D1`-`D4` (posées ou importées avant ces
scripts). Cause : le nœud `(model ...)` n'était pas systématiquement
recopié par les scripts de duplication utilisés au fil des sessions
précédentes. Corrigé en une passe : les 97 empreintes récupèrent le nœud
standard de leur type (`${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/
SOT-23.step`, `.../Resistor_SMD.3dshapes/R_0805_2012Metric.step`,
`.../Capacitor_SMD.3dshapes/C_0805_2012Metric.step`, offset/scale/rotate à
l'identité, repris des rescapés). `kicad-cli pcb drc` : 412 violations
avant et après, identique (le modèle 3D ne participe à aucune règle DRC).
Seule empreinte encore sans modèle à ce stade : `U4` (`lib:ER-OLEDM032-1`,
connecteur OLED custom) — même situation que NCM3S1205MC avant le point
(c), pas de modèle standard disponible.

**(e) Modèle 3D ER-OLEDM032-1.** Fourni directement par l'utilisateur
(`lib/ER-OLEDM032-1.STEP`, SolidWorks 2023, STEP AP214, ~4,4 Mo). Référencé
depuis `lib/ER-OLEDM032-1.kicad_mod` et la copie figée U4 dans
`shield.kicad_pcb`, offset/scale/rotate à l'identité (comme pour
NCM3S1205MC, alignement non vérifié visuellement par Claude). Les 158
empreintes du board ont désormais toutes un modèle 3D. `kicad-cli pcb drc`
inchangé (412 violations, mêmes catégories).

---

## 22. 45 footprints B.Cu gardaient leur sérigraphie/fab/courtyard sur la face avant (bug des mêmes scripts de duplication)

**Décision.** Signalé par l'utilisateur (groupe D4/R3/C3 correct en vue 3D,
groupe D9/R7/C7 — puis généralisé — absent/mal affiché). Vérifié sur les
158 footprints : **45 montés en B.Cu portaient encore des éléments
graphiques sur `F.SilkS`/`F.CrtYd`/`F.Fab`** au lieu de leurs équivalents
`B.*` — mêmes 45 réfs que la decision #20/#19 (`D25`-`D39`, `R24`-`R38`,
`C44`-`C58`). Deux sous-catégories : 32 avec corps sérigraphie + courtyard
+ contour fab non retournés du tout (copie brute de l'original F.Cu, ni
couche ni coordonnées changées) ; 13 avec seulement une propriété cachée
non-standard (`KiLib_Generator`, métadonnée de génération de footprint)
oubliée sur `F.SilkS` — invisible à l'oeil (propriété masquée) mais
révélatrice que même les passages "propres" de ce script ratent les
champs hors de la liste standard Reference/Value/Datasheet/Description.
Pastilles et modèle 3D déjà corrects dans les deux cas (uniquement
cosmétique/documentaire, aucun impact électrique).

**Diagnostic.** Comparé un trio cassé (`D25`) à un trio correct (`D36`,
puis `R3`/`C3`) élément par élément : le transform correct est **négation
du Y local** (coordonnées propres au footprint, centre = origine) +
permutation de couche `F.*`→`B.*`, conforme à la recette déjà documentée
dans `KICAD-EDITION-GROUPEE-KIPY.md` (miroir Y pour les pastilles,
protobuf absolu pour les formes côté kipy — ici vérifié que la même règle
de signe s'applique aux coordonnées locales du fichier texte). Script de
correction + un vérificateur réutilisable
(`check_mirrored_footprints.py`, racine du workspace) écrits et ajoutés à
la méthode documentée — voir ce fichier pour le détail et pourquoi
`lib_footprint_mismatch` seul ne suffit pas à détecter ce bug (bruit
préexistant, ne dit pas QUEL élément diverge).

**Incident pendant la correction.** KiCad était ouvert avec ce board
chargé (confirmé via `kipy.KiCad()` connecté) pendant que le fichier était
édité directement en texte — l'utilisateur travaillait en direct dans
l'éditeur PCB. Plusieurs passages se sont fait écraser partiellement : les
éléments de formes (338 éditions) ont fini par tenir, mais les 45
propriétés cachées (`KiLib_Generator`) sont revenues à leur état
`F.SilkS` d'origine à répétition, y compris après une correction vérifiée
immédiatement correcte — cohérent avec la session KiCad live qui
sauvegarde son état mémoire par-dessus l'édition texte. Résolu seulement
une fois l'utilisateur confirmé avoir fermé son edition. **Règle retenue,
ajoutée à `KICAD-EDITION-GROUPEE-KIPY.md`** : vérifier `kipy.KiCad()`
avant d'éditer le texte d'un `.kicad_pcb` ; si connecté, ne pas s'acharner
à re-corriger en boucle — demander à l'utilisateur de fermer le board
avant de repasser, ou traiter via kipy plutôt que par le texte.

**Vérification (une fois KiCad fermé, fichier stable).** `kicad-cli pcb
drc`, comparé par type à la toute première ligne de base de cette session
(412 violations hors `unconnected_items`, qui reste 313 inchangé de bout
en bout) : `lib_footprint_mismatch` 36 → 0 (y compris `R35`-`R38`, qui
faisaient partie du même bug — pas un bruit sans rapport comme
supposé un temps pendant l'incident ci-dessus) ; `npth_inside_courtyard`
2 → 0 et `courtyards_overlap` 2 → 1 (trous/courtyards mal positionnés
par le miroir manquant, maintenant corrects) ; `silk_over_copper` 80 → 75
(sérigraphie qui chevauchait du cuivre à sa mauvaise position d'origine) ;
`silk_overlap` 41 → 55, soit 14 nouvelles entrées, toutes citant des réfs
du lot corrigé (`D25`-`D35` contre `C44`-`C54`/`R29`/`R34`) —
chevauchements réels de sérigraphie entre trios voisins, invisibles tant
que les deux couches ne coïncidaient pas ; point ouvert de layout, pas
traité ici. `clearance` (93) et `text_height` (158) strictement
inchangés — confirme qu'aucun autre changement (routage, placement) ne
s'est glissé dans le fichier final malgré l'incident de sauvegarde
concurrente.

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
- Broche 7 de l'embase OLED (J10) : non étiquetée sur le plan constructeur
  fourni, laissée en NC par prudence (§15). À confirmer avec le datasheet
  complet de l'ER-OLEDM032-1B.
