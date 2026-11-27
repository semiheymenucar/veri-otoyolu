import os, time, json, hmac, secrets, sqlite3, urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import drive_motor
from sablon import ana_sayfa, kokpit, medya_goruntule, boyut_yaz

os.makedirs("dosyalar", exist_ok=True)
IBAN_NO = "TR43 0004 6001 4788 8000 3997 07"
ALICI_AD = "Akbank - Semih Eymen Uçar"
ADMIN_SIFRE = os.environ.get("ADMIN_SIFRE", "otoyol_gizli_9988")
QR_B64 = getattr(__import__("motor_v2"), "QR_B64", "") if os.path.exists("motor_v2.py") else ""

db = sqlite3.connect("otoyol.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS musteriler (anahtar TEXT PRIMARY KEY, ad TEXT, kalan_hak INTEGER DEFAULT 0, toplam_gecis INTEGER DEFAULT 0, dosya_adi TEXT DEFAULT '', ip TEXT DEFAULT '', kota_byte INTEGER DEFAULT 52428800, kullanilan_byte INTEGER DEFAULT 0, bitis_ts INTEGER DEFAULT 0)")
db.execute("CREATE TABLE IF NOT EXISTS islem_loglari (id INTEGER PRIMARY KEY AUTOINCREMENT, zaman TEXT, ip TEXT, islem TEXT, detay TEXT)")
cols = {r.pop(1) for r in map(list, db.execute("PRAGMA table_info(musteriler)").fetchall())}
for c_name in ("kota_byte", "kullanilan_byte", "bitis_ts"):
    if c_name not in cols:
        db.execute(f"ALTER TABLE musteriler ADD COLUMN {c_name} INTEGER DEFAULT 0")
db.commit()

RATE_MAP, BILETLER = {}, {}

def ip_al(h):
    f = h.headers.get("X-Forwarded-For", "")
    if f:
        return f.split(",").pop(0).strip()
    addr = list(h.client_address)
    return str(addr.pop(0))

def rate_izin(ip):
    simdi = time.time()
    k = [t for t in RATE_MAP.get(ip, []) if simdi - t < 60]
    if len(k) >= 45: return False
    k.append(simdi); RATE_MAP[ip] = k; return True

def log_yaz(ip, islem, detay):
    db.execute("INSERT INTO islem_loglari (zaman, ip, islem, detay) VALUES (?,?,?,?)", (datetime.now().strftime("%d.%m.%Y %H:%M:%S"), ip, islem, detay)); db.commit()

class Otoyol(BaseHTTPRequestHandler):
    def log_message(self, *a): return
    def html(self, kod, icerik):
        v = icerik.encode("utf-8")
        self.send_response(kod); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(v))); self.send_header("X-Frame-Options", "DENY"); self.end_headers(); self.wfile.write(v)

    def ham_veri_gonder(self, key, indir=False):
        r = db.execute("SELECT dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
        d = list(r).pop(0) if r else ""
        if not d: self.html(404, "<h3>❌ Kasada dosya yok.</h3>"); return
        if d.startswith("gdrive:"):
            _, fid, gad = d.split(":", 2)
            self.send_response(200); self.send_header("Content-Type", "application/octet-stream")
            if indir: self.send_header("Content-Disposition", f'attachment; filename="{gad}"')
            self.end_headers(); drive_motor.drive_indir_akisi(fid, self.wfile); return
        yol = os.path.join("dosyalar", d)
        if not os.path.exists(yol): self.html(404, "<h3>❌ Dosya yok.</h3>"); return
        v = open(yol, "rb").read()
        self.send_response(200); self.send_header("Content-Type", "application/octet-stream"); self.send_header("Content-Length", str(len(v)))
        if indir: self.send_header("Content-Disposition", f'attachment; filename="{d.replace(key+"_","")}"')
        self.end_headers(); self.wfile.write(v)

    def do_GET(self):
        ip = ip_al(self)
        if not rate_izin(ip): self.html(429, "<h3>⚠️ Çok fazla istek.</h3>"); return
        p = urllib.parse.urlparse(self.path); qs = urllib.parse.parse_qs(p.query)
        key = qs.get("anahtar", [""]).pop(0).strip()
        if p.path == "/":
            cnt = int(list(db.execute("SELECT COUNT(*) FROM musteriler WHERE ip=?", (ip,)).fetchone()).pop(0))
            ip_k = max(0, 5 - cnt)
            u = "<p style='color:#f87171;'>⚠️ Ücretsiz 5 deneme hakkı doldu.</p>" if ip_k == 0 else f"<p style='color:#34d399;'>🌐 IP: <code>{ip}</code> | Kalan Ücretsiz Kasa: <b>{ip_k} / 5</b></p>"
            self.html(200, ana_sayfa(u, IBAN_NO, ALICI_AD, QR_B64)); return
        if p.path == "/kontrol":
            r = db.execute("SELECT ad, kota_byte, kullanilan_byte, bitis_ts, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not r: self.html(404, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Anahtar Bulunamadı</h3><a href='/' style='color:#38bdf8;'>← Geri</a></body>"); return
            ad_p, kb, ub, bts, dp = r; aktif = int(bts or 0) > int(time.time()); gun = max(0, int((int(bts or 0) - int(time.time())) / 86400))
            kad = (dp or "Dosya yüklenmedi").split(":").pop(-1).replace(key + "_", "")
            btn = f"<a href='/onizle?anahtar={key}' style='background:#3b82f6;color:white;padding:10px 16px;border-radius:8px;text-decoration:none;'>👁️ Kasayı Aç</a> <a href='/indir?anahtar={key}' style='background:#10b981;color:white;padding:10px 16px;border-radius:8px;text-decoration:none;margin-left:8px;'>⬇️ İndir</a>" if aktif else "<p style='color:#fbbf24;'>🔒 Süre doldu (Dosyalar koruma kilidinde).</p>"
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>🛡️ Kasa Durumu</h2><p><b>Proje:</b> {ad_p} | <b>Süre:</b> {gun} gün kaldı</p><p><b>Alan:</b> {boyut_yaz(ub)} / {boyut_yaz(kb)}</p><p><b>Dosya:</b> {kad}</p>{btn}<br><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
        if p.path == "/onizle":
            adm = qs.get("admin", [""]).pop(0) == ADMIN_SIFRE
            r = db.execute("SELECT dosya_adi, bitis_ts FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not r: self.html(404, "<h3>❌ Dosya yok.</h3>"); return
            d_adi, bts = r
            if not d_adi: self.html(404, "<h3>❌ Dosya yok.</h3>"); return
            if not adm and int(bts or 0) <= int(time.time()): self.html(402, "<h3>🔒 Süre dolmuş.</h3>"); return
            b = secrets.token_urlsafe(24); BILETLER[b] = (key, time.time() + 600); kad = d_adi.split(":").pop(-1).replace(key + "_", "")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>📂 {kad}</h3>{medya_goruntule(key, kad, b)}<br><br><a href='/indir?anahtar={key}' style='background:#10b981;color:white;padding:10px 16px;border-radius:8px;text-decoration:none;'>⬇️ İndir</a></body>"); return
        if p.path == "/ham":
            kayit = BILETLER.get(qs.get("bilet", [""]).pop(0))
            if not kayit: self.html(403, "<h3>❌ Bilet doldu.</h3>"); return
            b_key, b_exp = kayit
            if b_exp < time.time(): self.html(403, "<h3>❌ Bilet doldu.</h3>"); return
            self.ham_veri_gonder(b_key, False); return
        if p.path == "/indir":
            r = db.execute("SELECT bitis_ts FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            bts = list(r).pop(0) if r else 0
            if int(bts or 0) <= int(time.time()): self.html(402, "<h3>🔒 Kasa süresi dolmuş veya geçersiz.</h3>"); return
            db.execute("UPDATE musteriler SET toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (key,)); db.commit()
            log_yaz(ip, "KASA_INDIRILDI", key); self.ham_veri_gonder(key, True); return
        if p.path == "/yonetim":
            if not hmac.compare_digest(qs.get("sifre", [""]).pop(0), ADMIN_SIFRE): self.html(403, "<h3>❌ Yetkisiz.</h3>"); return
            ekle = qs.get("ekle", [""]).pop(0).strip()
            if ekle:
                gb, gun = int(qs.get("gb", ["1"]).pop(0)), int(qs.get("gun", ["30"]).pop(0))
                r = db.execute("SELECT bitis_ts FROM musteriler WHERE anahtar=?", (ekle,)).fetchone()
                if r:
                    eski_b = list(r).pop(0)
                    y_bit = max(int(time.time()), int(eski_b or 0)) + (gun * 86400)
                    db.execute("UPDATE musteriler SET kota_byte=?, bitis_ts=? WHERE anahtar=?", (gb * (1024**3), y_bit, ekle)); db.commit()
                    log_yaz(ip, "PAKET_TANIMLANDI", f"{ekle} -> {gb} GB / {gun} Gün")
            rows = db.execute("SELECT anahtar, ad, kota_byte, kullanilan_byte, bitis_ts, dosya_adi, ip FROM musteriler ORDER BY rowid DESC").fetchall()
            logs = db.execute("SELECT zaman, ip, islem, detay FROM islem_loglari ORDER BY id DESC LIMIT 200").fetchall()
            self.html(200, kokpit(rows, logs, ADMIN_SIFRE)); return
        self.html(404, "<h3>404</h3>")

    def do_POST(self):
        ip = ip_al(self)
        if not rate_izin(ip): self.html(429, "<h3>⚠️ Çok fazla istek.</h3>"); return
        p = urllib.parse.urlparse(self.path)
        if p.path == "/anahtar_olustur":
            form = urllib.parse.parse_qs(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8", errors="ignore"))
            proje = form.get("proje_adi", ["Proje"]).pop(0)[:40]
            mb = int(form.get("deneme_mb", ["50"]).pop(0)); mb = mb if mb in (50, 100) else 50
            cnt = int(list(db.execute("SELECT COUNT(*) FROM musteriler WHERE ip=?", (ip,)).fetchone()).pop(0))
            if cnt >= 5:
                self.html(429, "<h3>⚠️ 5 deneme hakkı doldu.</h3>"); return
            anahtar = "vo_" + secrets.token_hex(12)
            db.execute("INSERT INTO musteriler (anahtar, ad, ip, kota_byte, kullanilan_byte, bitis_ts) VALUES (?,?,?,?,0,?)", (anahtar, proje, ip, mb * 1024 * 1024, int(time.time()) + 7 * 86400)); db.commit()
            log_yaz(ip, "DENEME_KASASI", f"{anahtar} ({mb} MB)")
            self.html(200, f"<body style='background:#0f172a;color:white;padding:30px;'><h2>🔑 {mb} MB Kasanız Hazır!</h2><p><code>{anahtar}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
        if p.path == "/oturum_ac":
            anahtar = self.headers.get("X-Anahtar", "").strip()
            d_adi = os.path.basename(urllib.parse.unquote(self.headers.get("X-Dosya-Adi", "dosya.bin")))
