"""Muuntaa YTJ-yrityslistan (iso CSV) automaation lista.csv:ksi.

Käyttö: python suodata.py "YTJ ... .csv"  ->  kirjoittaa lista.csv

Mukaan otetaan rivit, joilla
- on sähköpostiosoite, joka näyttää kelvolliselta
- Yrityksen status on Aktiivinen
- Yritysmuoto ei ole asunto- tai kiinteistöyhtiö
- Kannattaako kontaktoida? ei ole "Ei"
- Viesti lähetetty on tyhjä (heille ei ole jo lähetetty)
Sama osoite otetaan vain kerran. Jo olemassa olevan lista.csv:n järjestys säilyy,
ja uudet osoitteet lisätään loppuun.
"""
import csv
import re
import sys

POIS_YRITYSMUODOT = {"Keskinäinen kiinteistöosakeyhtiö", "Asunto-osakeyhtiö"}
EMAIL = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
ROSKA = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", "example.com", "sentry", "wixpress")


def main(lahde, kohde="lista.csv"):
    vanhat, nahdyt = [], set()
    try:
        with open(kohde, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                e = (r.get("email") or "").strip()
                if e and e.lower() not in nahdyt:
                    nahdyt.add(e.lower())
                    vanhat.append([e, r.get("nimi", ""), r.get("yritys", "")])
    except FileNotFoundError:
        pass

    uudet, syyt = [], {}
    with open(lahde, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            email = (r.get("Sähköposti") or "").strip()
            syy = None
            if not email:
                syy = "ei sähköpostia"
            elif not EMAIL.match(email) or email.lower().endswith(ROSKA) or any(x in email.lower() for x in ROSKA):
                syy = "virheellinen sähköposti"
            elif (r.get("Yrityksen status") or "").strip() != "Aktiivinen":
                syy = "ei aktiivinen"
            elif (r.get("Yritysmuoto") or "").strip() in POIS_YRITYSMUODOT:
                syy = "kiinteistöyhtiö"
            elif (r.get("Kannattaako kontaktoida?") or "").strip().lower() == "ei":
                syy = "ei kannata kontaktoida"
            elif (r.get("Viesti lähetetty") or "").strip():
                syy = "viesti jo lähetetty"
            elif email.lower() in nahdyt:
                syy = "tuplaosoite"
            if syy:
                syyt[syy] = syyt.get(syy, 0) + 1
                continue
            nahdyt.add(email.lower())
            uudet.append([email, "", (r.get("Nimi") or "").strip()])

    with open(kohde, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["email", "nimi", "yritys"])
        w.writerows(vanhat + uudet)
    print(f"lista.csv: {len(vanhat)} vanhaa + {len(uudet)} uutta = {len(vanhat) + len(uudet)} osoitetta")
    for s, n in sorted(syyt.items(), key=lambda x: -x[1]):
        print(f"  ohitettu ({s}): {n}")


if __name__ == "__main__":
    main(sys.argv[1])
