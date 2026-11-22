"""Lähettää yhden viestin käsin annettuun osoitteeseen (asetussivun lomakkeelta)."""
import os
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from laheta import LAHETTAJAN_NIMI, PORTTI, TILIT


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
    if not aihe or not viesti.strip():
        sys.exit("Aihe ja viesti ovat pakollisia.")
    if not salasana:
        sys.exit("SMTP_SALASANA puuttuu.")

    msg = EmailMessage()
    msg["From"] = formataddr((LAHETTAJAN_NIMI, tili))
    msg["To"] = vastaanottaja
    msg["Subject"] = aihe
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=tili.split("@")[1])
    msg.set_content(viesti)

    with smtplib.SMTP_SSL("mail." + tili.split("@")[1], PORTTI, timeout=60) as s:
        s.login(tili, salasana)
        s.send_message(msg)
    print(f"Lähetetty: {tili} -> {vastaanottaja}")


if __name__ == "__main__":
    main()
