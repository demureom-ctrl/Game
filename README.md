# المسابقة الكبرى — تشغيل الخادم محلياً

تنفيذ سريع لتشغيل الخادم الذي يخدم `index.html` ويعرض واجهة اللعبة مع قاعدة بيانات SQLite محلية.

الخطوات:

1. إنشاء بيئة افتراضية (موصى به):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. تثبيت المتطلبات:

```powershell
pip install -r requirements.txt
```

3. تشغيل الخادم:

```powershell
python server.py
```

4. افتح المتصفح وتوجه إلى: http://127.0.0.1:5000

ملاحظات:
- يمكنك إضافة أسئلة جديدة عبر POST إلى `/api/questions` بصيغة JSON: `{ "category":"ثقافة عامة", "difficulty":2, "question":"...", "answer":"...", "options":["a","b","c","d"] }`.
- لإدارة الأسئلة عبر واجهة بسيطة افتح: `http://127.0.0.1:5000/admin`.
