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
**GPIO-2** (J13, nouveau), **COM** (J14, nouveau). Désignateurs J5/J6/J7-J12
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

Seule exception volontaire à l'alternance stricte : la paire de référence
`VREF_ADC`/`VREFLO_SENSE` (ADC-2), qui reste adjacente (decision #3) en
positions 7/8 — la position 8 cède sa masse pour cette seule paire.

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

**Erratum (même décision) : positions 9/11 écartées au profit de 11/13.**
Le premier passage avait placé `I_SHUNT1_CMP` en position 9, juste après
`VREFLO_SENSE` (position 8) — sans masse entre les deux. Position 8 est
déjà l'exception à l'alternance stricte (paire de référence), donc la
position 9 qui la suit hérite du même défaut de blindage, cette fois
contre un signal `Rapide` (comparateur) non apparenté. Déplacé en
positions 11/13, pleinement entourées de masse des deux côtés, comme
`I_shunt1`/`I_shunt2` en 3/5. Position 9 redevient réserve.

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **I_shunt1** | 4 GND | 5 **I_shunt2** | 6 GND | 7 **VREF_ADC** | 8 **VREFLO_SENSE** |
| 9 **réserve ADC2-1** | 10 GND | 11 **I_SHUNT1_CMP** | 12 GND | 13 **I_SHUNT2_CMP** | 14 GND | 15 **réserve ADC2-2** | 16 GND |
| 17 **réserve ADC2-3** | 18 GND | 19 **réserve ADC2-4** | 20 **GND** | | | | |

`I_SHUNT1_CMP`/`I_SHUNT2_CMP` ne sont **pas** placés adjacents à
`I_shunt1`/`I_shunt2` malgré la parenté de mesure : la decision #4 exige
que les deux chemins restent électriquement indépendants (un défaut sur
le filtre ne doit pas désarmer la protection), les coller sur le
connecteur n'aiderait à rien et mélangerait visuellement deux chemins qui
ne doivent pas se confondre — contrairement à `VREF_ADC`/`VREFLO_SENSE`
(positions 7/8), qui sont une vraie paire de référence.

VREF_ADC et VREFLO_SENSE occupent les positions 7 et 8, adjacentes : c'est une
paire de référence, pas deux signaux indépendants. Le shield bufferise VREF_ADC
par un suiveur rail-to-rail avant de l'envoyer.

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

`nFAULT` remonte un défaut d'une carte DC/DC vers GPIO_1 (B28).
`CMP_OUT` sort le drapeau de défaut agrégé du C2000. L'I2C reste disponible pour
un capteur de température ou une EEPROM de calibration sur une carte DC/DC.
`CLB_OUT` (B27 du connecteur devkit) était orphelin — exporté sur aucune nappe
avant cette révision — et retrouve ici un foyer.

⚠️ **`Stage1_EN`, `Stage2_EN`, `HV_EN` et `Discharge` ne sont reliés à aucune
broche du connecteur devkit à ce jour** (ERC : `isolated_pin_label` sur les
quatre). Ces noms viennent de l'ancien firmware TMS320F28027 (GPIO16, GPIO17,
GPIO32, GPIO5) ; la nouvelle carte de conversion 0-500V aura un nouveau MCU et
choisira ses propres broches — tant que ce choix n'est pas fait, ces quatre
signaux restent à un seul bout. Pas un défaut de cette révision : la carte
elle-même est un projet séparé (voir `decisions.md` #17).

### GPIO-2 — réserve, extension logique future

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 **réserve GPIO2-1** | 4 GND | 5 **réserve GPIO2-2** | 6 GND | 7 **réserve GPIO2-3** | 8 GND |
| 9 **réserve GPIO2-4** | 10 GND | 11 **réserve GPIO2-5** | 12 GND | 13 **réserve GPIO2-6** | 14 GND | 15 **réserve GPIO2-7** | 16 GND |
| 17 **réserve GPIO2-8** | 18 GND | 19 **réserve GPIO2-9** | 20 **GND** | | | | |

Connecteur entièrement en réserve — aucun signal câblé aujourd'hui. Pour une
carte future dont le besoin en E/S logique ne ressemble à rien d'anticipé ici
(relais, capteurs tout-ou-rien, etc.).

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
GPIO-2 (aucun besoin logique connu au-delà de GPIO-1), ni COM (aucun bus
dans cette conception).

**Devkit C2000** — MCU, deux LDO 3,3 V (VDDIO et VDDA), JTAG, bouton reset, deux
LED, cavalier de boot.

**Devkit ESP32** — Wi-Fi, hôte FOTA, écran OLED en SPI sur nappe.

---

