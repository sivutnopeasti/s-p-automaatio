"""Lähettää yhden viestin käsin annettuun osoitteeseen (asetussivun lomakkeelta).

Jos viesti on tyhjä, lähetetään kampanjaviesti (viesti.html + viesti.txt).
Jos aihe on tyhjä, käytetään viesti.txt:n aihetta.
"""
import os
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from laheta import LAHETTAJAN_NIMI, PORTTI, TILIT, lue_viesti, tilin_salasana


def main():
    vastaanottaja = os.environ.get("VASTAANOTTAJA", "").strip()
    aihe = os.environ.get("AIHE", "").strip()
    viesti = os.environ.get("VIESTI", "").replace("\r\n", "\n")
    tili = os.environ.get("LAHETTAJA", TILIT[0]).strip()
    salasana = os.environ.get("SMTP_SALASANA", "")

    if "@" not in vastaanottaja or "\n" in vastaanottaja or "," in vastaanottaja:
        sys.exit("Virheellinen vastaanottaja.")
    if tili not in TILIT:
        sys.exit(f"Tuntematon lähettäjä: {tili}")
    html = None
    if not viesti.strip():
        pohja_aihe, viesti = lue_viesti()
        aihe = aihe or pohja_aihe.replace("{nimi}", "").replace(" ,", ",").strip()
        viesti = viesti.replace("{nimi}", "").replace(" ,", ",")
        if os.path.exists("viesti.html"):
            with open("viesti.html", encoding="utf-8") as f:
                html = f.read().replace("{nimi}", "").replace(" ,", ",")
    if not aihe:
        sys.exit("Aihe puuttuu.")
    if not salasana:
        sys.exit("SMTP_SALASANA puuttuu.")

    msg = EmailMessage()
    msg["From"] = formataddr((LAHETTAJAN_NIMI, tili))
    msg["To"] = vastaanottaja
    msg["Subject"] = aihe
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=tili.split("@")[1])
    msg.set_content(viesti)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP_SSL("mail." + tili.split("@")[1], PORTTI, timeout=60) as s:
            s.login(tili, tilin_salasana(tili, salasana))
            s.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        oma = "salasana_" + tili.split("@")[1].split(".")[0]
        print(f"::error title=Kirjautuminen epäonnistui::Palvelin hylkäsi tilin {tili} salasanan "
              f"({e.smtp_code}). Viestiä ei lähetetty. Tarkista salasana webmailista ja lisää se "
              f"tarvittaessa secretiksi {oma}. Voit testata asetussivun Testaa kirjautuminen -napilla.")
        sys.exit(1)
    except (OSError, smtplib.SMTPException) as e:
        print(f"::error title=Lähetys epäonnistui::{tili} -> {vastaanottaja}: {type(e).__name__}: {e}")
        sys.exit(1)
    print(f"Lähetetty{' (kampanjaviesti)' if html else ''}: {tili} -> {vastaanottaja}")


if __name__ == "__main__":
    main()
