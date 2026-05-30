# 🎯 دليل الميزات المتقدمة والتخصيص

## الميزات المتقدمة في المتجر

### 1. نظام البحث والتصفية المتقدم

**البحث الفوري:**
```
اكتب في Search Box أي كلمة
يبحث تلقائياً في الاسم والوصف
```

**التصفية حسب الفئة:**
```
6 فئات متاحة:
👔 رجالي
👗 نسائي  
👶 أطفال
👟 أحذية
⌚ إكسسوارات
⛹️ ملابس رياضية
```

### 2. إدارة المخزون

كل منتج يحتفظ بـ:
- الكمية المتاحة
- المقاسات المتعددة
- الألوان المتنوعة
- تفاصيل المادة

### 3. نظام التقييمات

المنتجات تأتي مع:
- تقييم من 5 نجوم
- عدد التقييمات
- عرض بصري للتقييم

### 4. نظام الطلبات

تتبع كامل:
- معلومات العميل
- تفاصيل الطلب
- الحالة (قيد المعالجة/مُسلَّم)
- تاريخ الطلب

---

## 🎨 التخصيص المتقدم

### تغيير الألوان بالكامل

في `app.py`، ابحث عن:
```css
:root {
    --primary: #1a1a2e;    /* اللون الأساسي */
    --accent: #e94560;     /* لون التركيز */
    --light: #f8f9fa;      /* اللون الفاتح */
    --text: #333;          /* لون النص */
    --border: #e0e0e0;     /* لون الحدود */
}
```

**أمثلة ألوان:**
```
أزرق احترافي:
--primary: #003d7a;
--accent: #0066cc;

أخضر عصري:
--primary: #1b5e20;
--accent: #4caf50;

برتقالي نابض:
--primary: #e65100;
--accent: #ff6f00;

بنفسجي فاخر:
--primary: #4a148c;
--accent: #9c27b0;
```

### تغيير الخطوط

الموقع يستخدم:
```css
font-family: 'Cairo', 'Segoe UI', sans-serif;
```

للتغيير، أضف في CSS:
```html
<link href="https://fonts.googleapis.com/css2?family=YOUR_FONT&display=swap" rel="stylesheet">
```

### تغيير الأيقونات

المنتجات تستخدم emoji. غيّرها في:
```python
['👕', '👗', '👶', '👟', '⌚', '⛹️'][hash(p['name']) % 6]
```

إلى أي emoji تريد!

---

## 🔐 التخصيص الأمني

### تغيير بيانات الأدمن

في `init_db()` function:
```python
# تغيير اسم المستخدم
c.execute('INSERT INTO admins (username, password) VALUES (?, ?)', 
          ('your_username', admin_password))

# تغيير كلمة المرور
admin_password = hashlib.sha256('your_strong_password'.encode()).hexdigest()
```

### إضافة عدة مستخدمين أدمن

```python
admins = [
    ('admin', hashlib.sha256('password1'.encode()).hexdigest()),
    ('manager', hashlib.sha256('password2'.encode()).hexdigest()),
    ('editor', hashlib.sha256('password3'.encode()).hexdigest()),
]
for username, password in admins:
    c.execute('INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)', 
              (username, password))
```

---

## 📊 إضافة ميزات جديدة

### 1. إضافة حقل الصورة

عدّل جدول المنتجات:
```python
# في create table:
image_url TEXT

# في HTML:
<input type="url" name="image_url" placeholder="رابط صورة المنتج">

# في العرض:
<img src="{p['image_url']}" alt="{p['name']}" style="width: 100%; height: 280px; object-fit: cover;">
```

### 2. نظام الخصومات

أضف حقل في جدول المنتجات:
```python
discount INTEGER DEFAULT 0  # النسبة المئوية

# في العرض:
original_price = p['price']
discount_price = original_price * (1 - p['discount'] / 100)
<span style="text-decoration: line-through;">{original_price}</span>
<strong>{discount_price}</strong>
```

### 3. نظام التطبيق الفوري (Favorites)

أضف جدول جديد:
```python
c.execute('''
    CREATE TABLE favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_ip TEXT,
        product_id INTEGER,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
''')
```

### 4. نظام التعليقات والتقييمات

```python
c.execute('''
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        rating INTEGER,
        comment TEXT,
        customer_name TEXT,
        review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
''')
```

---

## 🛒 إضافة سلة التسوق

### خطوة 1: جدول جديد
```python
c.execute('''
    CREATE TABLE cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        product_id INTEGER,
        quantity INTEGER,
        size TEXT,
        color TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
''')
```

### خطوة 2: دالة إضافة للسلة
```python
@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    session_id = session.get('session_id', str(uuid.uuid4()))
    quantity = request.form.get('quantity', 1)
    size = request.form.get('size')
    color = request.form.get('color')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO cart (session_id, product_id, quantity, size, color)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, product_id, quantity, size, color))
    conn.commit()
    conn.close()
    
    return redirect('/cart')
```

### خطوة 3: صفحة السلة
```python
@app.route('/cart')
def view_cart():
    session_id = session.get('session_id')
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT c.*, p.name, p.price 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.session_id = ?
    ''', (session_id,))
    items = c.fetchall()
    conn.close()
    
    total = sum(item['quantity'] * item['price'] for item in items)
    # عرض HTML مع الفئات
    return render_html(items, total)
```

---

## 💳 إضافة نظام الدفع (Stripe)

### 1. التثبيت
```bash
pip install stripe
```

### 2. الإعدادات
```python
import stripe

stripe.api_key = "your_stripe_secret_key"
```

### 3. دالة الدفع
```python
@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'egp',
                    'product_data': {'name': product_name},
                    'unit_amount': int(price * 100),
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url='http://localhost:5000/success',
            cancel_url='http://localhost:5000/cancel',
        )
    except Exception as e:
        return str(e)
    
    return redirect(session.url, code=303)
```

---

## 📧 إرسال البريد الإلكتروني

### 1. التثبيت
```bash
pip install flask-mail
```

### 2. الإعدادات
```python
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_password'

mail = Mail(app)
```

### 3. إرسال تأكيد الطلب
```python
def send_order_confirmation(order_id, email):
    msg = Message(
        subject='تأكيد طلبك',
        recipients=[email],
        body=f'شكراً لطلبك! رقم الطلب: {order_id}'
    )
    mail.send(msg)
```

---

## 📱 تحسين الموبايل

المتجر بالفعل responsive، لكن يمكن تحسينه:

```css
/* للشاشات الصغيرة */
@media (max-width: 768px) {
    .products-grid {
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 15px;
    }
    
    .header-content {
        flex-direction: column;
        gap: 10px;
    }
    
    .search-box {
        max-width: 100%;
        margin: 10px 0;
    }
}
```

---

## 📊 إضافة لوحة إحصائيات

```python
@app.route('/admin/analytics')
def analytics():
    conn = get_db()
    c = conn.cursor()
    
    # مبيعات اليوم
    c.execute('''
        SELECT SUM(total_price) as today_sales 
        FROM orders 
        WHERE DATE(order_date) = DATE('now')
    ''')
    today_sales = c.fetchone()['today_sales'] or 0
    
    # المنتج الأكثر مبيعاً
    c.execute('''
        SELECT p.name, COUNT(*) as sales_count 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        GROUP BY p.id 
        ORDER BY sales_count DESC 
        LIMIT 1
    ''')
    top_product = c.fetchone()
    
    conn.close()
    
    return render_analytics(today_sales, top_product)
```

---

## 🔍 تحسين محركات البحث (SEO)

أضف في HTML:
```html
<meta name="description" content="متجر ملابس أنيق بأسعار منافسة">
<meta name="keywords" content="ملابس, تسوق, موضة, أزياء">
<meta name="author" content="VESTIQUE">
<meta property="og:title" content="VESTIQUE - متجر الملابس">
<meta property="og:description" content="أفضل الملابس بأسعار منافسة">
<meta property="og:image" content="logo.png">
```

---

## 🚀 التطوير المستمر

### خطوات للتطوير:
1. أضف ميزات واحدة تلو الأخرى
2. اختبر كل ميزة جيداً
3. احفظ نسخة احتياطية
4. انشر على الإنترنت

### الميزات المستقبلية المقترحة:
- [ ] تطبيق موبايل (Flutter/React Native)
- [ ] نظام CRM للعملاء
- [ ] تحليلات متقدمة
- [ ] توصيات ذكية (AI)
- [ ] نظام الاشتراكات
- [ ] برنامج الولاء

---

## 🎓 الموارد للتعلم

**لـ Python/Flask:**
- https://flask.palletsprojects.com/
- https://www.freecodecamp.org/

**لـ Databases:**
- https://www.sqlite.org/
- https://www.postgresql.org/

**لـ Web Design:**
- https://www.w3schools.com/
- https://css-tricks.com/

**لـ APIs:**
- https://stripe.com/docs
- https://www.twilio.com/docs

---

## 💬 مساعدة

هل تريد إضافة ميزة معينة؟ تواصل معي!

---

**استمتع ببناء متجر احترافي! 🎉**
