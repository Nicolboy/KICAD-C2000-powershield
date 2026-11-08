# Revue de schéma — KICAD-C2000-powershield — 2026-11-02

Schéma analysé : `shield.kicad_sch` (10 feuilles filles). Base de règles :
`donnees/kb/base/SCH.yaml` (41 règles). Config projet : `revue_schema.yaml` (validée avec
l'utilisateur le 2026-11-02). Revue en lecture seule — aucune modification du schéma.

Modules exclus des règles internes (devkits + OLED) : `J7`/`J8` (ESP32-C6), `J17`/`J18` (C2000),
`U4` (OLED). Connecteurs externes déclarés : `J9` (alim 11-25V), `J15` (USB-C PD).

**9 constats automatisés déclenchent une action** (sur 54 au total) : 3 problèmes confirmés, 21 à
vérifier. Le reste est soit conforme (25), soit hors-périmètre manuel (condensateurs sans champs).

## 🔴 Bloquant

### SCH-001 — Diode ESD/TVS sur chaque interface externe — ⚠️ PROBLÈME sur J9
> Place une diode de protection ESD (signal) ou TVS (alimentation) directement aux bornes de
> chaque connecteur... accessible à l'utilisateur.

- **J9** (entrée 11-25V) : aucun composant de `references_protection` (BAT54S/ESDA25W/Z3SMCxxx)
  trouvé sur le net `VIN_PWR`. À corriger ou à confirmer qu'une protection existe sous une autre
  référence non listée dans la config.
- **J15** (USB-C PD) : ok, protection trouvée sur toutes les broches.

[9 Schematic Rules to NEVER Break @ 00:53](https://www.youtube.com/watch?v=97ZTkxzq-dI&t=53s)

### SCH-026 — Pull-ups I2C uniques, jamais cumulées — ⚠️ PROBLÈME sur 4 nets
> I2C est un bus open-drain — sans pull-up, les lignes ne remontent pas au niveau haut.

- **`I2C_SCL`, `I2C_SCL_MCU`, `I2C_SDA`, `I2C_SDA_MCU`** : zéro résistance de pull-up réelle
  détectée (ni série, ni vers un rail) sur ces 4 nets.
- Pour comparaison, les bus isolés sont corrects : `ESP32_SCL_ISO`/`ESP32_SDA_ISO` (côté ISO1640,
  R45/R46) et `STUSB_SCL`/`STUSB_SDA` (R55/R56) ont chacun exactement 1 pull-up.
- À vérifier : ces 4 nets sans pull-up sont-ils un bus I2C réellement utilisé sur cette carte, ou
  des nets d'un bus prévu mais pas encore câblé/peuplé ?

[9 Schematic Rules to NEVER Break @ 06:49](https://www.youtube.com/watch?v=97ZTkxzq-dI&t=409s)

### SCH-022 — Condensateur de sécurité / barrière d'isolement — ⚠️ PROBLÈME sur FL3, FL4
> Tout composant ayant des broches dans deux domaines de masse différents est une violation, sauf
> élément de barrière déclaré.

- **FL3** relie les domaines `flottant_u2` et `primaire` ; **FL4** relie `flottant_u3` et
  `primaire`. Ni l'un ni l'autre n'est dans `elements_barriere`.
- **U2, U3** (NCM3S1205MC) et **U6** (ISO1640BD) sont bien déclarés comme éléments de barrière —
  ok.
- **À trancher (pas une évidence côté script)** : FL3/FL4 sont-ils une référence de masse
  intentionnelle (ferrite reliant la masse flottante au primaire pour les courants de fuite/CEM,
  une technique courante sur ce type de montage), ou un pont qui affaiblit réellement
  l'isolement ? Si intentionnel, ajouter leur valeur à `elements_barriere`.

[7 Capacitors You Should NEVER Use in a Product @ 13:54](https://www.youtube.com/watch?v=eqVQLcbSVIk&t=834s)

## 🟠 Important — à vérifier

### SCH-009 — Découplage par broche d'alimentation (valeur et nombre)
Rails où le nombre de caps ~100 nF est inférieur au nombre de broches `power_in` hors module :
`5V_ISO_SW`, `U2_VINF`, `U3_VINF`, `VBUS_IN` (0 cap ~100nF, seulement du bulk 4,7-10 µF) ;
`3V3_ESP32` et `3V3_ISO` (moins de caps 100nF que de broches, mais certaines présentes).
`3V3_PROT` et `VREG_2V7` sont conformes.
[9 Power Supply Design Rules @ ...](https://www.youtube.com/watch?v=Hzm4ajEsNsg) · voir aussi SCH-018 (techno par rôle, cap bulk attendu pas forcément 100nF sur ces nets précis — à relire avec le rôle réel du rail avant de conclure).

### SCH-036 — Points de test
Aucun footprint `TestPoint*` trouvé sur les 13 rails identifiés (`3V3_ESP32`, `3V3_ISO`,
`3V3_PROT`, `5V_C2000`, `5V_ESP32`, `5V_ISO`, `5V_ISO_SW`, `5V_NUM`, `U2_VINF`, `U3_VINF`,
`VBUS_IN`, `VREG_1V2`, `VREG_2V7`). Cohérent avec un schéma encore en cours de finalisation —
à ajouter avant routage (SCH-036 insiste : plus coûteux à ajouter après placement).

### SCH-025 — Accès de programmation — fiabilité limitée de ce contrôle
Les nets `_EN` détectés (`HV_EN_MCU`, `PWM_EN`, `Stage1_EN_MCU`, `Stage2_EN_MCU`,
`Stage_hv_EN`, `Stage_inter_hv_EN`, `Vht_EN`, `Vhv_EN`) sont tous des *enables de puissance*
(connecteur trouvé sur chacun), pas des lignes de debug/programmation — le heuristique « EN »
est trop générique ici. Seul `VBUS_EN_SNK` (interne, pas de connecteur) est pertinent mais ce
n'est pas non plus une ligne de programmation. **L'accès de programmation réel (liaison UART
ESP32↔C2000, TMS_TXD/TMS_RXD du brochage) n'a pas été détecté par ce contrôle automatisé — à
vérifier manuellement.**

## Vérifications spécifiques au projet (modules, isolement)

### Interface modules ESP32/C2000 (hors SCH.yaml)
- **Broches de strapping ESP32** (`GPIO4/MTMS`, `GPIO5/MTDI`, `GPIO8` sur J7 ; `GPIO15`, `GPIO9`
  sur J8) : toutes **non connectées** côté shield — ok, cohérent avec le CSV (« libre, broche de
  strapping »).
- **Reverse-power** : `J7` (3V3_ESP32) n'a pas d'autre source `power_out` sur son net — ok.
  Vérification non concluante pour J17/J18 (C2000) et U4 — à confirmer manuellement, les pins
  `power_out` de ces modules n'ont pas été identifiées avec certitude par le script.
- **OR-ing générique** : `U2` et `U3` partagent 2 sorties `power_out` sur le net `GND` —
  vraisemblablement les deux retours secondaires des convertisseurs isolés (pas un conflit
  d'alimentation), mais à confirmer : ce n'est pas un cas d'OR-ing de rail de puissance classique,
  le contrôle générique n'est pas taillé pour ce cas précis.

## Règles manuelles applicables, non automatisées — à vérifier dans une prochaine passe

Ces règles s'appliquent à ce projet (USB-PD, connecteurs métalliques externes, MOSFET de
commutation, multi-rails) mais n'ont pas été lues ligne à ligne dans les 10 feuilles pour cette
première exécution — à faire au prochain passage, pas de verdict inventé ici :

| Règle | Pourquoi applicable ici |
|---|---|
| SCH-002 | J9/J15 sont des connecteurs métalliques externes — blindage relié masse à vérifier |
| SCH-003 | USB-C + frontières de domaines d'isolement — filtrage mode commun à vérifier |
| SCH-004/005 | J9 (11-25V) et J15 (USB-PD jusqu'à 20V/5A) — TVS/OVP et PTC/eFuse à vérifier |
| SCH-010 | Déclassement tension/puissance — aucun champ Voltage sur les composants, à vérifier à la main |
| SCH-014 | Choix des régulateurs (VREG_2V7, VREG_1V2, etc.) — dropout/dissipation à vérifier |
| SCH-033 | Entrée USB-PD (STUSB4531) — filtrage d'entrée robuste à vérifier |
| SCH-037 | Vérification empreinte/brochage vs datasheet — à faire composant par composant |

**Non applicables à ce projet** (pas de condition correspondante identifiée) : SCH-006/007/028
(pas de charge inductive type relais/moteur identifiée), SCH-011/012/013 (pas de batterie),
SCH-029/030/031/032 (pas de quartz externe, section RF/antenne, ampli audio ou driver LED au
niveau du shield — ces sujets sont internes aux modules devkit s'ils existent).

**Condensateurs — SCH-015/016/017/018/019/020/021** : aucun champ `Dielectric`/`Voltage` trouvé
sur les condensateurs du projet ; ces règles restent manuelles. Convention de champs proposée
(non appliquée au schéma) : `Dielectric` (C0G/NP0, X7R, X5R, Y5V, Z5U, X2, Y1...) et `Voltage`
(tension nominale) comme champs de symbole personnalisés.

## ERC (`kicad-cli sch erc`)

314 violations brutes → **277 cosmétiques** (`endpoint_off_grid`, grille de connexion) filtrées.

**18 violations internes aux modules** (J7/J8/J17/J18/U4), hors périmètre de cette revue — pour
mémoire, pas supprimées : broches non pilotées/non connectées des devkits eux-mêmes (ex. RST,
GPIO11/TMS_TXD de J7), déjà couvertes par le contrôle d'interface module ci-dessus quand c'est une
broche de strapping.

**18 violations pertinentes restantes** (hors modules, hors cosmétique) — à trier manuellement,
non détaillées ligne à ligne ici par souci de place ; disponibles dans le JSON brut
(`resultats_final.json`, clé `erc.pertinentes`).

## Mise à jour de la base de règles

Suite à ce test réel, les règles suivantes passent de `manuel` à `semi-auto` dans `SCH.yaml`
(contrôle automatisé réellement exercé avec succès) : **SCH-001, SCH-022, SCH-025, SCH-026,
SCH-036**. `SCH.yaml.bak-2026-11-02` sauvegardé avant modification.
