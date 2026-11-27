import os, time, json, hmac, secrets, sqlite3, urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import drive_motor
from sablon import ana_sayfa, kokpit, medya_goruntule, boyut_yaz

os.makedirs("dosyalar", exist_ok=True)
IBAN_NO = "TR43 0004 6001 4788 8000 3997 07"
ALICI_AD = "Akbank - Semih Eymen Uçar"
ADMIN_SIFRE = os.environ.get("ADMIN_SIFRE", "otoyol_gizli_9988")
QR_B64 = "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"

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

import urllib.request
def ai_odeme_isle(metin, ip):
    key_ai = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key_ai: return False, "API yok"
    prompt = "Asagidaki banka bildirim metnini analiz et. Hesaba gelen TL tutarini (sadece tam sayi) ve aciklamadaki vo_ ile baslayan anahtari cikar. Sadece JSON dondur: {\"gelen\": true/false, \"tutar\": 0, \"anahtar\": \"vo_...\"}. Metin: " + metin[:1500]
    req = urllib.request.Request(f"https://googleapis.com{key_ai}", data=json.dumps({"contents":[{"parts":[{"text":prompt}]}]}).encode(), headers={"Content-Type":"application/json"})
    res = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    txt = res["candidates"][0]["content"]["parts"][0]["text"]
    j = json.loads(txt[txt.find("{"):txt.rfind("}")+1])
    if not j.get("gelen"): return False, "Gelen degil"
    t, k = int(j.get("tutar", 0)), str(j.get("anahtar", "")).strip()
    p_map = {39:(1,7), 89:(1,30), 399:(1,365), 129:(10,7), 299:(10,30), 1490:(10,365), 490:(100,7), 990:(100,30), 4490:(100,365)}
    if t not in p_map: return False, f"Tutar eslesmedi:{t}"
    r = db.execute("SELECT bitis_ts FROM musteriler WHERE anahtar=?", (k,)).fetchone()
    if not r: return False, f"Anahtar yok:{k}"
    gb, gun = p_map[t]
    y_bit = max(int(time.time()), int(list(r).pop(0) or 0)) + (gun * 86400)
    db.execute("UPDATE musteriler SET kota_byte=?, bitis_ts=? WHERE anahtar=?", (gb*(1024**3), y_bit, k)); db.commit()
    log_yaz(ip, "AI_OTOMATIK_ONAY", f"{k} -> {t} TL = {gb} GB / {gun} Gun")
    return True, f"{k} -> {gb} GB / {gun} Gun"

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
        if p.path == "/ai_odeme_onay":
            if not hmac.compare_digest(self.headers.get("X-Odeme-Kod", ""), os.environ.get("ODEME_GIZLI_KOD", "vo_ai_kilit_2026")):
                self.html(403, "Yetkisiz"); return
            govde = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8", errors="ignore")
            ok, msg = ai_odeme_isle(govde, ip)
            self.html(200 if ok else 400, msg); return
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
        if p.path == "/yedek_yukle":
            anahtar = self.headers.get("X-Anahtar", "").strip()
            d_adi = os.path.basename(urllib.parse.unquote(self.headers.get("X-Dosya-Adi", "dosya.bin")))
            t_boyut = int(self.headers.get("X-Toplam-Boyut", 0))
            r = db.execute("SELECT kota_byte, bitis_ts FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            if not r or int(r or 0) <= int(time.time()): self.html(402, "<h3>🔒 Süre dolmuş veya geçersiz.</h3>"); return
            if t_boyut > int(r or 0): self.html(402, "<h3>⚠️ Kasa limiti aşıldı!</h3>"); return
            veri = self.rfile.read(t_boyut)
            g_ad = f"{anahtar}_{d_adi}"
            open(os.path.join("dosyalar", g_ad), "wb").write(veri)
            db.execute("UPDATE musteriler SET dosya_adi=?, kullanilan_byte=?, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (g_ad, len(veri), anahtar)); db.commit()
            log_yaz(ip, "KASA_YUKLENDI", f"{anahtar} -> {d_adi} ({boyut_yaz(len(veri))})")
            self.html(200, f"<body style='background:#0f172a;color:white;padding:30px;'><h2>🛡️ Kasaya Mühürlendi! ({boyut_yaz(len(veri))})</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;'>📂 Kasayı Aç →</a></body>"); return
        if p.path == "/oturum_ac":
            anahtar = self.headers.get("X-Anahtar", "").strip()
            d_adi = os.path.basename(urllib.parse.unquote(self.headers.get("X-Dosya-Adi", "dosya.bin")))
            t_boyut = int(self.headers.get("X-Toplam-Boyut", 0))
            r = db.execute("SELECT kota_byte, bitis_ts FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            if not r: self.html(403, "<h3>❌ Geçersiz Anahtar.</h3>"); return
            kb, bts = r
            if int(bts or 0) <= int(time.time()): self.html(402, "<h3>🔒 Süre dolmuş.</h3>"); return
            if t_boyut > int(kb or 0): self.html(402, "<h3>⚠️ Kasa limiti aşıldı!</h3>"); return
            if t_boyut > drive_motor.havuz_bos_alan(): self.html(507, "<h3>⚠️ Bulut havuzu dolu.</h3>"); return
            u = drive_motor.oturum_ac(f"{anahtar}_{d_adi}", t_boyut, self.headers.get("Origin", ""))
            if not u: self.html(500, "<h3>⚠️ Tünel açılamadı.</h3>"); return
            v = json.dumps({"upload_url": u}).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(v))); self.end_headers(); self.wfile.write(v); return
        if p.path == "/yukleme_tamamla":
            anahtar = self.headers.get("X-Anahtar", "").strip()
            d_adi = os.path.basename(urllib.parse.unquote(self.headers.get("X-Dosya-Adi", "dosya.bin")))
            fid = self.headers.get("X-File-Id", "").strip()
            r = db.execute("SELECT kota_byte, dosya_adi FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            gb = drive_motor.dosya_dogrula(fid) if fid else None
            if not r or gb is None: self.html(400, "<h3>❌ Doğrulama başarısız.</h3>"); return
            kb, eski_d = r
            if gb > int(kb or 0): drive_motor.dosya_sil(fid); self.html(402, "<h3>⚠️ Limit aşıldı.</h3>"); return
            if eski_d and eski_d.startswith("gdrive:"): drive_motor.dosya_sil(eski_d.split(":", 2).pop(1))
            db.execute("UPDATE musteriler SET dosya_adi=?, kullanilan_byte=?, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (f"gdrive:{fid}:{d_adi}", gb, anahtar)); db.commit()
            log_yaz(ip, "KASA_YUKLENDI", f"{anahtar} -> {d_adi}")
            self.html(200, f"<body style='background:#0f172a;color:white;padding:30px;'><h2>🛡️ Kasaya Mühürlendi!</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;'>📂 Aç →</a></body>"); return
        self.html(404, "<h3>404</h3>")

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), Otoyol).serve_forever()
