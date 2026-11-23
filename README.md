# Säpöautomaatio

Yksinkertainen sähköpostiautomaatio: lähettää päivittäin säädettävän määrän viestejä CSV-listalta SMTP:llä, vuorotellen tileiltä `ugc@visioreach.fi` ja `ugc@visiosites.fi`.

## Tiedostot

| Tiedosto | Mitä |
|---|---|
| `lista.csv` | Vastaanottajat, sarakkeet `email,nimi,yritys` (nimi ja yritys vapaaehtoisia) |
| `suodata.py` | Muuntaa YTJ-yrityslistan `lista.csv`:ksi: `python suodata.py "YTJ....csv"` |
| `viesti.txt` | Viesti. Ensimmäinen rivi `Aihe: ...`, `{nimi}` korvataan nimellä (ilman nimeä "Hei {nimi}," → "Hei,") |
| `viesti.html` | Viestin HTML-versio (UGC Suomen tyyli). Lähetetään tekstiversion rinnalla, `{nimi}` toimii samoin |
| `config.json` | `paivittainen_maara` ja `kaytossa` (päivitetään asetussivulta) |
| `lahetetyt.csv` | Kenelle on jo lähetetty. Kenellekään ei lähetetä kahdesti |
| `estetyt.csv` | Osoitteet, joille ei lähetetä koskaan (esim. peruutukset) |
| `docs/index.html` | Asetussivu liukusäätimellä (GitHub Pages) |
| `laheta.py` | Lähetysskripti |
| `testaa.py` | Kirjautumistesti molemmille tileille (SMTP 465/587, IMAP 993), ei lähetä mitään |
| `yksi.py` | Yksittäisen viestin lähetys (asetussivun lomake) |

## Miten toimii

GitHub Actions yrittää ajaa `laheta.py`:n ma–pe kerran tunnissa klo 9–17 (talviaika). Ensimmäinen onnistunut ajo lähettää päivän määrän, myöhemmät eivät lähetä mitään, ellei määrää nosteta. Skripti lähettää päivän määrän verran viestejä listan alusta, 30–90 sekunnin tauoilla, ja kirjaa ne `lahetetyt.csv`:hen. Salasana tulee repon secretistä `salasana`. SMTP: `mail.<domain>`, portti 465 (SSL).

## Asetussivu

Osoite: https://sivutnopeasti.github.io/s-p-automaatio/

Pages otetaan käyttöön kerran: Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, kansio `/docs`. Pagesiin julkaistaan vain `docs`-kansio.

 Syötä kerran GitHub fine-grained token, jolla on tähän repoon oikeudet *Contents: Read and write* ja *Actions: Read and write*. Liukusäätimellä valitaan määrä päivässä ja ruksilla lähetys päälle/pois.

## Testaus

Actions → *Lähetä sähköpostit* → *Run workflow*: kuivaharjoitus on oletuksena päällä, jolloin mitään ei lähetetä, vaan lokiin tulostetaan kenelle olisi lähtenyt.

## Yksittäinen viesti

Asetussivun lomakkeella voi lähettää yhden viestin mihin tahansa osoitteeseen. Lomake käynnistää työnkulun *Lähetä yksi viesti*, ja viesti lähtee noin minuutissa. Huom: julkisessa repossa työnkulun ajot (ja siis osoite ja viesti) näkyvät kaikille.

## Vastaukset

Asetussivun *Vastaukset*-osio näyttää molempien tilien saapuneet viestit keskusteluina, ja niihin voi vastata suoraan. Vastaus lähtee samalta tililtä, jolle viesti tuli, ja se jatkaa samaa sähköpostiketjua.

- Työnkulku *Postilaatikko* hakee viestit IMAPilla (mail.<domain>:993) 15 minuutin välein tai *Päivitä nyt* -napista. Haku kattaa 90 päivää.
- Viestit tallennetaan haaraan `postilaatikko` **salattuna** (AES-GCM, avain johdettu secretistä `salasana`). Sivu purkaa ne selaimessa, kun syötät saman salasanan.
- Vastaukset lähetetään salattuina työnkulun syötteenä, joten osoitteet ja tekstit eivät näy julkisissa lokeissa. Vastaus tallennetaan myös tilin Lähetetyt-kansioon, joten se näkyy myös webmailissa.
