"""Lähettää päivän sähköpostit listasta SMTP:llä, vuorotellen kahdelta tililtä.

Asetukset: config.json (paivittainen_maara, kaytossa)
Vastaanottajat: lista.csv (sarakkeet email, nimi)
Viesti: viesti.txt (ensimmäinen rivi "Aihe: ...", {nimi} korvataan)
       viesti.html (valinnainen HTML-versio, lähetetään tekstiversion rinnalla)
Lähetetyt: lahetetyt.csv (kenellekään ei lähetetä kahdesti)
Estetyt: estetyt.csv (näille ei lähetetä koskaan)
Salasana: ympäristömuuttuja SMTP_SALASANA (GitHubin secret "salasana")
"""
import csv
import json
import os
import random
import smtplib
import sys
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

TILIT = ["ugc@visioreach.fi", "ugc@visiosites.fi"]
LAHETTAJAN_NIMI = "UGC Suomi"
PORTTI = 465
VIIVE_SEK = (30, 90)  # satunnainen tauko viestien välillä


def tilin_salasana(tili, oletus):
    """Tilikohtainen salasana, jos secret on asetettu (esim. SMTP_SALASANA_VISIOSITES),
    muuten yhteinen salasana."""
    nimi = "SMTP_SALASANA_" + tili.split("@")[1].split(".")[0].upper()
    return os.environ.get(nimi) or oletus


def lue_csv(polku):
    if not os.path.exists(polku):
        return []
    with open(polku, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def lue_viesti():
    with open("viesti.txt", encoding="utf-8") as f:
        rivit = f.read().splitlines()
    if not rivit or not rivit[0].lower().startswith("aihe:"):
        sys.exit("viesti.txt: ensimmäisen rivin pitää olla 'Aihe: ...'")
    aihe = rivit[0].split(":", 1)[1].strip()
    runko = "\n".join(rivit[1:]).strip() + "\n"
    return aihe, runko


def main():
    kuivaharjoitus = os.environ.get("KUIVAHARJOITUS", "").lower() in ("1", "true", "kylla")
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)
    if not config.get("kaytossa") and not kuivaharjoitus:
        print("Lähetys ei ole käytössä (config.json: kaytossa = false).")
        return
    maara = max(0, int(config.get("paivittainen_maara", 0)))

    salasana = os.environ.get("SMTP_SALASANA", "")
    if not salasana and not kuivaharjoitus:
        sys.exit("SMTP_SALASANA puuttuu.")

    lahetetyt = {r["email"].strip().lower() for r in lue_csv("lahetetyt.csv")}
    estetyt = {r["email"].strip().lower() for r in lue_csv("estetyt.csv")}
    jono, nahdyt = [], set()
    for r in lue_csv("lista.csv"):
        email = (r.get("email") or "").strip()
        avain = email.lower()
        if "@" not in email or avain in lahetetyt or avain in estetyt or avain in nahdyt:
            continue
        nahdyt.add(avain)
        jono.append((email, (r.get("nimi") or "").strip()))

    tanaan = datetime.now(timezone.utc).date().isoformat()
    tanaan_rivit = [r for r in lue_csv("lahetetyt.csv") if r["aika"].startswith(tanaan)]
    tanaan_lahetetty = len(tanaan_rivit)
    per_tili = {t: sum(1 for r in tanaan_rivit if r.get("lahettaja") == t) for t in TILIT}
    jono = jono[: max(0, maara - tanaan_lahetetty)]
    print(f"Päivän raja {maara}, tänään jo {tanaan_lahetetty}, nyt lähetetään {len(jono)}.")
    if not jono:
        return

    aihe_pohja, runko_pohja = lue_viesti()
    html_pohja = None
    if os.path.exists("viesti.html"):
        with open("viesti.html", encoding="utf-8") as f:
            html_pohja = f.read()
    yhteydet, rikki = {}, set()

    def rakenna(tili, email, kutsu):
        msg = EmailMessage()
        msg["From"] = formataddr((LAHETTAJAN_NIMI, tili))
        msg["To"] = email
        msg["Subject"] = aihe_pohja.replace("{nimi}", kutsu).replace(" ,", ",").strip()
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=tili.split("@")[1])
        msg["List-Unsubscribe"] = f"<mailto:{tili}?subject=unsubscribe>"
        msg.set_content(runko_pohja.replace("{nimi}", kutsu).replace(" ,", ","))
        if html_pohja:
            msg.add_alternative(html_pohja.replace("{nimi}", kutsu).replace(" ,", ","), subtype="html")
        return msg

    def laheta_tililta(tili, msg):
        for yritys in range(2):
            try:
                if tili not in yhteydet:
                    s = smtplib.SMTP_SSL("mail." + tili.split("@")[1], PORTTI, timeout=60)
                    s.login(tili, tilin_salasana(tili, salasana))
                    yhteydet[tili] = s
                yhteydet[tili].send_message(msg)
                return
            except smtplib.SMTPServerDisconnected:
                yhteydet.pop(tili, None)  # yhteys katkesi tauon aikana, avataan uusi
                if yritys:
                    raise

    try:
        for i, (email, nimi) in enumerate(jono):
            kutsu = nimi  # ilman nimeä "Hei {nimi}," -> "Hei,"
            while True:
                toimivat = [t for t in TILIT if t not in rikki]
                if not toimivat:
                    sys.exit("Kirjautuminen epäonnistui kaikilla tileillä.")
                tili = min(toimivat, key=lambda t: per_tili[t])  # tasan toimiville tileille
                msg = rakenna(tili, email, kutsu)
                if kuivaharjoitus:
                    break
                try:
                    laheta_tililta(tili, msg)
                    break
                except smtplib.SMTPAuthenticationError:
                    print(f"VIRHE: kirjautuminen epäonnistui tilillä {tili}, käytetään muita tilejä.")
                    rikki.add(tili)
            per_tili[tili] += 1
            if kuivaharjoitus:
                print(f"[KUIVA] {tili} -> {email}: {msg['Subject']}")
                continue

            with open("lahetetyt.csv", "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), email, tili])
            print(f"Lähetetty {i + 1}/{len(jono)}: {tili} -> {email}")
            if i < len(jono) - 1:
                time.sleep(random.uniform(*VIIVE_SEK))
    finally:
        for s in yhteydet.values():
            try:
                s.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
