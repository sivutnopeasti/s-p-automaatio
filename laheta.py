"""Lähettää päivän sähköpostit listasta SMTP:llä, vuorotellen kahdelta tililtä.

Asetukset: config.json (paivittainen_maara, kaytossa)
Vastaanottajat: lista.csv (sarakkeet email, nimi)
Viesti: viesti.txt (ensimmäinen rivi "Aihe: ...", {nimi} korvataan)
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
LAHETTAJAN_NIMI = "Visio"
PORTTI = 465
VIIVE_SEK = (30, 90)  # satunnainen tauko viestien välillä


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
    tanaan_lahetetty = sum(1 for r in lue_csv("lahetetyt.csv") if r["aika"].startswith(tanaan))
    jono = jono[: max(0, maara - tanaan_lahetetty)]
    print(f"Päivän raja {maara}, tänään jo {tanaan_lahetetty}, nyt lähetetään {len(jono)}.")
    if not jono:
        return

    aihe_pohja, runko_pohja = lue_viesti()
    yhteydet = {}
    try:
        for i, (email, nimi) in enumerate(jono):
            tili = TILIT[i % len(TILIT)]
            kutsu = nimi or "siellä"
            msg = EmailMessage()
            msg["From"] = formataddr((LAHETTAJAN_NIMI, tili))
            msg["To"] = email
            msg["Subject"] = aihe_pohja.replace("{nimi}", kutsu)
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid(domain=tili.split("@")[1])
            msg["List-Unsubscribe"] = f"<mailto:{tili}?subject=unsubscribe>"
            msg.set_content(runko_pohja.replace("{nimi}", kutsu))

            if kuivaharjoitus:
                print(f"[KUIVA] {tili} -> {email}: {msg['Subject']}")
                continue

            for yritys in range(2):
                try:
                    if tili not in yhteydet:
                        palvelin = "mail." + tili.split("@")[1]
                        s = smtplib.SMTP_SSL(palvelin, PORTTI, timeout=60)
                        s.login(tili, salasana)
                        yhteydet[tili] = s
                    yhteydet[tili].send_message(msg)
                    break
                except smtplib.SMTPServerDisconnected:
                    yhteydet.pop(tili, None)  # yhteys katkesi tauon aikana, avataan uusi
                    if yritys:
                        raise

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
