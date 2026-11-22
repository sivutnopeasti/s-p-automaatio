"""Lähettää vastauksen ketjuun. Syöte tulee asetussivulta salattuna
(ympäristömuuttuja VASTAUS), jotta osoite ja teksti eivät näy julkisissa lokeissa.

Purettu syöte: {tili, vastaanottaja, aihe, teksti, in_reply_to, references, lainaus}
Vastaus tallennetaan myös tilin Lähetetyt-kansioon, jotta se näkyy ketjussa.
"""
import imaplib
import json
import os
import smtplib
import sys
import time
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from laheta import LAHETTAJAN_NIMI, PORTTI, TILIT, tilin_salasana
from postilaatikko import lahetetyt_kansio
from salaus import pura


def main():
    salasana = os.environ.get("SMTP_SALASANA", "")
    if not salasana:
        sys.exit("SMTP_SALASANA puuttuu.")
    try:
        v = pura(json.loads(os.environ["VASTAUS"]), salasana)
    except Exception:
        sys.exit("Vastauksen purku epäonnistui (väärä salasana asetussivulla?).")

    tili = v.get("tili", "")
    vastaanottaja = (v.get("vastaanottaja") or "").strip()
    if tili not in TILIT:
        sys.exit("Tuntematon tili.")
    if "@" not in vastaanottaja or any(c in vastaanottaja for c in ",;\r\n"):
        sys.exit("Virheellinen vastaanottaja.")
    teksti = (v.get("teksti") or "").strip()
    if not teksti:
        sys.exit("Tyhjä vastaus.")

    aihe = (v.get("aihe") or "").strip()
    if not aihe.lower().startswith(("re:", "vs:")):
        aihe = "Re: " + aihe
    msg = EmailMessage()
    msg["From"] = formataddr((LAHETTAJAN_NIMI, tili))
    msg["To"] = vastaanottaja
    msg["Subject"] = aihe
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=tili.split("@")[1])
    irt = (v.get("in_reply_to") or "").strip()
    if irt:
        msg["In-Reply-To"] = irt
        msg["References"] = ((v.get("references") or "") + " " + irt).strip()
    lainaus = (v.get("lainaus") or "").strip()
    if lainaus:
        teksti += "\n\n" + "\n".join("> " + r for r in lainaus.splitlines())
    msg.set_content(teksti + "\n")

    domain = tili.split("@")[1]
    with smtplib.SMTP_SSL("mail." + domain, PORTTI, timeout=60) as s:
        s.login(tili, tilin_salasana(tili, salasana))
        s.send_message(msg)
    print(f"Vastaus lähetetty tililtä {tili}.")

    try:
        imap = imaplib.IMAP4_SSL("mail." + domain, 993, timeout=60)
        imap.login(tili, tilin_salasana(tili, salasana))
        kansio = lahetetyt_kansio(imap)
        if kansio:
            imap.append(f'"{kansio}"', "\\Seen", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        imap.logout()
    except Exception as e:
        print(f"Kopio Lähetetyt-kansioon epäonnistui: {type(e).__name__}", file=sys.stderr)


if __name__ == "__main__":
    main()
