# Asuli Review Bridge

Ali Elmalı'nın Asuli deneyiminden çıkarılmış, taşınabilir bir danışma projesi.
Gemini, Claude (Abdur) ve Kimi'den görüş alınabilir; yanıt sorusuna bağlanır,
operatörün gerekçeli kararı ayrı kaydedilir. Model cevabı komut çalıştırmaz.

## İlk deneme: anahtarsız, ücretsiz, çevrimdışı

Python 3.11 veya üzeri gerekir. Kaynak dizininden:

```bash
export PYTHONPATH="$PWD/src"
python3 examples/offline_demo.py
python3 -m unittest discover -s tests -v
```

Örnek, geçici veritabanında sentetik bir soruyu işler: Bir belgenin elle
oluşturulup okunması, zamanlanmış otomatik teslimin çalıştığını kanıtlar mı?
MOCK cevabı açıkça örnek olarak işaretlenir; gerçek model değerlendirmesi değildir.

## Neler var?

- Birbirine bağlı soru ve yanıt kayıtları.
- Model görüşünden ayrı ACCEPT / REJECT / NEEDS_EVIDENCE kararı.
- Eşzamanlı işçilerin aynı soruyu tekrar almamasını sağlayan SQLite rezervasyonu.
- İnsan tarafından okunabilir Markdown çıktısı.
- İsteğe bağlı üç API adaptörü ve çevrimdışı davranış testleri.

Üretimdeki Asuli scriptleri doğrudan kopyalanmadı. Orijinal sistemin ortak MD
posta kutusu yerine bu sürümde SQLite esas kayıt, Markdown ise görünüm olarak
kullanılıyor. Bu yeni tasarımı makalede anlatılan eski canlı testlere mal etmiyoruz.

## Gerçek modele bağlanma

`.env.example` yalnız değişken adlarını gösterir; otomatik yüklenmez. Seçilen
sağlayıcının anahtarını ve erişimin olan model adını ortam değişkenlerinde
tanımladıktan sonra `--allow-network` açıkça verilmelidir. İngilizce
[README](README.md) komutları ve sağlayıcı eşlemelerini gösterir.

Bu pakette ücretli API testi yapılmadı. Adaptörler sahte HTTP yanıtlarıyla
kontrol edildi. Token sınırı parasal harcama garantisi değildir. Anahtar veya
özel içerik gönderilmeden önce sağlayıcı erişimi ve fiyatı ayrıca kontrol edilir.

## Kesinti olursa

Çağrıdan önce kayıt INFLIGHT yapılır. Süreç ölürse kayıt orada kalır; hata veya
yarım cevapta HOLD olur. Otomatik yeniden deneme yoktur: sağlayıcı isteği
almış ve ücretlendirmiş olabilir. Tekrar göndermeden önce operatör mutabakatı
gerekir. Dış API için exactly-once garantisi verilmez.

## Makale ile ilişkisi

[Makale eşlemesi](docs/article-companion.md), hangi fikrin hangi modülde
gösterildiğini açıklar. Gerçek GitHub deposu yayımlandıktan sonra makaledeki
bağlantılar doğrulanmış commit veya tag'e sabitlenmelidir.

Notion/Telegram entegrasyonu, zamanlayıcı, sistem yönetimi, otomatik onay ve
nicel doğruluk benchmark'ı bu ilk sürümün kapsamında değildir. Gerçek çalışma
kayıtları, hesap bilgileri ve özel yollar pakete alınmadı.

Lisans seçimi bekleniyor; bu hazırlık paketi açık kaynak lisansı vermez.
