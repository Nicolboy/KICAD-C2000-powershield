# Nappes shield, alimentation, et répartition des cartes

Ce document décrit les quatre nappes vers les cartes DC/DC enfichables, et la
chaîne d'alimentation du shield lui-même. **Le connecteur devkit, le brochage
des 64 broches, le JTAG et la mécanique sont dans
[`spec-devkit.md`](spec-devkit.md)**, qui fait autorité pour cette partie-là.

**Changement par rapport à `shield-c2000`** : il n'y a plus de carte de
puissance séparée. Le shield reçoit directement le 11-25V externe et produit
ses propres rails isolés — voir §1 "Alimentation" et §2. Conséquence directe :
les quatre nappes, qui ne portaient aucune alimentation, portent désormais
une masse et un 3,3V dédiés à l'isolation des cartes DC/DC (decision #13,
`decisions.md`).

## 1. Les quatre nappes

Quatre connecteurs IDC **2 × 10** à sertir, détrompeur de série (taille
standard de nappe, 20 voies — agrandi depuis le 2×8 breakaway de
`shield-c2000`, decision #13). **3V3_ISO et GND occupent les positions 1 et
2** (alimentation du côté commande des isolateurs de chaque carte DC/DC, pas
un signal — convention reprise du connecteur `CpuOut1`/`CTRL_C2000_OUT`
d'`alim-flyback-filament`, decision #14), puis **alternance signal / masse
stricte 1:1 sur les positions 3 à 18** (les 16 signaux, inchangés par
rapport à avant, décalés de 2 crans).

### ADC-1 — mesures tension et température

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 GND | 4 **Vin** | 5 GND | 6 **Vout** | 7 GND | 8 **V1** |
| 9 GND | 10 **Temp1** | 11 GND | 12 **Temp2** | 13 GND | 14 **Iin** | 15 GND | 16 **Iout** |
| 17 **GND** | 18 **réserve 1** | | | | | | |

### ADC-2 — shunts, référence, réserves

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 GND | 4 **I_shunt1** | 5 GND | 6 **I_shunt2** | 7 GND | 8 **VREF_ADC** |
| 9 **VREFLO_SENSE** | 10 GND | 11 GND | 12 **réserve 2** | 13 GND | 14 **réserve 3** | 15 GND | 16 **réserve 4** |
| 17 **GND** | 18 **réserve 5** | | | | | | |

VREF_ADC et VREFLO_SENSE occupent les positions 8 et 9, adjacentes : c'est une
paire de référence, pas deux signaux indépendants. Le shield bufferise VREF_ADC
par un suiveur rail-to-rail avant de l'envoyer.

**C'est cette même paire qui sert de référence aux isolateurs ratiométriques
(suffixe "R", type AMC0311R/AMC0302R) des cartes DC/DC** — leur broche REFIN
se raccorde à VREF_ADC, pas à 3V3_ISO. Faire porter la précision ADC par
l'alimentation de l'isolateur (asservir 3V3_ISO à VDDA) serait le mauvais
outil : un LDO n'a pas la stabilité d'une vraie référence. 3V3_ISO reste un
3,3V fixe, simple alimentation logique, pas une référence.

Les cinq réserves correspondent exactement aux cinq voies ADC libres du
connecteur devkit — A12, A14, A15, A17, A18. Une voie ajoutée plus tard se câble
de bout en bout sans retoucher aucune carte.

### PWM — commandes rapides

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 GND | 4 **PWM1_A** | 5 GND | 6 **PWM1_B** | 7 GND | 8 **PWM2_A** |
| 9 GND | 10 **PWM2_B** | 11 GND | 12 **PWM3_A** | 13 GND | 14 **PWM3_B** | 15 GND | 16 **PWM4_A** |
| 17 **GND** | 18 **PWM4_B** | | | | | | |

Seules lignes à fronts rapides de l'ensemble. PWM3 et PWM4 restent en réserve, en
paires complémentaires HRPWM avec temps mort matériel.

### GPIO — commandes lentes, sécurité, service

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| 1 **3V3_ISO** | 2 **GND** | 3 GND | 4 **Stage1_EN** | 5 GND | 6 **Stage2_EN** | 7 GND | 8 **HV_EN** |
| 9 GND | 10 **Discharge** | 11 GND | 12 **CMP_OUT** | 13 GND | 14 **nFAULT** | 15 GND | 16 **I2C_SCL** |
| 17 **GND** | 18 **I2C_SDA** | | | | | | |

`nFAULT` remonte un défaut d'une carte DC/DC vers GPIO_1 (B28).
`CMP_OUT` sort le drapeau de défaut agrégé du C2000. L'I2C reste disponible pour
un capteur de température ou une EEPROM de calibration sur une carte DC/DC.

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
                └──→ GND + 3V3_ISO sur les 4 nappes (positions 2/1)
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
quatre nappes DC/DC, taille en dessous (2×8 au lieu de 2×10, le module
n'a que 16 broches). Alimenté avec l'ESP32 (voir § Alimentation ci-dessus),
pas sur un rail dédié.

| Broche | Signal OLED | Net / GPIO ESP32 |
|---|---|---|
| 1 | VSS | GND |
| 2 | VCC | 5V_ESP32 |
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
pas besoin). Se raccordent aux 4 nappes 2×10 ; tirent leur alimentation de
commande sur 3V3_ISO (position 1), référencent leurs isolateurs
ratiométriques sur VREF_ADC si besoin de précision ADC.

**Devkit C2000** — MCU, deux LDO 3,3 V (VDDIO et VDDA), JTAG, bouton reset, deux
LED, cavalier de boot.

**Devkit ESP32** — Wi-Fi, hôte FOTA, écran OLED en SPI sur nappe.

---

