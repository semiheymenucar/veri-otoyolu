import math
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
                gereken_hak = max(1, math.ceil(len(icerik) / (50 * 1024 * 1024)))
            if kalan < gereken_hak:
                    log_yaz(ip, "ONIZLEME_ENGELLENDI", f"{key} (Kota 0)")
                    self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ Kotanız Bitti!</h3><p><b>100 TL = 30 Hak</b> veya <b>250 TL = 100 Hak</b> IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})<br>Açıklama: <code>{key}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
                db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-?, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (key,)); db.commit()
                log_yaz(ip, "DOSYA_GORUNTULENDI", f"{key} (Harcanan: {gereken_hak} Hak | Kalan: {kalan - gereken_hak})")
            bilet = secrets.token_urlsafe(24)
            BILETLER[bilet] = (key, time.time() + 30)
            self.html(200, sablon.medya_goruntule(key, (d_adi or "oyun_yama_v1.pak").replace(key + "_", ""), bilet)); return
        if p.path == "/indir" or self.headers.get("X-API-Key"):
            kh = key or self.headers.get("X-API-Key")
            row = db.execute("SELECT kalan_hak FROM musteriler WHERE anahtar=?", (kh,)).fetchone()
            if not row: self.html(401, "<h3>Geçersiz Anahtar</h3>"); return
            kalan = sum(int(v) for v in row)
            gereken_hak = max(1, math.ceil(len(icerik) / (50 * 1024 * 1024)))
            if kalan < gereken_hak:
                log_yaz(ip, "INDIRME_ENGELLENDI", f"{kh} (Kota 0)")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ Kotanız Bitti!</h3><p><b>100 TL = 30 Hak</b> veya <b>250 TL = 100 Hak</b> IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})<br>Açıklama: <code>{kh}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-?, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (kh,)); db.commit()
            log_yaz(ip, "VERI_INDIRILDI", f"{kh} (Harcanan: {gereken_hak} Hak | Kalan: {kalan - gereken_hak})"); self.ham_veri_gonder(kh, True); return
        if p.path == "/kontrol":
            r = db.execute("SELECT ad, kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not r: self.html(200, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Anahtar Bulunamadı</h3><a href='/' style='color:#38bdf8;'>← Geri</a></body>"); return
            ad_p, kalan_p, dosya_p = r
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>📂 Depo Durumu</h2><p><b>Proje:</b> {ad_p}</p><p><b>Dosya:</b> {(dosya_p or 'oyun_yama_v1.pak').replace(key+'_','')}</p><p><b>Kalan Hak:</b> <b>{kalan_p}</b></p><a href='/onizle?anahtar={key}' style='display:inline-block;background:#3b82f6;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;'>👁️ / 🎵 Dosyayı Aç</a> <a href='/indir?anahtar={key}' style='display:inline-block;background:#10b981;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;margin-left:8px;'>⬇️ İndir</a><br><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
        if p.path == "/":
            ip_k = max(0, 10 - ip_kullanim_bul(ip))
            uyari = f"<p style='color:#f87171;'>⚠️ IP ({ip}) 10 ücretsiz hak doldu! <b>100 TL = 30 Hak</b> veya <b>250 TL = 100 Hak</b> yükleyin.</p>" if ip_k == 0 else f"<p style='color:#34d399;'>🌐 IP: <code>{ip}</code> | Kalan Ücretsiz Anahtar: <b>{ip_k} / 10</b></p>"
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
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ IP ({ip}) 10 Ücretsiz Hak Doldu!</h3><p><b>100 TL = 30 Hak</b> veya <b>250 TL = 100 Hak</b> IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})</p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
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
            gereken_hak = max(1, math.ceil(len(icerik) / (50 * 1024 * 1024)))
            if kalan < gereken_hak:
                log_yaz(ip, "YUKLEME_ENGELLENDI", f"{anahtar} (Kota 0)")
                odeme_linki = "https://shopier.com"
                qr_resim_url = "data:image/png;base64,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"
                self.html(402, f"""<body style="font-family:sans-serif;background:#0f172a;color:white;padding:20px;max-width:480px;margin:auto;">
                <div style="background:#1e293b;padding:20px;border-radius:12px;border:1px solid #334155;">
                <h2 style="color:#f87171;margin-top:0;">⚠️ Yetersiz Hak (Kalan: {kalan} | Gereken: {gereken_hak})</h2>
                <p style="color:#cbd5e1;">Devam etmek için <b>100 TL = 30 Hak</b> veya <b>250 TL = 100 Hak</b> paketini seçin:</p>
                <button type="button" onclick="navigator.clipboard.writeText('{IBAN_NO}'); this.innerText='✅ IBAN Kopyalandı! Banka Uygulamanızdan Yapıştırın'; this.style.background='#10b981';" style="width:100%;border:none;cursor:pointer;display:block;text-align:center;background:#22c55e;color:#0f172a;font-weight:bold;padding:14px;border-radius:8px;margin:15px 0;font-size:15px;">⚡ IBAN Kopyala — Tüm Bankalar / FAST (100 TL / 250 TL)</button>
                <div style="text-align:center;background:#0f172a;padding:15px;border-radius:8px;margin-bottom:15px;">
                <p style="margin:0 0 10px 0;font-size:14px;color:#94a3b8;">📱 Banka Uygulamanızın İçindeki 'QR İşlemleri' Bölümünden Okutun (Normal kameradan değil):</p>
                <img src="{qr_resim_url}" alt="TR Karekod" style="width:210px;height:auto;border-radius:8px;background:white;padding:5px;">
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
            db.execute("UPDATE musteriler SET dosya_adi=?, kalan_hak=kalan_hak-?, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (g_ad, gereken_hak, anahtar)); db.commit()
            log_yaz(ip, "DOSYA_YUKLENDI", f"{anahtar} -> {os.path.basename(d_adi)} (Harcanan: {gereken_hak} Hak | Kalan: {kalan - gereken_hak})")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>🚀 Dosya Yüklendi! (Harcanan: {gereken_hak} Hak | Kalan Hak: {kalan - gereken_hak})</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;font-weight:bold;'>📂 Dosyayı Aç (Gör / Dinle / İndir) →</a></body>")

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), Otoyol).serve_forever()
