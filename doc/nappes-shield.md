# Nappes shield, alimentation, et répartition des cartes

Ce document décrit les six nappes vers les cartes DC/DC enfichables, et la
chaîne d'alimentation du shield lui-même. **Le connecteur devkit, le brochage
des 64 broches, le JTAG et la mécanique sont dans
[`spec-devkit.md`](spec-devkit.md)**, qui fait autorité pour cette partie-là.

**Changement par rapport à `KICAD-C2000-devkit`** : il n'y a plus de carte de
puissance séparée. Le shield reçoit directement le 11-25V externe et produit
ses propres rails isolés — voir §1 "Alimentation" et §2. Conséquence directe :
les nappes, qui ne portaient aucune alimentation, portent désormais
une masse et un 3,3V dédiés à l'isolation des cartes DC/DC (decision #13,
`decisions.md`). Passage de quatre à six nappes en decision #17.

## 1. Les six nappes — un backplane fixe, pas un connecteur par carte

**Révision (decision #17) : passage de quatre à six nappes, et changement du
séquencement signal/masse.** Chaque carte fille se raccorde à ce même jeu de
six connecteurs standard, n'utilisant que les broches dont elle a besoin (le
reste en l'air) — pas de connecteur sur mesure par carte. Une carte peut ne
peupler que 3 ou 4 des 6 connecteurs (ex. une carte DC/DC n'a besoin d'aucun
bus) ; un connecteur non peuplé côté carte fille ne coûte rien côté shield.

Six connecteurs IDC **2 × 10** identiques (20 voies, même référence pour
toutes — contrainte de stock : pas de taille plus grande), détrompeur de
série : **ADC-1** (J1), **ADC-2** (J2), **PWM** (J3), **GPIO-1** (J4),
**logic/CLB** (J13, nouveau — ex "GPIO-2", renommée en decision #20),
**COM** (J14, nouveau). Désignateurs J5/J6/J7-J12
déjà pris ailleurs dans le projet (devkit, OLED, alimentation) — J13/J14
choisis pour ne pas entrer en collision.

**Position 1 = `3V3_ISO`, position 2 = `GND`** (alimentation du côté commande
des isolateurs de chaque carte DC/DC, pas un signal — convention reprise du
connecteur `CpuOut1`/`CTRL_C2000_OUT` d'`alim-flyback-filament`, decision
#14), puis **signal sur les positions impaires (3 à 19), masse sur les
positions paires (4 à 20)** — changement par rapport à la révision
précédente, qui plaçait la masse en 2 *et* 3 avant le premier signal en 4.
Ce reséquencement gagne **un emplacement signal de plus par connecteur** (9
au lieu de 8) sans changer la taille du connecteur : les positions 19/20,
jusque-là non définies, sont maintenant pleinement utilisées.

Aucune exception à l'alternance stricte. La paire de référence
`VREF_ADC`/`VREFLO_SENSE` (ADC-2) avait initialement reçu une dérogation
(positions 7/8 adjacentes, decision #3) ; supprimée en decision #19
(deuxième erratum) — leur lien électrique passe par le suiveur
rail-to-rail du shield, pas par leur proximité sur la nappe, donc
l'adjacence n'apportait rien et sacrifiait le blindage masse d'une
position par ailleurs utilisable par un signal `Rapide`.

### ADC-1 — mesures tension et température

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **Vin** | 4 GND | 5 **Vout** | 6 GND | 7 **V1** | 8 GND |
| 9 **Temp1** | 10 GND | 11 **Temp2** | 12 GND | 13 **Iin** | 14 GND | 15 **Iout** | 16 GND |
| 17 **réserve ADC1-1** | 18 GND | 19 **réserve ADC1-2** | 20 **GND** | | | | |

### ADC-2 — shunts, référence, réserves

**Corrigé (decision #19) : le brochage omettait `I_SHUNT1_CMP`/
`I_SHUNT2_CMP`.** Seule la voie filtrée (`I_shunt1`/`I_shunt2`, chemin
`_MES`) était câblée ; la decision #4 impose pourtant que chaque shunt
sorte **deux fois** — un chemin direct, sans filtre, vers le comparateur.
Les deux signaux manquants prennent la place de deux des six réserves
(réserves : 6 → 4).

**Deuxième erratum (même décision) : l'exception d'adjacence 7/8
supprimée, tout le connecteur repasse en alternance stricte.** Le
premier passage gardait `VREF_ADC`/`VREFLO_SENSE` adjacents en 7/8 (une
exception à l'alternance, héritée de la decision #3) et plaçait
`I_SHUNT1_CMP` juste derrière en position 9 — sans masse entre les deux,
un signal `Rapide` (comparateur, fronts rapides) collé à une référence
analogique précise. Plutôt que de recaser seulement `I_SHUNT1_CMP`/
`I_SHUNT2_CMP` ailleurs, la paire de référence elle-même est déplacée en
positions 3/5 : chaque position impaire du connecteur est maintenant
entourée de masse des deux côtés, **sans exception**. `VREF_ADC`/
`VREFLO_SENSE` perdent leur adjacence directe mais gagnent un blindage
complet — ce qui compte pour une référence qui alimente aussi le REFIN
des isolateurs ratiométriques (voir plus bas). `I_shunt1`/`I_shunt2`
cèdent leurs positions 3/5 et reculent en 7/9 (toujours entourées de
masse, toujours adjacentes entre elles via la masse de la position 8).
Une réserve est perdue dans l'échange (la position 9, ancien slot libre,
porte maintenant `I_shunt2`) : réserves 4 → **3**.

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **VREFLO_SENSE** | 4 GND | 5 **VREF_ADC** | 6 GND | 7 **I_shunt1** | 8 **GND** |
| 9 **I_shunt2** | 10 GND | 11 **I_SHUNT1_CMP** | 12 GND | 13 **I_SHUNT2_CMP** | 14 GND | 15 **réserve ADC2-1** | 16 GND |
| 17 **réserve ADC2-2** | 18 GND | 19 **réserve ADC2-3** | 20 **GND** | | | | |

`I_SHUNT1_CMP`/`I_SHUNT2_CMP` (positions 11/13) ne sont **pas** placés
adjacents à `I_shunt1`/`I_shunt2` (positions 7/9, séparées par la masse
de la position 10) malgré la parenté de mesure : la decision #4 exige
que les deux chemins restent électriquement indépendants (un défaut sur
le filtre ne doit pas désarmer la protection), les coller sur le
connecteur n'aiderait à rien et mélangerait visuellement deux chemins qui
ne doivent pas se confondre.

VREF_ADC et VREFLO_SENSE (positions 5/3) forment une paire de référence,
pas deux signaux indépendants — mais contrairement au premier passage,
elles n'ont plus besoin d'être physiquement adjacentes sur le connecteur
pour ça : le lien électrique entre les deux se fait par le suiveur
rail-to-rail du shield, pas par leur proximité sur la nappe. Le shield
bufferise VREF_ADC par ce suiveur avant de l'envoyer.

**C'est cette même paire qui sert de référence aux isolateurs ratiométriques
(suffixe "R", type AMC0311R/AMC0302R) des cartes DC/DC** — leur broche REFIN
se raccorde à VREF_ADC, pas à 3V3_ISO. Faire porter la précision ADC par
l'alimentation de l'isolateur (asservir 3V3_ISO à VDDA) serait le mauvais
outil : un LDO n'a pas la stabilité d'une vraie référence. 3V3_ISO reste un
3,3V fixe, simple alimentation logique, pas une référence.

Les cinq voies ADC libres du connecteur devkit (A12, A14, A15, A17, A18,
noms `ADC_8` à `ADC_12`) restent la source destinée aux réserves ci-dessus —
pas encore câblées jusqu'ici (ERC : `isolated_pin_label`, point pré-existant,
non traité dans cette passe). Une voie ajoutée plus tard se câble de bout en
bout sans retoucher aucune carte.

### PWM — commandes rapides

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **PWM1_A** | 4 GND | 5 **PWM1_B** | 6 GND | 7 **PWM2_A** | 8 GND |
| 9 **PWM2_B** | 10 GND | 11 **PWM3_A** | 12 GND | 13 **PWM3_B** | 14 GND | 15 **PWM4_A** | 16 GND |
| 17 **PWM4_B** | 18 GND | 19 **réserve PWM-1** | 20 **GND** | | | | |

Seules lignes à fronts rapides de l'ensemble. PWM3 et PWM4 restent en réserve, en
paires complémentaires HRPWM avec temps mort matériel.

### GPIO-1 — commandes lentes, sécurité, service

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **Stage1_EN** | 4 GND | 5 **Stage2_EN** | 6 GND | 7 **HV_EN** | 8 GND |
| 9 **Discharge** | 10 GND | 11 **CMP_OUT** | 12 GND | 13 **nFAULT** | 14 GND | 15 **I2C_SCL** | 16 GND |
| 17 **I2C_SDA** | 18 GND | 19 **CLB_OUT** | 20 **GND** | | | | |

`nFAULT` remonte un défaut d'une carte DC/DC vers `~{FAULT_MCU}` (B28, nom en
logique négative depuis la decision #20). `CMP_OUT` sort le drapeau de défaut
agrégé du C2000. L'I2C reste disponible pour un capteur de température ou une
EEPROM de calibration sur une carte DC/DC. `CLB_OUT` (B27 du connecteur devkit)
était orphelin — exporté sur aucune nappe avant la decision #19 — et retrouve
ici un foyer.

**`Stage1_EN`, `Stage2_EN`, `HV_EN` et `Discharge` sont maintenant reliés**
(decision #20) : devkit modifié pour sortir GPIO9/GPIO20/GPIO21/GPIO41 sur le
connecteur A (4 masses sacrifiées, voir decision #20), protégés par un trio
chacun (`protection_nappe.kicad_sch`, R = 10 Ω, signaux classés `Rapide`), et
présents **à la fois** ici et sur la nappe logic/CLB ci-dessous — un seul des
deux points d'accès est réellement utilisé selon la carte fille branchée.

### GPIO-2 → nappe logic — entrées/sorties du bloc CLB

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **CLB_Out_1** | 4 GND | 5 **CLB_Out_2** | 6 GND | 7 **CLB_Out_3** | 8 GND |
| 9 **CLB_Out_4** | 10 GND | 11 **CLB_In_1** | 12 GND | 13 **CLB_In_2** | 14 GND | 15 **CLB_In_3** | 16 GND |
| 17 **CLB_In_4** | 18 GND | 19 **CLB_In_5** | 20 **GND** | | | | |

Renommée en decision #20 : le CLB (Configurable Logic Block) du F28P551, utilisé
comme un mini CPLD, a besoin d'E/S physiques. `CLB_Out_1`-`4` et `CLB_In_1`-`5`
sont des **noms de broche cosmétiques** sur le connecteur (même principe que
`GPIOxx/fonction` côté devkit) — le net électrique réel reste le vrai nom de
signal, pour qu'il fusionne avec les autres nappes :

| Broche | Nom cosmétique | Net réel | Origine |
|---|---|---|---|
| 3 | `CLB_Out_1` | `Stage1_EN` | neuf (GPIO9, pilotable aussi par le CLB en matériel) |
| 5 | `CLB_Out_2` | `Stage2_EN` | neuf (GPIO20, logiciel seul) |
| 7 | `CLB_Out_3` | `HV_EN` | neuf (GPIO21, logiciel seul) |
| 9 | `CLB_Out_4` | `Discharge` | neuf (GPIO41, logiciel seul) |
| 11 | `CLB_In_1` | `CAN_RX` | lu en plus de la nappe COM, CAN continue de fonctionner |
| 13 | `CLB_In_2` | `CAN_TX` | idem |
| 15 | `CLB_In_3` | `PWM2_B` | lu en plus de la nappe PWM, le canal garde son rôle complémentaire |
| 17 | `CLB_In_4` | `PWM3_B` | idem |
| 19 | `CLB_In_5` | `PWM4_B` | idem |

Les 4 sorties sont neuves côté MCU (voir decision #20) ; les 5 entrées sont de
simples lectures supplémentaires de signaux déjà câblés ailleurs — aucune
d'elles ne perd sa fonction d'origine.

### COM — bus de communication (UART, SPI, CAN)

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **UART_TX** | 4 GND | 5 **UART_RX** | 6 GND | 7 **SPI_CLK** | 8 GND |
| 9 **SPI_SIMO** | 10 GND | 11 **SPI_SOMI** | 12 GND | 13 **SPI_STE** | 14 GND | 15 **CAN_TX** | 16 GND |
| 17 **CAN_RX** | 18 GND | 19 **réserve COM-1** | 20 **GND** | | | | |

Logique 3,3V brute uniquement : les transceivers CAN et RS-485/Modbus vivent
sur chaque carte fille qui en a besoin (cohérent avec la decision #13 — chaque
carte porte l'isolation que *sa* fonction exige), pas sur le shield. Modbus
n'a pas de signal propre : c'est `UART_TX`/`UART_RX` + un transceiver RS-485
côté carte fille, avec sa propre broche `DE`/`RE` gérée localement si besoin.

### Connecteurs dédiés — carte HV et carte Filament (HT)

**Écart assumé à la decision #17** (décision #26, `decisions.md`) : ces deux
cartes ont plus de signaux à échanger que les réserves des six nappes
partagées ne peuvent en offrir d'un coup. Chaque carte reçoit son propre
connecteur IDC 2×10, en plus des six nappes ci-dessus — pas à la place.

**Carte HV** — `connecteur_carte_hv.kicad_sch`, deux connecteurs :

| Broche | `J19` (`NAPPE_HV_ADC`) | Broche | `J20` (`NAPPE_HV_DIO`) |
|---|---|---|---|
| 1 | `3V3_ISO` | 1 | `3V3_ISO` |
| 3 | `Vin` | 3 | `PWM1_A` |
| 5 | `Iin` | 5 | `Stage1_EN` |
| 7 | `V1` | 7 | `PWM2_A` |
| 9 | `I_shunt1` | 9 | `Stage2_EN` |
| 11 | `I_SHUNT1_CMP` | 11 | `HV_EN` |
| 13 | `Vout` | 13 | `Discharge` |
| 15 | `Iout` | 15 | réserve |
| 17 | `I_shunt2` | 17 | `Temp1` |
| 19 | `I_SHUNT2_CMP` | 19 | `Temp2` |

(positions paires = GND, comme sur les six nappes). Tous ces signaux sont
déjà protégés ailleurs dans le projet — simple deuxième point d'accès,
aucun composant de protection neuf sur cette feuille.

**Carte Filament (HT)** — `connecteur_ht.kicad_sch`, un connecteur `J21`
(`NAPPE_FILAMENT_HT`) :

| Broche | Signal | Origine |
|---|---|---|
| 1 | `3V3_ISO` | — |
| 3 | `PWM3_A` | nappe PWM, déjà protégé |
| 5 | `CMP_OUT` | nappe GPIO-1, déjà protégé |
| 7 | `PWM3_B` | nappe PWM, déjà protégé |
| 9 | `CLB_OUT` | nappe GPIO-1, déjà protégé |
| 11 | `Vht` | `ADC_8_MCU`→`ADC_12_MCU`, neuf (trio R=100 Ω) |
| 13 | `Temp_ht` | `ADC_10_MCU`, neuf (trio R=100 Ω) |
| 15 | `I_Shunt_ht` | `ADC_11_MCU`, neuf (trio R=100 Ω) |
| 17 | `I_Shunt_ht_comp` | `ADC_8_MCU`, neuf (trio R=22 Ω, chemin comparateur `CMPSS3`) |
| 19 | `V_bias` | `ADC_12_MCU`, neuf (trio R=100 Ω) |

Les cinq voies ADC du connecteur devkit (`ADC_8`-`ADC_12`), posées depuis le
début mais jamais câblées, sont maintenant **toutes** affectées — plus
aucune réserve analogique disponible ailleurs dans le projet. Détail complet
(pourquoi `ADC_8` spécifiquement, gabarit de trio, rappel de la config
`CMPSS3` côté firmware hors périmètre) : decision #26.

### Alimentation — chaîne complète sur le shield

Plus de carte de puissance séparée : le shield reçoit le **11-25V externe**
et produit lui-même ses rails isolés, via **deux NCM3S1205MC-R7** distincts
(Murata, 9-36V→5V/600mA max, isolation 5000VAC — un par domaine, pour ne pas
coupler le bruit numérique sur l'alimentation de l'isolation) :

```
J_PWR (11-25V externe, présent aux deux modules en permanence, non coupé)
   │
   ├── NCM3S1205MC #1 — domaine "numérique"
   │        ├── Cavalier C2000 (2 pts, 2,54mm) → +5V connecteur devkit C2000
   │        └── Cavalier ESP32 (2 pts, 2,54mm) → +5V connecteur devkit ESP32
   │                   └──→ OLED (alimenté avec l'ESP32)
   │
   └── NCM3S1205MC #2 — domaine "isolation E/S"
            Cavalier E/S (2 pts, 2,54mm)
            │
          LDO linéaire 3,3V fixe + zener de protection en sortie
                └──→ GND + 3V3_ISO sur les six nappes (positions 2/1)
```

**Coupure par destination** : trois cavaliers indépendants (C2000 / ESP32 /
E/S), chacun côté régulé (5V ou 3,3V), pas un cavalier unique sur le 11-25V
brut — le module #1 reste partagé entre les deux devkits, c'est le seul
endroit où une coupure individuelle a un sens.

**Masses secondaires des deux NCM3S1205MC : reliées, en un point unique**
(étoile). Le 3V3_ISO alimente le côté commande/non-isolé des isolateurs des
cartes DC/DC — c'est ce côté-là qui doit partager la référence du C2000 qui
lit leur sortie, sinon le signal n'a pas de référence valable une fois relu.
L'isolation galvanique réelle se fait à l'intérieur de chaque puce
isolatrice, pas entre les deux domaines de ce shield. Point unique (pas
deux jonctions) pour éviter la boucle de masse — même principe que le point
de jonction VSS/VSSA unique déjà utilisé sur les devkits (`spec-devkit.md`).

**Protection 3,3V — crowbar de sortie contre une panne du LDO**, pas de
l'ESD générique : une zener entre 3V3_ISO et masse, calibrée juste au-dessus
de 3,3V, écrête si le pass-transistor du LDO lâche et laisse passer le 5V
d'entrée vers la sortie (mode de panne déjà vécu). Valeur exacte et tenue en
courant à calculer une fois le modèle de LDO choisi.

**Point ouvert, à chiffrer avant de sourcer** : budget de courant de chaque
rail 5V (600mA dispo chacun) — #1 face à 2 devkits + OLED, #2 face au LDO
3,3V + la consommation réelle des cartes DC/DC côté isolation, encore
inconnue tant qu'aucune carte fille n'est spécifiée.

### Alimentation cartes filles — USB-C Power Delivery (feuille `USB_PD`)

Deuxième entrée d'alimentation, séparée du 11-25V ci-dessus (confirmé par
l'utilisateur — pas une fusion) : un récepteur USB-C (Würth 632722100213,
6 broches CC1/CC2/VBUS×2/GND×2, pas de D+/D-/SBU) négocie jusqu'à 100W
(20V/5A) via un STUSB4531QTR, et alimente **en daisy chain** les cartes
filles via un connecteur dédié — convention d'interface, la propagation
carte-à-carte est hors périmètre de ce dépôt.

```
USB-C (Würth 632722100213) — VBUS_IN, CC1, CC2, GND
   │
STUSB4531QTR — négociation PD autonome (dead battery), alimenté sur VBUS_IN
   │  VBUS_EN_SNK → réseau R (100k/22k) → grille T1 (filtrage 100R/100nF)
   │  DISCH/VBUS_VS_DISCH → décharge autonome système/réceptacle
   │  SCL/SDA/ALERT → bus I2C dédié ESP32 (GPIO22/23/21, PAS celui des
   │       nappes qui reste au C2000) — supervision seulement, l'autorun
   │       négocie sans lui
   │
   ▼
T1 (SQJ459EP-T2_GE3, PMOS) — unique interrupteur de puissance, pas d'eFuse
   │
   ▼
VBUS_OUT → connecteur de sortie puissance cartes filles (daisy chain)
```

`HV_EN`/`Discharge` (nappe GPIO-1, decision #17/#20) **ne sont pas
mêlés à ce circuit** — signaux distincts, à ne pas confondre : le
STUSB4531QTR gère sa propre coupure/décharge en autonome.

Détail complet (BOM, choix de composants, justification) :
`doc/decisions.md` (nouvelle décision, référencée depuis le sommaire).

### Embase OLED — J10, IDC 2 × 8 détrompée

Écran `ER-OLEDM032-1B` (SPI 4 fils), nappe 16 voies vers une embase IDC
2 × 8 à sertir, détrompeur de série — même famille de connecteur que les
nappes DC/DC, taille en dessous (2×8 au lieu de 2×10, le module
n'a que 16 broches). Alimenté par la sortie 3,3V du LDO de la carte ESP32
(`3V3_ESP32`, J1 broche 1 — `doc/brochage-esp32.csv` : "ne pas alimenter
depuis le shield", le shield ne fait que tirer du courant dessus), pas par
le rail 5V du shield : tous les signaux échangés (SCK/MOSI/CS/DC/RST)
sont en logique 3,3V, le VCC de l'écran doit être au même niveau pour que
les seuils d'entrée restent cohérents.

| Broche | Signal OLED | Net / GPIO ESP32 |
|---|---|---|
| 1 | VSS | GND |
| 2 | VCC | 3V3_ESP32 → J1-1 (sortie LDO 3,3V de la carte ESP32) |
| 3 | — | NC (mode I2C/parallèle, inutilisé en SPI) |
| 4 | CLK | OLED_SCK → GPIO6 (FSPICLK natif) |
| 5 | MOSI | OLED_MOSI → GPIO7 (FSPID natif) |
| 6 | — | NC |
| 7 | — | NC *(zone non étiquetée sur le plan constructeur, laissée non connectée par prudence — à reconfirmer si le datasheet complet ER-OLEDM032-1B devient disponible)* |
| 8-13 | GND ×6 | GND |
| 14 | D/C | OLED_DC → GPIO19 |
| 15 | /RST | OLED_RST → GPIO20 |
| 16 | /CS | OLED_CS → GPIO18 (FSPICS2 natif) |

Symbole `OLED_SPI_2x8` dans `lib/C2000_Devkit_Connectors.kicad_sym`,
empreinte `Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical`. Placé sur
`connecteur_devkit.kicad_sch` (feuille des connecteurs devkit/ESP32), les
labels `OLED_*` y existaient déjà sur les broches natives de l'ESP32 —
seule l'embase physique manquait.

## 2. Répartition des cartes

**Shield** — support mécanique des deux devkits, **alimentation complète**
(11-25V→5V isolé ×2, 3,3V isolation + protection), adaptation de brochage,
conditionnement analogique (filtres anti-repliement, suiveur VREF,
dédoublement des voies shunt), protections, embase nappe OLED (détail
ci-dessus). Aucune
isolation propre au shield — elle est désormais portée par les cartes DC/DC
enfichables, selon leurs besoins propres.

**Cartes DC/DC (enfichables, une par fonction)** — portent chacune
l'isolation galvanique que leur fonction exige (ou aucune, si elle n'en a
pas besoin). Se raccordent aux nappes 2×10 dont elles ont besoin — **pas
forcément les six** : un connecteur non peuplé côté carte fille ne coûte
rien côté shield. Tirent leur alimentation de commande sur 3V3_ISO
(position 1), référencent leurs isolateurs ratiométriques sur VREF_ADC si
besoin de précision ADC.

*Exemple — convertisseur 0-500V (refonte de `TMS320F28027-dualboost`)* :
peuple ADC-1, ADC-2 et PWM en entier, et seulement GPIO-1 côté logique — ni
logic/CLB (pas de besoin de glue logic sur cette carte), ni COM (aucun bus
dans cette conception).

**Devkit C2000** — MCU, deux LDO 3,3 V (VDDIO et VDDA), JTAG, bouton reset, deux
LED, cavalier de boot.

**Devkit ESP32** — Wi-Fi, hôte FOTA, écran OLED en SPI sur nappe.

---

