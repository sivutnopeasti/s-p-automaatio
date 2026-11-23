"""Testaa kirjautumisen molemmille tileille lähettämättä mitään.

Kokeilee SMTP 465 (SSL), SMTP 587 (STARTTLS) ja IMAP 993 sekä yhteisellä
salasanalla että tilikohtaisella salasanalla (jos asetettu).
Tulokset tulostetaan GitHubin huomautuksina, jotka asetussivu näyttää.
"""
import imaplib
import os
import smtplib
import socket
import ssl

from laheta import TILIT


def kokeile(nimi, fn):
    try:
        fn()
        return f"{nimi} OK"
    except smtplib.SMTPAuthenticationError as e:
        return f"{nimi} HYLÄTTY ({e.smtp_code})"
    except imaplib.IMAP4.error as e:
        return f"{nimi} HYLÄTTY ({str(e)[:60]})"
    except Exception as e:
        return f"{nimi} VIRHE ({type(e).__name__})"


def smtp465(palvelin, tili, pw):
    with smtplib.SMTP_SSL(palvelin, 465, timeout=30) as s:
        s.login(tili, pw)


def smtp587(palvelin, tili, pw):
    with smtplib.SMTP(palvelin, 587, timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(tili, pw)


def imap993(palvelin, tili, pw):
    m = imaplib.IMAP4_SSL(palvelin, 993, timeout=30)
    try:
        m.login(tili, pw)
    finally:
        try:
            m.logout()
        except Exception:
            pass


def main():
    yhteinen = os.environ.get("SMTP_SALASANA", "")
    for tili in TILIT:
        domain = tili.split("@")[1]
        palvelin = "mail." + domain
        try:
            ip = socket.gethostbyname(palvelin)
            try:
                nimi = socket.gethostbyaddr(ip)[0]
            except Exception:
                nimi = "?"
        except Exception:
            ip, nimi = "ei löydy", "?"
        oma_avain = "SMTP_SALASANA_" + domain.split(".")[0].upper()
        oma = os.environ.get(oma_avain, "")
        salasanat = [("yhteinen salasana (salasana)", yhteinen)]
        if oma:
            salasanat.append((f"oma salasana (salasana_{domain.split('.')[0]})", oma))
        for kuvaus, pw in salasanat:
            if not pw:
                print(f"::warning title={tili}::{kuvaus} puuttuu")
                continue
            tulokset = [kokeile("SMTP 465", lambda: smtp465(palvelin, tili, pw)),
                        kokeile("SMTP 587", lambda: smtp587(palvelin, tili, pw)),
                        kokeile("IMAP 993", lambda: imap993(palvelin, tili, pw))]
            ok = all(t.endswith("OK") for t in tulokset)
            taso = "notice" if ok else "error"
            print(f"::{taso} title={tili}::{kuvaus}: {', '.join(tulokset)}. Palvelin {palvelin} = {ip} ({nimi})")
    print("Valmis.")


if __name__ == "__main__":
    main()
