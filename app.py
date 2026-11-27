import secrets, time
BILETLER = {}
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
db.execute("INSERT OR IGNORE INTO musteriler VALUES ('anahtar_oyun_studyo_1', 'Indie Oyun Ekibi', 1, 0, 'oyun_yama_v1.pak', 'sistem')")
db.commit()

os.makedirs("dosyalar", exist_ok=True)
open("dosyalar/oyun_yama_v1.pak", "wb").write(b"GERCEK_OYUN_VERI_PAKETI_1001" * 100)

def log_yaz(ip, islem, detay):
    z = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute("INSERT INTO loglar (zaman, ip, islem, detay) VALUES (?, ?, ?, ?)", (z, ip, islem, detay))
    db.commit()
    with open("otoyol_kayitlar.log", "a", encoding="utf-8") as lf:
        lf.write(f"{z} | {ip} | {islem} | {detay}\n")

def ip_kullanim_bul(ip):
    r = db.execute("SELECT COUNT(*) FROM musteriler WHERE ip=?", (ip,)).fetchone()
    for val in r: return int(val)
    return 0

def tur_bul(ad):
    k = ad.lower()
    if k.endswith((".jpg", ".jpeg")): return "image/jpeg"
    if k.endswith(".png"): return "image/png"
    if k.endswith(".webp"): return "image/webp"
    if k.endswith(".mp3"): return "audio/mpeg"
    if k.endswith(".wav"): return "audio/wav"
    if k.endswith((".m4a", ".aac")): return "audio/mp4"
    if k.endswith(".mp4"): return "video/mp4"
    if k.endswith(".pdf"): return "application/pdf"
    return "text/plain; charset=utf-8"
class Otoyol(BaseHTTPRequestHandler):
    def ip_bul(self):
        fwd = self.headers.get("X-Forwarded-For", "")
        return fwd.split(",").pop(0).strip() if fwd else str(self.client_address)

    def html(self, kod, metin):
        self.send_response(kod)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(metin.encode("utf-8"))

    def ham_veri_gonder(self, key, indir):
        row = db.execute("SELECT dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
        if not row: self.html(404, "Bulunamadi"); return
        d_adi = ""
        for v in row: d_adi = v
        yol = os.path.join("dosyalar", d_adi or "oyun_yama_v1.pak")
        if not os.path.exists(yol): yol = "dosyalar/oyun_yama_v1.pak"
        ad, veri = os.path.basename(yol).replace(key + "_", ""), open(yol, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream" if indir else tur_bul(ad))
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Content-Disposition", f'attachment; filename="{ad}"' if indir else "inline")
        self.end_headers()
        self.wfile.write(veri)
    def do_GET(self):
        p = urlparse(self.path); q = parse_qs(p.query); key = "".join(q.get("anahtar", [])).strip(); ip = self.ip_bul()
        if p.path == "/yonetim":
            if "".join(q.get("sifre", [])) != GIZLI: self.html(403, "Yetkisiz"); return
            if "ekle" in q:
                h = "".join(q.get("ekle", [])); m = int("".join(q.get("miktar", ["100"])) or 100)
                db.execute("UPDATE musteriler SET kalan_hak=kalan_hak+? WHERE anahtar=?", (m, h)); db.commit()
                log_yaz(ip, "MANUEL_KOTA", f"{h} ({m:+d} Hak)")
            self.html(200, sablon.kokpit(db.execute("SELECT anahtar, ad, kalan_hak, toplam_gecis, dosya_adi, ip FROM musteriler").fetchall(), db.execute("SELECT zaman, ip, islem, detay FROM loglar ORDER BY id DESC LIMIT 200").fetchall(), GIZLI)); return
        if p.path == "/otomatik-onay":
            if "".join(q.get("gizli", [])) != GIZLI: self.send_response(403); self.end_headers(); return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak+100 WHERE anahtar=?", (key,)); db.commit()
            log_yaz(ip, "OTOMATIK_ODEME", f"{key} (+100 Hak)"); self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return
        if p.path == "/ham":
            b = "".join(q.get("bilet", [])).strip()
            kayit = BILETLER.get(b)
            if not kayit or time.time() > kayit[1]:
                self.html(403, "<h3>403 Yasak: Gecersiz veya suresi dolmus medya bileti!</h3>"); return
            self.ham_veri_gonder(kayit[0], False); return
        if p.path == "/onizle":
            row = db.execute("SELECT kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not row: self.html(401, "<h3>Geçersiz Anahtar</h3>"); return
            kalan, d_adi = row
            if "".join(q.get("admin", [])) != GIZLI:
                if kalan <= 0:
                    log_yaz(ip, "ONIZLEME_ENGELLENDI", f"{key} (Kota 0)")
                    self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ Kotanız Bitti!</h3><p><b>100 TL = 100 Hak</b> IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})<br>Açıklama: <code>{key}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
                db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (key,)); db.commit()
                log_yaz(ip, "DOSYA_GORUNTULENDI", f"{key} (Kalan: {kalan - 1})")
            bilet = secrets.token_urlsafe(24)
            BILETLER[bilet] = (key, time.time() + 30)
            self.html(200, sablon.medya_goruntule(key, (d_adi or "oyun_yama_v1.pak").replace(key + "_", ""), bilet)); return
        if p.path == "/indir" or self.headers.get("X-API-Key"):
            kh = key or self.headers.get("X-API-Key")
            row = db.execute("SELECT kalan_hak FROM musteriler WHERE anahtar=?", (kh,)).fetchone()
            if not row: self.html(401, "<h3>Geçersiz Anahtar</h3>"); return
            kalan = sum(int(v) for v in row)
            if kalan <= 0:
                log_yaz(ip, "INDIRME_ENGELLENDI", f"{kh} (Kota 0)")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ Kotanız Bitti!</h3><p><b>100 TL = 100 Hak</b> IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})<br>Açıklama: <code>{kh}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (kh,)); db.commit()
            log_yaz(ip, "VERI_INDIRILDI", f"{kh} (Kalan: {kalan - 1})"); self.ham_veri_gonder(kh, True); return
        if p.path == "/kontrol":
            r = db.execute("SELECT ad, kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not r: self.html(200, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Anahtar Bulunamadı</h3><a href='/' style='color:#38bdf8;'>← Geri</a></body>"); return
            ad_p, kalan_p, dosya_p = r
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>📂 Depo Durumu</h2><p><b>Proje:</b> {ad_p}</p><p><b>Dosya:</b> {(dosya_p or 'oyun_yama_v1.pak').replace(key+'_','')}</p><p><b>Kalan Hak:</b> <b>{kalan_p}</b></p><a href='/onizle?anahtar={key}' style='display:inline-block;background:#3b82f6;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;'>👁️ / 🎵 Dosyayı Aç</a> <a href='/indir?anahtar={key}' style='display:inline-block;background:#10b981;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;margin-left:8px;'>⬇️ İndir</a><br><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
        if p.path == "/":
            ip_k = max(0, 10 - ip_kullanim_bul(ip))
            uyari = f"<p style='color:#f87171;'>⚠️ IP ({ip}) 10 ücretsiz hak doldu! <b>100 TL = 100 Hak</b> yükleyin.</p>" if ip_k == 0 else f"<p style='color:#34d399;'>🌐 IP: <code>{ip}</code> | Kalan Ücretsiz Anahtar: <b>{ip_k} / 10</b></p>"
            self.html(200, sablon.ana_sayfa(uyari, BANKA_ADI, ALICI_AD, IBAN_NO)); return
    def do_POST(self):
        ip_k = self.ip_bul()
        if "/anahtar" in self.path or "/olustur" in self.path or self.path == "/":
            cl = int(self.headers.get("Content-Length", 0))
            if cl < 2048:
                sayi = db.execute("SELECT COUNT(*) FROM musteriler WHERE ip=?", (ip_k,)).fetchone()[0]
                if sayi[0] >= 10:
                    log_yaz(ip_k, "ANAHTAR_LIMITI", "10 ucretsiz anahtar hakki doldu")
                    self.html(403, "<body style=\"font-family:sans-serif;background:#0f172a;color:white;padding:30px;\"><h3>🚫 Ücretsiz API Anahtarı Alma Hakkınız Doldu (10/10)!</h3><p>Her API anahtarı tek kullanımlıktır ve maksimum 10 adet ücretsiz alabilirsiniz.</p><a href=\"/\" style=\"color:#38bdf8;\">← Ana Sayfa</a></body>")
                    return

        ham = self.rfile.read(int(self.headers.get("Content-Length", 0))); ip = self.ip_bul()
        if self.path == "/kayit":
            ip_k = max(0, 10 - ip_kullanim_bul(ip))
            if ip_k <= 0:
                log_yaz(ip, "IP_LIMIT_DOLU", "Engellendi")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ IP ({ip}) 10 Ücretsiz Hak Doldu!</h3><p><b>100 TL = 100 Hak</b> IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})</p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            ad = "".join(parse_qs(ham.decode()).get("ad", ["Proje"])); k = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, 1, 0, 'oyun_yama_v1.pak', ?)", (k, ad, ip)); db.commit()
            log_yaz(ip, "YENI_KAYIT", f"{ad} ({k}) | Kalan: {ip_k - 1}")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>✅ Anahtarınız: <code>{k}</code></h2><p>Bu anahtarda <b>10</b> hak var. (IP kalan: <b>{ip_k - 1} / 10</b>)</p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>")
        elif self.path == "/yukle":
            m = BytesParser(policy=default).parsebytes(f"Content-Type: {self.headers.get('Content-Type')}\r\n\r\n".encode() + ham)
            anahtar, d_adi, icerik = "", "", b""
            for part in m.iter_parts():
                if part.get_param("name", header="content-disposition") == "anahtar": anahtar = part.get_content().strip()
                elif part.get_param("name", header="content-disposition") == "dosya": d_adi = part.get_filename() or ""; icerik = part.get_payload(decode=True)
            row = db.execute("SELECT kalan_hak FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            if not row or not d_adi:
                self.html(400, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Geçersiz Anahtar veya Dosya</h3><a href='/' style='color:#38bdf8;'>Geri</a></body>"); return
            kalan = sum(int(v) for v in row)
            if kalan <= 0:
                log_yaz(ip, "YUKLEME_ENGELLENDI", f"{anahtar} (Kota 0)")
                odeme_linki = "https://shopier.com"
                qr_resim_url = "https://hizliresim.com"
                self.html(402, f"""<body style="font-family:sans-serif;background:#0f172a;color:white;padding:20px;max-width:480px;margin:auto;">
                <div style="background:#1e293b;padding:20px;border-radius:12px;border:1px solid #334155;">
                <h2 style="color:#f87171;margin-top:0;">⚠️ Kotanız Bitti (0 Hak)</h2>
                <p style="color:#cbd5e1;">Devam etmek için <b>100 TL = 100 Hak</b> paketini seçin:</p>
                <a href="{odeme_linki}" target="_blank" style="display:block;text-align:center;background:#22c55e;color:#0f172a;font-weight:bold;text-decoration:none;padding:14px;border-radius:8px;margin:15px 0;">💳 Kart ile 5 Saniyede Öde (100 TL)</a>
                <div style="text-align:center;background:#0f172a;padding:15px;border-radius:8px;margin-bottom:15px;">
                <p style="margin:0 0 10px 0;font-size:14px;color:#94a3b8;">📱 Mobil Bankacılıktan Karekod Okut:</p>
                <img src="{qr_resim_url}" alt="TR Karekod" style="width:160px;height:160px;border-radius:8px;background:white;padding:5px;">
                </div>
                <div style="background:#0f172a;padding:15px;border-radius:8px;font-size:14px;">
                <p style="margin:0 0 10px 0;color:#94a3b8;">🏦 Veya Tek Tıkla IBAN Gönder:</p>
                <div style="margin-bottom:8px;">IBAN:<br><code id="iban" style="color:#38bdf8;font-size:13px;">{IBAN_NO}</code>
                <button onclick="kopyala('iban', this)" style="float:right;background:#3b82f6;color:white;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;">📋 Kopyala</button></div>
                <p style="margin:8px 0;">Alıcı: <b>{ALICI_AD}</b></p>
                <div style="margin-top:8px;">Açıklama (Zorunlu):<br><code id="aciklama" style="color:#fbbf24;font-size:15px;font-weight:bold;">{anahtar}</code>
                <button onclick="kopyala('aciklama', this)" style="float:right;background:#10b981;color:white;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;">📋 Kopyala</button></div>
                </div>
                <div style="margin-top:20px;text-align:center;"><a href="/" style="color:#38bdf8;text-decoration:none;">← Ana Sayfaya Dön</a></div>
                </div>
                <script>
                function kopyala(id, btn) {{
                    navigator.clipboard.writeText(document.getElementById(id).innerText);
                    var eski = btn.innerText; btn.innerText = "✅ Kopyalandı!";
                    setTimeout(() => {{ btn.innerText = eski; }}, 2000);
                }}
                </script></body>"""); return
            g_ad = f"{anahtar}_{os.path.basename(d_adi)}"
            open(os.path.join("dosyalar", g_ad), "wb").write(icerik)
            db.execute("UPDATE musteriler SET dosya_adi=?, kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (g_ad, anahtar)); db.commit()
            log_yaz(ip, "DOSYA_YUKLENDI", f"{anahtar} -> {os.path.basename(d_adi)} (Kalan: {kalan - 1})")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>🚀 Dosya Yüklendi! (Kalan Hak: {kalan - 1})</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;font-weight:bold;'>📂 Dosyayı Aç (Gör / Dinle / İndir) →</a></body>")

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), Otoyol).serve_forever()
