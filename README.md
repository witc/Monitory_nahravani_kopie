[[_TOC_]]

# Seznameni

Repo obsahuje 2 nastroje potrebne k nahrani a kalibraci FENCEE monitoru MX. Prvni tool nahrava program + MAC do MCU a zaroven testuje RF (TX + RX).
Druhy nastroj slouzi k bezdratovemu kalibrovani mereni impulsu na generatoru. To je provadeno pres USB RF link LoRa - ktery se pred kalibraci sparuje s kalibrovanym monitorem a dale s nim projde celou kalibracni rutinu.

## Soubory:

Oba nastroje pouzivaji nektere dalsi tridy spolecne - napr. USB_Rf_Link pro komunikaci s MX ci pripravkem pro prepnuti RF switche z Generatoru na spektralni analyzator

### Nastroj pro nahravani programu:
-Nazev MX_Flasher.py
Pro nahravani jsou nutne 2 soubory:
1. FENCEE_Monitor.binary
2. FENCEE_Monitor.map

Vsechny uspesne nahrane desky jsou zaznamenany v SQLite databazy s vlastnim vysledkem testu

### Nastroj pro kalibraci pulzu:
Nazev MX_PulseCalibByRf.py

## Nastaveni:
Nektere parametry je mozne menit pres MxFlasherConfig.conf  
jsou to:
- IP adresy pripojenych pristroju
- minimalni vysilaci vykon pro projduti TX testem

## Postup kalibrace:

kalibracni procesy a podrobnejsji popis je ulozen v repu zde: https://jirikrsek.visualstudio.com/FENCEE%20MONITOR/_wiki/wikis/FENCEE-MONITOR.wiki/34/Kalibrace
