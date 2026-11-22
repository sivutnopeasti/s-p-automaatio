"""Hakee molempien tilien saapuneet ja lähetetyt vastaukset IMAPilla ja
kirjoittaa ne salattuna tiedostoon postilaatikko.json (vain salasanalla luettavissa).

Ympäristö: SMTP_SALASANA (sama salasana IMAPille ja salaukselle).
"""
import email
import hashlib
import html
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import getaddresses, parseaddr, parsedate_to_datetime

from laheta import TILIT, tilin_salasana
from salaus import salaa

PAIVIA = 90          # kuinka kauas taaksepäin haetaan
MAKS_PER_KANSIO = 300
MAKS_TEKSTI = 20000


def dekoodaa(arvo):
    if not arvo:
        return ""
    try:
        return str(make_header(decode_header(arvo)))
    except Exception:
        return str(arvo)


def html_tekstiksi(h):
    h = re.sub(r"(?is)<(script|style|head).*?</\1>", "", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", h).strip()


def runko(msg):
    teksti, htmlosa = None, None
    for osa in msg.walk() if msg.is_multipart() else [msg]:
        if osa.get_content_maintype() == "multipart" or osa.get_filename():
            continue
        tyyppi = osa.get_content_type()
        try:
            data = osa.get_payload(decode=True) or b""
            sisalto = data.decode(osa.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            continue
        if tyyppi == "text/plain" and teksti is None:
            teksti = sisalto
        elif tyyppi == "text/html" and htmlosa is None:
            htmlosa = sisalto
    if teksti is None and htmlosa is not None:
        teksti = html_tekstiksi(htmlosa)
    return (teksti or "").strip()[:MAKS_TEKSTI]


def lahetetyt_kansio(imap):
    typ, rivit = imap.list()
    nimet = []
    for r in rivit or []:
        r = r.decode(errors="replace")
        nimi = r.rsplit(' "', 1)[-1].strip('"') if ' "' in r else r.split()[-1]
        if "\\Sent" in r:
            return nimi
        nimet.append(nimi)
    for ehdokas in ("INBOX.Sent", "Sent", "INBOX.Sent Items", "Sent Items"):
        if ehdokas in nimet:
            return ehdokas
    return None


def hae_kansio(imap, kansio, tili, suunta):
    typ, _ = imap.select(f'"{kansio}"', readonly=True)
    if typ != "OK":
        return []
    alku = (datetime.now() - timedelta(days=PAIVIA)).strftime("%d-%b-%Y")
    typ, data = imap.search(None, "SINCE", alku)
    idt = data[0].split()[-MAKS_PER_KANSIO:] if typ == "OK" and data and data[0] else []
    viestit = []
    for i in idt:
        typ, osat = imap.fetch(i, "(BODY.PEEK[])")
        if typ != "OK" or not osat or not isinstance(osat[0], tuple):
            continue
        msg = email.message_from_bytes(osat[0][1])
        lah_nimi, lah = parseaddr(dekoodaa(msg.get("From")))
        vastaanottajat = [a for _, a in getaddresses([dekoodaa(msg.get("To", ""))]) if a]
        try:
            pvm = parsedate_to_datetime(msg.get("Date")).astimezone(timezone.utc).isoformat(timespec="seconds")
        except Exception:
            pvm = ""
        vastapuoli = (vastaanottajat[0] if suunta == "out" and vastaanottajat else lah).lower()
        viestit.append({
            "tili": tili,
            "suunta": suunta,
            "vastapuoli": vastapuoli,
            "lahettaja": lah,
            "lahettaja_nimi": lah_nimi,
            "vastaanottaja": ", ".join(vastaanottajat),
            "aihe": dekoodaa(msg.get("Subject")),
            "pvm": pvm,
            "message_id": (msg.get("Message-ID") or "").strip(),
            "references": " ".join((msg.get("References") or "").split()),
            "teksti": runko(msg),
        })
    return viestit


def hae_kaikki(salasana):
    viestit, virheet = [], []
    for tili in TILIT:
        try:
            imap = imaplib.IMAP4_SSL("mail." + tili.split("@")[1], 993, timeout=60)
            imap.login(tili, tilin_salasana(tili, salasana))
            viestit += hae_kansio(imap, "INBOX", tili, "in")
            sent = lahetetyt_kansio(imap)
            if sent:
                viestit += hae_kansio(imap, sent, tili, "out")
            imap.logout()
        except Exception as e:
            virheet.append(f"{tili}: {type(e).__name__}")
            print(f"Virhe tilillä {tili}: {type(e).__name__}: {e}", file=sys.stderr)
    viestit = [v for v in viestit if v["vastapuoli"] not in TILIT]
    viestit.sort(key=lambda v: v["pvm"])
    return viestit, virheet


def main():
    salasana = os.environ.get("SMTP_SALASANA", "")
    if not salasana:
        sys.exit("SMTP_SALASANA puuttuu.")
    viestit, virheet = hae_kaikki(salasana)
    tiiviste = hashlib.sha256(json.dumps(viestit, sort_keys=True).encode()).hexdigest()[:16]
    vanha = {}
    if os.path.exists("postilaatikko.json"):
        with open("postilaatikko.json", encoding="utf-8") as f:
            vanha = json.load(f)
    if vanha.get("tiiviste") == tiiviste and not virheet:
        print(f"Ei muutoksia ({len(viestit)} viestiä).")
        return
    sisalto = {"paivitetty": datetime.now(timezone.utc).isoformat(timespec="seconds"), "virheet": virheet, "viestit": viestit}
    with open("postilaatikko.json", "w", encoding="utf-8") as f:
        json.dump({"tiiviste": tiiviste, **salaa(sisalto, salasana)}, f)
    print(f"Tallennettu {len(viestit)} viestiä." + (f" Virheet: {virheet}" if virheet else ""))


if __name__ == "__main__":
    main()
