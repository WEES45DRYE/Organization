
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import json
from datetime import datetime
import os
 
app = Flask(__name__)
app.secret_key = 'clothing_store_secret_2024'
 
DB_NAME = 'clothing_store.db'
 
@app.before_request
def create_database():
    if not os.path.exists(DB_NAME):
        init_db()
 
def init_db():
    if os.path.exists(DB_NAME):
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, price REAL NOT NULL, category TEXT NOT NULL,
        size TEXT, color TEXT, material TEXT, gender TEXT, description TEXT,
        stock INTEGER DEFAULT 0, image TEXT, rating REAL DEFAULT 0, reviews INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, icon TEXT)''')
    c.execute('''CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL, customer_phone TEXT NOT NULL,
        customer_address TEXT NOT NULL, order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_price REAL NOT NULL, status TEXT DEFAULT 'قيد المعالجة', payment_method TEXT)''')
    c.execute('''CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, price REAL NOT NULL,
        size TEXT, color TEXT,
        FOREIGN KEY(order_id) REFERENCES orders(id), FOREIGN KEY(product_id) REFERENCES products(id))''')
    c.execute('''CREATE TABLE admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    categories = [('الرجال','👔'),('النساء','👗'),('الأطفال','👶'),('أحذية','👟'),('إكسسوارات','🧢'),('ملابس رياضية','⛹️')]
    c.executemany('INSERT INTO categories (name, icon) VALUES (?, ?)', categories)
    sample_products = [
        ('تيشيرت أسود', 149, 'الرجال', 'S,M,L,XL', 'أسود', 'قطن 100%', 'رجالي', 'تيشيرت كلاسيكي عالي الجودة', 100, 'tshirt_black', 4.5, 23),
        ('هودي بيج', 219, 'الرجال', 'S,M,L,XL', 'بيج', 'قطن مزيج', 'رجالي', 'هودي مريح للإرتداء اليومي', 80, 'hoodie_beige', 4.7, 45),
        ('قميص أسود', 179, 'الرجال', 'S,M,L,XL', 'أسود', 'قطن ناعم', 'رجالي', 'قميص أنيق مناسب لكل المناسبات', 60, 'shirt_black', 4.6, 38),
        ('تيشيرت أبيض', 129, 'الرجال', 'S,M,L,XL', 'أبيض', 'قطن خالص', 'رجالي', 'تيشيرت أبيض كلاسيكي', 90, 'tshirt_white', 4.3, 29),
        ('جاكيت كاجوال', 279, 'الرجال', 'M,L,XL', 'بيج', 'قماش ممزوج', 'رجالي', 'جاكيت خفيف مناسب للربيع', 40, 'jacket_beige', 4.8, 67),
        ('بنطال جينز', 199, 'الرجال', 'M,L,XL,XXL', 'أزرق داكن', 'جينز مرن', 'رجالي', 'بنطال جينز عصري ومريح', 70, 'jeans', 4.4, 52),
        ('فستان سهرة', 450, 'النساء', 'XS,S,M,L', 'أسود', 'حرير مخلوط', 'نسائي', 'فستان فاخر للمناسبات', 30, 'dress', 4.9, 78),
        ('حذاء رياضي', 350, 'أحذية', '36-45', 'أبيض', 'جلد صناعي', 'موحد', 'حذاء رياضي مريح وعصري', 50, 'sneaker', 4.5, 41),
    ]
    c.executemany('''INSERT INTO products (name,price,category,size,color,material,gender,description,stock,image,rating,reviews)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', sample_products)
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    c.execute('INSERT INTO admins (username, password) VALUES (?, ?)', ('admin', admin_password))
    conn.commit()
    conn.close()
 
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
 
def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()
 
# ============ الصفحة الرئيسية ============
@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    query = 'SELECT * FROM products WHERE stock > 0'
    params = []
    if category:
        query += ' AND category = ?'
        params.append(category)
    if search:
        query += ' AND (name LIKE ? OR description LIKE ?)'
        params.append(f'%{search}%')
        params.append(f'%{search}%')
    c.execute(query, params)
    products = c.fetchall()
    c.execute('SELECT * FROM categories ORDER BY name')
    categories = c.fetchall()
    conn.close()
 
    # emoji mapping for product placeholders
    emoji_map = {
        'tshirt_black': '🖤', 'tshirt_white': '🤍', 'hoodie_beige': '🧥',
        'shirt_black': '👔', 'jacket_beige': '🧣', 'jeans': '👖',
        'dress': '👗', 'sneaker': '👟'
    }
 
    products_html = ''
    for p in products:
        emoji = emoji_map.get(p['image'], '👕')
        stars = '★' * int(p['rating']) + '☆' * (5 - int(p['rating']))
        products_html += f'''
        <div class="product-card">
            <div class="card-img">
                <span class="card-emoji">{emoji}</span>
                <button class="wishlist-btn" onclick="toggleWish(this)">♡</button>
                <div class="card-overlay">
                    <button class="quick-add" onclick="showToast()">أضف للسلة</button>
                </div>
            </div>
            <div class="card-body">
                <p class="card-cat">{p['category']}</p>
                <h3 class="card-name">{p['name']}</h3>
                <div class="card-footer">
                    <span class="card-price">{p['price']:.0f} ر.س</span>
                    <span class="card-stars">{stars}</span>
                </div>
            </div>
        </div>'''
 
    cats_html = f'<a href="/" class="cat-pill {"active" if not category else ""}">الكل</a>'
    for cat in categories:
        active = 'active' if category == cat['name'] else ''
        cats_html += f'<a href="/?category={cat["name"]}" class="cat-pill {active}">{cat["name"]}</a>'
 
    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VESTIQUE — أزياء تعبر عنك</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap" rel="stylesheet">
<style>
:root {{
    --black: #0d0d0d;
    --white: #f5f0eb;
    --beige: #c8b99a;
    --beige-light: #e8dfd3;
    --beige-dark: #a09070;
    --gray: #6b6b6b;
    --gray-light: #ebebeb;
    --accent: #1a1a1a;
}}
 
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
 
body {{
    font-family: 'Tajawal', sans-serif;
    background: var(--white);
    color: var(--black);
    line-height: 1.6;
}}
 
/* ====== NAVBAR ====== */
nav {{
    position: fixed; top: 0; width: 100%; z-index: 1000;
    background: var(--black);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 40px; height: 64px;
    border-bottom: 1px solid #222;
}}
 
.nav-logo {{
    font-size: 22px; font-weight: 900; letter-spacing: 4px;
    color: var(--white); text-decoration: none;
}}
 
.nav-links {{
    display: flex; gap: 28px; list-style: none;
}}
 
.nav-links a {{
    color: #aaa; text-decoration: none; font-size: 14px;
    font-weight: 500; letter-spacing: 1px;
    transition: color 0.2s;
}}
 
.nav-links a:hover {{ color: var(--white); }}
 
.nav-icons {{
    display: flex; gap: 20px; align-items: center;
}}
 
.nav-icons a {{
    color: #aaa; text-decoration: none; font-size: 18px;
    transition: color 0.2s;
}}
 
.nav-icons a:hover {{ color: var(--white); }}
 
/* ====== HERO ====== */
.hero {{
    margin-top: 64px;
    background: var(--black);
    min-height: 88vh;
    display: grid; grid-template-columns: 1fr 1fr;
    position: relative; overflow: hidden;
}}
 
.hero-content {{
    display: flex; flex-direction: column;
    justify-content: center;
    padding: 80px 60px;
    z-index: 2;
}}
 
.hero-tag {{
    font-size: 12px; letter-spacing: 4px; color: var(--beige);
    text-transform: uppercase; margin-bottom: 20px;
    font-weight: 500;
}}
 
.hero-title {{
    font-size: clamp(42px, 5vw, 72px);
    font-weight: 900; line-height: 1.05;
    color: var(--white);
    margin-bottom: 24px;
}}
 
.hero-title span {{
    color: var(--beige);
    font-style: italic;
}}
 
.hero-sub {{
    color: #888; font-size: 16px; margin-bottom: 48px;
    max-width: 380px; line-height: 1.8;
}}
 
.hero-btns {{
    display: flex; gap: 16px; flex-wrap: wrap;
}}
 
.btn-primary {{
    padding: 16px 36px;
    background: var(--white); color: var(--black);
    border: none; border-radius: 2px;
    font-size: 14px; font-weight: 700; letter-spacing: 2px;
    cursor: pointer; text-decoration: none;
    transition: all 0.3s;
    text-transform: uppercase;
}}
 
.btn-primary:hover {{
    background: var(--beige);
}}
 
.btn-outline {{
    padding: 16px 36px;
    background: transparent; color: var(--white);
    border: 1px solid #444; border-radius: 2px;
    font-size: 14px; font-weight: 500; letter-spacing: 2px;
    cursor: pointer; text-decoration: none;
    transition: all 0.3s;
    text-transform: uppercase;
}}
 
.btn-outline:hover {{
    border-color: var(--beige); color: var(--beige);
}}
 
.hero-visual {{
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #1a1a1a 0%, #2a2520 100%);
    position: relative; overflow: hidden;
    font-size: 220px;
}}
 
.hero-visual::before {{
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at center, rgba(200,185,154,0.15) 0%, transparent 70%);
}}
 
.hero-badge {{
    position: absolute; bottom: 40px; right: 40px;
    background: var(--beige); color: var(--black);
    padding: 16px 24px; border-radius: 2px;
    font-size: 12px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase;
}}
 
.hero-dots {{
    position: absolute; bottom: 40px; left: 60px;
    display: flex; gap: 8px;
}}
 
.hero-dots span {{
    width: 8px; height: 8px; border-radius: 50%;
    background: #444; cursor: pointer; transition: 0.3s;
}}
 
.hero-dots span.active {{ background: var(--beige); width: 24px; border-radius: 4px; }}
 
/* ====== CATEGORIES ====== */
.section {{
    padding: 80px 40px;
    max-width: 1300px; margin: 0 auto;
}}
 
.section-header {{
    display: flex; align-items: baseline;
    justify-content: space-between; margin-bottom: 40px;
}}
 
.section-title {{
    font-size: 28px; font-weight: 800; letter-spacing: 1px;
}}
 
.section-link {{
    color: var(--gray); font-size: 13px; text-decoration: none;
    letter-spacing: 1px; border-bottom: 1px solid var(--gray);
    padding-bottom: 2px; transition: 0.2s;
}}
 
.section-link:hover {{ color: var(--black); border-color: var(--black); }}
 
.categories-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}}
 
.cat-card {{
    background: var(--black);
    border-radius: 4px; overflow: hidden;
    cursor: pointer; text-decoration: none;
    position: relative; height: 200px;
    display: flex; align-items: flex-end;
    padding: 20px;
    transition: transform 0.3s;
}}
 
.cat-card:hover {{ transform: scale(1.02); }}
 
.cat-card-emoji {{
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 64px; opacity: 0.6;
}}
 
.cat-card-info {{
    position: relative; z-index: 2;
}}
 
.cat-card-name {{
    color: var(--white); font-size: 18px; font-weight: 800;
    display: block; margin-bottom: 4px;
}}
 
.cat-card-link {{
    color: var(--beige); font-size: 12px; letter-spacing: 1px;
}}
 
.cat-card:nth-child(1) {{ background: #1a1a1a; }}
.cat-card:nth-child(2) {{ background: #2d2520; }}
.cat-card:nth-child(3) {{ background: #1e2228; }}
.cat-card:nth-child(4) {{ background: #221a1a; }}
 
/* ====== PROMO BANNER ====== */
.promo-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 16px; padding: 0 40px 80px;
    max-width: 1300px; margin: 0 auto;
}}
 
.promo-card {{
    border-radius: 4px; overflow: hidden;
    position: relative; height: 300px;
    display: flex; align-items: center;
    padding: 40px;
    cursor: pointer;
}}
 
.promo-card:nth-child(1) {{
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
}}
 
.promo-card:nth-child(2) {{
    background: linear-gradient(135deg, #c8b99a 0%, #a09070 100%);
}}
 
.promo-card-emoji {{
    position: absolute; left: 0; top: 0; right: 0; bottom: 0;
    display: flex; align-items: center; justify-content: flex-end;
    font-size: 120px; padding: 20px; opacity: 0.3;
}}
 
.promo-content {{ position: relative; z-index: 2; }}
 
.promo-discount {{
    font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
    margin-bottom: 12px; font-weight: 600;
}}
 
.promo-card:nth-child(1) .promo-discount {{ color: var(--beige); }}
.promo-card:nth-child(2) .promo-discount {{ color: var(--black); }}
 
.promo-big {{
    font-size: 52px; font-weight: 900; line-height: 1;
    margin-bottom: 8px;
}}
 
.promo-card:nth-child(1) .promo-big {{ color: var(--white); }}
.promo-card:nth-child(2) .promo-big {{ color: var(--black); }}
 
.promo-sub {{
    font-size: 13px; margin-bottom: 24px;
}}
 
.promo-card:nth-child(1) .promo-sub {{ color: #888; }}
.promo-card:nth-child(2) .promo-sub {{ color: #555; }}
 
.promo-btn {{
    display: inline-block; padding: 10px 24px;
    font-size: 12px; letter-spacing: 2px; font-weight: 700;
    text-transform: uppercase; border-radius: 2px;
    text-decoration: none; transition: 0.3s;
}}
 
.promo-card:nth-child(1) .promo-btn {{
    background: var(--white); color: var(--black);
}}
 
.promo-card:nth-child(2) .promo-btn {{
    background: var(--black); color: var(--white);
}}
 
/* ====== FILTER PILLS ====== */
.filters-bar {{
    display: flex; gap: 10px; flex-wrap: wrap;
    padding: 0 40px; margin-bottom: 40px;
    max-width: 1300px; margin-left: auto; margin-right: auto;
    padding-bottom: 0;
}}
 
.cat-pill {{
    padding: 8px 20px; border-radius: 100px;
    font-size: 13px; font-weight: 500; letter-spacing: 0.5px;
    cursor: pointer; text-decoration: none;
    border: 1.5px solid var(--gray-light);
    color: var(--gray); background: transparent;
    transition: all 0.2s;
}}
 
.cat-pill:hover, .cat-pill.active {{
    background: var(--black); color: var(--white);
    border-color: var(--black);
}}
 
/* ====== PRODUCTS GRID ====== */
.products-section {{
    padding: 0 40px 80px;
    max-width: 1300px; margin: 0 auto;
}}
 
.products-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 24px;
}}
 
.product-card {{
    background: white;
    border-radius: 4px; overflow: hidden;
    transition: box-shadow 0.3s;
    cursor: pointer;
}}
 
.product-card:hover {{
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}}
 
.card-img {{
    background: var(--gray-light);
    height: 280px; position: relative;
    display: flex; align-items: center; justify-content: center;
    overflow: hidden;
}}
 
.card-emoji {{
    font-size: 80px; transition: transform 0.3s;
    display: block;
}}
 
.product-card:hover .card-emoji {{ transform: scale(1.1); }}
 
.wishlist-btn {{
    position: absolute; top: 12px; right: 12px;
    width: 36px; height: 36px; border-radius: 50%;
    background: white; border: none; cursor: pointer;
    font-size: 16px; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: 0.2s;
}}
 
.wishlist-btn:hover {{ transform: scale(1.1); }}
.wishlist-btn.active {{ color: #e94560; }}
 
.card-overlay {{
    position: absolute; bottom: 0; left: 0; right: 0;
    padding: 16px;
    background: linear-gradient(transparent, rgba(0,0,0,0.7));
    transform: translateY(100%);
    transition: transform 0.3s;
}}
 
.product-card:hover .card-overlay {{ transform: translateY(0); }}
 
.quick-add {{
    width: 100%; padding: 10px;
    background: var(--white); color: var(--black);
    border: none; border-radius: 2px; cursor: pointer;
    font-size: 13px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; transition: 0.2s;
}}
 
.quick-add:hover {{ background: var(--beige); }}
 
.card-body {{ padding: 16px; }}
 
.card-cat {{
    font-size: 11px; letter-spacing: 2px; color: var(--gray);
    text-transform: uppercase; margin-bottom: 6px;
}}
 
.card-name {{
    font-size: 15px; font-weight: 700; margin-bottom: 10px;
    color: var(--black); line-height: 1.3;
}}
 
.card-footer {{
    display: flex; align-items: center; justify-content: space-between;
}}
 
.card-price {{
    font-size: 17px; font-weight: 800; color: var(--black);
}}
 
.card-stars {{
    font-size: 12px; color: var(--beige-dark); letter-spacing: 1px;
}}
 
/* ====== FEATURES BAR ====== */
.features-bar {{
    background: var(--black);
    padding: 40px;
}}
 
.features-inner {{
    max-width: 1300px; margin: 0 auto;
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 32px;
}}
 
.feature-item {{
    text-align: center; color: var(--white);
}}
 
.feature-icon {{
    font-size: 28px; margin-bottom: 12px; display: block;
}}
 
.feature-title {{
    font-size: 14px; font-weight: 700; letter-spacing: 1px;
    margin-bottom: 4px;
}}
 
.feature-sub {{
    font-size: 12px; color: #666;
}}
 
/* ====== SEARCH IN NAV ====== */
.search-form {{
    display: flex; align-items: center; gap: 8px;
}}
 
.search-form input {{
    background: #1a1a1a; border: 1px solid #333;
    color: white; padding: 6px 14px;
    border-radius: 2px; font-size: 13px;
    outline: none; width: 180px;
}}
 
.search-form input::placeholder {{ color: #555; }}
 
.search-form button {{
    background: none; border: none;
    color: #888; cursor: pointer; font-size: 16px;
}}
 
/* ====== TOAST ====== */
.toast {{
    position: fixed; bottom: 30px; left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: var(--black); color: white;
    padding: 14px 28px; border-radius: 4px;
    font-size: 14px; font-weight: 500;
    transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    z-index: 9999; pointer-events: none;
    border: 1px solid #333;
}}
 
.toast.show {{ transform: translateX(-50%) translateY(0); }}
 
footer {{
    background: #0a0a0a; color: #444;
    text-align: center; padding: 24px;
    font-size: 13px; letter-spacing: 1px;
}}
</style>
</head>
<body>
 
<!-- NAVBAR -->
<nav>
    <a href="/" class="nav-logo">VESTIQUE</a>
    <ul class="nav-links">
        <li><a href="/?category=الرجال">الرجال</a></li>
        <li><a href="/?category=النساء">النساء</a></li>
        <li><a href="/?category=الأطفال">الأطفال</a></li>
        <li><a href="/?category=أحذية">أحذية</a></li>
        <li><a href="/?category=إكسسوارات">إكسسوارات</a></li>
        <li><a href="#">العروض</a></li>
        <li><a href="#">اتصل بنا</a></li>
    </ul>
    <div class="nav-icons">
        <form class="search-form" method="GET" action="/">
            <input type="text" name="search" placeholder="بحث..." value="{search}">
            <button type="submit">🔍</button>
        </form>
        <a href="/admin" title="لوحة التحكم">⚙️</a>
        <a href="#" title="المفضلة">♡</a>
        <a href="#" title="السلة">🛍</a>
    </div>
</nav>
 
<!-- HERO -->
<section class="hero">
    <div class="hero-content">
        <p class="hero-tag">مجموعة صيف 2024</p>
        <h1 class="hero-title">أزياء<br><span>تعبّر</span><br>عنك</h1>
        <p class="hero-sub">اكتشف أحدث التشكيلات لصيف 2024 — أناقة حقيقية لكل يوم</p>
        <div class="hero-btns">
            <a href="/?category=الرجال" class="btn-primary">تسوق الآن</a>
            <a href="#products" class="btn-outline">استكشف المجموعة</a>
        </div>
        <div class="hero-dots" style="position:relative;bottom:auto;left:auto;margin-top:60px;">
            <span class="active"></span><span></span><span></span>
        </div>
    </div>
    <div class="hero-visual">
        👔
        <div class="hero-badge">جديد — صيف 2024</div>
    </div>
</section>
 
<!-- CATEGORIES -->
<div class="section">
    <div class="section-header">
        <h2 class="section-title">تسوق حسب الفئة</h2>
        <a href="/" class="section-link">عرض الكل ←</a>
    </div>
    <div class="categories-grid">
        <a href="/?category=الرجال" class="cat-card">
            <div class="cat-card-emoji">👔</div>
            <div class="cat-card-info">
                <span class="cat-card-name">رجال</span>
                <span class="cat-card-link">تسوق الآن ›</span>
            </div>
        </a>
        <a href="/?category=النساء" class="cat-card">
            <div class="cat-card-emoji">👗</div>
            <div class="cat-card-info">
                <span class="cat-card-name">نساء</span>
                <span class="cat-card-link">تسوق الآن ›</span>
            </div>
        </a>
        <a href="/?category=الأطفال" class="cat-card">
            <div class="cat-card-emoji">👶</div>
            <div class="cat-card-info">
                <span class="cat-card-name">أطفال</span>
                <span class="cat-card-link">تسوق الآن ›</span>
            </div>
        </a>
        <a href="/?category=إكسسوارات" class="cat-card">
            <div class="cat-card-emoji">🧢</div>
            <div class="cat-card-info">
                <span class="cat-card-name">إكسسوارات</span>
                <span class="cat-card-link">تسوق الآن ›</span>
            </div>
        </a>
    </div>
</div>
 
<!-- PROMO BANNERS -->
<div class="promo-grid">
    <div class="promo-card">
        <div class="promo-card-emoji">🔥</div>
        <div class="promo-content">
            <p class="promo-discount">خصم حتى</p>
            <p class="promo-big">50%</p>
            <p class="promo-sub">على مجموعة مختارة</p>
            <a href="/" class="promo-btn">تسوق الآن</a>
        </div>
    </div>
    <div class="promo-card">
        <div class="promo-card-emoji">✨</div>
        <div class="promo-content">
            <p class="promo-discount">وصل حديثاً</p>
            <p class="promo-big">مجموعة<br>الصيف</p>
            <p class="promo-sub">الجديدة</p>
            <a href="/?category=الرجال" class="promo-btn">تسوق الآن ›</a>
        </div>
    </div>
</div>
 
<!-- PRODUCTS -->
<div id="products" class="section" style="padding-top:0">
    <div class="section-header">
        <h2 class="section-title">الأكثر مبيعاً</h2>
        <a href="/" class="section-link">عرض الكل ←</a>
    </div>
</div>
 
<div class="filters-bar" style="margin-bottom:24px;">
    {cats_html}
</div>
 
<div class="products-section">
    <div class="products-grid">
        {products_html if products_html else '<p style="color:#999;text-align:center;grid-column:1/-1;padding:60px">لا توجد منتجات</p>'}
    </div>
    <div style="text-align:center;margin-top:48px;">
        <a href="/" class="btn-primary" style="display:inline-block;">عرض المزيد</a>
    </div>
</div>
 
<!-- FEATURES BAR -->
<div class="features-bar">
    <div class="features-inner">
        <div class="feature-item">
            <span class="feature-icon">🛡️</span>
            <p class="feature-title">دفع آمن 100%</p>
            <p class="feature-sub">مع ضمان حماية بياناتك</p>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🚚</span>
            <p class="feature-title">شحن سريع</p>
            <p class="feature-sub">توصيل خلال 2-2 أيام</p>
        </div>
        <div class="feature-item">
            <span class="feature-icon">↩️</span>
            <p class="feature-title">إرجاع سهل</p>
            <p class="feature-sub">إرجاع مجاني خلال 14 يوم</p>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🎧</span>
            <p class="feature-title">خدمة العملاء</p>
            <p class="feature-sub">متاح 24/7 لمساعدتك</p>
        </div>
    </div>
</div>
 
<footer>
    <p style="letter-spacing:3px;font-size:11px;">© 2024 VESTIQUE — جميع الحقوق محفوظة</p>
</footer>
 
<div class="toast" id="toast">✓ تمت الإضافة للسلة</div>
 
<script>
function showToast() {{
    const t = document.getElementById('toast');
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}}
 
function toggleWish(btn) {{
    btn.classList.toggle('active');
    btn.textContent = btn.classList.contains('active') ? '♥' : '♡';
}}
</script>
</body>
</html>'''
    return html
 
# ============ لوحة التحكم (نفس الكود) ============
@app.route('/admin')
def admin_login():
    html = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة التحكم</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Tajawal', sans-serif; background: #0d0d0d;
               display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1a1a1a; padding: 50px; border-radius: 4px;
               width: 100%; max-width: 380px; border: 1px solid #2a2a2a; }
        h1 { color: #f5f0eb; text-align: center; margin-bottom: 8px; font-size: 24px; }
        p { color: #555; text-align: center; margin-bottom: 32px; font-size: 13px; }
        label { display: block; color: #888; font-size: 12px; letter-spacing: 1px; margin-bottom: 8px; text-transform: uppercase; }
        input { width: 100%; padding: 12px; background: #0d0d0d; border: 1px solid #2a2a2a;
                color: white; border-radius: 2px; font-size: 14px; margin-bottom: 20px; outline: none; }
        input:focus { border-color: #c8b99a; }
        button { width: 100%; padding: 14px; background: #f5f0eb; color: #0d0d0d;
                 border: none; border-radius: 2px; font-size: 14px; font-weight: 700;
                 letter-spacing: 2px; cursor: pointer; text-transform: uppercase; }
        button:hover { background: #c8b99a; }
    </style>
</head>
<body>
    <div class="box">
        <h1>VESTIQUE</h1>
        <p>تسجيل الدخول للوحة التحكم</p>
        <form method="POST" action="/admin/login">
            <label>اسم المستخدم</label>
            <input type="text" name="username" required>
            <label>كلمة المرور</label>
            <input type="password" name="password" required>
            <button type="submit">دخول</button>
        </form>
    </div>
</body>
</html>'''
    return html
 
@app.route('/admin/login', methods=['POST'])
def admin_login_post():
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
    return '<html dir="rtl"><body style="font-family:Tajawal;text-align:center;padding:50px;background:#0d0d0d;color:white;"><h1>❌ بيانات غير صحيحة</h1><a href="/admin" style="color:#c8b99a;">← العودة</a></body></html>'
 
@app.route('/admin/dashboard')
def admin_dashboard():
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
<head><meta charset="UTF-8"><title>لوحة التحكم</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Tajawal',sans-serif; background:#0d0d0d; color:white; }}
header {{ background:#1a1a1a; padding:20px 40px; border-bottom:1px solid #2a2a2a;
          display:flex; justify-content:space-between; align-items:center; }}
header h1 {{ font-size:20px; letter-spacing:2px; color:#f5f0eb; }}
.logout {{ color:#555; text-decoration:none; font-size:13px; border:1px solid #333;
           padding:8px 16px; border-radius:2px; transition:0.2s; }}
.logout:hover {{ color:white; border-color:#555; }}
.container {{ max-width:1100px; margin:0 auto; padding:40px 20px; }}
.stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-bottom:40px; }}
.stat {{ background:#1a1a1a; border:1px solid #2a2a2a; padding:28px; border-radius:4px; }}
.stat h3 {{ color:#555; font-size:12px; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px; }}
.stat .num {{ font-size:36px; font-weight:900; color:#c8b99a; }}
.nav-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}
.nav-card {{ background:#1a1a1a; border:1px solid #2a2a2a; padding:24px;
             border-radius:4px; text-decoration:none; color:white; transition:0.2s; }}
.nav-card:hover {{ border-color:#c8b99a; }}
.nav-card h3 {{ font-size:16px; margin-bottom:8px; }}
.nav-card p {{ color:#555; font-size:13px; }}
</style>
</head>
<body>
<header>
    <h1>VESTIQUE — لوحة التحكم</h1>
    <a href="/admin/logout" class="logout">تسجيل خروج</a>
</header>
<div class="container">
    <div class="stats">
        <div class="stat"><h3>المنتجات</h3><div class="num">{product_count}</div></div>
        <div class="stat"><h3>الطلبات</h3><div class="num">{order_count}</div></div>
        <div class="stat"><h3>المبيعات</h3><div class="num">{total:.0f} ر.س</div></div>
    </div>
    <div class="nav-grid">
        <a href="/admin/products" class="nav-card"><h3>📦 المنتجات</h3><p>إضافة وحذف المنتجات</p></a>
        <a href="/admin/categories" class="nav-card"><h3>📂 الفئات</h3><p>إدارة فئات المتجر</p></a>
        <a href="/admin/orders" class="nav-card"><h3>📋 الطلبات</h3><p>عرض وإدارة الطلبات</p></a>
    </div>
</div>
</body>
</html>'''
    return html
 
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin')
 
@app.route('/admin/products')
def admin_products():
    if not session.get('admin'):
        return redirect('/admin')
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY id DESC')
    products = c.fetchall()
    conn.close()
    rows = ''
    for p in products:
        rows += f'<tr><td>{p["id"]}</td><td>{p["name"]}</td><td>{p["price"]:.0f}</td><td>{p["category"]}</td><td>{p["stock"]}</td><td><a href="/admin/product/{p["id"]}/delete" onclick="return confirm(\'حذف؟\')" style="color:#e94560;">حذف</a></td></tr>'
    html = f'''<!DOCTYPE html><html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>المنتجات</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Tajawal',sans-serif;background:#0d0d0d;color:white}}
header{{background:#1a1a1a;padding:20px 40px;border-bottom:1px solid #2a2a2a}}
.container{{max-width:1100px;margin:0 auto;padding:40px 20px}}
.btn{{display:inline-block;padding:10px 24px;background:#f5f0eb;color:#0d0d0d;text-decoration:none;border-radius:2px;font-weight:700;font-size:13px;letter-spacing:1px;margin-bottom:24px;margin-left:10px}}
table{{width:100%;border-collapse:collapse;background:#1a1a1a;border-radius:4px;overflow:hidden}}
th{{background:#111;color:#888;padding:14px;text-align:right;font-size:12px;letter-spacing:1px}}
td{{padding:14px;border-bottom:1px solid #222;font-size:14px}}
tr:hover td{{background:#1f1f1f}}a{{color:#c8b99a}}</style>
</head><body>
<header><h1 style="font-size:18px;letter-spacing:2px;">إدارة المنتجات</h1></header>
<div class="container">
<a href="/admin/product/new" class="btn">+ منتج جديد</a>
<a href="/admin/dashboard" class="btn" style="background:#2a2a2a;color:white;">← رجوع</a>
<table><tr><th>ID</th><th>الاسم</th><th>السعر</th><th>الفئة</th><th>المخزون</th><th>حذف</th></tr>{rows}</table>
</div></body></html>'''
    return html
 
@app.route('/admin/product/new', methods=['GET', 'POST'])
def admin_product_new():
    if not session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO products (name,price,category,size,color,material,gender,description,stock) VALUES (?,?,?,?,?,?,?,?,?)',
            (request.form.get('name'), request.form.get('price'), request.form.get('category'),
             request.form.get('size'), request.form.get('color'), request.form.get('material'),
             request.form.get('gender'), request.form.get('description'), request.form.get('stock', 0)))
        conn.commit(); conn.close()
        return redirect('/admin/products')
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT name FROM categories')
    categories = [row['name'] for row in c.fetchall()]; conn.close()
    opts = ''.join([f'<option>{cat}</option>' for cat in categories])
    html = f'''<!DOCTYPE html><html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>منتج جديد</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Tajawal',sans-serif;background:#0d0d0d;color:white}}
header{{background:#1a1a1a;padding:20px 40px;border-bottom:1px solid #2a2a2a}}
.container{{max-width:560px;margin:40px auto;padding:0 20px}}
.box{{background:#1a1a1a;border:1px solid #2a2a2a;padding:32px;border-radius:4px}}
label{{display:block;color:#888;font-size:12px;letter-spacing:1px;margin-bottom:8px;text-transform:uppercase}}
input,select,textarea{{width:100%;padding:10px;background:#0d0d0d;border:1px solid #2a2a2a;color:white;border-radius:2px;font-size:14px;margin-bottom:20px;outline:none;font-family:Tajawal}}
input:focus,select:focus{{border-color:#c8b99a}}
button{{width:100%;padding:14px;background:#f5f0eb;color:#0d0d0d;border:none;border-radius:2px;font-weight:700;font-size:14px;letter-spacing:2px;cursor:pointer;text-transform:uppercase}}</style>
</head><body>
<header><h1 style="font-size:18px;letter-spacing:2px;">إضافة منتج جديد</h1></header>
<div class="container"><div class="box">
<form method="POST">
<label>اسم المنتج</label><input type="text" name="name" required>
<label>السعر (ر.س)</label><input type="number" name="price" step="0.01" required>
<label>الفئة</label><select name="category">{opts}</select>
<label>المقاس</label><input type="text" name="size" placeholder="S, M, L, XL">
<label>اللون</label><input type="text" name="color" placeholder="أسود, أبيض">
<label>المادة</label><input type="text" name="material">
<label>الجنس</label><select name="gender"><option>رجالي</option><option>نسائي</option><option>أطفال</option><option>موحد</option></select>
<label>الوصف</label><textarea name="description" rows="3"></textarea>
<label>المخزون</label><input type="number" name="stock" value="0">
<button type="submit">حفظ المنتج</button>
</form></div></div></body></html>'''
    return html
 
@app.route('/admin/product/<int:pid>/delete')
def admin_product_delete(pid):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (pid,))
    conn.commit(); conn.close()
    return redirect('/admin/products')
 
@app.route('/admin/categories')
def admin_categories():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM categories'); categories = c.fetchall(); conn.close()
    rows = ''.join([f'<tr><td>{cat["name"]}</td><td><a href="/admin/category/{cat["id"]}/delete" onclick="return confirm(\'حذف؟\')" style="color:#e94560;">حذف</a></td></tr>' for cat in categories])
    return f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>الفئات</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Tajawal',sans-serif;background:#0d0d0d;color:white}}
header{{background:#1a1a1a;padding:20px 40px;border-bottom:1px solid #2a2a2a}}
.container{{max-width:560px;margin:40px auto;padding:0 20px}}
.box{{background:#1a1a1a;border:1px solid #2a2a2a;padding:32px;border-radius:4px;margin-bottom:24px}}
input{{width:100%;padding:10px;background:#0d0d0d;border:1px solid #2a2a2a;color:white;border-radius:2px;font-size:14px;margin-bottom:16px;outline:none}}
button{{width:100%;padding:12px;background:#f5f0eb;color:#0d0d0d;border:none;border-radius:2px;font-weight:700;cursor:pointer}}
table{{width:100%;border-collapse:collapse;background:#1a1a1a;border-radius:4px}}
th{{background:#111;color:#888;padding:12px;text-align:right;font-size:12px}}
td{{padding:12px;border-bottom:1px solid #222}}</style>
</head><body><header><h1 style="font-size:18px;letter-spacing:2px;">إدارة الفئات</h1></header>
<div class="container">
<div class="box"><h3 style="margin-bottom:20px;color:#c8b99a;">إضافة فئة جديدة</h3>
<form method="POST" action="/admin/category/add"><input type="text" name="name" placeholder="اسم الفئة" required><button type="submit">إضافة</button></form></div>
<table><tr><th>الفئة</th><th>حذف</th></tr>{rows}</table>
</div></body></html>'''
 
@app.route('/admin/category/add', methods=['POST'])
def admin_category_add():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); c = conn.cursor()
    c.execute('INSERT INTO categories (name) VALUES (?)', (request.form.get('name'),))
    conn.commit(); conn.close()
    return redirect('/admin/categories')
 
@app.route('/admin/category/<int:cid>/delete')
def admin_category_delete(cid):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); c = conn.cursor()
    c.execute('DELETE FROM categories WHERE id = ?', (cid,))
    conn.commit(); conn.close()
    return redirect('/admin/categories')
 
@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY id DESC'); orders = c.fetchall(); conn.close()
    rows = ''.join([f'<tr><td>{o["id"]}</td><td>{o["customer_name"]}</td><td>{o["customer_phone"]}</td><td>{o["total_price"]:.0f}</td><td>{o["status"]}</td><td>{o["order_date"]}</td></tr>' for o in orders]) or '<tr><td colspan="6" style="text-align:center;color:#555;padding:40px;">لا توجد طلبات</td></tr>'
    return f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>الطلبات</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Tajawal',sans-serif;background:#0d0d0d;color:white}}
header{{background:#1a1a1a;padding:20px 40px;border-bottom:1px solid #2a2a2a}}
.container{{max-width:1100px;margin:40px auto;padding:0 20px}}
table{{width:100%;border-collapse:collapse;background:#1a1a1a;border-radius:4px}}
th{{background:#111;color:#888;padding:14px;text-align:right;font-size:12px;letter-spacing:1px}}
td{{padding:14px;border-bottom:1px solid #222;font-size:14px}}</style>
</head><body><header><h1 style="font-size:18px;letter-spacing:2px;">الطلبات</h1></header>
<div class="container"><table><tr><th>ID</th><th>العميل</th><th>الهاتف</th><th>الإجمالي</th><th>الحالة</th><th>التاريخ</th></tr>{rows}</table></div></body></html>'''
 
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    print('🚀 VESTIQUE starting...')
    app.run(debug=debug, host='0.0.0.0', port=port)
