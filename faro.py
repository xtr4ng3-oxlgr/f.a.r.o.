from __future__ import annotations

import csv
import html
import json
import os
import re
import shutil
import sqlite3
import sys
import traceback
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception as exc:
    print("FARO requiere Tkinter instalado con Python.")
    print(exc)
    raise SystemExit(1)


APP_NAME = "FARO"
APP_VERSION = "5.4.0"
AUTHOR = "xtr4ng3"
APP_TITLE = "FARO v5.4 - Protección familiar contra estafas"


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "faro_data"
REPORTS_DIR = DATA_DIR / "reports"
EXPORTS_DIR = DATA_DIR / "exports"
BACKUPS_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "faro.sqlite3"
ERROR_LOG = DATA_DIR / "faro_error.log"


DEFAULT_PHRASES = [
    ("familia_numero_nuevo", "Soy tu nieto, cambié de número", 35),
    ("familia_numero_nuevo", "Soy tu hijo, cambié de número", 35),
    ("familia_numero_nuevo", "Estoy usando otro número", 30),
    ("familia_urgencia", "Me mandé una cagada", 40),
    ("familia_urgencia", "Estoy en un problema y necesito plata", 45),
    ("familia_urgencia", "No tengo plata, estoy acá", 35),
    ("familia_urgencia", "Me pasó algo y necesito ayuda urgente", 40),
    ("secreto", "No le digas a nadie", 50),
    ("secreto", "No avises a mamá", 50),
    ("secreto", "Esto queda entre nosotros", 40),
    ("codigo", "Pasame el código", 55),
    ("codigo", "Te va a llegar un código", 55),
    ("codigo", "Necesito el token", 55),
    ("codigo", "Decime la clave", 60),
    ("banco", "Soy del banco", 40),
    ("banco", "Tu cuenta fue bloqueada", 45),
    ("banco", "Necesito validar tus datos", 45),
    ("banco", "Se detectó una transferencia sospechosa", 45),
    ("soporte", "Instalá esta aplicación", 60),
    ("soporte", "Necesito controlar tu teléfono", 65),
    ("soporte", "Abrí AnyDesk", 70),
    ("premio", "Ganaste un premio", 35),
    ("premio", "Tenés un beneficio para cobrar", 35),
    ("link", "Entrá a este link", 40),
    ("transferencia", "Pasame el alias", 40),
    ("transferencia", "Mandame una transferencia urgente", 50),
    ("comprobante", "Te mandé un comprobante", 25),
]



OFFICIAL_EMAIL_PROFILES = {
    "ARCA / ex AFIP": {
        "domains": ["arca.gob.ar"],
        "watch_domains": ["afip.gob.ar"],
        "report": "phishing@arca.gob.ar",
        "rules": [
            "ARCA no solicita pagos ni datos personales por mail.",
            "Las notificaciones fiscales se verifican en Domicilio Fiscal Electrónico.",
            "Mensajes que invocan AFIP o reclaman deuda/pago por link son de alto riesgo."
        ],
        "keywords": ["arca", "afip", "fiscal", "deuda", "impositiva", "clave fiscal", "fiscalización", "fiscalizacion", "monotributo"]
    },
    "ANSES": {
        "domains": ["anses.gob.ar"],
        "report": "denuncias@anses.gob.ar",
        "rules": [
            "ANSES no pide datos personales, bancarios ni claves por correo, SMS, WhatsApp o teléfono.",
            "Los canales seguros son Mi ANSES, Atención Virtual y el 130."
        ],
        "keywords": ["anses", "jubilación", "jubilacion", "pensión", "pension", "beneficio", "bono", "auh", "progresar"]
    },
    "Banco Nación": {
        "domains": ["bna.com.ar"],
        "report": "",
        "rules": [
            "El banco no solicita información confidencial por email, mensajes ni llamadas.",
            "Conviene ingresar escribiendo la web oficial manualmente."
        ],
        "keywords": ["banco nación", "banco nacion", "bna", "home banking", "token", "clave", "cuenta"]
    },
    "Santander Argentina": {
        "domains": ["santander.com.ar", "mails.santander.com.ar", "novedades.santander.com.ar"],
        "report": "delitosinformaticos@santander.com.ar",
        "official_emails": ["mensajesyavisos@mails.santander.com.ar", "comunicaciones@novedades.santander.com.ar"],
        "rules": [
            "Santander publica mails oficiales específicos y una casilla para reportar phishing.",
            "No pide claves, códigos de seguridad ni datos personales por mensaje, email o redes."
        ],
        "keywords": ["santander", "superclub", "santi", "clave santander", "token", "cuenta"]
    },
    "Banco Galicia": {
        "domains": ["bancogalicia.com.ar", "bancogalicia.com"],
        "report": "bancogalicia@bancogalicia.com.ar",
        "rules": [
            "Galicia no pide revelar o verificar claves por teléfono, SMS, WhatsApp, Telegram ni páginas referenciadas desde correos.",
            "Para online banking se recomienda escribir manualmente la URL oficial."
        ],
        "keywords": ["galicia", "banco galicia", "token galicia", "clave", "online banking"]
    },
    "Banco Macro": {
        "domains": ["macro.com.ar"],
        "report": "",
        "rules": [
            "Banco Macro indica que jamás se comparten usuario, clave o token.",
            "Las operaciones deben hacerse en sitios oficiales."
        ],
        "keywords": ["macro", "banco macro", "token", "clave", "cuenta"]
    },
    "Mercado Pago": {
        "domains": ["mercadopago.com", "mercadolibre.com", "mercadolibre.com.ar"],
        "report": "",
        "rules": [
            "Mercado Pago indica verificar que el remitente termine en @mercadopago.com.",
            "No se deben compartir contraseña, códigos de verificación ni tarjeta completa.",
            "No se deben instalar programas o abrir links enviados por desconocidos."
        ],
        "keywords": ["mercado pago", "mercadopago", "mercado libre", "mercadolibre", "mp", "billetera", "cvu"]
    },
    "Correo Argentino": {
        "domains": ["correoargentino.com.ar"],
        "link_domains": ["correoargentino.com.ar", "epago.correoargentino.com.ar"],
        "report": "denunciasufeci@mpf.gov.ar",
        "rules": [
            "Correo Argentino alertó sobre mails falsos que piden pagar cánones por liberar envíos.",
            "Para envíos internacionales el portal habilitado es epago.correoargentino.com.ar.",
            "No se deben ingresar datos de tarjetas ni claves en enlaces sospechosos."
        ],
        "keywords": ["correo argentino", "argentina post", "paquete", "envío", "envio", "aduana", "liberación", "liberacion", "entrega"]
    },
    "Personal / Flow / Telecom": {
        "domains": ["personal.com.ar", "telecom.com.ar", "flow.com.ar"],
        "report": "",
        "rules": [
            "Personal advierte que el phishing imita bancos, empresas o contactos y usa urgencia.",
            "Ningún banco ni empresa seria debería pedir datos sensibles por email, SMS o redes."
        ],
        "keywords": ["personal", "flow", "telecom", "factura", "deuda", "servicio", "internet"]
    },
    "Microsoft / Outlook / Hotmail": {
        "domains": ["microsoft.com", "microsoftsupport.com", "mail.support.microsoft.com", "office365support.com", "techsupport.microsoft.com", "accountprotection.microsoft.com"],
        "danger_free_domains": ["outlook.com", "hotmail.com", "live.com", "msn.com"],
        "report": "",
        "rules": [
            "Un correo que dice ser soporte de Microsoft desde outlook.com, hotmail.com u otro dominio gratuito debe tratarse como sospechoso.",
            "Microsoft 365 puede mostrar avisos reales dentro de Office o la cuenta Microsoft, pero no se deben seguir links raros ni compartir claves.",
            "Mensajes que amenazan con cerrar Hotmail/Outlook para siempre suelen ser anzuelo de phishing."
        ],
        "keywords": ["microsoft", "outlook", "hotmail", "office", "office 365", "microsoft 365", "onedrive", "cuenta microsoft"]
    },
    "Google / Gmail": {
        "domains": ["google.com", "accounts.google.com", "googlemail.com"],
        "danger_free_domains": ["gmail.com"],
        "report": "",
        "rules": [
            "Gmail.com es un servicio para usuarios; no convierte un mensaje en correo oficial de Google.",
            "Los avisos de seguridad deben verificarse entrando manualmente a la cuenta de Google.",
            "Un remitente aparentemente real también puede ser usado en campañas sofisticadas; no basta con mirar el nombre."
        ],
        "keywords": ["google", "gmail", "drive", "cuenta google", "accounts.google", "verificación", "verificacion"]
    },
    "Netflix": {
        "domains": ["netflix.com"],
        "report": "",
        "rules": [
            "Los avisos de pago o suscripción deben verificarse entrando manualmente a la cuenta oficial.",
            "No se deben ingresar tarjetas desde links inesperados."
        ],
        "keywords": ["netflix", "suscripción", "suscripcion", "pago", "tarjeta", "facturación", "facturacion"]
    }
}

FREE_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "outlook.com", "live.com", "yahoo.com", "icloud.com",
    "proton.me", "protonmail.com", "aol.com", "msn.com"
}

EMAIL_SCAM_SCENARIOS = {
    "microsoft_365_hotmail_closure": {
        "label": "Microsoft 365 / Hotmail: amenaza de baja o cierre",
        "keywords": ["microsoft 365", "office 365", "hotmail", "outlook", "se acaba", "expira", "baja", "cerrar", "cerrada", "perder", "cuenta"],
        "weight": 45,
        "explain": "Puede haber avisos reales de Microsoft 365 dentro de Office o la cuenta Microsoft, pero los mails que amenazan con cerrar Hotmail/Outlook y piden actuar por link son muy sospechosos."
    },
    "tax_debt_arca": {
        "label": "ARCA / AFIP: deuda, fiscalización o pago por link",
        "keywords": ["arca", "afip", "deuda", "fiscalización", "fiscalizacion", "clave fiscal", "pago", "embargo", "judicial"],
        "weight": 55,
        "explain": "ARCA no pide pagos ni datos personales por mail; se verifica en el Domicilio Fiscal Electrónico."
    },
    "anses_benefit_data": {
        "label": "ANSES: bono, beneficio o datos personales",
        "keywords": ["anses", "bono", "beneficio", "jubilación", "jubilacion", "pensión", "pension", "cbu", "cvu", "datos personales"],
        "weight": 50,
        "explain": "ANSES no solicita datos personales o bancarios por email, SMS, WhatsApp o llamada."
    },
    "bank_token_password": {
        "label": "Banco: clave, token, tarjeta o validación urgente",
        "keywords": ["banco", "token", "clave", "contraseña", "pin", "tarjeta", "validar", "bloqueada", "transferencia"],
        "weight": 55,
        "explain": "Los bancos no deben pedir claves, tokens ni datos sensibles por correo o mensaje."
    },
    "correo_argentino_fee": {
        "label": "Correo Argentino: paquete, aduana, canon o dirección",
        "keywords": ["correo argentino", "argentina post", "paquete", "envío", "envio", "aduana", "canon", "liberar", "entrega", "dirección", "direccion"],
        "weight": 45,
        "explain": "Hay estafas que simulan envíos y piden pagos o datos de tarjeta. Verificar solo por el portal oficial."
    },
    "mercadopago_code_or_app": {
        "label": "Mercado Pago: código, CVU, app o cuenta bloqueada",
        "keywords": ["mercado pago", "mercadopago", "código", "codigo", "verificación", "verificacion", "cvu", "cuenta bloqueada", "instalar"],
        "weight": 45,
        "explain": "No se deben compartir códigos, contraseña ni instalar programas por pedidos recibidos por mail o mensaje."
    },
    "generic_urgency_link": {
        "label": "Urgencia + link + pedido de datos",
        "keywords": ["urgente", "último aviso", "ultimo aviso", "24 horas", "72 horas", "click", "clic", "link", "actualizar datos", "verificar datos"],
        "weight": 35,
        "explain": "La urgencia y el link son señales típicas de phishing."
    }
}

def email_domain(address: str) -> str:
    m = re.search(r"(?i)([a-z0-9._%+\-]+)@([a-z0-9.\-]+\.[a-z]{2,})", address or "")
    return m.group(2).lower() if m else ""

def domain_matches(domain: str, allowed: list[str]) -> bool:
    domain = (domain or "").lower().strip()
    for a in allowed:
        a = a.lower().strip()
        if domain == a or domain.endswith("." + a):
            return True
    return False

def detect_claimed_entity(sender: str, subject: str, body: str, selected: str) -> str:
    if selected and selected != "No sé / Otro":
        return selected
    text = f"{sender} {subject} {body}".lower()
    best = "No sé / Otro"
    best_hits = 0
    for name, profile in OFFICIAL_EMAIL_PROFILES.items():
        hits = sum(1 for k in profile.get("keywords", []) if k.lower() in text)
        if hits > best_hits:
            best_hits = hits
            best = name
    return best

def levenshtein(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    if len(a) < len(b):
        return levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j-1] + 1, prev[j] + 1, prev[j-1] + (ca != cb)))
        prev = cur
    return prev[-1]

def possible_domain_lookalike(domain: str, profile: dict) -> list[str]:
    root = (domain or "").split(".")[0].replace("-", "").replace("_", "")
    hits = []
    for official in profile.get("domains", []) + profile.get("watch_domains", []):
        off_root = official.split(".")[0].replace("-", "").replace("_", "")
        if len(root) >= 5 and len(off_root) >= 5:
            d = levenshtein(root, off_root)
            if 0 < d <= 2:
                hits.append(official)
    return hits

def extract_urls_from_text(text: str) -> list[str]:
    return sorted(set(m.group(0).strip(".,);]") for m in re.finditer(r"(?i)\bhttps?://[^\s<>'\)]+|www\.[^\s<>'\)]+", text or "")))

def analyze_email_message(sender: str, claimed_entity: str, subject: str, body: str, flags: dict | None = None) -> dict:
    flags = flags or {}
    sender = sender or ""
    subject = subject or ""
    body = body or ""
    text = f"{subject}\n{body}"
    lower = text.lower()
    sender_dom = email_domain(sender)
    entity = detect_claimed_entity(sender, subject, body, claimed_entity)
    profile = OFFICIAL_EMAIL_PROFILES.get(entity, {})
    score = 0
    reasons = []
    explanations = []
    scenario_hits = []

    def add(points: int, reason: str, explain: str = ""):
        nonlocal score
        score += points
        reasons.append(reason)
        if explain:
            explanations.append(explain)

    if not sender_dom:
        add(25, "No se pudo reconocer un dominio de correo válido.", "Si no se ve claramente quién envió el correo, conviene no confiar.")
    elif sender_dom in FREE_EMAIL_DOMAINS and entity != "No sé / Otro":
        add(45, f"El remitente usa un correo gratuito ({sender_dom}) para decir ser {entity}.", "Una empresa u organismo no debería escribir desde Gmail/Hotmail/Outlook común para pedir datos o pagos.")

    if profile:
        allowed = profile.get("domains", [])
        if sender_dom:
            if not domain_matches(sender_dom, allowed):
                if sender_dom in profile.get("danger_free_domains", []):
                    add(45, f"El dominio {sender_dom} no es dominio oficial de soporte de {entity}.", "Puede ser un dominio de usuario o correo gratuito, no una cuenta oficial de la entidad.")
                elif domain_matches(sender_dom, profile.get("watch_domains", [])):
                    add(30, f"El dominio {sender_dom} requiere revisión especial para {entity}.", "Aunque parezca conocido, el contenido debe verificarse por canal oficial.")
                else:
                    add(38, f"El dominio {sender_dom} no coincide con la lista oficial cargada para {entity}.", "No significa culpabilidad, pero sí exige verificación por canal oficial.")
            else:
                add(0, f"El dominio del remitente coincide con lista permitida para {entity}.", "Aun si el dominio coincide, no compartas claves ni datos por correo.")

            looks = possible_domain_lookalike(sender_dom, profile)
            if looks:
                add(35, f"El dominio se parece a uno oficial: {', '.join(looks)}.", "Los dominios parecidos son una técnica común de phishing.")

        for rule in profile.get("rules", []):
            explanations.append(rule)

    suspicious_flags = [
        ("asks_password", 45, "El correo pide contraseña, PIN o clave."),
        ("asks_code", 50, "El correo pide código, token o verificación."),
        ("asks_payment", 35, "El correo pide pago, transferencia o regularización."),
        ("asks_card", 45, "El correo pide datos de tarjeta."),
        ("has_attachment", 25, "El correo trae adjunto inesperado."),
        ("has_link", 25, "El correo trae link para entrar o verificar."),
        ("urgent", 25, "El correo usa urgencia o amenaza."),
        ("threat_closure", 35, "El correo amenaza con cerrar, bloquear o dar de baja una cuenta."),
        ("asks_install", 50, "El correo pide instalar una app o programa."),
    ]
    for key, points, reason in suspicious_flags:
        if flags.get(key):
            add(points, reason)

    urls = extract_urls_from_text(text)
    if urls:
        add(18, "Se detectaron links dentro del correo.", "No abras links desde correos dudosos; entrá manualmente al sitio oficial.")

    for scenario_id, scenario in EMAIL_SCAM_SCENARIOS.items():
        hits = [k for k in scenario["keywords"] if k.lower() in lower]
        if len(hits) >= 2:
            add(int(scenario["weight"]), f"Coincide con escenario: {scenario['label']}.", scenario["explain"])
            scenario_hits.append({"id": scenario_id, "label": scenario["label"], "hits": hits[:8]})

    if entity == "Microsoft / Outlook / Hotmail" and "hotmail" in lower and ("baja" in lower or "cerr" in lower or "perder" in lower):
        add(40, "Amenaza relacionada con baja/cierre de Hotmail.", "Los avisos de suscripción se revisan desde la cuenta Microsoft u Office, no desde links dudosos.")

    if entity == "ARCA / ex AFIP" and any(w in lower for w in ["pago", "deuda", "clave fiscal", "fiscalización", "embargo"]):
        add(50, "Correo fiscal con pago/deuda/clave fiscal.", "ARCA no pide pagos ni datos personales por mail.")

    if entity == "ANSES" and any(w in lower for w in ["cbu", "cvu", "datos", "bancarios", "bono", "beneficio"]):
        add(45, "Correo de ANSES con datos/beneficios.", "ANSES no solicita datos personales o bancarios por email.")

    score = min(score, 100)
    level, color = risk_level(score)

    if score >= 90:
        recommendation = "NO CONFIAR. No abras links, no descargues adjuntos y no respondas. Pedí ayuda o verificá por canal oficial."
    elif score >= 75:
        recommendation = "Alto riesgo. No avances desde ese correo. Entrá manualmente al sitio oficial o consultá con alguien de confianza."
    elif score >= 45:
        recommendation = "Revisar antes de responder. El remitente o el contenido tienen señales sospechosas."
    elif score >= 20:
        recommendation = "Precaución. Puede ser legítimo, pero verificá dominio, enlaces y contenido antes de actuar."
    else:
        recommendation = "No se detectaron señales fuertes. Igual nunca compartas claves, códigos, tarjeta o datos sensibles por correo."

    return {
        "id": str(uuid.uuid4()),
        "created_at": now_iso(),
        "sender": sender,
        "sender_domain": sender_dom,
        "claimed_entity": entity,
        "subject": subject,
        "body_preview": body[:500],
        "risk_score": score,
        "risk_level": level,
        "color": color,
        "recommendation": recommendation,
        "reasons": reasons or ["No se detectaron señales fuertes en el correo."],
        "explanations": list(dict.fromkeys(explanations))[:12],
        "scenario_hits": scenario_hits,
        "urls": urls,
    }


LANG = {
    "es": {
        "home": "Inicio",
        "live_call": "Llamada en vivo",
        "contacts": "Contactos",
        "lists": "Listas",
        "scanner": "Scanner de links",
        "email": "Analizador de correos",
        "records": "Registros",
        "reports": "Reportes",
        "settings": "Configuración",
        "subtitle": "Asistente de protección familiar contra estafas digitales",
        "warning": "Si algo parece urgente, extraño o le piden dinero/códigos: deténgase. FARO puede ayudarle a avisar a su gente de confianza.",
    },
    "en": {
        "home": "Home",
        "live_call": "Live call",
        "contacts": "Contacts",
        "lists": "Lists",
        "scanner": "Link scanner",
        "email": "Email analyzer",
        "records": "Records",
        "reports": "Reports",
        "settings": "Settings",
        "subtitle": "Family protection assistant against digital scams",
        "warning": "If something feels urgent, strange, or asks for money/codes: pause. FARO can help alert trusted people.",
    },
    "pt": {
        "home": "Início",
        "live_call": "Chamada ao vivo",
        "contacts": "Contatos",
        "lists": "Listas",
        "scanner": "Scanner de links",
        "email": "Analisador de e-mails",
        "records": "Registros",
        "reports": "Relatórios",
        "settings": "Configuração",
        "subtitle": "Assistente de proteção familiar contra golpes digitais",
        "warning": "Se algo parece urgente, estranho ou pede dinheiro/códigos: pare. FARO pode ajudar a avisar pessoas de confiança.",
    }
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    EXPORTS_DIR.mkdir(exist_ok=True)
    BACKUPS_DIR.mkdir(exist_ok=True)


def log_error(exc: BaseException) -> None:
    ensure_dirs()
    with ERROR_LOG.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 90 + "\n")
        f.write(now_iso() + "\n")
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)


def db() -> sqlite3.Connection:
    ensure_dirs()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def dict_rows(rows) -> list[dict]:
    return [dict(r) for r in rows]


def init_db() -> None:
    with db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS contacts(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            relation TEXT,
            phone TEXT,
            email TEXT,
            aliases TEXT,
            trust_level TEXT NOT NULL DEFAULT 'normal',
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS phrase_rules(
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            phrase TEXT NOT NULL,
            weight INTEGER NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            custom INTEGER NOT NULL DEFAULT 0
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS live_sessions(
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            caller_number TEXT,
            claimed_relation TEXT,
            claimed_name TEXT,
            transcript TEXT,
            selected_phrases_json TEXT,
            flags_json TEXT,
            comparison_json TEXT,
            risk_score INTEGER,
            risk_level TEXT,
            recommendation TEXT,
            actions_json TEXT,
            protection_mode INTEGER NOT NULL DEFAULT 0
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS link_scans(
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            original TEXT,
            normalized TEXT,
            defanged TEXT,
            host TEXT,
            scheme TEXT,
            path TEXT,
            risk_score INTEGER,
            risk_level TEXT,
            recommendation TEXT,
            signals_json TEXT
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS email_scans(
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            sender TEXT,
            sender_domain TEXT,
            claimed_entity TEXT,
            subject TEXT,
            body_preview TEXT,
            risk_score INTEGER,
            risk_level TEXT,
            recommendation TEXT,
            reasons_json TEXT,
            explanations_json TEXT,
            scenario_hits_json TEXT,
            urls_json TEXT
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS alerts(
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            session_id TEXT,
            contact_id TEXT,
            channel TEXT,
            prepared_message TEXT
        )
        """)

        if con.execute("SELECT value FROM settings WHERE key='language'").fetchone() is None:
            con.execute("INSERT INTO settings(key,value) VALUES('language','es')")
        if con.execute("SELECT value FROM settings WHERE key='auto_open_whatsapp_on_critical'").fetchone() is None:
            con.execute("INSERT INTO settings(key,value) VALUES('auto_open_whatsapp_on_critical','yes')")
        if con.execute("SELECT value FROM settings WHERE key='critical_threshold'").fetchone() is None:
            con.execute("INSERT INTO settings(key,value) VALUES('critical_threshold','90')")
        if con.execute("SELECT value FROM settings WHERE key='preventive_alert_threshold'").fetchone() is None:
            con.execute("INSERT INTO settings(key,value) VALUES('preventive_alert_threshold','43')")
        if con.execute("SELECT value FROM settings WHERE key='urgent_alert_threshold'").fetchone() is None:
            con.execute("INSERT INTO settings(key,value) VALUES('urgent_alert_threshold','70')")
        if con.execute("SELECT value FROM settings WHERE key='max_auto_tabs'").fetchone() is None:
            con.execute("INSERT INTO settings(key,value) VALUES('max_auto_tabs','3')")

        phrase_count = con.execute("SELECT COUNT(*) AS c FROM phrase_rules").fetchone()["c"]
        if phrase_count == 0:
            for category, phrase, weight in DEFAULT_PHRASES:
                con.execute("""
                INSERT INTO phrase_rules(id,category,phrase,weight,enabled,custom)
                VALUES(?,?,?,?,1,0)
                """, (str(uuid.uuid4()), category, phrase, weight))


def get_setting(key: str, default: str = "") -> str:
    with db() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with db() as con:
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))


def clean_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")



def normalize_whatsapp_phone(phone: str) -> str:
    raw = clean_phone(phone)
    if not raw:
        return ""
    # Argentina helper:
    # If user writes 11/291/etc without country code, FARO cannot know for sure.
    # Keep conservative. Do not invent full number except removing a leading 0 after 54.
    if raw.startswith("540"):
        raw = "54" + raw[3:]
    return raw

def whatsapp_web_url(phone: str, text: str) -> str:
    clean = normalize_whatsapp_phone(phone)
    return f"https://web.whatsapp.com/send?phone={clean}&text={quote(text)}"

def whatsapp_wa_me_url(phone: str, text: str) -> str:
    clean = normalize_whatsapp_phone(phone)
    return f"https://wa.me/{clean}?text={quote(text)}"

def looks_like_whatsapp_phone(phone: str) -> bool:
    clean = normalize_whatsapp_phone(phone)
    # Minimal sanity check: international numbers usually have at least 10 digits.
    return clean.isdigit() and len(clean) >= 10

def last_digits(value: str, count: int = 4) -> str:
    v = clean_phone(value)
    return v[-count:] if len(v) >= count else v


def defang(value: str) -> str:
    return (value or "").replace("https://", "hxxps://").replace("http://", "hxxp://").replace(".", "[.]")


def normalize_url(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if not re.match(r"(?i)^https?://", v):
        return "https://" + v
    return v


def risk_level(score: int) -> tuple[str, str]:
    if score >= 90:
        return "PROTECCIÓN INMEDIATA", "#7a0015"
    if score >= 75:
        return "ALTO RIESGO", "#b00020"
    if score >= 45:
        return "REVISAR ANTES DE RESPONDER", "#d98200"
    if score >= 20:
        return "PRECAUCIÓN", "#b59b00"
    return "BAJO RIESGO", "#0b7a3b"


def risk_recommendation(score: int) -> str:
    if score >= 90:
        return (
            "FARO detectó riesgo crítico. Mantenga la calma. No entregue dinero, códigos ni datos. "
            "FARO preparará ayuda con sus contactos de confianza."
        )
    if score >= 75:
        return (
            "No siga la conversación si puede evitarlo. No envíe dinero, no comparta códigos "
            "y pida ayuda a contactos de confianza."
        )
    if score >= 45:
        return "No avance todavía. Verifique por WhatsApp o llamada al número guardado de la persona que dicen ser."
    if score >= 20:
        return "Tenga cuidado. Pida una confirmación por otro canal antes de responder."
    return "No se detectaron señales fuertes, pero no comparta códigos ni dinero sin verificar."



def alert_tier(score: int) -> str:
    urgent = int(get_setting("urgent_alert_threshold", "70") or "70")
    preventive = int(get_setting("preventive_alert_threshold", "43") or "43")
    if score >= urgent:
        return "urgent"
    if score >= preventive:
        return "preventive"
    return "none"

def alert_button_text(score: int) -> str:
    tier = alert_tier(score)
    if tier == "urgent":
        return "🚨 ALERTA URGENTE"
    if tier == "preventive":
        return "🟡 AVISAR: NECESITO ASEGURAR"
    return "🛡️ AVISAR"

def get_contacts() -> list[dict]:
    with db() as con:
        return dict_rows(con.execute("SELECT * FROM contacts ORDER BY CASE trust_level WHEN 'extreme' THEN 0 ELSE 1 END, name ASC").fetchall())


def get_extreme_contacts() -> list[dict]:
    with db() as con:
        return dict_rows(con.execute("SELECT * FROM contacts WHERE trust_level='extreme' ORDER BY name ASC").fetchall())


def get_phrase_rules(enabled_only: bool = True) -> list[dict]:
    with db() as con:
        if enabled_only:
            return dict_rows(con.execute("SELECT * FROM phrase_rules WHERE enabled=1 ORDER BY category, weight DESC").fetchall())
        return dict_rows(con.execute("SELECT * FROM phrase_rules ORDER BY category, weight DESC").fetchall())


def contact_search_text(contact: dict) -> str:
    return " ".join([
        contact.get("name", ""),
        contact.get("relation", ""),
        contact.get("aliases", ""),
        contact.get("notes", "")
    ]).lower()


def find_claimed_contacts(claimed_relation: str, claimed_name: str) -> list[dict]:
    relation = (claimed_relation or "").lower().strip()
    name = (claimed_name or "").lower().strip()
    terms = [x for x in [relation, name] if x]

    if not terms:
        return []

    matches = []
    for c in get_contacts():
        hay = contact_search_text(c)
        if any(t in hay or hay in t for t in terms if len(t) >= 2):
            matches.append(c)
    return matches


def compare_call(caller_number: str, claimed_relation: str, claimed_name: str) -> dict:
    caller_clean = clean_phone(caller_number)
    contacts = get_contacts()

    exact_matches = []
    last4_matches = []
    last6_matches = []

    for c in contacts:
        c_phone = clean_phone(c.get("phone", ""))
        if not c_phone or not caller_clean:
            continue
        if c_phone == caller_clean:
            exact_matches.append(c)
        elif len(caller_clean) >= 4 and len(c_phone) >= 4 and last_digits(c_phone, 4) == last_digits(caller_clean, 4):
            last4_matches.append(c)
        if len(caller_clean) >= 6 and len(c_phone) >= 6 and last_digits(c_phone, 6) == last_digits(caller_clean, 6):
            last6_matches.append(c)

    claimed_contacts = find_claimed_contacts(claimed_relation, claimed_name)

    status = "unknown"
    notes = []

    if exact_matches:
        status = "exact_match"
        notes.append("El número coincide exactamente con un contacto guardado. Conviene confirmar por mensaje antes de seguir.")
    elif last6_matches:
        status = "partial_last6"
        notes.append("Los últimos 6 dígitos coinciden con un contacto. Verifique antes de confiar.")
    elif last4_matches:
        status = "partial_last4"
        notes.append("Los últimos 4 dígitos coinciden con un contacto. No alcanza para confiar.")
    else:
        status = "no_phone_match"
        notes.append("El número no coincide con contactos guardados.")

    if claimed_contacts:
        notes.append("FARO encontró contactos que podrían coincidir con la persona que dicen ser.")
    else:
        notes.append("No se encontró coincidencia clara con la persona que dicen ser.")

    if caller_clean and claimed_contacts and not exact_matches:
        notes.append("Dicen ser alguien conocido desde un número distinto. Verifique con el contacto guardado antes de seguir.")

    return {
        "caller_number": caller_number,
        "caller_clean": caller_clean,
        "status": status,
        "exact_matches": exact_matches,
        "last6_matches": last6_matches,
        "last4_matches": last4_matches,
        "claimed_contacts": claimed_contacts,
        "notes": notes,
    }


def analyze_live_call(payload: dict) -> dict:
    score = 0
    reasons = []

    def add(points: int, reason: str):
        nonlocal score
        score += points
        reasons.append(reason)

    caller_number = payload.get("caller_number", "")
    claimed_relation = payload.get("claimed_relation", "")
    claimed_name = payload.get("claimed_name", "")
    transcript = payload.get("transcript", "")
    selected_phrases = payload.get("selected_phrases", [])
    flags = payload.get("flags", {})

    comparison = compare_call(caller_number, claimed_relation, claimed_name)

    if comparison["status"] == "no_phone_match":
        add(25, "El número no coincide con contactos guardados.")
    elif comparison["status"] == "partial_last4":
        add(15, "Solo coinciden los últimos 4 dígitos; no es suficiente para confiar.")
    elif comparison["status"] == "partial_last6":
        add(10, "Coincidencia parcial de últimos 6 dígitos; requiere verificación.")
    elif comparison["status"] == "exact_match":
        add(5, "El número coincide, pero se recomienda confirmar por otro canal.")

    if claimed_relation and not comparison["claimed_contacts"]:
        add(18, "Dicen ser alguien conocido, pero FARO no encontró coincidencia clara en contactos.")

    for key, points, reason in [
        ("urgent", 18, "La llamada usa urgencia o presión."),
        ("money", 35, "Pidieron dinero o transferencia."),
        ("code", 45, "Pidieron código, token o clave."),
        ("secret", 40, "Pidieron no contarle a nadie."),
        ("new_number", 30, "Dicen ser familiar con número nuevo."),
        ("bank", 35, "Dicen ser banco, billetera virtual o soporte."),
        ("install_app", 50, "Pidieron instalar una app."),
        ("remote", 55, "Pidieron acceso remoto."),
        ("link", 28, "Mandaron un link."),
        ("threat", 28, "Amenazaron con bloqueo, deuda, multa o pérdida de cuenta."),
    ]:
        if flags.get(key):
            add(points, reason)

    phrase_rules = get_phrase_rules(True)
    combined_text = " ".join([transcript] + selected_phrases).lower()
    already_added = set()

    for rule in phrase_rules:
        phrase = rule["phrase"].lower()
        if phrase and phrase in combined_text and rule["phrase"] not in already_added:
            add(int(rule["weight"]), f"Frase coincidente: “{rule['phrase']}”.")
            already_added.add(rule["phrase"])

    for phrase in selected_phrases:
        matching = [r for r in phrase_rules if r["phrase"] == phrase]
        if matching and phrase not in already_added:
            r = matching[0]
            add(int(r["weight"]), f"Frase seleccionada: “{r['phrase']}”.")
            already_added.add(phrase)

    if re.search(r"(?i)c[oó]digo|token|otp|clave|pin|contrase", transcript):
        add(40, "El texto menciona códigos, claves o contraseña.")
    if re.search(r"(?i)transfer|alias|cbu|cvu|plata|dinero|dep[oó]sito", transcript):
        add(30, "El texto menciona dinero, transferencia o alias.")
    if re.search(r"(?i)no le digas|no cuentes|secreto|entre nosotros", transcript):
        add(35, "El texto pide secreto.")
    if re.search(r"(?i)urgente|ahora|r[aá]pido|ya", transcript):
        add(18, "El texto usa urgencia.")
    if re.search(r"(?i)http|www\.|\.com|\.ar|link", transcript):
        add(24, "El texto menciona un link.")

    score = min(score, 100)
    level, color = risk_level(score)

    actions = []
    tier = alert_tier(score)
    if score >= 90:
        actions.extend([
            "FARO activará modo protección visible.",
            "No entregue dinero, códigos ni datos.",
            "Toque AVISAR AHORA y FARO abrirá WhatsApp con mensajes preparados para contactos de confianza.",
            "Revise y confirme los envíos."
        ])
    elif tier == "urgent":
        actions.extend([
            "ALERTA URGENTE: toque ALERTA URGENTE para pedir ayuda.",
            "No entregue dinero, códigos ni datos.",
            "Verifique con una persona cercana antes de seguir."
        ])
    elif tier == "preventive":
        actions.extend([
            "AVISO PREVENTIVO: toque AVISAR para asegurar la situación.",
            "No avance con pagos, códigos ni links hasta verificar.",
            "Pida ayuda a un contacto cercano."
        ])
    else:
        actions.extend([
            "Verificar de todos modos antes de compartir datos.",
            "No compartir códigos ni dinero."
        ])


    return {
        "score": score,
        "level": level,
        "color": color,
        "reasons": reasons or ["No se detectaron señales fuertes, pero FARO recomienda verificar por otro canal."],
        "recommendation": risk_recommendation(score),
        "comparison": comparison,
        "actions": actions,
        "protection_mode": score >= int(get_setting("critical_threshold", "90")),
        "alert_tier": alert_tier(score),
    }


def analyze_url(value: str) -> dict:
    original = (value or "").strip()
    normalized = normalize_url(original)
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    score = 0
    signals = []

    def add(points: int, code: str, detail: str):
        nonlocal score
        score += points
        signals.append({"code": code, "weight": points, "detail": detail})

    if not original:
        add(0, "empty", "No se ingresó un link.")
    if scheme == "http":
        add(22, "plain_http", "El link usa HTTP sin cifrado.")
    if host.startswith("xn--") or ".xn--" in host:
        add(30, "punycode", "Dominio punycode, posible engaño visual.")
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        add(24, "ip_host", "Usa una IP como destino.")
    if host.count("-") >= 3:
        add(16, "many_hyphens", "Tiene muchos guiones.")
    if host.count(".") >= 3:
        add(12, "many_subdomains", "Tiene muchos subdominios.")
    if len(host) > 45:
        add(12, "long_host", "Dominio inusualmente largo.")
    if "@" in original:
        add(28, "at_symbol", "Contiene @, puede ocultar destino.")

    shorteners = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly", "shorturl.at", "rebrand.ly"}
    if host in shorteners:
        add(30, "shortener", "Usa acortador de links.")

    risk_words = ["login", "verify", "secure", "wallet", "gift", "free", "update", "support", "account", "confirm", "validation", "premio", "ganaste", "bloqueo", "seguridad", "pago", "transferencia", "reembolso", "banco", "bank"]
    all_text = f"{host} {path} {query}".lower()
    for word in risk_words:
        if word in all_text:
            add(6, f"keyword_{word}", f"Contiene palabra de riesgo: {word}")

    for key in ["token", "auth", "password", "pass", "session", "code", "otp", "clave", "pin"]:
        if re.search(rf"(?i)(^|[?&]){re.escape(key)}=", "?" + query):
            add(22, f"sensitive_query_{key}", f"Parámetro sensible: {key}")

    brands = ["mercadopago", "paypal", "google", "microsoft", "facebook", "instagram", "whatsapp", "netflix", "amazon", "santander", "galicia", "macro", "bbva", "uala", "visa", "mastercard"]
    compact = host.replace("-", "").replace("_", "")
    for brand in brands:
        if brand in compact:
            add(8, f"brand_{brand}", f"Menciona o imita marca: {brand}")

    score = min(score, 100)
    level, color = risk_level(score)
    return {
        "id": str(uuid.uuid4()),
        "created_at": now_iso(),
        "original": original,
        "normalized": normalized,
        "defanged": defang(original),
        "host": host,
        "scheme": scheme,
        "path": path,
        "risk_score": score,
        "risk_level": level,
        "color": color,
        "recommendation": risk_recommendation(score),
        "signals": signals or [{"code": "no_strong_signal", "weight": 0, "detail": "No se detectaron señales fuertes."}],
    }


class FaroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_db()
        self.lang = get_setting("language", "es")
        self.t = LANG.get(self.lang, LANG["es"])
        self.selected_session_id = None
        self.last_text = ""

        self.title(APP_TITLE)
        self.geometry("1300x840")
        self.minsize(1120, 740)
        self.configure(bg="#f5f7fb")

        self.font_title = ("Segoe UI", 28, "bold")
        self.font_big = ("Segoe UI", 17, "bold")
        self.font_mid = ("Segoe UI", 13)
        self.font_small = ("Segoe UI", 11)

        self.create_style()
        self.build_shell()
        self.show_home()

    def create_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", font=self.font_mid, padding=9)
        style.configure("Big.TButton", font=self.font_big, padding=14)
        style.configure("Nav.TButton", font=("Segoe UI", 14, "bold"), padding=13)
        style.configure("TLabel", font=self.font_mid, background="#f5f7fb")
        style.configure("Title.TLabel", font=self.font_title, background="#f5f7fb", foreground="#14304a")
        style.configure("Sub.TLabel", font=("Segoe UI", 14), background="#f5f7fb", foreground="#425466")
        style.configure("TCheckbutton", font=("Segoe UI", 11), background="#f5f7fb")
        style.configure("TRadiobutton", font=("Segoe UI", 12), background="#eef3f8")

    def safe(self, fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                log_error(exc)
                messagebox.showerror("FARO", f"Ocurrió un error.\n\nDetalle guardado en:\n{ERROR_LOG}\n\n{exc}")
        return wrapper

    def build_shell(self):
        self.header = tk.Frame(self, bg="#f5f7fb")
        self.header.pack(fill="x", padx=20, pady=(14, 6))
        ttk.Label(self.header, text="FARO", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.header, text=f"{self.t['subtitle']} · Creado por {AUTHOR}", style="Sub.TLabel").pack(anchor="w")

        self.main = tk.Frame(self, bg="#f5f7fb")
        self.main.pack(fill="both", expand=True, padx=18, pady=10)

        self.nav = tk.Frame(self.main, bg="#eef3f8", highlightthickness=1, highlightbackground="#d8e1ea")
        self.nav.pack(side="left", fill="y", padx=(0, 14))
        self.nav.configure(width=300)
        self.nav.pack_propagate(False)

        self.content = tk.Frame(self.main, bg="#f5f7fb")
        self.content.pack(side="right", fill="both", expand=True)

        self.build_nav()

    def build_nav(self):
        for child in self.nav.winfo_children():
            child.destroy()

        tk.Label(self.nav, text="MENÚ", font=("Segoe UI", 16, "bold"), bg="#eef3f8", fg="#14304a").pack(anchor="w", padx=16, pady=(18, 10))
        buttons = [
            ("🏠 " + self.t["home"], self.show_home),
            ("☎️ " + self.t["live_call"], self.show_live_call),
            ("🔗 " + self.t["scanner"], self.show_link_scanner),
            ("📧 " + self.t.get("email", "Analizador de correos"), self.show_email_analyzer),
            ("👨‍👩‍👧 " + self.t["contacts"], self.show_contacts),
            ("🧠 " + self.t["lists"], self.show_lists),
            ("📚 " + self.t["records"], self.show_records),
            ("🛡️ Modo protección", self.show_protection_center),
            ("📄 " + self.t["reports"], self.show_reports),
            ("⚙️ " + self.t["settings"], self.show_settings),
        ]
        for text, cmd in buttons:
            ttk.Button(self.nav, text=text, command=self.safe(cmd), style="Nav.TButton").pack(fill="x", padx=14, pady=5)

        tk.Label(
            self.nav,
            text=f"FARO v{APP_VERSION}\nCreado por {AUTHOR}\n\nAbre WhatsApp con mensajes preparados.\nLa persona confirma el envío.",
            font=("Segoe UI", 10),
            bg="#eef3f8",
            fg="#425466",
            wraplength=260,
            justify="left"
        ).pack(side="bottom", anchor="w", padx=16, pady=18)

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def page_title(self, title: str, subtitle: str = ""):
        ttk.Label(self.content, text=title, style="Title.TLabel").pack(anchor="w", pady=(0, 4))
        if subtitle:
            ttk.Label(self.content, text=subtitle, style="Sub.TLabel").pack(anchor="w", pady=(0, 14))

    def copy_text(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text or "")
        self.update_idletasks()
        self.last_text = text or ""


    def open_whatsapp_prepared(self, phone: str, text: str, context: str = "whatsapp"):
        clean = normalize_whatsapp_phone(phone)
        if not looks_like_whatsapp_phone(phone):
            messagebox.showwarning(
                "FARO - WhatsApp",
                "El número no parece estar en formato internacional.\n\n"
                "Para Argentina conviene cargarlo así:\n"
                "549 + característica + número\n\n"
                "Ejemplo: 549291XXXXXXX\n\n"
                "Sin +, sin espacios, sin guiones."
            )
            return False

        self.copy_text(text)
        # Prefer WhatsApp Web on desktop. Also open wa.me as fallback if needed.
        opened = webbrowser.open(whatsapp_web_url(clean, text), new=2)
        if not opened:
            webbrowser.open(whatsapp_wa_me_url(clean, text), new=2)
        return True

    def show_home(self):
        self.clear_content()
        self.page_title("FARO v4", "Protección familiar en vivo para llamadas, mensajes, links y pedidos sospechosos.")

        warn = tk.Frame(self.content, bg="#fff4d8", highlightthickness=1, highlightbackground="#d6a800")
        warn.pack(fill="x", pady=12)
        tk.Label(
            warn,
            text="🛡️ " + self.t["warning"],
            font=("Segoe UI", 17, "bold"),
            bg="#fff4d8",
            fg="#6b4b00",
            wraplength=920,
            justify="left"
        ).pack(anchor="w", padx=18, pady=16)

        reassurance = tk.Frame(self.content, bg="#e8f4ff", highlightthickness=1, highlightbackground="#9cc8ef")
        reassurance.pack(fill="x", pady=(0, 12))
        tk.Label(
            reassurance,
            text="FARO no lo deja solo: si detecta riesgo crítico, prepara ayuda, abre WhatsApp con sus contactos cercanos y deja mensajes claros para pedir asistencia.",
            font=("Segoe UI", 15, "bold"),
            bg="#e8f4ff",
            fg="#14304a",
            wraplength=920,
            justify="left"
        ).pack(anchor="w", padx=18, pady=14)

        grid = tk.Frame(self.content, bg="#f5f7fb")
        grid.pack(fill="both", expand=True, pady=10)

        cards = [
            ("☎️", "Llamada en vivo", "Toque respuestas simples mientras ocurre la llamada. FARO compara y protege.", self.show_live_call),
            ("🛡️", "Modo protección", "Riesgo crítico: mensajes listos para contactos de confianza.", self.show_protection_center),
            ("👨‍👩‍👧", "Contactos cercanos", "Cargue personas de confianza extrema para recibir ayuda inmediata.", self.show_contacts),
            ("🔗", "Scanner de links", "Revise links sin abrirlos y copie una versión segura para enviar.", self.show_link_scanner),
            ("📧", "Analizador de correos", "Revise remitentes, dominios oficiales y temas típicos de estafa.", self.show_email_analyzer),
        ]

        for i, (icon, title, desc, cmd) in enumerate(cards):
            card = tk.Frame(grid, bg="white", highlightthickness=1, highlightbackground="#d8e1ea")
            card.grid(row=i//2, column=i%2, sticky="nsew", padx=10, pady=10)
            tk.Label(card, text=icon, font=("Segoe UI Emoji", 36), bg="white").pack(anchor="w", padx=18, pady=(16, 0))
            tk.Label(card, text=title, font=("Segoe UI", 20, "bold"), bg="white", fg="#14304a").pack(anchor="w", padx=18)
            tk.Label(card, text=desc, font=("Segoe UI", 12), bg="white", fg="#425466", wraplength=390, justify="left").pack(anchor="w", padx=18, pady=(4, 14))
            ttk.Button(card, text="Abrir", command=self.safe(cmd), style="Big.TButton").pack(anchor="w", padx=18, pady=(0, 18))

        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def show_live_call(self):
        self.clear_content()
        self.page_title("Llamada en vivo", "La persona protegida solo toca respuestas. FARO compara número, identidad y frases sospechosas.")

        outer = tk.Frame(self.content, bg="#f5f7fb")
        outer.pack(fill="both", expand=True)

        left = tk.Frame(outer, bg="#f5f7fb")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(outer, bg="#eef3f8", highlightthickness=1, highlightbackground="#d8e1ea")
        right.pack(side="right", fill="y")
        right.configure(width=420)
        right.pack_propagate(False)

        prompt = tk.Frame(left, bg="#e8f4ff", highlightthickness=1, highlightbackground="#9cc8ef")
        prompt.pack(fill="x", pady=(0, 10))
        tk.Label(
            prompt,
            text="PASO 1: mire el número que aparece en el teléfono y escríbalo acá. Si no puede, escriba los últimos 4 números.",
            font=("Segoe UI", 15, "bold"),
            bg="#e8f4ff",
            fg="#14304a",
            wraplength=780,
            justify="left"
        ).pack(anchor="w", padx=14, pady=10)

        caller_var = tk.StringVar()
        claimed_relation = tk.StringVar(value="nieto")
        claimed_name = tk.StringVar()

        top = tk.Frame(left, bg="#f5f7fb")
        top.pack(fill="x")

        ttk.Label(top, text="Número que llama").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=caller_var, font=("Segoe UI", 15)).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(2, 8))

        ttk.Label(top, text="Dice ser").grid(row=0, column=1, sticky="w")
        ttk.Combobox(top, textvariable=claimed_relation, values=[
            "nieto", "nieta", "hijo", "hija", "sobrino", "sobrina", "amigo", "banco", "soporte", "vendedor", "desconocido"
        ], state="readonly", font=("Segoe UI", 14)).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(2, 8))

        ttk.Label(top, text="Nombre que dijo").grid(row=0, column=2, sticky="w")
        ttk.Entry(top, textvariable=claimed_name, font=("Segoe UI", 15)).grid(row=1, column=2, sticky="ew", pady=(2, 8))

        top.columnconfigure(0, weight=2)
        top.columnconfigure(1, weight=1)
        top.columnconfigure(2, weight=2)

        flags_defs = [
            ("new_number", "Dice que cambió de número"),
            ("urgent", "Dice que es urgente"),
            ("money", "Pide plata / transferencia"),
            ("code", "Pide código / token / clave"),
            ("secret", "Pide no contarle a nadie"),
            ("bank", "Dice ser banco / soporte"),
            ("install_app", "Pide instalar app"),
            ("remote", "Pide controlar el equipo"),
            ("link", "Manda un link"),
            ("threat", "Amenaza con bloqueo/deuda"),
        ]
        flags = {k: tk.BooleanVar() for k, _ in flags_defs}

        flags_frame = tk.LabelFrame(left, text="Toque lo que está pasando", bg="#f5f7fb", font=self.font_mid)
        flags_frame.pack(fill="x", pady=8)

        for i, (key, label) in enumerate(flags_defs):
            ttk.Checkbutton(flags_frame, text=label, variable=flags[key]).grid(row=i//2, column=i%2, sticky="w", padx=8, pady=5)
        flags_frame.columnconfigure(0, weight=1)
        flags_frame.columnconfigure(1, weight=1)

        ttk.Label(left, text="Frases rápidas que dijo la persona").pack(anchor="w", pady=(8, 2))
        phrase_holder = tk.Frame(left, bg="#f5f7fb")
        phrase_holder.pack(fill="x")

        selected_phrases = []
        phrase_rules = get_phrase_rules(True)[:18]

        def add_phrase(phrase: str):
            selected_phrases.append(phrase)
            transcript.insert("end", phrase + "\n")
            analyze_action()

        for i, rule in enumerate(phrase_rules):
            b = ttk.Button(phrase_holder, text=rule["phrase"], command=lambda p=rule["phrase"]: add_phrase(p))
            b.grid(row=i//3, column=i%3, sticky="ew", padx=4, pady=4)
        for c in range(3):
            phrase_holder.columnconfigure(c, weight=1)

        ttk.Label(left, text="Anote palabras exactas si puede").pack(anchor="w", pady=(8, 2))
        transcript = tk.Text(left, height=5, font=("Segoe UI", 12), wrap="word")
        transcript.pack(fill="x")

        tk.Label(right, text="Análisis en vivo", font=("Segoe UI", 20, "bold"), bg="#eef3f8", fg="#14304a").pack(anchor="w", padx=16, pady=(16, 4))
        risk_label = tk.Label(right, text="Sin analizar", font=("Segoe UI", 18, "bold"), bg="#eef3f8", fg="#425466", wraplength=370, justify="left")
        risk_label.pack(anchor="w", padx=16, pady=8)

        protection_banner = tk.Label(
            right,
            text="",
            font=("Segoe UI", 13, "bold"),
            bg="#eef3f8",
            fg="#14304a",
            wraplength=360,
            justify="left"
        )
        protection_banner.pack(anchor="w", padx=16, pady=(0, 8))

        result_box = tk.Text(right, height=20, font=("Segoe UI", 11), wrap="word")
        result_box.pack(fill="both", expand=True, padx=16, pady=8)

        avisar_button = tk.Button(
            right,
            text="🛡️ AVISAR AHORA",
            font=("Segoe UI", 18, "bold"),
            bg="#b00020",
            fg="white",
            activebackground="#7a0015",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=14,
            state="disabled"
        )
        avisar_button.pack(fill="x", padx=16, pady=(4, 14))

        current = {}

        def collect():
            return {
                "caller_number": caller_var.get().strip(),
                "claimed_relation": claimed_relation.get().strip(),
                "claimed_name": claimed_name.get().strip(),
                "transcript": transcript.get("1.0", "end").strip(),
                "selected_phrases": selected_phrases[:],
                "flags": {k: v.get() for k, v in flags.items()},
            }

        def render(data: dict):
            current.clear()
            current.update(data)
            risk_label.configure(text=f"{data['level']}\n{data['score']}/100", fg=data["color"])

            if data.get("alert_tier") == "urgent" or data.get("protection_mode"):
                protection_banner.configure(
                    text="🚨 Alerta urgente. Toque ALERTA URGENTE para abrir WhatsApp con sus contactos cercanos.",
                    fg="#7a0015"
                )
                avisar_button.configure(text="🚨 ALERTA URGENTE", state="normal", bg="#b00020")
            elif data.get("alert_tier") == "preventive":
                protection_banner.configure(
                    text="🟡 Aviso preventivo. Toque AVISAR para pedir ayuda y asegurar la situación.",
                    fg="#8a5a00"
                )
                avisar_button.configure(text="🟡 AVISAR: NECESITO ASEGURAR", state="normal", bg="#d98200")
            else:
                protection_banner.configure(text="FARO está observando señales y comparando datos.", fg="#14304a")
                avisar_button.configure(text="🛡️ AVISAR", state="disabled", bg="#9ca3af")

            result_box.configure(state="normal")
            result_box.delete("1.0", "end")
            result_box.insert("end", "Qué hacer ahora:\n")
            for a in data["actions"]:
                result_box.insert("end", f"• {a}\n")
            result_box.insert("end", "\nMotivos:\n")
            for r in data["reasons"]:
                result_box.insert("end", f"• {r}\n")
            result_box.insert("end", "\nComparación:\n")
            for n in data["comparison"]["notes"]:
                result_box.insert("end", f"• {n}\n")
            result_box.insert("end", "\nFrase segura para decir:\n")
            result_box.insert("end", "• Ahora no puedo resolver esto. Te voy a verificar por otro medio.\n")
            result_box.configure(state="disabled")
            self.last_text = json.dumps(data, ensure_ascii=False, indent=2)

        def analyze_action():
            data = analyze_live_call(collect())
            render(data)

        def save_session(auto_alert: bool = True):
            if not current:
                analyze_action()
            payload = collect()
            data = current or analyze_live_call(payload)
            sid = str(uuid.uuid4())
            with db() as con:
                con.execute("""
                INSERT INTO live_sessions(
                    id, created_at, caller_number, claimed_relation, claimed_name, transcript,
                    selected_phrases_json, flags_json, comparison_json, risk_score, risk_level,
                    recommendation, actions_json, protection_mode
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    sid, now_iso(), payload["caller_number"], payload["claimed_relation"], payload["claimed_name"], payload["transcript"],
                    json.dumps(payload["selected_phrases"], ensure_ascii=False),
                    json.dumps(payload["flags"], ensure_ascii=False),
                    json.dumps(data["comparison"], ensure_ascii=False),
                    int(data["score"]), data["level"], data["recommendation"],
                    json.dumps(data["actions"], ensure_ascii=False),
                    1 if data.get("protection_mode") else 0
                ))
            self.selected_session_id = sid

            if data.get("alert_tier") in ("preventive", "urgent") and auto_alert:
                self.activate_visible_protection(sid, show_notice=True)
            else:
                messagebox.showinfo("FARO", "Llamada registrada.")
                self.show_protection_center(sid)

        avisar_button.configure(command=self.safe(lambda: save_session(True)))

        actions = tk.Frame(left, bg="#f5f7fb")
        actions.pack(fill="x", pady=10)

        ttk.Button(actions, text="Actualizar análisis", command=self.safe(analyze_action), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Guardar", command=self.safe(lambda: save_session(False)), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Avisar ahora", command=self.safe(lambda: save_session(True)), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Copiar análisis", command=self.safe(lambda: self.copy_text(self.last_text)), style="Big.TButton").pack(side="left", padx=5)

    def build_session_message(self, session: dict, target: str = "family") -> str:
        claim = f"{session.get('claimed_relation','')} {session.get('claimed_name','')}".strip()
        caller = session.get("caller_number", "No indicado")
        risk = f"{session.get('risk_level','SIN ANALIZAR')} ({session.get('risk_score','--')}/100)"
        transcript = session.get("transcript", "") or "No indicado"

        if target == "claimed":
            return "\n".join([
                "FARO - Verificación de seguridad",
                "",
                f"Recibí una llamada de alguien que dice ser: {claim or 'una persona conocida'}.",
                f"Número que aparece llamando: {caller}",
                "",
                "Necesito confirmar que realmente sos vos antes de responder o hacer cualquier cosa.",
                "Por favor respondeme por este medio con una confirmación clara.",
                "",
                "No voy a enviar dinero, códigos ni datos hasta verificar.",
                "",
                f"Mensaje preparado por FARO · creado por {AUTHOR}"
            ])

        tier = "URGENTE" if int(session.get("risk_score", 0) or 0) >= int(get_setting("urgent_alert_threshold", "70") or "70") else "PREVENTIVO"
        intro = "Estoy recibiendo una llamada y necesito asegurar que todo esté bien." if tier == "PREVENTIVO" else "Estoy recibiendo una llamada sospechosa y necesito ayuda urgente."
        return "\n".join([
            f"FARO - Aviso {tier}",
            "",
            intro,
            f"Riesgo detectado: {risk}",
            f"Número que llama: {caller}",
            f"Dicen ser: {claim or 'No indicado'}",
            "",
            "Lo que se anotó de la llamada:",
            transcript,
            "",
            "FARO recomienda:",
            session.get("recommendation", "No responder hasta verificar."),
            "",
            "Por favor ayudame a revisar esto ahora. No voy a enviar dinero, códigos ni datos hasta confirmar.",
            "",
            f"Mensaje preparado por FARO · creado por {AUTHOR}"
        ])

    def get_session(self, session_id: str | None) -> dict | None:
        if not session_id:
            return None
        with db() as con:
            r = con.execute("SELECT * FROM live_sessions WHERE id=?", (session_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        for k in ["selected_phrases_json", "flags_json", "comparison_json", "actions_json"]:
            try:
                d[k] = json.loads(d.get(k) or "[]")
            except Exception:
                pass
        return d

    def latest_session_id(self) -> str | None:
        with db() as con:
            r = con.execute("SELECT id FROM live_sessions ORDER BY created_at DESC LIMIT 1").fetchone()
        return r["id"] if r else None

    def activate_visible_protection(self, session_id: str, show_notice: bool = True):
        session = self.get_session(session_id)
        if not session:
            messagebox.showwarning("FARO", "No se encontró la llamada registrada.")
            return

        extreme_contacts = get_extreme_contacts()
        if not extreme_contacts:
            messagebox.showwarning(
                "FARO",
                "FARO detectó riesgo crítico, pero no hay contactos de confianza extrema cargados.\n\nCargue contactos marcados como 'extreme'."
            )
            self.show_contacts()
            return

        max_tabs = int(get_setting("max_auto_tabs", "3") or "3")
        msg = self.build_session_message(session, "family")
        self.copy_text(msg)

        opened = 0
        for contact in extreme_contacts[:max_tabs]:
            phone = clean_phone(contact.get("phone", ""))
            if not phone:
                continue
            with db() as con:
                con.execute("""
                INSERT INTO alerts(id,created_at,session_id,contact_id,channel,prepared_message)
                VALUES(?,?,?,?,?,?)
                """, (str(uuid.uuid4()), now_iso(), session_id, contact["id"], "visible_auto_whatsapp_protection", msg))
            self.open_whatsapp_prepared(phone, msg)
            opened += 1

        if show_notice:
            messagebox.showinfo(
                "FARO - Modo protección",
                f"FARO abrió WhatsApp con mensajes preparados para {opened} contacto(s) de confianza extrema.\n\nRevise cada pestaña y confirme el envío."
            )

        self.show_protection_center(session_id)

    def show_protection_center(self, session_id: str | None = None):
        self.clear_content()
        self.page_title("Modo protección", "Mensajes claros para pedir ayuda y verificar identidad.")

        session_id = session_id or self.selected_session_id or self.latest_session_id()
        session = self.get_session(session_id)
        if not session:
            ttk.Label(self.content, text="No hay llamada registrada todavía.", style="Sub.TLabel").pack(anchor="w", pady=12)
            ttk.Button(self.content, text="Ir a Llamada en vivo", command=self.safe(self.show_live_call), style="Big.TButton").pack(anchor="w")
            return

        comparison = session.get("comparison_json", {})
        claimed_contacts = comparison.get("claimed_contacts", []) if isinstance(comparison, dict) else []

        contacts = get_contacts()
        if not contacts:
            ttk.Label(self.content, text="No hay contactos cargados.", style="Sub.TLabel").pack(anchor="w", pady=12)
            ttk.Button(self.content, text="Cargar contactos", command=self.safe(self.show_contacts), style="Big.TButton").pack(anchor="w")
            return

        outer = tk.Frame(self.content, bg="#f5f7fb")
        outer.pack(fill="both", expand=True)

        left = tk.Frame(outer, bg="#f5f7fb")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(outer, bg="#eef3f8", highlightthickness=1, highlightbackground="#d8e1ea")
        right.pack(side="right", fill="y")
        right.configure(width=400)
        right.pack_propagate(False)

        status = tk.Frame(left, bg="#fff4d8" if session.get("risk_score", 0) >= 90 else "#e8f4ff", highlightthickness=1, highlightbackground="#d6a800")
        status.pack(fill="x", pady=(0, 10))
        tk.Label(
            status,
            text=f"Estado: {session.get('risk_level')} · {session.get('risk_score')}/100\nFARO está listo para ayudar. No comparta dinero, códigos ni datos hasta verificar.",
            font=("Segoe UI", 15, "bold"),
            bg=status["bg"],
            fg="#6b0015" if session.get("risk_score", 0) >= 90 else "#14304a",
            wraplength=780,
            justify="left"
        ).pack(anchor="w", padx=14, pady=12)

        tk.Label(left, text="Mensaje para contactos cercanos", font=("Segoe UI", 15, "bold"), bg="#f5f7fb", fg="#14304a").pack(anchor="w")
        family_msg = tk.Text(left, height=12, font=("Segoe UI", 12), wrap="word")
        family_msg.pack(fill="x", pady=(4, 10))
        family_msg.insert("end", self.build_session_message(session, "family"))

        tk.Label(left, text="Mensaje para verificar con quien dicen ser", font=("Segoe UI", 15, "bold"), bg="#f5f7fb", fg="#14304a").pack(anchor="w")
        claimed_msg = tk.Text(left, height=9, font=("Segoe UI", 12), wrap="word")
        claimed_msg.pack(fill="x", pady=(4, 10))
        claimed_msg.insert("end", self.build_session_message(session, "claimed"))

        tk.Label(right, text="Acciones visibles", font=("Segoe UI", 18, "bold"), bg="#eef3f8", fg="#14304a").pack(anchor="w", padx=16, pady=(16, 8))

        tk.Label(
            right,
            text="FARO abre WhatsApp con el mensaje preparado. Usted revisa y confirma cada envío.",
            font=("Segoe UI", 11),
            bg="#eef3f8",
            fg="#425466",
            wraplength=350,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        target_var = tk.StringVar(value=(claimed_contacts[0]["id"] if claimed_contacts else contacts[0]["id"]))

        tk.Label(right, text="Verificar con:", font=("Segoe UI", 12, "bold"), bg="#eef3f8", fg="#14304a").pack(anchor="w", padx=16, pady=(10, 4))
        for c in claimed_contacts[:5] or contacts[:5]:
            ttk.Radiobutton(right, text=f"{c['name']} - {c.get('relation','')}", variable=target_var, value=c["id"]).pack(anchor="w", padx=16, pady=2)

        def get_contact(cid: str) -> dict | None:
            for c in contacts:
                if c["id"] == cid:
                    return c
            return None

        def open_whatsapp(contact: dict, text: str, channel: str):
            phone = clean_phone(contact.get("phone", ""))
            if not phone:
                messagebox.showwarning("FARO", f"{contact.get('name','Contacto')} no tiene teléfono.")
                return
            self.copy_text(text)
            with db() as con:
                con.execute("""
                INSERT INTO alerts(id,created_at,session_id,contact_id,channel,prepared_message)
                VALUES(?,?,?,?,?,?)
                """, (str(uuid.uuid4()), now_iso(), session["id"], contact["id"], channel, text))
            self.open_whatsapp_prepared(phone, text)

        def verify_claimed():
            c = get_contact(target_var.get())
            if not c:
                return
            open_whatsapp(c, claimed_msg.get("1.0", "end").strip(), "verify_claimed")

        ttk.Button(right, text="Abrir WhatsApp a confianza extrema", command=self.safe(lambda: self.activate_visible_protection(session["id"], True)), style="Big.TButton").pack(fill="x", padx=16, pady=(18, 8))
        ttk.Button(right, text="Verificar con quien dicen ser", command=self.safe(verify_claimed), style="Big.TButton").pack(fill="x", padx=16, pady=8)
        ttk.Button(right, text="Copiar alerta familiar", command=self.safe(lambda: self.copy_text(family_msg.get("1.0", "end").strip())), style="Big.TButton").pack(fill="x", padx=16, pady=8)


    def show_email_analyzer(self):
        self.clear_content()
        self.page_title("Analizador de correos", "Revise remitente, entidad declarada y contenido antes de tocar links o responder.")

        outer = tk.Frame(self.content, bg="#f5f7fb")
        outer.pack(fill="both", expand=True)

        left = tk.Frame(outer, bg="#f5f7fb")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(outer, bg="#eef3f8", highlightthickness=1, highlightbackground="#d8e1ea")
        right.pack(side="right", fill="y")
        right.configure(width=430)
        right.pack_propagate(False)

        sender_var = tk.StringVar()
        entity_var = tk.StringVar(value="No sé / Otro")
        subject_var = tk.StringVar()

        ttk.Label(left, text="Correo del remitente").pack(anchor="w")
        ttk.Entry(left, textvariable=sender_var, font=("Segoe UI", 14)).pack(fill="x", pady=(2, 8))

        ttk.Label(left, text="¿De quién dice ser?").pack(anchor="w")
        ttk.Combobox(left, textvariable=entity_var, values=["No sé / Otro"] + list(OFFICIAL_EMAIL_PROFILES.keys()), state="readonly", font=("Segoe UI", 13)).pack(fill="x", pady=(2, 8))

        ttk.Label(left, text="Asunto del correo").pack(anchor="w")
        ttk.Entry(left, textvariable=subject_var, font=("Segoe UI", 14)).pack(fill="x", pady=(2, 8))

        ttk.Label(left, text="Pegue lo que dice el correo").pack(anchor="w")
        body_box = tk.Text(left, height=11, font=("Segoe UI", 12), wrap="word")
        body_box.pack(fill="both", expand=True, pady=(2, 8))

        flags_frame = tk.LabelFrame(left, text="Marque lo que pide o amenaza el correo", bg="#f5f7fb", font=self.font_mid)
        flags_frame.pack(fill="x", pady=8)

        flag_defs = [
            ("asks_password", "Pide contraseña / PIN / clave"),
            ("asks_code", "Pide código / token / verificación"),
            ("asks_payment", "Pide pago / transferencia / deuda"),
            ("asks_card", "Pide tarjeta o datos bancarios"),
            ("has_attachment", "Trae adjunto inesperado"),
            ("has_link", "Trae link para entrar/verificar"),
            ("urgent", "Dice urgente / último aviso"),
            ("threat_closure", "Amenaza con cerrar o bloquear cuenta"),
            ("asks_install", "Pide instalar app/programa"),
        ]
        flag_vars = {k: tk.BooleanVar() for k, _ in flag_defs}
        for i, (key, label) in enumerate(flag_defs):
            ttk.Checkbutton(flags_frame, text=label, variable=flag_vars[key]).grid(row=i//2, column=i%2, sticky="w", padx=8, pady=4)
        flags_frame.columnconfigure(0, weight=1)
        flags_frame.columnconfigure(1, weight=1)

        tk.Label(right, text="Resultado", font=("Segoe UI", 20, "bold"), bg="#eef3f8", fg="#14304a").pack(anchor="w", padx=16, pady=(16, 4))
        risk_label = tk.Label(right, text="Sin analizar", font=("Segoe UI", 18, "bold"), bg="#eef3f8", fg="#425466", wraplength=380, justify="left")
        risk_label.pack(anchor="w", padx=16, pady=8)

        result_box = tk.Text(right, height=28, font=("Segoe UI", 11), wrap="word")
        result_box.pack(fill="both", expand=True, padx=16, pady=8)

        current = {}

        def paste_body():
            try:
                body_box.delete("1.0", "end")
                body_box.insert("end", self.clipboard_get())
            except Exception:
                messagebox.showwarning("FARO", "No se pudo leer el portapapeles.")

        def analyze_action():
            data = analyze_email_message(
                sender_var.get().strip(),
                entity_var.get().strip(),
                subject_var.get().strip(),
                body_box.get("1.0", "end").strip(),
                {k: v.get() for k, v in flag_vars.items()}
            )
            current.clear()
            current.update(data)
            risk_label.configure(text=f"{data['risk_level']}\n{data['risk_score']}/100", fg=data["color"])

            result_box.configure(state="normal")
            result_box.delete("1.0", "end")
            result_box.insert("end", f"Entidad detectada: {data['claimed_entity']}\n")
            result_box.insert("end", f"Dominio remitente: {data['sender_domain'] or 'No detectado'}\n\n")
            result_box.insert("end", "Recomendación:\n")
            result_box.insert("end", data["recommendation"] + "\n\n")

            result_box.insert("end", "Motivos:\n")
            for r in data["reasons"]:
                result_box.insert("end", f"• {r}\n")

            if data["scenario_hits"]:
                result_box.insert("end", "\nEscenarios reconocidos:\n")
                for s in data["scenario_hits"]:
                    result_box.insert("end", f"• {s['label']}\n")

            if data["explanations"]:
                result_box.insert("end", "\nReglas útiles:\n")
                for e in data["explanations"]:
                    result_box.insert("end", f"• {e}\n")

            if data["urls"]:
                result_box.insert("end", "\nLinks encontrados:\n")
                for u in data["urls"]:
                    result_box.insert("end", f"• {defang(u)}\n")

            result_box.insert("end", "\nQué hacer:\n")
            result_box.insert("end", "• No responder desde este correo si hay duda.\n")
            result_box.insert("end", "• No tocar links del correo.\n")
            result_box.insert("end", "• Entrar manualmente al sitio oficial o pedir ayuda a un contacto cercano.\n")
            result_box.configure(state="disabled")
            self.last_text = json.dumps(data, ensure_ascii=False, indent=2)

        def save_scan():
            if not current:
                analyze_action()
            d = current
            with db() as con:
                con.execute("""
                INSERT INTO email_scans(
                    id, created_at, sender, sender_domain, claimed_entity, subject, body_preview,
                    risk_score, risk_level, recommendation, reasons_json, explanations_json,
                    scenario_hits_json, urls_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    d["id"], d["created_at"], d["sender"], d["sender_domain"], d["claimed_entity"],
                    d["subject"], d["body_preview"], int(d["risk_score"]), d["risk_level"],
                    d["recommendation"], json.dumps(d["reasons"], ensure_ascii=False),
                    json.dumps(d["explanations"], ensure_ascii=False),
                    json.dumps(d["scenario_hits"], ensure_ascii=False),
                    json.dumps(d["urls"], ensure_ascii=False),
                ))
            messagebox.showinfo("FARO", "Análisis de correo guardado.")

        actions = tk.Frame(left, bg="#f5f7fb")
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Pegar cuerpo", command=self.safe(paste_body), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Analizar correo", command=self.safe(analyze_action), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Guardar", command=self.safe(save_scan), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Copiar resultado", command=self.safe(lambda: self.copy_text(self.last_text)), style="Big.TButton").pack(side="left", padx=5)


    def show_contacts(self):
        self.clear_content()
        self.page_title("Contactos", "Cargue familiares, contactos oficiales y personas de confianza extrema.")

        outer = tk.Frame(self.content, bg="#f5f7fb")
        outer.pack(fill="both", expand=True)

        left = tk.Frame(outer, bg="#f5f7fb")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(outer, bg="#eef3f8", highlightthickness=1, highlightbackground="#d8e1ea")
        right.pack(side="right", fill="y")
        right.configure(width=380)
        right.pack_propagate(False)

        tree = ttk.Treeview(left, columns=("name", "relation", "phone", "trust"), show="headings")
        for col, text, width in [("name", "Nombre", 170), ("relation", "Relación", 140), ("phone", "Teléfono", 160), ("trust", "Confianza", 130)]:
            tree.heading(col, text=text)
            tree.column(col, width=width)
        tree.pack(fill="both", expand=True)

        name = tk.StringVar()
        relation = tk.StringVar()
        phone = tk.StringVar()
        email = tk.StringVar()
        aliases = tk.StringVar()
        trust = tk.StringVar(value="normal")
        notes = tk.StringVar()

        fields = [("Nombre", name), ("Relación: nieto, hijo, banco, médico", relation), ("Teléfono con código de país", phone), ("Email", email), ("Alias / apodos separados por coma", aliases), ("Notas", notes)]
        for label, var in fields:
            ttk.Label(right, text=label).pack(anchor="w", padx=16, pady=(8, 2))
            ttk.Entry(right, textvariable=var, font=self.font_mid).pack(fill="x", padx=16)

        ttk.Label(right, text="Nivel de confianza").pack(anchor="w", padx=16, pady=(8, 2))
        ttk.Combobox(right, textvariable=trust, values=["normal", "extreme"], state="readonly", font=self.font_mid).pack(fill="x", padx=16)
        tk.Label(right, text="'extreme' = contacto más cercano para alertas críticas.", font=("Segoe UI", 10), bg="#eef3f8", fg="#425466", wraplength=330, justify="left").pack(anchor="w", padx=16, pady=(4, 6))

        def refresh():
            tree.delete(*tree.get_children())
            for c in get_contacts():
                tree.insert("", "end", iid=c["id"], values=(c["name"], c.get("relation",""), c.get("phone",""), c.get("trust_level","")))

        def add():
            if not name.get().strip():
                messagebox.showwarning("FARO", "Ingrese un nombre.")
                return
            with db() as con:
                con.execute("""
                INSERT INTO contacts(id,name,relation,phone,email,aliases,trust_level,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                """, (str(uuid.uuid4()), name.get().strip(), relation.get().strip(), phone.get().strip(), email.get().strip(), aliases.get().strip(), trust.get(), notes.get().strip(), now_iso()))
            name.set(""); relation.set(""); phone.set(""); email.set(""); aliases.set(""); notes.set(""); trust.set("normal")
            refresh()

        def delete():
            sel = tree.selection()
            if not sel:
                return
            if messagebox.askyesno("FARO", "¿Eliminar contacto seleccionado?"):
                with db() as con:
                    con.execute("DELETE FROM contacts WHERE id=?", (sel[0],))
                refresh()

        ttk.Button(right, text="Agregar contacto", command=self.safe(add), style="Big.TButton").pack(fill="x", padx=16, pady=14)
        ttk.Button(right, text="Eliminar seleccionado", command=self.safe(delete), style="Big.TButton").pack(fill="x", padx=16, pady=6)

        def test_whatsapp():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("FARO", "Seleccione un contacto para probar WhatsApp.")
                return
            contact_id = sel[0]
            for c in get_contacts():
                if c["id"] == contact_id:
                    msg = "FARO - Prueba de WhatsApp. Si ves este mensaje preparado, el contacto está bien configurado."
                    self.open_whatsapp_prepared(c.get("phone", ""), msg, "test")
                    return

        ttk.Button(right, text="Probar WhatsApp", command=self.safe(test_whatsapp), style="Big.TButton").pack(fill="x", padx=16, pady=6)

        refresh()

    def show_lists(self):
        self.clear_content()
        self.page_title("Listas comparativas", "Frases internas que FARO usa para comparar lo que dice el posible estafador.")

        outer = tk.Frame(self.content, bg="#f5f7fb")
        outer.pack(fill="both", expand=True)

        left = tk.Frame(outer, bg="#f5f7fb")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(outer, bg="#eef3f8", highlightthickness=1, highlightbackground="#d8e1ea")
        right.pack(side="right", fill="y")
        right.configure(width=380)
        right.pack_propagate(False)

        tree = ttk.Treeview(left, columns=("category", "phrase", "weight", "enabled", "custom"), show="headings")
        for col, text, width in [("category", "Categoría", 140), ("phrase", "Frase", 360), ("weight", "Peso", 70), ("enabled", "Activa", 70), ("custom", "Custom", 70)]:
            tree.heading(col, text=text)
            tree.column(col, width=width)
        tree.pack(fill="both", expand=True)

        category = tk.StringVar(value="custom")
        phrase = tk.StringVar()
        weight = tk.IntVar(value=30)

        ttk.Label(right, text="Categoría").pack(anchor="w", padx=16, pady=(12, 2))
        ttk.Entry(right, textvariable=category, font=self.font_mid).pack(fill="x", padx=16)
        ttk.Label(right, text="Frase").pack(anchor="w", padx=16, pady=(12, 2))
        ttk.Entry(right, textvariable=phrase, font=self.font_mid).pack(fill="x", padx=16)
        ttk.Label(right, text="Peso de riesgo 1-80").pack(anchor="w", padx=16, pady=(12, 2))
        ttk.Spinbox(right, from_=1, to=80, textvariable=weight, font=self.font_mid).pack(fill="x", padx=16)

        def refresh():
            tree.delete(*tree.get_children())
            for r in get_phrase_rules(False):
                tree.insert("", "end", iid=r["id"], values=(r["category"], r["phrase"], r["weight"], "sí" if r["enabled"] else "no", "sí" if r["custom"] else "no"))

        def add_phrase_rule():
            if not phrase.get().strip():
                messagebox.showwarning("FARO", "Ingrese una frase.")
                return
            with db() as con:
                con.execute("""
                INSERT INTO phrase_rules(id,category,phrase,weight,enabled,custom)
                VALUES(?,?,?,?,1,1)
                """, (str(uuid.uuid4()), category.get().strip() or "custom", phrase.get().strip(), int(weight.get())))
            phrase.set("")
            refresh()

        def toggle_enabled():
            sel = tree.selection()
            if not sel:
                return
            rid = sel[0]
            with db() as con:
                row = con.execute("SELECT enabled FROM phrase_rules WHERE id=?", (rid,)).fetchone()
                if row:
                    con.execute("UPDATE phrase_rules SET enabled=? WHERE id=?", (0 if row["enabled"] else 1, rid))
            refresh()

        ttk.Button(right, text="Agregar frase", command=self.safe(add_phrase_rule), style="Big.TButton").pack(fill="x", padx=16, pady=14)
        ttk.Button(right, text="Activar/Desactivar", command=self.safe(toggle_enabled), style="Big.TButton").pack(fill="x", padx=16, pady=6)

        refresh()

    def show_link_scanner(self):
        self.clear_content()
        self.page_title("Scanner de links", "Revisa señales del link sin abrirlo.")

        url_var = tk.StringVar()
        ttk.Label(self.content, text="Link o dominio").pack(anchor="w")
        ttk.Entry(self.content, textvariable=url_var, font=("Segoe UI", 15)).pack(fill="x", pady=(2, 8))

        result = tk.Frame(self.content, bg="#eef3f8", highlightthickness=1, highlightbackground="#d8e1ea")
        result.pack(fill="both", expand=True, pady=8)

        risk_label = tk.Label(result, text="Sin analizar", font=("Segoe UI", 22, "bold"), bg="#eef3f8", fg="#425466")
        risk_label.pack(anchor="w", padx=18, pady=(18, 6))
        box = tk.Text(result, font=("Consolas", 11), wrap="word")
        box.pack(fill="both", expand=True, padx=18, pady=8)

        current = {}

        def paste():
            try:
                url_var.set(self.clipboard_get().strip())
            except Exception:
                pass

        def analyze():
            data = analyze_url(url_var.get())
            current.clear(); current.update(data)
            risk_label.configure(text=f"{data['risk_level']} · {data['risk_score']}/100", fg=data["color"])
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("end", f"Original: {data['original']}\nDefanged: {data['defanged']}\nHost: {data['host']}\nRecomendación: {data['recommendation']}\n\n")
            box.insert("end", "Señales:\n")
            for s in data["signals"]:
                box.insert("end", f"• {s['code']} (+{s['weight']}): {s['detail']}\n")
            box.configure(state="disabled")
            self.last_text = json.dumps(data, ensure_ascii=False, indent=2)

        def save():
            if not current:
                analyze()
            d = current
            with db() as con:
                con.execute("""
                INSERT INTO link_scans(id,created_at,original,normalized,defanged,host,scheme,path,risk_score,risk_level,recommendation,signals_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """, (d["id"], d["created_at"], d["original"], d["normalized"], d["defanged"], d["host"], d["scheme"], d["path"], int(d["risk_score"]), d["risk_level"], d["recommendation"], json.dumps(d["signals"], ensure_ascii=False)))
            messagebox.showinfo("FARO", "Scanner guardado.")

        actions = tk.Frame(self.content, bg="#f5f7fb")
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Pegar", command=self.safe(paste), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Analizar", command=self.safe(analyze), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Guardar", command=self.safe(save), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="Copiar defanged", command=self.safe(lambda: self.copy_text(current.get("defanged", defang(url_var.get())))), style="Big.TButton").pack(side="left", padx=5)

    def show_records(self):
        self.clear_content()
        self.page_title("Registros", "Llamadas en vivo, alertas y links escaneados.")

        tabs = ttk.Notebook(self.content)
        tabs.pack(fill="both", expand=True)

        sessions_frame = tk.Frame(tabs, bg="#f5f7fb")
        links_frame = tk.Frame(tabs, bg="#f5f7fb")
        alerts_frame = tk.Frame(tabs, bg="#f5f7fb")
        tabs.add(sessions_frame, text="Llamadas")
        tabs.add(links_frame, text="Links")
        tabs.add(alerts_frame, text="Alertas")

        tree = ttk.Treeview(sessions_frame, columns=("date", "caller", "claim", "risk", "score"), show="headings")
        for col, text, width in [("date", "Fecha", 160), ("caller", "Número", 150), ("claim", "Dice ser", 180), ("risk", "Riesgo", 230), ("score", "Score", 80)]:
            tree.heading(col, text=text); tree.column(col, width=width)
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        with db() as con:
            rows = dict_rows(con.execute("SELECT * FROM live_sessions ORDER BY created_at DESC").fetchall())
        for r in rows:
            tree.insert("", "end", iid=r["id"], values=(r["created_at"], r["caller_number"], f"{r['claimed_relation']} {r['claimed_name']}", r["risk_level"], r["risk_score"]))

        btns = tk.Frame(sessions_frame, bg="#f5f7fb")
        btns.pack(fill="x", padx=8, pady=8)

        def view_session():
            sel = tree.selection()
            if not sel:
                return
            self.selected_session_id = sel[0]
            self.show_json_window("Detalle de llamada", self.get_session(sel[0]))

        ttk.Button(btns, text="Ver detalle", command=self.safe(view_session), style="Big.TButton").pack(side="left", padx=5)
        ttk.Button(btns, text="Modo protección", command=self.safe(lambda: self.show_protection_center(tree.selection()[0] if tree.selection() else None)), style="Big.TButton").pack(side="left", padx=5)

        ltree = ttk.Treeview(links_frame, columns=("date", "url", "host", "risk", "score"), show="headings")
        for col, text, width in [("date", "Fecha", 160), ("url", "URL segura", 300), ("host", "Host", 180), ("risk", "Riesgo", 220), ("score", "Score", 80)]:
            ltree.heading(col, text=text); ltree.column(col, width=width)
        ltree.pack(fill="both", expand=True, padx=8, pady=8)
        with db() as con:
            scans = dict_rows(con.execute("SELECT * FROM link_scans ORDER BY created_at DESC").fetchall())
        for s in scans:
            ltree.insert("", "end", iid=s["id"], values=(s["created_at"], s["defanged"], s["host"], s["risk_level"], s["risk_score"]))

        atree = ttk.Treeview(alerts_frame, columns=("date", "session", "contact", "channel"), show="headings")
        for col, text, width in [("date", "Fecha", 160), ("session", "Sesión", 180), ("contact", "Contacto", 160), ("channel", "Canal", 220)]:
            atree.heading(col, text=text); atree.column(col, width=width)
        atree.pack(fill="both", expand=True, padx=8, pady=8)
        with db() as con:
            alerts = dict_rows(con.execute("""
            SELECT alerts.*, contacts.name AS contact_name
            FROM alerts LEFT JOIN contacts ON alerts.contact_id=contacts.id
            ORDER BY alerts.created_at DESC
            """).fetchall())
        for a in alerts:
            atree.insert("", "end", iid=a["id"], values=(a["created_at"], a["session_id"], a.get("contact_name",""), a["channel"]))

    def show_reports(self):
        self.clear_content()
        self.page_title("Reportes", "Exportar HTML, CSV, JSON y backup SQLite.")

        info = tk.Text(self.content, height=10, font=("Segoe UI", 13), wrap="word")
        info.pack(fill="x", pady=8)
        info.insert("end", "FARO v4 exporta llamadas, comparaciones, alertas preparadas, links escaneados y contactos de confianza.\n\n")
        info.insert("end", "Los archivos se guardan localmente en faro_data/reports, faro_data/exports y faro_data/backups.\n")
        info.configure(state="disabled")

        ttk.Button(self.content, text="Generar paquete de reporte", command=self.safe(self.export_all), style="Big.TButton").pack(anchor="w", pady=8)
        ttk.Button(self.content, text="Abrir carpeta de datos", command=self.safe(self.open_data_folder), style="Big.TButton").pack(anchor="w", pady=8)

    def export_all(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = REPORTS_DIR / f"faro_v4_report_{stamp}.html"
        json_path = EXPORTS_DIR / f"faro_v4_to_civitas_argus_{stamp}.json"
        sessions_csv = EXPORTS_DIR / f"faro_v4_sessions_{stamp}.csv"
        links_csv = EXPORTS_DIR / f"faro_v4_links_{stamp}.csv"
        backup_path = BACKUPS_DIR / f"faro_v4_backup_{stamp}.sqlite3"

        with db() as con:
            sessions = dict_rows(con.execute("SELECT * FROM live_sessions ORDER BY created_at DESC").fetchall())
            links = dict_rows(con.execute("SELECT * FROM link_scans ORDER BY created_at DESC").fetchall())
            contacts = dict_rows(con.execute("SELECT * FROM contacts ORDER BY name ASC").fetchall())
            alerts = dict_rows(con.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall())
            email_scans = dict_rows(con.execute("SELECT * FROM email_scans ORDER BY created_at DESC").fetchall())

        rows_sessions = "".join(
            f"<tr><td>{html.escape(s.get('created_at',''))}</td><td>{html.escape(s.get('caller_number',''))}</td><td>{html.escape((s.get('claimed_relation','')+' '+s.get('claimed_name','')).strip())}</td><td>{html.escape(s.get('risk_level',''))}</td><td>{s.get('risk_score','')}</td><td>{html.escape(s.get('recommendation',''))}</td></tr>"
            for s in sessions
        )
        rows_links = "".join(
            f"<tr><td>{html.escape(l.get('created_at',''))}</td><td><code>{html.escape(l.get('defanged',''))}</code></td><td>{html.escape(l.get('host',''))}</td><td>{html.escape(l.get('risk_level',''))}</td><td>{l.get('risk_score','')}</td></tr>"
            for l in links
        )

        html_doc = f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>FARO v4 Report</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fb;color:#17212b;padding:32px}}
h1,h2{{color:#14304a}} .card{{background:white;border:1px solid #d8e1ea;border-radius:16px;padding:18px;margin:16px 0}}
table{{width:100%;border-collapse:collapse;background:white}} th,td{{border-bottom:1px solid #d8e1ea;padding:10px;text-align:left;vertical-align:top}}
th{{background:#eef3f8;color:#14304a}} code{{font-family:Consolas,monospace}}
.footer{{margin-top:32px;color:#425466;font-weight:bold}}
</style></head>
<body>
<h1>FARO v4</h1>
<p>Asistente de protección familiar contra estafas digitales · Creado por {AUTHOR}</p>
<div class="card">
<b>Generado:</b> {now_iso()}<br>
<b>Llamadas registradas:</b> {len(sessions)}<br>
<b>Links escaneados:</b> {len(links)}<br>
<b>Contactos:</b> {len(contacts)}<br>
<b>Alertas preparadas:</b> {len(alerts)}<br>\n<b>Correos analizados:</b> {len(email_scans)}
</div>
<h2>Llamadas en vivo</h2>
<table><tr><th>Fecha</th><th>Número</th><th>Dice ser</th><th>Riesgo</th><th>Score</th><th>Recomendación</th></tr>{rows_sessions}</table>
<h2>Links escaneados</h2>
<table><tr><th>Fecha</th><th>URL segura</th><th>Host</th><th>Riesgo</th><th>Score</th></tr>{rows_links}</table>
<p class="footer">FARO v4 · Diseño y dirección: {AUTHOR}</p>
</body></html>"""
        html_path.write_text(html_doc, encoding="utf-8")

        with sessions_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id","created_at","caller_number","claimed_relation","claimed_name","risk_score","risk_level","recommendation","transcript","protection_mode"])
            writer.writeheader()
            for s in sessions:
                writer.writerow({k: s.get(k, "") for k in writer.fieldnames})

        with links_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id","created_at","original","defanged","host","risk_score","risk_level","recommendation"])
            writer.writeheader()
            for l in links:
                writer.writerow({k: l.get(k, "") for k in writer.fieldnames})

        json_path.write_text(json.dumps({
            "source": "FARO",
            "version": APP_VERSION,
            "author": AUTHOR,
            "target": "CIVITAS/ARGUS",
            "type": "family_protection_anti_fraud_records",
            "created_at": now_iso(),
            "sessions": sessions,
            "link_scans": links,
            "contacts_count": len(contacts),
            "alerts": alerts,
            "email_scans": email_scans,
            "privacy_note": "Local export. Share only with consent."
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        if DB_PATH.exists():
            shutil.copy2(DB_PATH, backup_path)

        messagebox.showinfo("FARO", f"Reporte generado:\n{html_path}\n\nExport:\n{json_path}")
        self.open_data_folder()

    def show_settings(self):
        self.clear_content()
        self.page_title("Configuración", "Idioma, modo protección y firma del proyecto.")

        ttk.Label(self.content, text=f"Autor visible: {AUTHOR}", style="Sub.TLabel").pack(anchor="w", pady=6)
        ttk.Label(self.content, text=f"Versión: {APP_VERSION}", style="Sub.TLabel").pack(anchor="w", pady=6)

        auto_var = tk.BooleanVar(value=(get_setting("auto_open_whatsapp_on_critical", "yes") == "yes"))
        threshold_var = tk.StringVar(value=get_setting("critical_threshold", "90"))
        preventive_var = tk.StringVar(value=get_setting("preventive_alert_threshold", "43"))
        urgent_var = tk.StringVar(value=get_setting("urgent_alert_threshold", "70"))
        tabs_var = tk.StringVar(value=get_setting("max_auto_tabs", "3"))

        def save_settings():
            set_setting("auto_open_whatsapp_on_critical", "yes" if auto_var.get() else "no")
            set_setting("critical_threshold", threshold_var.get().strip() or "90")
            set_setting("preventive_alert_threshold", preventive_var.get().strip() or "43")
            set_setting("urgent_alert_threshold", urgent_var.get().strip() or "70")
            set_setting("max_auto_tabs", tabs_var.get().strip() or "3")
            messagebox.showinfo("FARO", "Configuración guardada.")

        ttk.Checkbutton(self.content, text="Abrir WhatsApp automáticamente al detectar riesgo crítico", variable=auto_var).pack(anchor="w", pady=8)
        ttk.Label(self.content, text="Umbral aviso preventivo").pack(anchor="w", pady=(12, 2))
        ttk.Entry(self.content, textvariable=preventive_var, font=self.font_mid).pack(anchor="w")
        ttk.Label(self.content, text="Umbral alerta urgente").pack(anchor="w", pady=(12, 2))
        ttk.Entry(self.content, textvariable=urgent_var, font=self.font_mid).pack(anchor="w")
        ttk.Label(self.content, text="Umbral de protección crítica").pack(anchor="w", pady=(12, 2))
        ttk.Entry(self.content, textvariable=threshold_var, font=self.font_mid).pack(anchor="w")
        ttk.Label(self.content, text="Máximo de pestañas WhatsApp a abrir").pack(anchor="w", pady=(12, 2))
        ttk.Entry(self.content, textvariable=tabs_var, font=self.font_mid).pack(anchor="w")

        ttk.Button(self.content, text="Guardar configuración", command=self.safe(save_settings), style="Big.TButton").pack(anchor="w", pady=12)

        def set_lang(lang):
            set_setting("language", lang)
            self.lang = lang
            self.t = LANG.get(lang, LANG["es"])
            self.build_nav()
            self.show_home()

        ttk.Button(self.content, text="Español", command=self.safe(lambda: set_lang("es")), style="Big.TButton").pack(anchor="w", pady=6)
        ttk.Button(self.content, text="English", command=self.safe(lambda: set_lang("en")), style="Big.TButton").pack(anchor="w", pady=6)
        ttk.Button(self.content, text="Português", command=self.safe(lambda: set_lang("pt")), style="Big.TButton").pack(anchor="w", pady=6)
        ttk.Button(self.content, text="Abrir carpeta de datos", command=self.safe(self.open_data_folder), style="Big.TButton").pack(anchor="w", pady=12)

    def show_json_window(self, title: str, data):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("850x650")
        txt = tk.Text(win, font=("Consolas", 11), wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("end", json.dumps(data, ensure_ascii=False, indent=2))
        txt.configure(state="disabled")
        ttk.Button(win, text="Copiar", command=self.safe(lambda: self.copy_text(json.dumps(data, ensure_ascii=False, indent=2)))).pack(pady=8)

    def open_data_folder(self):
        ensure_dirs()
        try:
            if os.name == "nt":
                os.startfile(str(DATA_DIR))
            elif sys.platform == "darwin":
                os.system(f'open "{DATA_DIR}"')
            else:
                os.system(f'xdg-open "{DATA_DIR}"')
        except Exception:
            messagebox.showinfo("FARO", str(DATA_DIR))


def main():
    ensure_dirs()
    init_db()
    app = FaroApp()
    app.mainloop()


if __name__ == "__main__":
    main()
