# 🆘 دليل حل المشاكل والأسئلة الشائعة

---

## 🐛 المشاكل الشائعة وحلولها

### المشكلة 1: "No module named 'flask'"

**الرسالة:**
```
ModuleNotFoundError: No module named 'flask'
```

**الأسباب المحتملة:**
- لم تثبت المكتبات
- استخدام Python الخطأ
- Virtual environment غير مفعّل

**الحلول:**

**الحل 1 (الأسهل):**
```bash
pip install -r requirements.txt
```

**الحل 2 (إذا لم ينجح الأول):**
```bash
pip install Flask==2.3.3
pip install Werkzeug==2.3.7
pip install gunicorn==21.2.0
```

**الحل 3 (Windows):**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**الحل 4 (Mac/Linux):**
```bash
python3 -m pip install -r requirements.txt
```

---

### المشكلة 2: "Address already in use"

**الرسالة:**
```
OSError: [Errno 48] Address already in use
```

**المعنى:**
Port 5000 مستخدم من تطبيق آخر

**الحلول:**

**الحل 1: تغيير الـ Port**

في `app.py`، جد:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

غيّر 5000 إلى رقم آخر:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # أو 3000, 8080, 9000
```

ثم شغّل المتصفح على:
```
http://localhost:8000
```

**الحل 2: إغلاق التطبيق السابق**

**على Windows:**
```bash
# ابحث عن العملية
netstat -ano | findstr :5000

# اغلق العملية (مثال)
taskkill /PID 1234 /F
```

**على Mac/Linux:**
```bash
# ابحث عن العملية
lsof -i :5000

# اغلق العملية
kill -9 1234
```

---

### المشكلة 3: "No such table: products"

**الرسالة:**
```
sqlite3.OperationalError: no such table: products
```

**السبب:**
قاعدة البيانات معطوبة أو لم تُنشأ

**الحل:**
```bash
# احذف ملف قاعدة البيانات
rm clothing_store.db

# أو على Windows:
del clothing_store.db

# ثم شغّل التطبيق مرة أخرى
python app.py
```

البرنامج سينشئ قاعدة البيانات تلقائياً!

---

### المشكلة 4: كلمة المرور الافتراضية لا تعمل

**السبب:**
قد كنت غيّرتها سابقاً ونسيتها

**الحل 1: إعادة تعيين**
```bash
# احذف قاعدة البيانات
rm clothing_store.db

# شغّل التطبيق (الكلمة الافتراضية ستعود)
python app.py

# كلمة المرور: admin123
```

**الحل 2: غيّرها برمجياً**

في `app.py`، جد:
```python
admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
```

غيّر `admin123` لكلمتك الجديدة، ثم احذف الـ DB وشغّل التطبيق مرة أخرى

---

### المشكلة 5: الصفحة تحمّل ببطء

**الأسباب:**
- الجهاز بطيء
- اتصال ضعيف
- عدد المنتجات كثير جداً

**الحلول:**

**الحل 1: تقليل البيانات**
```python
# في index route، غيّر من:
c.execute('SELECT * FROM products WHERE stock > 0')

# إلى:
c.execute('SELECT * FROM products WHERE stock > 0 LIMIT 50')
```

**الحل 2: تحسين قاعدة البيانات**
```python
# أضف index على جدول المنتجات:
c.execute('CREATE INDEX idx_category ON products(category)')
c.execute('CREATE INDEX idx_name ON products(name)')
```

**الحل 3: تقليل الصور**
إذا كنت تستخدم صور، استخدم صور مضغوطة

---

### المشكلة 6: الموقع لا يعمل بعد النشر

**على Render:**

**الحل 1: اعرض السجلات**
في Render Dashboard:
- اذهب إلى "Logs"
- اقرأ الأخطاء بعناية

**الحل 2: تحقق من Requirements**
تأكد من وجود `gunicorn` في `requirements.txt`:
```
Flask==2.3.3
gunicorn==21.2.0
```

**الحل 3: تحقق من Start Command**
يجب أن يكون:
```
gunicorn app:app
```

**الحل 4: أعد النشر**
```bash
git add .
git commit -m "Fix"
git push origin main
```

---

### المشكلة 7: قاعدة البيانات تُحذف بعد النشر

**السبب:**
Render حذف البيانات عند إعادة التشغيل

**الحل الأفضل: استخدام PostgreSQL**

1. في Render، أنشئ PostgreSQL Database
2. نسخ الـ DATABASE_URL
3. عدّل `app.py`:

```python
import os
import psycopg2
from psycopg2 import sql

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn
```

---

### المشكلة 8: الملفات المرفوعة لا تُحفظ

**السبب:**
Render لا يحفظ الملفات على القرص الصلب

**الحل:**
استخدم AWS S3 أو Cloudinary للملفات

```python
from cloudinary import uploader

def upload_image(file):
    result = uploader.upload(file)
    return result['secure_url']
```

---

## ❓ الأسئلة الشائعة (FAQ)

### س1: كيف أضيف منتج جديد؟

**الخطوات:**
1. ادخل لوحة التحكم: `/admin`
2. اضغط "إدارة المنتجات"
3. اضغط "+ إضافة منتج جديد"
4. ملأ البيانات بعناية
5. اضغط "حفظ المنتج"

**نصيحة:** استخدم أوصاف واضحة وجذابة لزيادة المبيعات

---

### س2: كيف أحذف منتج؟

**الطريقة:**
1. في لوحة التحكم → إدارة المنتجات
2. جد المنتج في الجدول
3. اضغط "حذف"
4. تأكيد الحذف

**تحذير:** الحذف نهائي ولا يمكن التراجع!

---

### س3: كيف أغيّر السعر؟

**الحالية:** لا توجد ميزة تعديل مباشرة

**الحل:**
1. احذف المنتج
2. أضفه مرة أخرى بالسعر الجديد

**الحل الأفضل:** أطلب تطويراً لإضافة ميزة التعديل

---

### س4: كم منتج يمكن أن أضيف؟

**الإجابة:** لا توجد حد نظري

- SQLite: يدعم ملايين الصفوف
- الموقع الخاص بك: بدون حد

**نصيحة:** ابدأ بـ 20-30 منتج وزيادتهم مع الوقت

---

### س5: هل يدعم الدفع الإلكتروني؟

**الآن:** لا

**الخيارات:**
1. إضافة Stripe (راجع ADVANCED_FEATURES.md)
2. إضافة Paymob
3. شغّل كمتجر بدون دفع أونلاين (كاش عند الاستقبال)

---

### س6: كيف أزيد عدد الفئات؟

**الطريقة:**
1. في لوحة التحكم → إدارة الفئات
2. اكتب اسم الفئة
3. اضغط "إضافة"

**الفئات الموجودة:**
- 👔 رجالي
- 👗 نسائي
- 👶 أطفال
- 👟 أحذية
- ⌚ إكسسوارات
- ⛹️ ملابس رياضية

---

### س7: كيف أغيّر اسم المتجر؟

**الطريقة:**

في `app.py`، ابحث عن:
```python
<a href="/" class="logo">VESTIQUE</a>
```

غيّر `VESTIQUE` لاسم متجرك:
```python
<a href="/" class="logo">MY_STORE</a>
```

ثم أعد تشغيل التطبيق

---

### س8: كيف أغيّر الألوان؟

**الطريقة:**

في `app.py`، ابحث عن:
```css
:root {
    --primary: #1a1a2e;
    --accent: #e94560;
    --light: #f8f9fa;
}
```

استخدم hex colors من: https://htmlcolorcodes.com

مثال - ألوان زرقاء:
```css
--primary: #003d7a;      /* أزرق داكن */
--accent: #0066cc;       /* أزرق فاتح */
--light: #f0f8ff;        /* أزرق جداً فاتح */
```

---

### س9: هل يعمل بدون إنترنت؟

**الإجابة:** نعم، يعمل محلياً بدون إنترنت

لكن **لا يمكن نشره على الإنترنت بدون إنترنت**

---

### س10: كيف أعمل backup لقاعدة البيانات؟

**الطريقة:**
```bash
# انسخ ملف قاعدة البيانات
cp clothing_store.db clothing_store.db.backup

# أو على Windows:
copy clothing_store.db clothing_store.db.backup
```

**التوصية:** احفظ نسخة احتياطية أسبوعياً

---

### س11: هل يدعم اللغة الإنجليزية؟

**الآن:** لا، المتجر عربي فقط

**لإضافة دعم انجليزي:** 
تحتاج تطوير لتبديل اللغات (i18n)

---

### س12: كيف أزيد أمان الموقع؟

**الإجراءات:**

1. **غيّر كلمة المرور الافتراضية:**
```python
admin_password = hashlib.sha256('PASSWORD_STRONG_VERY_LONG'.encode()).hexdigest()
```

2. **استخدم HTTPS:**
تلقائي على Render/Heroku

3. **لا تشارك كلمة المرور:**
احفظها في مكان آمن

4. **نسخ احتياطية:**
كل أسبوع

5. **محدث المتطلبات:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

---

### س13: كيف أُقيّم أداء الموقع؟

**الأدوات:**

1. **Render Analytics:**
   - في Render Dashboard
   - اعرض الـ Metrics

2. **Google Analytics:**
   - أضف tracking code
   - راقب الزيارات

3. **Lighthouse:**
   - في Chrome DevTools
   - اختبر الأداء

---

### س14: كيف أزيد سرعة الموقع؟

**الطرق:**

1. **استخدم CDN:**
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/...">
```

2. **ضغط الصور:**
استخدم TinyPNG

3. **تقليل البيانات:**
عرض 50 منتج بدل الكل

4. **تخزين مؤقت (Cache):**
```python
@app.after_request
def add_cache_headers(response):
    response.cache_control.max_age = 3600
    return response
```

---

### س15: هل يدعم الشحن والتوصيل؟

**الآن:** لا

**لإضافتها:**
1. أضف جدول carriers
2. اربط Aramex أو SMSA
3. احسب تكلفة الشحن

---

## 🔧 نصائح عامة

### للحصول على أفضل الأداء:

```
✅ أعد تشغيل التطبيق مرة يومياً
✅ احفظ نسخة احتياطية أسبوعياً
✅ حدّث الأسعار بناءً على الطلب
✅ أزل المنتجات المنتهية
✅ أضف منتجات جديدة بانتظام
✅ راقب الطلبات الجديدة
```

### للأمان:

```
✅ غيّر كلمة المرور كل شهر
✅ استخدم كلمة قوية (أحرف + أرقام + رموز)
✅ لا تشارك البيانات الحساسة
✅ احفظ نسخة احتياطية من كل شيء
✅ استخدم VPN إذا كنت على WiFi عام
```

---

## 📞 متى تطلب المساعدة؟

**اطلب مساعدة إذا:**
- واجهت خطأ لم تفهمه
- أردت إضافة ميزة معقدة
- كان الموقع بطيء جداً
- فقدت البيانات

**قدم معك:**
- رسالة الخطأ كاملة
- خطوات إعادة المشكلة
- نسخة الـ Python والـ Flask
- لقطة شاشة (Screenshot)

---

**الآن أنت مستعد للتعامل مع أي مشكلة! 💪**

استمتع بمتجرك الإلكتروني! 🚀
