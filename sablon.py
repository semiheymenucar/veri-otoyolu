def ana_sayfa(uyari, banka, alici, iban):
    return f"""<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Veri Otoyolu</title>
    <style>body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#f8fafc;max-width:680px;margin:20px auto;padding:16px}}.kutu{{background:#1e293b;padding:20px;border-radius:12px;margin-bottom:16px;border:1px solid #334155}}input,button{{padding:12px;border-radius:8px;border:none;font-size:15px;margin-top:8px;width:100%;box-sizing:border-box}}input{{background:#0f172a;color:white;border:1px solid #475569}}button{{background:#3b82f6;color:white;font-weight:bold;cursor:pointer}}.yesil{{background:#10b981}}.mor{{background:#8b5cf6}}</style></head>
    <body><h1>🚀 Veri Otoyolu</h1>
    <div class='kutu'><h3>1. Ücretsiz Anahtar Al</h3>{uyari}<form method='POST' action='/kayit'><input name='ad' placeholder='Proje Adı' required><button>API Anahtarı Üret</button></form></div>
    <div class='kutu'><h3>2. Dosya Yükle (Her Yükleme = 1 Hak)</h3><form method='POST' action='/yukle' enctype='multipart/form-data'><input name='anahtar' placeholder='vo_...' required><input type='file' name='dosya' required><button class='yesil'>Dosyayı Otoyola Yükle</button></form></div>
    <div class='kutu'><h3>3. Dosyamı Gör / Dinle ve İndir</h3><form method='GET' action='/kontrol'><input name='anahtar' placeholder='vo_...' required><button class='mor'>📂 Dosyayı Aç</button></form></div>
    <div class='kutu'><h3>4. Otomatik Kota (100 TL = 100 Hak)</h3><p><b>{banka} - {alici}</b><br>IBAN: <code>{iban}</code><br><small>Açıklamaya sadece API anahtarınızı yazın. Ödeme algılandığında hesabınıza <b>100 Hak</b> otomatik tanımlanır.</small></p></div></body></html>"""

def dosya_rozeti(dosya_adi):
    ad = (dosya_adi or "").lower()
    if ad.endswith((".mp4", ".webm", ".mov", ".avi", ".mkv")): return "🎬 Video"
    if ad.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")): return "🖼️ Foto"
    if ad.endswith((".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac")): return "🎵 Müzik"
    if ad.endswith((".pak", ".zip", ".rar", ".exe", ".apk", ".iso", ".7z")): return "🎮 Oyun/Paket"
    if ad.endswith(".pdf"): return "📄 PDF"
    return "📦 Veri"

def medya_goruntule(key, dosya_adi, bilet=""):
    ad = dosya_adi.lower()
    src = f"/ham?bilet={bilet}"
    rozet = dosya_rozeti(dosya_adi)
    if ad.endswith((".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac")):
        icerik = f"<h3>{rozet} — İndirmeden Dinle</h3><p>{dosya_adi}</p><audio controls autoplay preload='metadata' style='width:100%;margin-top:15px;'><source src='{src}'></audio>"
    elif ad.endswith((".mp4", ".webm", ".mov", ".avi", ".mkv")):
        icerik = f"<h3>{rozet} — İndirmeden İzle</h3><p>{dosya_adi}</p><video controls autoplay playsinline preload='metadata' style='max-width:100%;max-height:70vh;border-radius:12px;background:#000;'><source src='{src}'></video>"
    elif ad.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        icerik = f"<h3>{rozet} — İndirmeden Bak</h3><p>{dosya_adi}</p><img src='{src}' style='max-width:100%;max-height:75vh;border-radius:12px;'>"
    elif ad.endswith(".pdf"):
        icerik = f"<h3>{rozet} — İndirmeden Oku</h3><iframe src='{src}' style='width:100%;height:75vh;border:none;background:white;border-radius:8px;'></iframe>"
    else:
        icerik = f"<h3>{rozet} — Dosya Bilgisi</h3><p><b>Dosya Adı:</b> {dosya_adi}</p><p style='color:#94a3b8;'>Bu dosya bir oyun/arşiv paketi olduğu için tarayıcıda oynatılamaz, türü yukarıda doğrulandı.</p>"
    return f"<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{dosya_adi}</title></head><body style='font-family:-apple-system,sans-serif;background:#0f172a;color:white;max-width:800px;margin:20px auto;padding:20px;text-align:center;'>{icerik}<br><br><a href='/indir?anahtar={key}' style='display:inline-block;background:#10b981;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;'>⬇️ İstersen İndir</a> <a href='/' style='display:inline-block;background:#334155;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;margin-left:8px;'>← Ana Sayfa</a></body></html>"

def kokpit(rows, logs, gizli):
    tr = "".join([f"<tr><td>{ad}</td><td><code style='word-break:break-all;'>{k}</code></td><td>{m_ip}</td><td><b>{kalan}</b></td><td>{gecis}</td><td style='white-space:nowrap;'><span style='background:#334155;padding:3px 7px;border-radius:6px;font-size:12px;margin-right:6px;'>{dosya_rozeti(dosya)}</span>{(dosya or 'oyun_yama_v1.pak').replace(k+'_','')}</td><td style='white-space:nowrap;'><a href='/onizle?anahtar={k}&admin={gizli}' target='_blank' style='background:#0284c7;color:white;padding:5px 10px;border-radius:6px;text-decoration:none;font-weight:bold;margin-right:6px;'>👁️ Bak</a><form method='GET' action='/yonetim' style='display:inline;'><input type='hidden' name='sifre' value='{gizli}'><input type='hidden' name='ekle' value='{k}'><input type='number' name='miktar' value='100' style='width:55px;padding:4px;background:#0f172a;color:white;border:1px solid #475569;border-radius:4px;'><button type='submit' style='background:#10b981;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;margin-left:4px;'>Ver</button></form></td></tr>" for k, ad, kalan, gecis, dosya, m_ip in rows])
    ltr = "".join([f"<tr><td style='white-space:nowrap;'>{z}</td><td><code>{l_ip}</code></td><td><b>{isl}</b></td><td style='word-break:break-word;'>{det}</td></tr>" for z, l_ip, isl, det in logs])
    return f"<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='refresh' content='15'><title>Kokpit - Canlı Takip</title></head><body style='font-family:-apple-system,sans-serif;background:#0f172a;color:white;padding:16px;margin:0;'><h2>🎛️ Veri Otoyolu Kokpit <span style='font-size:13px;color:#34d399;font-weight:normal;'>(● Canlı Güncelleniyor)</span></h2><div style='overflow-x:auto;border:1px solid #334155;border-radius:8px;'><table cellpadding='8' style='border-collapse:collapse;width:100%;min-width:720px;font-size:14px;'><tr style='background:#1e293b;'><th>Proje</th><th>Anahtar</th><th>IP</th><th>Kalan Hak</th><th>İşlem</th><th>Tür & Dosya</th><th>İşlem / Bak</th></tr>{tr}</table></div><h3>📜 Kalıcı İşlem Günlüğü (Son 200 Hareket)</h3><div style='overflow-x:auto;border:1px solid #334155;border-radius:8px;'><table cellpadding='8' style='border-collapse:collapse;width:100%;min-width:500px;font-size:14px;'><tr style='background:#1e293b;'><th>Zaman</th><th>IP Adresi</th><th>İşlem</th><th>Detay</th></tr>{ltr}</table></div><br><a href='/' style='color:#38bdf8;text-decoration:none;'>← Ana Sayfa</a></body></html>"
