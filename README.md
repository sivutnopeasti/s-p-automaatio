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
| `docs/index.html` | Asetussivu liukusäätimellä (GitHub Pages) |
| `laheta.py` | Lähetysskripti |
| `yksi.py` | Yksittäisen viestin lähetys (asetussivun lomake) |

## Miten toimii

GitHub Actions ajaa `laheta.py`:n ma–pe klo 7 UTC (9 tai 10 Suomen aikaa). Skripti lähettää päivän määrän verran viestejä listan alusta, 30–90 sekunnin tauoilla, ja kirjaa ne `lahetetyt.csv`:hen. Salasana tulee repon secretistä `salasana`. SMTP: `mail.<domain>`, portti 465 (SSL).

## Asetussivu

Osoite: https://sivutnopeasti.github.io/s-p-automaatio/

Pages otetaan käyttöön kerran: Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, kansio `/docs`. Pagesiin julkaistaan vain `docs`-kansio.

 Syötä kerran GitHub fine-grained token, jolla on tähän repoon oikeudet *Contents: Read and write* ja *Actions: Read and write*. Liukusäätimellä valitaan määrä päivässä ja ruksilla lähetys päälle/pois.

## Testaus

Actions → *Lähetä sähköpostit* → *Run workflow*: kuivaharjoitus on oletuksena päällä, jolloin mitään ei lähetetä, vaan lokiin tulostetaan kenelle olisi lähtenyt.

## Yksittäinen viesti

Asetussivun lomakkeella voi lähettää yhden viestin mihin tahansa osoitteeseen. Lomake käynnistää työnkulun *Lähetä yksi viesti*, ja viesti lähtee noin minuutissa. Huom: julkisessa repossa työnkulun ajot (ja siis osoite ja viesti) näkyvät kaikille.
