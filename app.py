from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3, os, uuid, sablon
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from email.parser import BytesParser
from email.policy import default

IBAN_NO, ALICI_AD, BANKA_ADI, GIZLI = "TR43 0004 6001 4788 8000 3997 07", "Semih Eymen Uçar", "Akbank", "otoyol_gizli_9988"

db = sqlite3.connect("otoyol.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS musteriler (anahtar TEXT PRIMARY KEY, ad TEXT, kalan_hak INTEGER, toplam_gecis INTEGER, dosya_adi TEXT, ip TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS loglar (id INTEGER PRIMARY KEY AUTOINCREMENT, zaman TEXT, ip TEXT, islem TEXT, detay TEXT)")
db.execute("INSERT OR IGNORE INTO musteriler VALUES ('anahtar_oyun_studyo_1', 'Indie Oyun Ekibi', 10, 0, 'oyun_yama_v1.pak', 'sistem')")
db.commit()

os.makedirs("dosyalar", exist_ok=True)
open("dosyalar/oyun_yama_v1.pak", "wb").write(b"GERCEK_OYUN_VERI_PAKETI_1001" * 100)

def log_yaz(ip, islem, detay):
    db.execute("INSERT INTO loglar (zaman, ip, islem, detay) VALUES (?, ?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip, islem, detay))
    db.commit()

def ip_kullanim_bul(ip):
    r = db.execute("SELECT COALESCE(SUM(toplam_gecis), 0) FROM musteriler WHERE ip=?", (ip,)).fetchone()
    for val in r: return int(val)
    return 0

class Otoyol(BaseHTTPRequestHandler):
    def ip_bul(self):
        fwd = self.headers.get("X-Forwarded-For", "")
        return fwd.split(",").pop(0).strip() if fwd else str(self.client_address)

    def html(self, kod, metin):
        self.send_response(kod); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(metin.encode("utf-8"))

    def gonder(self, key, indir):
        ip = self.ip_bul()
        row = db.execute("SELECT kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
        if not row:
            self.html(401, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Geçersiz Anahtar</h3><a href='/' style='color:#38bdf8;'>Geri</a></body>"); return
        kalan, d_adi = row
        if indir:
            if kalan <= 0:
                log_yaz(ip, "KOTA_BITTI", f"{key} | 100 TL = 100 Hak gerekli")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ 10 Ücretsiz Hakkınız Doldu!</h3><p><b>IP:</b> <code>{ip}</code><br>Devam etmek için <b>100 TL = 100 Hak</b> yükleyin.<br><b>IBAN:</b> <code>{IBAN_NO}</code> ({ALICI_AD})<br><b>Açıklama:</b> <code>{key}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (key,)); db.commit()
            log_yaz(ip, "VERI_CEKILDI", f"{key} (Kalan: {kalan - 1})")
        yol = os.path.join("dosyalar", d_adi or "oyun_yama_v1.pak")
        if not os.path.exists(yol): yol = "dosyalar/oyun_yama_v1.pak"
        ad, veri = os.path.basename(yol).replace(key + "_", ""), open(yol, "rb").read()
        k = ad.lower()
        tur = "application/octet-stream" if indir else ("image/jpeg" if k.endswith((".jpg",".jpeg")) else "image/png" if k.endswith(".png") else "application/pdf" if k.endswith(".pdf") else "text/plain; charset=utf-8")
        self.send_response(200); self.send_header("Content-Type", tur); self.send_header("Content-Length", str(len(veri)))
        self.send_header("Content-Disposition", f'attachment; filename="{ad}"' if indir else "inline"); self.end_headers()
        self.wfile.write(veri)

    def do_GET(self):
        p = urlparse(self.path); q = parse_qs(p.query); key = "".join(q.get("anahtar", [])).strip(); ip = self.ip_bul()
        if p.path == "/yonetim":
            if "".join(q.get("sifre", [])) != GIZLI: self.html(403, "Yetkisiz"); return
            if "ekle" in q:
                h = "".join(q.get("ekle", []))
                db.execute("UPDATE musteriler SET kalan_hak=kalan_hak+100 WHERE anahtar=?", (h,)); db.commit()
                log_yaz(ip, "MANUEL_KOTA", f"{h} (+100 Hak)")
            self.html(200, sablon.kokpit(db.execute("SELECT anahtar, ad, kalan_hak, toplam_gecis, dosya_adi, ip FROM musteriler").fetchall(), db.execute("SELECT zaman, ip, islem, detay FROM loglar ORDER BY id DESC LIMIT 40").fetchall(), GIZLI)); return
        if p.path == "/otomatik-onay":
            if "".join(q.get("gizli", [])) != GIZLI: self.send_response(403); self.end_headers(); return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak+100 WHERE anahtar=?", (key,)); db.commit()
            log_yaz(ip, "OTOMATIK_ODEME", f"{key} (+100 Hak)"); self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return
        if p.path == "/indir": self.gonder(key, True); return
        if p.path == "/onizle": self.gonder(key, q.get("admin") != [GIZLI]); return
        if p.path == "/kontrol":
            r = db.execute("SELECT ad, kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not r: self.html(200, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Anahtar Bulunamadı</h3><a href='/' style='color:#38bdf8;'>← Geri</a></body>"); return
            ad_p, kalan_p, dosya_p = r
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>📂 Depo Durumu</h2><p><b>Proje:</b> {ad_p}</p><p><b>Dosya:</b> {(dosya_p or 'oyun_yama_v1.pak').replace(key+'_','')}</p><p><b>Kalan Hak:</b> {kalan_p}</p><a href='/indir?anahtar={key}' style='display:inline-block;background:#10b981;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;'>⬇️ İndir</a> <a href='/onizle?anahtar={key}' target='_blank' style='display:inline-block;background:#3b82f6;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;margin-left:8px;'>👁️ İndirmeden Gör</a><br><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
        if p.path == "/" and not self.headers.get("X-API-Key"):
            ip_kalan = max(0, 10 - ip_kullanim_bul(ip))
            uyari = f"<p style='color:#f87171;'>⚠️ IP adresiniz ({ip}) için 10 ücretsiz hak doldu! <b>100 TL = 100 Hak</b> yükleyin.</p>" if ip_kalan == 0 else f"<p style='color:#34d399;'>🌐 IP Adresiniz: <code>{ip}</code> | Kalan Ücretsiz Hakkınız: <b>{ip_kalan} / 10</b></p>"
            self.html(200, sablon.ana_sayfa(uyari, BANKA_ADI, ALICI_AD, IBAN_NO)); return
        self.gonder(self.headers.get("X-API-Key"), True)

    def do_POST(self):
        ham = self.rfile.read(int(self.headers.get("Content-Length", 0))); ip = self.ip_bul()
        if self.path == "/kayit":
            ip_kalan = max(0, 10 - ip_kullanim_bul(ip))
            if ip_kalan <= 0:
                log_yaz(ip, "IP_LIMIT_DOLU", "Yeni anahtar engellendi")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ IP ({ip}) İçin 10 Ücretsiz Hak Doldu!</h3><p><b>100 TL = 100 Hak</b> için IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})</p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            ad = "".join(parse_qs(ham.decode()).get("ad", ["Proje"])); k = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, ?, 0, 'oyun_yama_v1.pak', ?)", (k, ad, ip_kalan, ip)); db.commit()
            log_yaz(ip, "YENI_KAYIT", f"{ad} ({k}) | Kalan: {ip_kalan}")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>✅ Anahtarınız: <code>{k}</code></h2><p>IP ({ip}) kalan ücretsiz hak: <b>{ip_kalan}</b></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>")
        elif self.path == "/yukle":
            m = BytesParser(policy=default).parsebytes(f"Content-Type: {self.headers.get('Content-Type')}\r\n\r\n".encode() + ham)
            anahtar, d_adi, icerik = "", "", b""
            for part in m.iter_parts():
                if part.get_param("name", header="content-disposition") == "anahtar": anahtar = part.get_content().strip()
                elif part.get_param("name", header="content-disposition") == "dosya": d_adi = part.get_filename() or ""; icerik = part.get_payload(decode=True)
            if not db.execute("SELECT 1 FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone() or not d_adi:
                self.html(400, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Geçersiz Anahtar/Dosya</h3><a href='/' style='color:#38bdf8;'>Geri</a></body>"); return
            g_ad = f"{anahtar}_{os.path.basename(d_adi)}"
            r_hak = db.execute("SELECT kalan_hak FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            for hk in r_hak:
                if hk <= 0: self.html(402, "<h3>⚠️ Kotanız Bitti! 100 TL = 100 Hak yükleyin.</h3>"); return
            open(os.path.join("dosyalar", g_ad), "wb").write(icerik)
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (anahtar,))
            db.execute("UPDATE musteriler SET dosya_adi=? WHERE anahtar=?", (g_ad, anahtar)); db.commit()
            log_yaz(ip, "DOSYA_YUKLENDI", f"{anahtar} -> {os.path.basename(d_adi)}")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>🚀 Dosya Yüklendi!</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;font-weight:bold;'>📂 Dosyayı Gör ve İndir →</a></body>")

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), Otoyol).serve_forever()
