# Säpöautomaatio

Yksinkertainen sähköpostiautomaatio: lähettää päivittäin säädettävän määrän viestejä CSV-listalta SMTP:llä, vuorotellen tileiltä `ugc@visioreach.fi` ja `ugc@visiosites.fi`.

## Tiedostot

| Tiedosto | Mitä |
|---|---|
| `lista.csv` | Vastaanottajat, sarakkeet `email,nimi` (nimi vapaaehtoinen) |
| `viesti.txt` | Viesti. Ensimmäinen rivi `Aihe: ...`, `{nimi}` korvataan nimellä |
| `config.json` | `paivittainen_maara` ja `kaytossa` (päivitetään asetussivulta) |
| `lahetetyt.csv` | Kenelle on jo lähetetty. Kenellekään ei lähetetä kahdesti |
| `estetyt.csv` | Osoitteet, joille ei lähetetä koskaan (esim. peruutukset) |
| `index.html` | Asetussivu liukusäätimellä |
| `laheta.py` | Lähetysskripti |

## Miten toimii

GitHub Actions ajaa `laheta.py`:n ma–pe klo 7 UTC (9 tai 10 Suomen aikaa). Skripti lähettää päivän määrän verran viestejä listan alusta, 30–90 sekunnin tauoilla, ja kirjaa ne `lahetetyt.csv`:hen. Salasana tulee repon secretistä `salasana`. SMTP: `mail.<domain>`, portti 465 (SSL).

## Asetussivu

Avaa `index.html` selaimessa (tai GitHub Pagesista). Syötä kerran GitHub fine-grained token, jolla on tähän repoon oikeus *Contents: Read and write*. Liukusäätimellä valitaan määrä päivässä ja ruksilla lähetys päälle/pois.

## Testaus

Actions → *Lähetä sähköpostit* → *Run workflow*: kuivaharjoitus on oletuksena päällä, jolloin mitään ei lähetetä, vaan lokiin tulostetaan kenelle olisi lähtenyt.
