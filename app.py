
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import json
from datetime import datetime
import os
 
app = Flask(__name__)
app.secret_key = 'clothing_store_secret_2024'
 
DB_NAME = 'clothing_store.db'
 
# تأكد من إنشاء قاعدة البيانات عند البدء
@app.before_request
def create_database():
    """تأكد من وجود قاعدة البيانات"""
    if not os.path.exists(DB_NAME):
        init_db()
 
# ============ تهيئة قاعدة البيانات ============
 
def init_db():
    """إنشاء قاعدة البيانات والجداول"""
    if os.path.exists(DB_NAME):
        return
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # جدول المنتجات
    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            size TEXT,
            color TEXT,
            material TEXT,
            gender TEXT,
            description TEXT,
            stock INTEGER DEFAULT 0,
            image TEXT,
            rating REAL DEFAULT 0,
            reviews INTEGER DEFAULT 0
        )
    ''')
    
    # جدول الفئات
    c.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon TEXT
        )
    ''')
    
    # جدول الطلبات
    c.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'قيد المعالجة',
            payment_method TEXT
        )
    ''')
    
    # جدول تفاصيل الطلبات
    c.execute('''
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            size TEXT,
            color TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # جدول الأدمن
    c.execute('''
        CREATE TABLE admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # إدراج الفئات
    categories = [
        ('رجالي', '👔'),
        ('نسائي', '👗'),
        ('أطفال', '👶'),
        ('أحذية', '👟'),
        ('إكسسوارات', '⌚'),
        ('ملابس رياضية', '⛹️')
    ]
    c.executemany('INSERT INTO categories (name, icon) VALUES (?, ?)', categories)
    
    # إدراج منتجات نموذجية
    sample_products = [
        ('تيشيرت كوتن كلاسيكي', 150, 'رجالي', 'S, M, L, XL', 'أسود, أبيض, أزرق', 'قطن 100%', 'رجالي', 'تيشيرت عالي الجودة مصنوع من قطن خالص', 100, '', 4.5, 23),
        ('فستان سهرة أنيق', 450, 'نسائي', 'XS, S, M, L', 'أحمر, أسود, بيج', 'حرير مخلوط', 'نسائي', 'فستان فاخر مناسب للمناسبات الخاصة', 45, '', 4.8, 67),
        ('بنطال جينز مرن', 280, 'رجالي', 'M, L, XL, XXL', 'أزرق داكن, أسود', 'جينز مرن', 'رجالي', 'بنطال جينز مريح وعصري', 80, '', 4.6, 45),
        ('حجاب شيفون فاخر', 120, 'إكسسوارات', 'موحد', 'أحمر, عنابي, أسود, بيج', 'شيفون ناعم', 'نسائي', 'حجاب شيفون فاخر وناعم الملمس', 150, '', 4.7, 89),
        ('حذاء رياضي براق', 450, 'أحذية', '36-45', 'أبيض, أسود, رمادي', 'جلد صناعي مريح', 'موحد', 'حذاء رياضي مريح مع دعم عالي وتصميم عصري', 120, '', 4.4, 56),
        ('جاكت شتوي فخم', 550, 'رجالي', 'M, L, XL', 'أسود, بني, رمادي', 'صوف مخلوط', 'رجالي', 'جاكت شتوي فاخر وفخم', 40, '', 4.9, 78),
        ('فستان كاجوال', 250, 'نسائي', 'S, M, L', 'أزرق فاتح, بيج, وردي', 'قطن مزيج', 'نسائي', 'فستان مريح للارتداء اليومي', 90, '', 4.3, 34),
        ('شورت صيفي', 180, 'رجالي', 'S, M, L, XL', 'أزرق, رمادي, أسود', 'قطن خفيف', 'رجالي', 'شورت صيفي مريح وخفيف', 110, '', 4.2, 29),
    ]
    c.executemany('''
        INSERT INTO products (name, price, category, size, color, material, gender, description, stock, image, rating, reviews)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_products)
    
    # إضافة أدمن افتراضي
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    c.execute('INSERT INTO admins (username, password) VALUES (?, ?)', ('admin', admin_password))
    
    conn.commit()
    conn.close()
 
# ============ دوال مساعدة ============
 
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
 
def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()
 
# ============ الصفحات الرئيسية ============
 
@app.route('/')
def index():
    """الصفحة الرئيسية"""
    conn = get_db()
    c = conn.cursor()
    
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = 'SELECT * FROM products WHERE stock > 0'
    
    if category:
        query += f" AND category = '{category}'"
    if search:
        query += f" AND (name LIKE '%{search}%' OR description LIKE '%{search}%')"
    
    c.execute(query)
    products = c.fetchall()
    
    c.execute('SELECT * FROM categories ORDER BY name')
    categories = c.fetchall()
    
    conn.close()
    
    html = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VESTIQUE - متجر الملابس الحديث</title>
    <style>
        :root {
            --primary: #1a1a2e;
            --accent: #e94560;
            --light: #f8f9fa;
            --text: #333;
            --border: #e0e0e0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Cairo', 'Segoe UI', sans-serif;
            background: var(--light);
            color: var(--text);
            line-height: 1.6;
        }
        
        header {
            background: linear-gradient(135deg, var(--primary) 0%, #2d2d44 100%);
            color: white;
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--accent);
            text-decoration: none;
        }
        
        .search-box {
            flex: 1;
            max-width: 400px;
            margin: 0 30px;
            display: flex;
            gap: 8px;
        }
        
        .search-box input {
            flex: 1;
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            background: rgba(255,255,255,0.9);
        }
        
        .search-box button {
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
        }
        
        .admin-btn {
            padding: 8px 16px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        .filters {
            display: flex;
            gap: 10px;
            margin-bottom: 40px;
            flex-wrap: wrap;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .filters a {
            padding: 10px 20px;
            background: var(--light);
            color: var(--text);
            text-decoration: none;
            border-radius: 25px;
            border: 2px solid var(--border);
            transition: all 0.3s;
            font-weight: 500;
        }
        
        .filters a:hover {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .filters a.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 30px;
            margin-bottom: 50px;
        }
        
        .product-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }
        
        .product-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }
        
        .product-image {
            width: 100%;
            height: 280px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 80px;
            position: relative;
            overflow: hidden;
        }
        
        .product-image::after {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
            background-size: 20px 20px;
            animation: drift 20s linear infinite;
        }
        
        @keyframes drift {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        .product-info {
            padding: 20px;
        }
        
        .product-name {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 10px;
            color: var(--primary);
        }
        
        .product-desc {
            font-size: 13px;
            color: #666;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        
        .product-meta {
            font-size: 12px;
            color: #999;
            margin-bottom: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .product-meta span {
            background: var(--light);
            padding: 4px 10px;
            border-radius: 3px;
        }
        
        .product-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }
        
        .product-price {
            font-size: 20px;
            font-weight: 800;
            color: var(--accent);
        }
        
        .product-rating {
            font-size: 13px;
            color: #ffc107;
        }
        
        .btn-add {
            background: var(--primary);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-add:hover {
            background: var(--accent);
        }
        
        .empty {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 10px;
            color: #999;
        }
        
        .empty h2 {
            margin-bottom: 10px;
        }
        
        footer {
            background: var(--primary);
            color: white;
            text-align: center;
            padding: 30px 20px;
            margin-top: 50px;
        }
        
        .admin-link {
            position: fixed;
            bottom: 30px;
            left: 30px;
            padding: 15px 25px;
            background: var(--accent);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            box-shadow: 0 5px 20px rgba(233, 69, 96, 0.4);
            font-weight: 600;
            z-index: 50;
        }
        
        .admin-link:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(233, 69, 96, 0.6);
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <a href="/" class="logo">VESTIQUE</a>
            <div class="search-box">
                <form style="display: flex; gap: 8px; width: 100%;">
                    <input type="text" name="search" placeholder="ابحث عن منتج..." value="''' + search + '''">
                    <button type="submit">🔍</button>
                </form>
            </div>
            <a href="/admin" class="admin-btn">⚙️ لوحة التحكم</a>
        </div>
    </header>
    
    <div class="container">
        <div class="filters">
            <a href="/" class="''' + ('active' if not category else '') + '''">جميع المنتجات</a>
    '''
    
    for cat in categories:
        html += f'<a href="/?category={cat["name"]}" class="' + ('active' if category == cat["name"] else '') + f'">{cat["icon"]} {cat["name"]}</a>'
    
    html += '''
        </div>
        
        <div class="products-grid">
    '''
    
    if products:
        for p in products:
            rating_stars = '⭐' * int(p['rating'])
            html += f'''
                <div class="product-card">
                    <div class="product-image">{['👕', '👗', '👶', '👟', '⌚', '⛹️'][hash(p['name']) % 6]}</div>
                    <div class="product-info">
                        <div class="product-name">{p['name']}</div>
                        <div class="product-desc">{p['description']}</div>
                        <div class="product-meta">
                            <span>المقاس: {p['size']}</span>
                            <span>لون: {p['color']}</span>
                        </div>
                        <div class="product-footer">
                            <div>
                                <div class="product-price">{p['price']:.0f} ج.م</div>
                                <div class="product-rating">{rating_stars} ({p['reviews']})</div>
                            </div>
                            <button class="btn-add" onclick="alert('تمت الإضافة للسلة!')">أضف</button>
                        </div>
                    </div>
                </div>
            '''
    else:
        html += '<div class="empty" style="grid-column: 1/-1;"><h2>لا توجد منتجات متاحة</h2></div>'
    
    html += '''
        </div>
    </div>
    
    <footer>
        <p>&copy; 2024 VESTIQUE - متجر الملابس الحديث. جميع الحقوق محفوظة.</p>
    </footer>
    
    <a href="/admin" class="admin-link">⚙️</a>
</body>
</html>
    '''
    
    return html
 
# ============ لوحة التحكم ============
 
@app.route('/admin')
def admin_login():
    """صفحة دخول الأدمن"""
    html = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل دخول - لوحة التحكم</title>
    <style>
        body {
            font-family: 'Cairo', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #e94560 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        
        .login-container {
            background: white;
            padding: 50px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        
        .login-container h1 {
            text-align: center;
            color: #1a1a2e;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .login-container p {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #e94560;
            box-shadow: 0 0 0 3px rgba(233, 69, 96, 0.1);
        }
        
        .btn-login {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #1a1a2e 0%, #e94560 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(233, 69, 96, 0.4);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 لوحة التحكم</h1>
        <p>تسجيل الدخول لإدارة المتجر</p>
        
        <form method="POST" action="/admin/login">
            <div class="form-group">
                <label for="username">اسم المستخدم</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">كلمة المرور</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn-login">دخول</button>
        </form>
    </div>
</body>
</html>
    '''
    return html
 
@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """معالجة دخول الأدمن"""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM admins WHERE username = ?', (username,))
    admin = c.fetchone()
    conn.close()
    
    if admin and admin['password'] == hash_pwd(password):
        session['admin'] = True
        return redirect('/admin/dashboard')
    
    return '''
    <html dir="rtl">
    <body style="font-family: Cairo; text-align: center; padding: 50px;">
        <h1 style="color: red;">❌ بيانات غير صحيحة</h1>
        <p>اسم المستخدم أو كلمة المرور غير صحيحة</p>
        <a href="/admin" style="padding: 10px 20px; background: #e94560; color: white; text-decoration: none; border-radius: 5px;">← العودة</a>
    </body>
    </html>
    '''
 
@app.route('/admin/dashboard')
def admin_dashboard():
    """لوحة التحكم الرئيسية"""
    if not session.get('admin'):
        return redirect('/admin')
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as count FROM products')
    product_count = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM orders')
    order_count = c.fetchone()['count']
    
    c.execute('SELECT SUM(total_price) as total FROM orders')
    total = c.fetchone()['total'] or 0
    
    conn.close()
    
    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة التحكم</title>
    <style>
        :root {{
            --primary: #1a1a2e;
            --accent: #e94560;
            --light: #f8f9fa;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Cairo', sans-serif;
            background: var(--light);
        }}
        
        header {{
            background: var(--primary);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-box {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 5px solid var(--accent);
        }}
        
        .stat-box h3 {{
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        
        .stat-box .number {{
            font-size: 32px;
            font-weight: 800;
            color: var(--accent);
        }}
        
        .nav-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }}
        
        .nav-buttons a {{
            padding: 12px 25px;
            background: var(--accent);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }}
        
        .nav-buttons a:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(233, 69, 96, 0.3);
        }}
        
        .logout {{
            padding: 10px 20px;
            background: #999;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
        
        .logout:hover {{
            background: #666;
        }}
    </style>
</head>
<body>
    <header>
        <h1>👗 لوحة التحكم - VESTIQUE</h1>
        <a href="/admin/logout" class="logout">تسجيل خروج</a>
    </header>
    
    <div class="container">
        <div class="stats">
            <div class="stat-box">
                <h3>عدد المنتجات</h3>
                <div class="number">{product_count}</div>
            </div>
            <div class="stat-box">
                <h3>عدد الطلبات</h3>
                <div class="number">{order_count}</div>
            </div>
            <div class="stat-box">
                <h3>إجمالي المبيعات</h3>
                <div class="number">{total:.0f} ج.م</div>
            </div>
        </div>
        
        <div class="nav-buttons">
            <a href="/admin/products">📦 إدارة المنتجات</a>
            <a href="/admin/categories">📂 إدارة الفئات</a>
            <a href="/admin/orders">📋 عرض الطلبات</a>
        </div>
    </div>
</body>
</html>
    '''
    return html
 
@app.route('/admin/logout')
def admin_logout():
    """تسجيل خروج الأدمن"""
    session.clear()
    return redirect('/admin')
 
# ============ إدارة المنتجات ============
 
@app.route('/admin/products')
def admin_products():
    """صفحة إدارة المنتجات"""
    if not session.get('admin'):
        return redirect('/admin')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY id DESC')
    products = c.fetchall()
    conn.close()
    
    products_html = ''
    for p in products:
        products_html += f'''
            <tr>
                <td>{p['id']}</td>
                <td>{p['name']}</td>
                <td>{p['price']:.0f}</td>
                <td>{p['category']}</td>
                <td>{p['stock']}</td>
                <td>
                    <a href="/admin/product/{p['id']}/delete" onclick="return confirm('حذف؟')" style="color: red;">حذف</a>
                </td>
            </tr>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>إدارة المنتجات</title>
    <style>
        :root {{ --primary: #1a1a2e; --accent: #e94560; --light: #f8f9fa; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Cairo', sans-serif; background: var(--light); }}
        header {{ background: var(--primary); color: white; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}
        .btn {{ padding: 12px 25px; background: var(--accent); color: white; text-decoration: none; border-radius: 8px; margin-bottom: 20px; display: inline-block; font-weight: 600; }}
        table {{ width: 100%; background: white; border-collapse: collapse; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        th {{ background: var(--primary); color: white; padding: 15px; text-align: right; font-weight: 600; }}
        td {{ padding: 15px; border-bottom: 1px solid #e0e0e0; }}
        tr:hover {{ background: var(--light); }}
        a {{ color: var(--accent); text-decoration: none; }}
    </style>
</head>
<body>
    <header>
        <h1>إدارة المنتجات</h1>
    </header>
    
    <div class="container">
        <a href="/admin/product/new" class="btn">+ إضافة منتج جديد</a>
        <a href="/admin/dashboard" class="btn">← العودة</a>
        
        <table>
            <tr>
                <th>المعرّف</th>
                <th>الاسم</th>
                <th>السعر</th>
                <th>الفئة</th>
                <th>المخزون</th>
                <th>الإجراءات</th>
            </tr>
            {products_html}
        </table>
    </div>
</body>
</html>
    '''
    return html
 
@app.route('/admin/product/new', methods=['GET', 'POST'])
def admin_product_new():
    """إضافة منتج جديد"""
    if not session.get('admin'):
        return redirect('/admin')
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'price': request.form.get('price'),
            'category': request.form.get('category'),
            'size': request.form.get('size'),
            'color': request.form.get('color'),
            'material': request.form.get('material'),
            'gender': request.form.get('gender'),
            'description': request.form.get('description'),
            'stock': request.form.get('stock', 0)
        }
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO products (name, price, category, size, color, material, gender, description, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['price'], data['category'], data['size'], 
              data['color'], data['material'], data['gender'], data['description'], data['stock']))
        conn.commit()
        conn.close()
        
        return redirect('/admin/products')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT name FROM categories')
    categories = [row['name'] for row in c.fetchall()]
    conn.close()
    
    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>إضافة منتج</title>
    <style>
        :root {{ --primary: #1a1a2e; --accent: #e94560; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Cairo', sans-serif; background: #f8f9fa; }}
        header {{ background: var(--primary); color: white; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px 20px; }}
        .form-box {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #333; }}
        input, select, textarea {{ width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }}
        input:focus, select:focus, textarea:focus {{ outline: none; border-color: var(--accent); }}
        button {{ width: 100%; padding: 12px; background: var(--accent); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }}
        button:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
    <header><h1>إضافة منتج جديد</h1></header>
    
    <div class="container">
        <div class="form-box">
            <form method="POST">
                <div class="form-group">
                    <label>اسم المنتج</label>
                    <input type="text" name="name" required>
                </div>
                
                <div class="form-group">
                    <label>السعر</label>
                    <input type="number" name="price" step="0.01" required>
                </div>
                
                <div class="form-group">
                    <label>الفئة</label>
                    <select name="category" required>
                        <option>اختر فئة</option>
                        {''.join([f'<option>{cat}</option>' for cat in categories])}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>المقاس</label>
                    <input type="text" name="size" placeholder="S, M, L, XL">
                </div>
                
                <div class="form-group">
                    <label>اللون</label>
                    <input type="text" name="color" placeholder="أسود, أبيض, أحمر">
                </div>
                
                <div class="form-group">
                    <label>المادة</label>
                    <input type="text" name="material" placeholder="قطن, حرير, صوف">
                </div>
                
                <div class="form-group">
                    <label>الجنس</label>
                    <select name="gender">
                        <option>رجالي</option>
                        <option>نسائي</option>
                        <option>أطفال</option>
                        <option>موحد</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>الوصف</label>
                    <textarea name="description" rows="4"></textarea>
                </div>
                
                <div class="form-group">
                    <label>المخزون</label>
                    <input type="number" name="stock" value="0" required>
                </div>
                
                <button type="submit">حفظ المنتج</button>
            </form>
        </div>
    </div>
</body>
</html>
    '''
    return html
 
@app.route('/admin/product/<int:pid>/delete')
def admin_product_delete(pid):
    """حذف منتج"""
    if not session.get('admin'):
        return redirect('/admin')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (pid,))
    conn.commit()
    conn.close()
    
    return redirect('/admin/products')
 
# ============ إدارة الفئات ============
 
@app.route('/admin/categories')
def admin_categories():
    """إدارة الفئات"""
    if not session.get('admin'):
        return redirect('/admin')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM categories')
    categories = c.fetchall()
    conn.close()
    
    cat_html = ''
    for cat in categories:
        cat_html += f'''
            <tr>
                <td>{cat['name']}</td>
                <td><a href="/admin/category/{cat['id']}/delete" onclick="return confirm('حذف؟')" style="color: red;">حذف</a></td>
            </tr>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>إدارة الفئات</title>
    <style>
        :root {{ --primary: #1a1a2e; --accent: #e94560; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Cairo', sans-serif; background: #f8f9fa; }}
        header {{ background: var(--primary); color: white; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px 20px; }}
        .form-box {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        input {{ width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; }}
        button {{ width: 100%; padding: 12px; background: var(--accent); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }}
        table {{ width: 100%; background: white; border-collapse: collapse; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        th, td {{ padding: 15px; text-align: right; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: var(--primary); color: white; }}
    </style>
</head>
<body>
    <header><h1>إدارة الفئات</h1></header>
    
    <div class="container">
        <div class="form-box">
            <h2>إضافة فئة جديدة</h2>
            <form method="POST" action="/admin/category/add">
                <input type="text" name="name" placeholder="اسم الفئة" required>
                <button type="submit">إضافة</button>
            </form>
        </div>
        
        <table>
            <tr>
                <th>الفئة</th>
                <th>الإجراءات</th>
            </tr>
            {cat_html}
        </table>
    </div>
</body>
</html>
    '''
    return html
 
@app.route('/admin/category/add', methods=['POST'])
def admin_category_add():
    """إضافة فئة"""
    if not session.get('admin'):
        return redirect('/admin')
    
    name = request.form.get('name')
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO categories (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    
    return redirect('/admin/categories')
 
@app.route('/admin/category/<int:cid>/delete')
def admin_category_delete(cid):
    """حذف فئة"""
    if not session.get('admin'):
        return redirect('/admin')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM categories WHERE id = ?', (cid,))
    conn.commit()
    conn.close()
    
    return redirect('/admin/categories')
 
# ============ الطلبات ============
 
@app.route('/admin/orders')
def admin_orders():
    """عرض الطلبات"""
    if not session.get('admin'):
        return redirect('/admin')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY id DESC')
    orders = c.fetchall()
    conn.close()
    
    orders_html = ''
    for o in orders:
        orders_html += f'''
            <tr>
                <td>{o['id']}</td>
                <td>{o['customer_name']}</td>
                <td>{o['customer_phone']}</td>
                <td>{o['total_price']:.0f}</td>
                <td>{o['status']}</td>
                <td>{o['order_date']}</td>
            </tr>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>الطلبات</title>
    <style>
        :root {{ --primary: #1a1a2e; --accent: #e94560; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Cairo', sans-serif; background: #f8f9fa; }}
        header {{ background: var(--primary); color: white; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}
        table {{ width: 100%; background: white; border-collapse: collapse; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        th {{ background: var(--primary); color: white; padding: 15px; text-align: right; }}
        td {{ padding: 15px; border-bottom: 1px solid #e0e0e0; }}
    </style>
</head>
<body>
    <header><h1>الطلبات</h1></header>
    
    <div class="container">
        <table>
            <tr>
                <th>المعرّف</th>
                <th>الاسم</th>
                <th>الهاتف</th>
                <th>الإجمالي</th>
                <th>الحالة</th>
                <th>التاريخ</th>
            </tr>
            {orders_html if orders_html else '<tr><td colspan="6" style="text-align: center; color: #999;">لا توجد طلبات</td></tr>'}
        </table>
    </div>
</body>
</html>
    '''
    return html
 
# ============ تشغيل التطبيق ============
 
if __name__ == '__main__':
    # تأكد من إنشاء قاعدة البيانات
    init_db()
    
    # احصل على PORT من البيئة (Render يعطيها تلقائياً)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print('🚀 Server starting...')
    print('📊 Admin panel available')
    print('👤 Username: admin | Password: admin123')
    
    app.run(debug=debug, host='0.0.0.0', port=port)
