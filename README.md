# KICAD-C2000-power

Shield d'isolation, alimentation et interconnexion pour TMS320 C2000, conçu
sous KiCad 10.

Reprend le projet `shield` de [`KICAD-C2000-devkit`](https://github.com/Nicolboy/KICAD-C2000-devkit)
au moment où son rôle a dépassé le simple support mécanique des deux
devkits : il reçoit désormais le 11-25V externe et produit lui-même les
rails isolés (5V numérique ×2, 3,3V isolation + protection) qu'une carte
de puissance séparée portait jusque-là. D'où le changement de dépôt plutôt
qu'une extension sur place — `KICAD-C2000-devkit` reste inchangé, c'est
l'état précédent, pas un doublon à synchroniser.

Cible : une commande numérique de convertisseur de puissance isolé, pilotée
par un C2000 et supervisée par un ESP32-C6 pour le Wi-Fi, la mise à jour
FOTA et un écran OLED d'état.

---

## Architecture

| Carte | Rôle |
|---|---|
| **Shield** | Alimentation complète (11-25V→5V isolé ×2, 3,3V isolation + protection), support mécanique des deux devkits, adaptation de brochage, conditionnement analogique, protections, embase OLED |
| **Cartes DC/DC enfichables** | Une par fonction de puissance, portent chacune l'isolation galvanique qu'elle exige (ou aucune), raccordées au shield par les 4 nappes |
| **Devkit C2000** | MCU, deux LDO 3,3V, JTAG, bouton reset, LED, cavalier de boot |
| **Devkit ESP32** | Wi-Fi, hôte FOTA, écran OLED SPI (`ER-OLEDM032-1B`) |

Liaison shield ↔ cartes DC/DC : quatre nappes IDC 2 × 10 détrompées,
`3V3_ISO`/`GND` en positions 1/2 puis alternance signal/masse stricte 1:1
sur les 16 positions suivantes. Écran OLED : nappe IDC 2 × 8 détrompée
dédiée, alimentée avec l'ESP32. Détail complet dans
[`doc/nappes-shield.md`](doc/nappes-shield.md).

---

## Alimentation — deux NCM3S1205MC indépendants

Le shield reçoit le 11-25V externe et produit lui-même ses rails isolés via
deux convertisseurs Murata NCM3S1205MC (9-36V→5V/600mA, isolation 5000VAC)
— un par domaine, pour ne pas coupler le bruit numérique sur l'alimentation
de l'isolation :

- **#1 « numérique »** → cavaliers indépendants vers +5V devkit C2000 et
  +5V devkit ESP32 (qui alimente aussi l'OLED).
- **#2 « isolation E/S »** → LDO 3,3V + zener de protection → `3V3_ISO` et
  `GND` sur les 4 nappes, pour le côté commande des isolateurs des cartes
  DC/DC.

Masses secondaires des deux modules reliées en un point unique (étoile),
même principe que le point VSS/VSSA unique des devkits. Détail et
justification dans [`doc/decisions.md`](doc/decisions.md) (#13).

---

## Le brochage est du code

[`doc/spec-devkit.md`](doc/spec-devkit.md) fait autorité pour le connecteur
devkit 2 × 28 (hérité de `KICAD-C2000-devkit`, toujours valable).
[`doc/nappes-shield.md`](doc/nappes-shield.md) décrit les quatre nappes DC/DC
et l'embase OLED. Contrairement au dépôt d'origine, **il n'y a pas de
générateur ici** — `shield.kicad_sch` est édité à la main dès le départ
(`gen_devkit.py` et consorts restent dans `KICAD-C2000-devkit`, hors sujet
pour ce dépôt).

Les schémas ne contiennent aucun fil : toute la connectivité passe par des
étiquettes globales posées exactement sur la broche concernée — convention
commune à tous les projets KiCad de l'atelier, documentée dans
[`../KICAD.md`](../KICAD.md).

---

## Concevoir avec un agent

Une part du travail est faite par un agent : lecture de datasheet, choix de
boîtier et création d'empreinte custom quand nécessaire (ex.
`lib/NCM3S1205MC.kicad_mod`), pose des composants, étiquetage. Le placement
fin et le routage restent manuels.

---

## Reproduire

KiCad 10 requis, `kicad-cli` dans le `PATH`.

```bash
kicad-cli sch erc --exit-code-violations shield.kicad_sch
kicad-cli pcb drc --exit-code-violations shield.kicad_pcb
```

---

## État d'avancement

Travail en cours, et le dire plutôt que de le masquer :

- **Schéma** — six feuilles (connecteurs devkit/ESP32/OLED, nappes DC/DC,
  alimentation, trois feuilles de chaînes de protection). Toutes les
  broches réelles portent une empreinte. L'ERC reste à ~190 violations, de
  la même famille que le reste de l'atelier (`pin_not_connected`,
  `isolated_pin_label` sur des réserves non pilotées) — pas corrigées
  d'office, voir `doc/decisions.md`.
- **PCB** — 85 empreintes importées depuis le schéma, **pas encore
  routé** (0 piste, 0 via). Le placement et le routage demandent des choix
  de conception qui n'ont pas leur place dans un script.
- **Connecteur devkit C2000/ESP32, nappes DC/DC, embase OLED** — brochage
  figé, labels vérifiés par ERC contre les coordonnées réelles des broches.

Points laissés ouverts — modèle de LDO 3,3V, référence du connecteur
11-25V, broche 7 de l'embase OLED, budget de courant des rails 5V — sont
listés en fin de [`doc/decisions.md`](doc/decisions.md). Ils attendent une
lecture de datasheet ou une mesure, pas une estimation.

---

## Décisions à ne pas défaire

Quinze décisions documentées dans [`doc/decisions.md`](doc/decisions.md),
chacune avec sa raison et ce qui casse si on la défait. Héritées de
`KICAD-C2000-devkit` (#1 à #12) ou propres à ce dépôt (#13 à #15 : migration
de la conversion isolée sur le shield, renumérotation des nappes, embase
OLED et assignation des empreintes).

---

## Licence

[CERN-OHL-S v2](LICENSE) — CERN Open Hardware Licence, fortement réciproque.

Tu peux étudier, modifier, fabriquer et distribuer ce matériel. En
contrepartie, si tu distribues un produit fondé dessus, ou une version
modifiée, tu dois publier les sources correspondantes sous la même licence.
