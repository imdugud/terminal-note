**Q1: What are you really trying to do? What are the goals for my project?**

- Terminalden çıkmadan günlük işlerimi ve düşüncelerimi hızlıca kaydetmek.
- Task’leri en fazla 3 domain’e bölerek odaklı kalmak ve listenin şişmesini engellemek.
- Her sabah tek komutla (`today`) günümü görmek.
- Verilerimi düz metinde, okunabilir ve bana ait şekilde tutmak.
- Küçük, net kapsamlı ve adım adım büyüyebilen bir araç yapmak.

**Q2: What are the milestones of functionality?**

|Version|Core App Functionality|
|---|---|
|MVP|Domain `add`/`list` (max 3, ilk kurulumda tanımlama). Task `add` (tek domain zorunlu, opsiyonel tarih: `gün.ay.yıl`, `today`, `tomorrow`), `list today`, `done`. Journal `add` (saatle kaydedilir), `list today`. `today` görünümü (bugünkü + gecikmiş task’ler ve bugünkü journal). Düz metin kayıt, kalıcı ID’ler, `help`.|
|v1|Task `edit`, `remove`, `undone`. Task filtreleri (`week`, `overdue`, `all`, `-d domain`). Journal’ı tarihe göre listeleme. Domain `remove` (içinde task varsa taşıma kuralı). Tag’ler (`-t`) ve `tag list`. Tarih doğrulama.|
|v2|Calendar (`add`, `list week/month`, `edit`, `remove`, opsiyonel saat). Ideas (`add`, `list`, `remove`). Idea → task dönüştürme. `today` görünümüne calendar eklenmesi. Genel arama (`search`).|
|later|Kısa komut alias’ları, git ile yedekleme/senkronizasyon, tekrarlayan etkinlikler, dışa aktarma (Markdown), renkli çıktı.| 
