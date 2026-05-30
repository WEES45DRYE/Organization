from flask import Flask, request, jsonify, redirect, session, make_response
import os, re, base64
from functools import wraps
from jinja2 import Environment
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "regal_secret_2025"

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def get_setting(key, default=''):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key=%s", (key,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row['value'] if row else default
    except:
        return default

def set_setting(key, value):
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value=%s",
                (key, value, value))
    conn.commit(); cur.close(); conn.close()

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '👔',
            type TEXT DEFAULT 'main'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            old_price REAL,
            stock INTEGER DEFAULT 0,
            category_id INTEGER,
            image_url TEXT DEFAULT '',
            unit TEXT DEFAULT 'قطعة',
            sizes TEXT DEFAULT 'S,M,L,XL',
            featured INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer_name TEXT,
            customer_phone TEXT,
            customer_city TEXT,
            customer_address TEXT,
            notes TEXT,
            total REAL,
            shipping REAL DEFAULT 35,
            status TEXT DEFAULT 'جديد',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            qty INTEGER,
            price REAL,
            size TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT UNIQUE,
            city TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed data only if empty
    cur.execute("SELECT COUNT(*) FROM categories")
    count = cur.fetchone()['count']
    if count == 0:
        cats = [
            ("قمصان", "👔", "main"),
            ("بناطيل", "👖", "main"),
            ("جاكيتات", "🧥", "main"),
            ("أحذية", "👟", "main"),
            ("إكسسوار", "⌚", "main"),
            ("داخلية ورياضي", "🩱", "main"),
            ("العروض", "🏷️", "promo"),
        ]
        for c in cats:
            cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s)", c)

        products = [
            ("قميص أكسفورد كلاسيك",   "100% قطن مصري، مثالي للعمل والمناسبات", 249, 320,  50, 1, "قطعة", "S,M,L,XL,XXL", 1),
            ("قميص كاجوال مخطط",       "قماش ناعم مريح للاستخدام اليومي",       179, None, 40, 1, "قطعة", "S,M,L,XL",     1),
            ("بنطلون سليم فيت",        "قصة عصرية من قماش عالي الجودة",          389, None, 35, 2, "قطعة", "28,30,32,34,36",1),
            ("بنطلون جينز فاتح",       "جينز مريح بقصة كلاسيكية",               299, 380,  45, 2, "قطعة", "28,30,32,34,36",1),
            ("جاكيت كاجوال شتوي",      "دافئ وأنيق لكل المناسبات",              699, 850,  20, 3, "قطعة", "S,M,L,XL",     1),
            ("بليزر رسمي",             "تفصيل احترافي من قماش فاخر",             950, None, 15, 3, "قطعة", "46,48,50,52",  0),
            ("حذاء لوفر جلد",          "جلد طبيعي بتفصيل يدوي",                 550, None, 30, 4, "قطعة", "40,41,42,43,44,45", 1),
            ("حذاء رياضي",             "خفيف ومريح لكل الأوقات",                320, 420,  40, 4, "قطعة", "40,41,42,43,44,45", 1),
            ("ساعة يد كلاسيكية",       "سوار جلدي وإطار ستانلس ستيل ضد الماء", 850, None, 25, 5, "قطعة", "مقاس واحد",    1),
            ("حزام جلد طبيعي",         "إبزيم معدني أنيق متعدد الألوان",        120, 150,  60, 5, "قطعة", "S,M,L,XL",    0),
            ("تيشيرت بولو بريميوم",    "قطن بيما 100% ناعم ومريح",              179, 220,  55, 1, "قطعة", "S,M,L,XL,XXL", 1),
            ("شورت رياضي",             "مايكروفايبر سريع الجفاف",               149, None, 50, 6, "قطعة", "S,M,L,XL",    0),
        ]
        for p in products:
            cur.execute("""INSERT INTO products
                (name,description,price,old_price,stock,category_id,unit,sizes,featured)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", p)

        cur.execute("INSERT INTO admins (username,password) VALUES (%s,%s) ON CONFLICT DO NOTHING", ('admin','admin123'))

        defaults = [
            ('logo_type','emoji'), ('logo_emoji','👔'), ('logo_image',''),
            ('banner_image',''), ('site_name','ريجال'),
            ('site_subtitle','متجر الأزياء الرجالية'),
            ('shipping_cost','35'), ('free_shipping_from','500'),
            ('whatsapp',''), ('n8n_webhook',''), ('n8n_secret',''),
        ]
        for k,v in defaults:
            cur.execute("INSERT INTO settings (key,value) VALUES (%s,%s) ON CONFLICT DO NOTHING", (k,v))

    conn.commit(); cur.close(); conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated

jinja_env = Environment()

def render(tmpl_str, **ctx):
    ctx['session'] = session
    t = jinja_env.from_string(tmpl_str)
    return make_response(t.render(**ctx))

# ═══════════════════════════════════════════════
# STATIC UPLOADS
# ═══════════════════════════════════════════════
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ═══════════════════════════════════════════════
# API — PUBLIC
# ═══════════════════════════════════════════════
@app.route("/api/categories")
def api_categories():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY id")
    cats = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in cats])

@app.route("/api/products")
def api_products():
    cat    = request.args.get("category")
    search = request.args.get("search", "")
    conn = get_db(); cur = conn.cursor()
    q = "SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id"
    params = []
    wheres = []
    if cat:
        wheres.append("p.category_id=%s"); params.append(cat)
    if search:
        wheres.append("p.name ILIKE %s"); params.append(f"%{search}%")
    if wheres:
        q += " WHERE " + " AND ".join(wheres)
    q += " ORDER BY p.id DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/products/featured")
def api_featured():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.featured=1 ORDER BY p.id DESC LIMIT 12")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/settings")
def api_settings():
    keys = ['site_name','site_subtitle','logo_type','logo_emoji','logo_image',
            'banner_image','shipping_cost','free_shipping_from']
    return jsonify({k: get_setting(k) for k in keys})

@app.route("/api/orders", methods=["POST"])
def api_place_order():
    data = request.json
    shipping_cost = float(get_setting('shipping_cost', '35'))
    free_from = float(get_setting('free_shipping_from', '500'))
    subtotal = sum(i['price'] * i['qty'] for i in data['items'])
    shipping = 0 if subtotal >= free_from else shipping_cost

    conn = get_db(); cur = conn.cursor()
    cur.execute("""INSERT INTO orders
        (customer_name,customer_phone,customer_city,customer_address,notes,total,shipping)
        VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data.get("name"), data.get("phone"), data.get("city",""),
         data.get("address"), data.get("notes",""),
         subtotal + shipping, shipping))
    oid = cur.fetchone()['id']

    for item in data['items']:
        cur.execute("""INSERT INTO order_items
            (order_id,product_id,product_name,qty,price,size)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (oid, item.get("id"), item.get("name"), item.get("qty"),
             item.get("price"), item.get("size","")))

    try:
        cur.execute("INSERT INTO customers (name,phone,city,address) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (data.get("name"), data.get("phone"), data.get("city",""), data.get("address","")))
    except: pass

    conn.commit(); cur.close(); conn.close()

    # ── n8n webhook (اختياري) ───────────────────────
    webhook = get_setting('n8n_webhook', '')
    if webhook:
        try:
            import urllib.request, json as _json
            payload = _json.dumps({
                "event": "new_order",
                "order_id": oid,
                "customer": data.get("name"),
                "phone": data.get("phone"),
                "city": data.get("city",""),
                "total": subtotal + shipping,
                "items": data.get("items",[]),
            }).encode()
            req = urllib.request.Request(webhook, data=payload,
                headers={"Content-Type":"application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=5)
        except: pass

    return jsonify({"success": True, "order_id": oid})

# ═══════════════════════════════════════════════
# MCP WEBHOOK  (لربط Claude MCP أو أي نظام خارجي)
# POST /api/mcp  — يقبل actions: list_products, list_orders,
#                  update_order_status, add_product
# ═══════════════════════════════════════════════
@app.route("/api/mcp", methods=["POST"])
def api_mcp():
    secret = get_setting('n8n_secret', '')
    if secret:
        auth = request.headers.get('X-Secret', '') or request.json.get('secret','')
        if auth != secret:
            return jsonify({"error": "unauthorized"}), 401

    data = request.json
    action = data.get('action', '')

    conn = get_db(); cur = conn.cursor()

    if action == 'list_products':
        cur.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC LIMIT 50")
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"products": rows})

    elif action == 'list_orders':
        limit = int(data.get('limit', 20))
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT %s", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"orders": rows})

    elif action == 'get_order':
        oid = data.get('order_id')
        cur.execute("SELECT * FROM orders WHERE id=%s", (oid,))
        order = dict(cur.fetchone() or {})
        cur.execute("SELECT * FROM order_items WHERE order_id=%s", (oid,))
        items = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"order": order, "items": items})

    elif action == 'update_order_status':
        oid    = data.get('order_id')
        status = data.get('status')
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, oid))
        conn.commit(); cur.close(); conn.close()
        return jsonify({"success": True})

    elif action == 'add_product':
        p = data.get('product', {})
        cur.execute("""INSERT INTO products
            (name,description,price,old_price,stock,category_id,unit,sizes,featured)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (p.get('name'), p.get('description',''), float(p.get('price',0)),
             float(p.get('old_price')) if p.get('old_price') else None,
             int(p.get('stock',0)), int(p.get('category_id',1)),
             p.get('unit','قطعة'), p.get('sizes','S,M,L,XL'),
             1 if p.get('featured') else 0))
        new_id = cur.fetchone()['id']
        conn.commit(); cur.close(); conn.close()
        return jsonify({"success": True, "product_id": new_id})

    elif action == 'stats':
        cur.execute("SELECT COUNT(*) FROM products"); p = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM orders");   o = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='جديد'"); n = cur.fetchone()['count']
        cur.execute("SELECT COALESCE(SUM(total),0) FROM orders"); r = cur.fetchone()['coalesce']
        cur.execute("SELECT COUNT(*) FROM customers"); c = cur.fetchone()['count']
        cur.close(); conn.close()
        return jsonify({"products":p,"orders":o,"new_orders":n,"revenue":float(r),"customers":c})

    cur.close(); conn.close()
    return jsonify({"error": "unknown action"}), 400

# ═══════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (u,p))
        admin = cur.fetchone()
        cur.close(); conn.close()
        if admin:
            session["admin"] = u
            return redirect("/admin")
        error = "اسم المستخدم أو كلمة المرور غلط"
    return render(TMPL_LOGIN, error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")

@app.route("/admin")
@login_required
def admin_index():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products"); sp = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM orders");   so = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='جديد'"); sn = cur.fetchone()['count']
    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders"); sr = cur.fetchone()['coalesce']
    cur.execute("SELECT COUNT(*) FROM customers"); sc = cur.fetchone()['count']
    stats = {"products":sp,"orders":so,"new_orders":sn,"revenue":sr,"customers":sc}
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 7")
    recent_orders = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_INDEX, stats=stats, orders=recent_orders)

@app.route("/admin/products")
@login_required
def admin_products():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC")
    products = cur.fetchall()
    cur.execute("SELECT * FROM categories ORDER BY id")
    categories = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_PRODUCTS, products=products, categories=categories)

@app.route("/admin/products/add", methods=["POST"])
@login_required
def admin_add_product():
    f = request.form
    image_url = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f'/static/uploads/{filename}'
    conn = get_db(); cur = conn.cursor()
    cur.execute("""INSERT INTO products
        (name,description,price,old_price,stock,category_id,unit,sizes,featured,image_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (f["name"], f.get("description",""), float(f["price"]),
         float(f["old_price"]) if f.get("old_price") else None,
         int(f["stock"]), int(f["category_id"]), f["unit"],
         f.get("sizes","S,M,L,XL"),
         1 if f.get("featured") else 0, image_url))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/edit/<int:pid>", methods=["POST"])
@login_required
def admin_edit_product(pid):
    f = request.form
    new_image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_image_url = f'/static/uploads/{filename}'
    conn = get_db(); cur = conn.cursor()
    if new_image_url:
        cur.execute("""UPDATE products SET
            name=%s,description=%s,price=%s,old_price=%s,stock=%s,
            category_id=%s,unit=%s,sizes=%s,featured=%s,image_url=%s WHERE id=%s""",
            (f["name"], f.get("description",""), float(f["price"]),
             float(f["old_price"]) if f.get("old_price") else None,
             int(f["stock"]), int(f["category_id"]), f["unit"],
             f.get("sizes","S,M,L,XL"),
             1 if f.get("featured") else 0, new_image_url, pid))
    else:
        cur.execute("""UPDATE products SET
            name=%s,description=%s,price=%s,old_price=%s,stock=%s,
            category_id=%s,unit=%s,sizes=%s,featured=%s WHERE id=%s""",
            (f["name"], f.get("description",""), float(f["price"]),
             float(f["old_price"]) if f.get("old_price") else None,
             int(f["stock"]), int(f["category_id"]), f["unit"],
             f.get("sizes","S,M,L,XL"),
             1 if f.get("featured") else 0, pid))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/delete/<int:pid>")
@login_required
def admin_delete_product(pid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/categories")
@login_required
def admin_categories():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT c.*,(SELECT COUNT(*) FROM products WHERE category_id=c.id) as count FROM categories c ORDER BY c.id")
    cats = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_CATS, categories=cats)

@app.route("/admin/categories/add", methods=["POST"])
@login_required
def admin_add_category():
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s)",
        (request.form["name"], request.form["icon"], request.form.get("type","main")))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/categories")

@app.route("/admin/categories/edit/<int:cid>", methods=["POST"])
@login_required
def admin_edit_category(cid):
    f = request.form
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE categories SET name=%s,icon=%s,type=%s WHERE id=%s",
        (f["name"], f["icon"], f.get("type","main"), cid))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/categories")

@app.route("/admin/categories/delete/<int:cid>")
@login_required
def admin_delete_category(cid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE products SET category_id=NULL WHERE category_id=%s", (cid,))
    cur.execute("DELETE FROM categories WHERE id=%s", (cid,))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/categories")

@app.route("/admin/orders")
@login_required
def admin_orders():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_ORDERS, orders=orders)

@app.route("/admin/orders/<int:oid>")
@login_required
def admin_order_detail(oid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=%s", (oid,))
    order = cur.fetchone()
    cur.execute("SELECT * FROM order_items WHERE order_id=%s", (oid,))
    items = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_ORDER_DETAIL, order=order, items=items)

@app.route("/admin/orders/status/<int:oid>", methods=["POST"])
@login_required
def admin_update_status(oid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (request.form["status"], oid))
    conn.commit(); cur.close(); conn.close()
    return redirect(f"/admin/orders/{oid}")

@app.route("/admin/customers")
@login_required
def admin_customers():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY created_at DESC")
    customers = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_CUSTOMERS, customers=customers)

@app.route("/admin/settings")
@login_required
def admin_settings():
    keys = ['logo_type','logo_emoji','logo_image','banner_image','site_name',
            'site_subtitle','shipping_cost','free_shipping_from',
            'whatsapp','n8n_webhook','n8n_secret']
    settings = {k: get_setting(k) for k in keys}
    return render(TMPL_ADMIN_SETTINGS, settings=settings)

@app.route("/admin/settings/save", methods=["POST"])
@login_required
def admin_settings_save():
    f = request.form
    for key in ['site_name','site_subtitle','shipping_cost','free_shipping_from',
                'whatsapp','n8n_webhook','n8n_secret']:
        if f.get(key) is not None:
            set_setting(key, f.get(key,''))
    logo_type = f.get('logo_type', 'emoji')
    set_setting('logo_type', logo_type)
    if logo_type == 'emoji' and f.get('logo_emoji'):
        set_setting('logo_emoji', f['logo_emoji'])
    if logo_type == 'image' and 'logo_image' in request.files:
        file = request.files['logo_image']
        if file and file.filename and allowed_file(file.filename):
            filename = 'logo_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            set_setting('logo_image', f'/static/uploads/{filename}')
    if 'banner_image' in request.files:
        file = request.files['banner_image']
        if file and file.filename and allowed_file(file.filename):
            filename = 'banner_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            set_setting('banner_image', f'/static/uploads/{filename}')
    if f.get('remove_banner'):    set_setting('banner_image', '')
    if f.get('remove_logo_image'): set_setting('logo_image', ''); set_setting('logo_type', 'emoji')
    return redirect("/admin/settings")

@app.route("/")
def index():
    settings = {k: get_setting(k) for k in
        ['logo_type','logo_emoji','logo_image','banner_image',
         'site_name','site_subtitle','shipping_cost','free_shipping_from']}
    return render(TMPL_APP, **settings)

@app.before_request
def setup():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

_db_initialized = False

# ═══════════════════════════════════════════════
# TEMPLATES
# ═══════════════════════════════════════════════

TMPL_APP = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>{{ site_name }} - {{ site_subtitle }}</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{
  --navy:#0d1b2a;--navy2:#1b2d42;
  --gold:#c9a84c;--gold2:#e8c96b;
  --bg:#f4f2ee;--card:#fff;--text:#0d1b2a;
  --gray:#7a7a7a;--border:#e8e5df;--red:#e05252;
}
body{font-family:'Cairo',sans-serif;background:var(--bg);color:var(--text);max-width:430px;margin:0 auto;min-height:100vh}
/* Header */
.header{background:var(--navy);color:#fff;position:sticky;top:0;z-index:200;box-shadow:0 2px 10px rgba(0,0,0,.3)}
.header-top{display:flex;align-items:center;gap:10px;padding:10px 14px}
.logo{display:flex;align-items:center;gap:8px;text-decoration:none;color:#fff;flex-shrink:0;cursor:pointer}
.logo-icon{width:36px;height:36px;background:var(--gold);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;overflow:hidden;flex-shrink:0}
.logo-icon img{width:100%;height:100%;object-fit:contain;padding:3px}
.logo-text{font-size:17px;font-weight:900;line-height:1.1;letter-spacing:.5px}
.logo-sub{font-size:9px;opacity:.6;font-weight:400;letter-spacing:2px;text-transform:uppercase}
.search-bar{flex:1;display:flex;background:rgba(255,255,255,.12);border-radius:8px;padding:0 12px;align-items:center;gap:8px}
.search-bar input{flex:1;background:none;border:none;outline:none;color:#fff;font-family:'Cairo',sans-serif;font-size:13px;padding:9px 0}
.search-bar input::placeholder{color:rgba(255,255,255,.5)}
.header-actions{display:flex;gap:8px;flex-shrink:0}
.hbtn{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);color:#fff;padding:7px 11px;border-radius:8px;cursor:pointer;font-size:12px;font-family:'Cairo',sans-serif;display:flex;align-items:center;gap:5px;position:relative}
.badge{background:var(--gold);color:var(--navy);border-radius:50%;width:17px;height:17px;font-size:10px;display:flex;align-items:center;justify-content:center;position:absolute;top:-5px;right:-5px;font-weight:700}
/* Nav */
.cat-nav{background:var(--navy2);display:flex;overflow-x:auto;scrollbar-width:none;border-top:1px solid rgba(255,255,255,.06)}
.cat-nav::-webkit-scrollbar{display:none}
.cat-nav a{color:rgba(255,255,255,.7);text-decoration:none;padding:9px 14px;font-size:12px;white-space:nowrap;border-bottom:2px solid transparent;transition:.2s;font-family:'Cairo',sans-serif}
.cat-nav a:hover,.cat-nav a.active{color:#fff;border-bottom-color:var(--gold)}
/* Pages */
.page{display:none;padding-bottom:75px}
.page.active{display:block}
/* Hero */
.hero{background:var(--navy);padding:22px 18px;position:relative;overflow:hidden;min-height:170px;display:flex;align-items:center}
.hero::before{content:'';position:absolute;top:-40px;right:-30px;width:220px;height:220px;background:radial-gradient(circle,rgba(201,168,76,.2) 0%,transparent 70%);pointer-events:none}
.hero-content{position:relative;z-index:1;flex:1}
.hero-tag{background:var(--gold);color:var(--navy);font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;display:inline-block;margin-bottom:10px;letter-spacing:.5px}
.hero h2{font-size:20px;font-weight:900;color:#fff;margin-bottom:6px;line-height:1.35}
.hero p{font-size:12px;color:rgba(255,255,255,.65);margin-bottom:14px;line-height:1.6}
.hero-tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.hero-chip{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.85);font-size:11px;padding:3px 10px;border-radius:20px}
.hero-btn{background:var(--gold);color:var(--navy);border:none;padding:9px 22px;border-radius:22px;font-weight:700;cursor:pointer;font-size:13px;font-family:'Cairo',sans-serif}
.hero-emoji{font-size:90px;opacity:.12;position:absolute;left:-5px;bottom:-10px;transform:rotate(-15deg)}
.banner-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.25;z-index:0}
/* Sections */
.section{padding:14px 14px 0}
.sec-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.sec-title{font-size:15px;font-weight:700;display:flex;align-items:center;gap:6px}
.sec-title::before{content:'';width:3px;height:16px;background:var(--gold);border-radius:2px;display:inline-block}
.sec-link{color:var(--gold);font-size:12px;cursor:pointer;font-weight:600}
/* Categories horizontal */
.cats{display:flex;gap:10px;overflow-x:auto;padding-bottom:6px;scrollbar-width:none}
.cats::-webkit-scrollbar{display:none}
.cat-card{min-width:74px;background:var(--card);border-radius:14px;padding:11px 6px;text-align:center;cursor:pointer;border:2px solid transparent;transition:.2s;box-shadow:0 1px 5px rgba(0,0,0,.06);flex-shrink:0}
.cat-card.active,.cat-card:hover{border-color:var(--gold);background:#fdf8ec}
.cat-icon{font-size:24px}
.cat-name{font-size:10px;margin-top:4px;color:var(--gray);font-weight:600}
.cat-card.active .cat-name{color:var(--navy);font-weight:700}
/* Products */
.products-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.prod-card{background:var(--card);border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.07);cursor:pointer;transition:.2s;position:relative}
.prod-card:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.12)}
.prod-badge{position:absolute;top:8px;right:8px;background:var(--red);color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;z-index:1}
.prod-badge.new-b{background:var(--navy)}
.fav-btn{position:absolute;top:8px;left:8px;background:rgba(255,255,255,.85);border:none;border-radius:50%;width:28px;height:28px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;z-index:1}
.prod-img{height:130px;background:linear-gradient(145deg,#eae8e2,#d5d0c6);display:flex;align-items:center;justify-content:center;font-size:54px;overflow:hidden;position:relative}
.prod-img img{width:100%;height:100%;object-fit:contain;padding:10px}
.prod-info{padding:10px 10px 12px}
.prod-brand{font-size:10px;color:var(--gray);margin-bottom:2px;font-weight:600;letter-spacing:.3px;text-transform:uppercase}
.prod-name{font-size:12px;font-weight:700;margin-bottom:6px;line-height:1.4}
.prod-prices{display:flex;align-items:baseline;gap:5px;margin-bottom:8px}
.prod-price{color:var(--navy);font-weight:900;font-size:15px}
.prod-old{color:#bbb;font-size:11px;text-decoration:line-through}
.add-btn{width:100%;background:var(--navy);color:#fff;border:none;border-radius:9px;padding:7px;cursor:pointer;font-size:12px;font-weight:600;transition:.15s;font-family:'Cairo',sans-serif}
.add-btn:hover{background:var(--navy2)}
/* Cart */
.cart-item{background:#fff;border-radius:14px;padding:13px;margin-bottom:10px;display:flex;gap:11px;align-items:center;box-shadow:0 1px 5px rgba(0,0,0,.06)}
.cart-img{width:58px;height:58px;border-radius:10px;background:linear-gradient(145deg,#eae8e2,#d5d0c6);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0;overflow:hidden}
.cart-img img{width:100%;height:100%;object-fit:contain;padding:5px}
.cart-info{flex:1}
.cart-name{font-size:13px;font-weight:700}
.cart-size{font-size:11px;color:var(--gray);margin-top:1px}
.cart-price{font-size:13px;color:var(--navy);font-weight:700;margin-top:3px}
.qty-row{display:flex;align-items:center;gap:10px;margin-top:6px}
.qty-btn{background:var(--bg);border:1px solid var(--border);width:27px;height:27px;border-radius:50%;cursor:pointer;font-size:15px;display:flex;align-items:center;justify-content:center;font-weight:700}
.cart-del{background:none;border:none;cursor:pointer;font-size:19px;color:#ddd;transition:.15s}
.cart-del:hover{color:var(--red)}
.cart-summary{background:#fff;border-radius:16px;padding:16px;margin-bottom:10px;box-shadow:0 1px 6px rgba(0,0,0,.07)}
.sum-row{display:flex;justify-content:space-between;padding:6px 0;font-size:13px}
.sum-row.final{font-weight:700;font-size:16px;color:var(--navy);border-top:1px solid var(--border);margin-top:6px;padding-top:12px}
.checkout-btn{width:100%;background:var(--navy);color:#fff;border:none;border-radius:13px;padding:14px;font-size:15px;font-weight:700;margin-top:12px;cursor:pointer;font-family:'Cairo',sans-serif}
.empty{text-align:center;padding:55px 20px;color:var(--gray)}
.empty-icon{font-size:60px;margin-bottom:12px}
/* Modal */
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:300;justify-content:flex-end;flex-direction:column}
.overlay.open{display:flex}
.sheet{background:#fff;border-radius:22px 22px 0 0;padding:22px 18px;max-height:88vh;overflow-y:auto}
.sheet-handle{width:40px;height:4px;background:var(--border);border-radius:2px;margin:0 auto 16px}
.sheet-title{font-size:17px;font-weight:700;margin-bottom:18px;text-align:center}
.fg{margin-bottom:13px}
.fg label{display:block;font-size:12px;color:var(--gray);margin-bottom:4px;font-weight:600}
.fg input,.fg select,.fg textarea{width:100%;border:1.5px solid var(--border);border-radius:11px;padding:10px 13px;font-size:14px;font-family:'Cairo',sans-serif;outline:none;transition:.2s;background:#fff;color:var(--text)}
.fg input:focus,.fg select:focus{border-color:var(--gold)}
.order-preview{background:#f8f6f1;border-radius:10px;padding:12px;margin-bottom:13px;font-size:12px;color:#555;line-height:1.8}
.submit-btn{width:100%;background:var(--navy);color:#fff;border:none;border-radius:13px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;margin-top:5px;font-family:'Cairo',sans-serif}
.cancel-btn{width:100%;background:none;border:none;padding:10px;color:var(--gray);cursor:pointer;font-family:'Cairo',sans-serif}
/* Sizes */
.sizes{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 14px}
.sz{padding:6px 14px;border-radius:8px;border:1.5px solid var(--border);background:#fff;cursor:pointer;font-size:13px;font-family:'Cairo',sans-serif;font-weight:600;transition:.15s}
.sz:hover,.sz.active{border-color:var(--navy);background:var(--navy);color:#fff}
/* Orders */
.order-card{background:#fff;border-radius:15px;padding:14px;margin-bottom:10px;box-shadow:0 1px 5px rgba(0,0,0,.06)}
.order-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.order-num{font-weight:700;color:var(--navy);font-size:14px}
.status-pill{padding:3px 11px;border-radius:20px;font-size:11px;font-weight:700}
.s-new{background:#e8f0fe;color:#1a56c0}
.s-process{background:#fff3e0;color:#c66800}
.s-done{background:#e6f4ea;color:#1a7a3a}
.s-cancel{background:#ffebee;color:#c62828}
.order-date{font-size:11px;color:var(--gray);margin-bottom:5px}
.order-items-txt{font-size:12px;color:var(--gray);margin-bottom:8px;line-height:1.7}
.order-footer{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border);padding-top:10px}
/* Profile */
.profile-hero{background:var(--navy);padding:26px 20px;text-align:center;margin-bottom:14px;position:relative;overflow:hidden}
.profile-hero::before{content:'';position:absolute;top:-50px;right:-40px;width:160px;height:160px;background:radial-gradient(circle,rgba(201,168,76,.25) 0%,transparent 70%)}
.profile-avatar{width:70px;height:70px;background:rgba(201,168,76,.2);border:2px solid rgba(201,168,76,.4);border-radius:50%;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:30px;position:relative}
.menu-card{background:#fff;border-radius:14px;margin:0 14px 10px;box-shadow:0 1px 5px rgba(0,0,0,.05);overflow:hidden}
.menu-item{padding:13px 15px;display:flex;align-items:center;gap:12px;cursor:pointer;border-bottom:1px solid var(--border);transition:.15s}
.menu-item:last-child{border-bottom:none}
.menu-item:hover{background:#faf8f2}
.menu-icon{width:34px;height:34px;border-radius:9px;background:var(--bg);display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0}
.menu-text{flex:1;font-size:13px;font-weight:600}
.menu-arrow{color:#ccc;font-size:14px}
/* Toast */
.toast{position:fixed;bottom:85px;left:50%;transform:translateX(-50%);background:var(--navy);color:#fff;padding:10px 22px;border-radius:22px;font-size:13px;font-weight:700;opacity:0;transition:.3s;z-index:500;pointer-events:none;white-space:nowrap;border:1px solid rgba(201,168,76,.4);font-family:'Cairo',sans-serif}
.toast.show{opacity:1}
/* Bottom nav */
.bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:430px;background:var(--navy);display:flex;z-index:200;border-top:1px solid rgba(255,255,255,.06)}
.nav-btn{flex:1;padding:10px 0;border:none;background:none;cursor:pointer;color:rgba(255,255,255,.4);display:flex;flex-direction:column;align-items:center;font-size:10px;gap:3px;font-family:'Cairo',sans-serif;transition:.2s}
.nav-btn .ico{font-size:21px}
.nav-btn.active{color:var(--gold)}
/* Spinner */
.spinner{width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--navy);border-radius:50%;animation:spin .8s linear infinite;margin:35px auto}
@keyframes spin{to{transform:rotate(360deg)}}
/* detail */
.detail-img{height:180px;background:linear-gradient(145deg,#eae8e2,#d5d0c6);display:flex;align-items:center;justify-content:center;font-size:88px;border-radius:14px;margin-bottom:14px;overflow:hidden}
.detail-img img{width:100%;height:100%;object-fit:contain;padding:12px}
/* Wishlist */
.wish-item{background:#fff;border-radius:13px;padding:12px;display:flex;gap:11px;margin-bottom:9px;align-items:center;box-shadow:0 1px 5px rgba(0,0,0,.06)}
.wish-img{width:54px;height:54px;border-radius:9px;background:linear-gradient(145deg,#eae8e2,#d5d0c6);display:flex;align-items:center;justify-content:center;font-size:25px;flex-shrink:0;overflow:hidden}
.wish-img img{width:100%;height:100%;object-fit:contain;padding:4px}
/* Free shipping bar */
.free-bar{background:linear-gradient(90deg,#1b2d42,#0d1b2a);margin:12px 14px 0;border-radius:12px;padding:10px 14px;display:flex;align-items:center;gap:10px;font-size:12px;color:rgba(255,255,255,.8)}
.free-bar-track{flex:1;height:5px;background:rgba(255,255,255,.15);border-radius:3px;overflow:hidden}
.free-bar-fill{height:100%;background:var(--gold);border-radius:3px;transition:.4s}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-top">
    <div class="logo" onclick="showPage('home')">
      <div class="logo-icon">
        {% if logo_type == 'image' and logo_image %}
          <img src="{{ logo_image }}" alt="logo">
        {% else %}
          {{ logo_emoji or '👔' }}
        {% endif %}
      </div>
      <div>
        <div class="logo-text">{{ site_name or 'ريجال' }}</div>
        <div class="logo-sub">{{ site_subtitle or 'MENSWEAR' }}</div>
      </div>
    </div>
    <div class="search-bar">
      <span style="font-size:16px;opacity:.6">🔍</span>
      <input type="text" placeholder="ابحث عن منتج..." id="search-input" oninput="doSearch(this.value)">
    </div>
    <div class="header-actions">
      <button class="hbtn" onclick="showPage('cart')">
        🛒
        <div class="badge" id="cart-badge" style="display:none">0</div>
      </button>
    </div>
  </div>
  <nav class="cat-nav" id="cat-nav"></nav>
</div>

<!-- HOME PAGE -->
<div class="page active" id="page-home">
  <div class="hero">
    {% if banner_image %}
    <img class="banner-bg" src="{{ banner_image }}" alt="">
    {% else %}
    <div class="hero-emoji">👔</div>
    {% endif %}
    <div class="hero-content">
      <div class="hero-tag">🔥 أحدث التصاميم</div>
      <h2>الأناقة الرجالية<br>بمعاييرك أنت</h2>
      <p>أرقى الأقمشة وأحدث الصيحات لموسم 2025</p>
      <div class="hero-tags">
        <span class="hero-chip">✅ ماركات أصلية</span>
        <span class="hero-chip">🚚 توصيل سريع</span>
        <span class="hero-chip">↩️ إرجاع مجاني</span>
      </div>
      <button class="hero-btn" onclick="filterCat(0,null)">تسوق الآن ◀</button>
    </div>
  </div>

  <div id="free-shipping-bar" style="display:none" class="free-bar">
    <span>🚚</span>
    <div>
      <div id="free-bar-text"></div>
      <div class="free-bar-track"><div class="free-bar-fill" id="free-bar-fill" style="width:0%"></div></div>
    </div>
  </div>

  <div class="section">
    <div class="sec-row"><span class="sec-title">الأقسام</span></div>
    <div class="cats" id="cats-list"><div class="spinner"></div></div>
  </div>

  <div class="section" style="margin-top:14px">
    <div class="sec-row">
      <span class="sec-title" id="prod-title">منتجات مميزة</span>
      <span class="sec-link" onclick="filterCat(0,null)">الكل</span>
    </div>
    <div class="products-grid" id="products-grid"><div class="spinner"></div></div>
  </div>
</div>

<!-- CART PAGE -->
<div class="page" id="page-cart">
  <div style="padding:14px 14px 8px;font-size:15px;font-weight:700">🛒 سلة التسوق</div>
  <div style="padding:0 14px" id="cart-list"></div>
  <div style="padding:0 14px" id="cart-total-box"></div>
</div>

<!-- ORDERS PAGE -->
<div class="page" id="page-orders">
  <div style="padding:14px 14px 8px;font-size:15px;font-weight:700">📦 طلباتي</div>
  <div style="padding:0 14px" id="orders-list"></div>
</div>

<!-- PROFILE PAGE -->
<div class="page" id="page-profile">
  <div class="profile-hero">
    <div class="profile-avatar">👤</div>
    <div style="font-size:17px;font-weight:700;color:#fff;position:relative">أهلاً بك!</div>
    <div style="font-size:12px;color:rgba(255,255,255,.5);margin-top:3px;position:relative">{{ site_name }}</div>
  </div>
  <div class="menu-card">
    <div class="menu-item" onclick="showPage('orders')">
      <div class="menu-icon">📦</div><div class="menu-text">طلباتي</div><div class="menu-arrow">‹</div>
    </div>
    <div class="menu-item" onclick="showWishlist()">
      <div class="menu-icon">❤️</div><div class="menu-text">المفضلة</div><div class="menu-arrow">‹</div>
    </div>
    <div class="menu-item">
      <div class="menu-icon">📏</div><div class="menu-text">دليل المقاسات</div><div class="menu-arrow">‹</div>
    </div>
    <div class="menu-item">
      <div class="menu-icon">🚚</div><div class="menu-text">تتبع الشحنة</div><div class="menu-arrow">‹</div>
    </div>
  </div>
  <div class="menu-card">
    <div class="menu-item">
      <div class="menu-icon">📞</div><div class="menu-text">تواصل معنا</div><div class="menu-arrow">‹</div>
    </div>
    <div class="menu-item">
      <div class="menu-icon">⭐</div><div class="menu-text">قيّم التطبيق</div><div class="menu-arrow">‹</div>
    </div>
    <div class="menu-item">
      <div class="menu-icon">ℹ️</div><div class="menu-text">عن المتجر</div><div class="menu-arrow">‹</div>
    </div>
  </div>
</div>

<!-- Bottom Nav -->
<div class="bottom-nav">
  <button class="nav-btn active" onclick="showPage('home')"><span class="ico">🏠</span>الرئيسية</button>
  <button class="nav-btn" onclick="showPage('cart')"><span class="ico">🛒</span>السلة</button>
  <button class="nav-btn" onclick="showPage('orders')"><span class="ico">📦</span>طلباتي</button>
  <button class="nav-btn" onclick="showPage('profile')"><span class="ico">👤</span>حسابي</button>
</div>

<!-- Order Modal -->
<div class="overlay" id="order-overlay">
  <div class="sheet">
    <div class="sheet-handle"></div>
    <div class="sheet-title">🛒 إتمام الطلب</div>
    <div class="fg"><label>الاسم الكريم</label><input id="f-name" type="text" placeholder="مثال: محمد أحمد"></div>
    <div class="fg"><label>رقم الهاتف</label><input id="f-phone" type="tel" placeholder="01xxxxxxxxx"></div>
    <div class="fg"><label>المدينة</label>
      <select id="f-city">
        <option value="">اختر المدينة</option>
        <option>القاهرة</option><option>الجيزة</option><option>الإسكندرية</option>
        <option>المنصورة</option><option>طنطا</option><option>الزقازيق</option>
        <option>الإسماعيلية</option><option>بورسعيد</option><option>الأقصر</option>
        <option>أسوان</option><option>أسيوط</option><option>مدينة أخرى</option>
      </select>
    </div>
    <div class="fg"><label>عنوان التوصيل</label>
      <textarea id="f-address" rows="2" style="resize:none;width:100%;border:1.5px solid var(--border);border-radius:11px;padding:10px;font-family:'Cairo',sans-serif;font-size:14px;outline:none" placeholder="الشارع / المبنى / الدور"></textarea>
    </div>
    <div class="fg"><label>ملاحظات (اختياري)</label><input id="f-notes" placeholder="أي تعليمات للتوصيل"></div>
    <div class="order-preview" id="order-preview"></div>
    <button class="submit-btn" onclick="submitOrder()">✅ تأكيد الطلب</button>
    <button class="cancel-btn" onclick="closeOverlay('order-overlay')">إلغاء</button>
  </div>
</div>

<!-- Product Detail Modal -->
<div class="overlay" id="detail-overlay">
  <div class="sheet" id="detail-sheet"></div>
</div>

<!-- Wishlist Modal -->
<div class="overlay" id="wish-overlay">
  <div class="sheet">
    <div class="sheet-handle"></div>
    <div class="sheet-title">❤️ المفضلة</div>
    <div id="wish-content"></div>
    <button class="cancel-btn" onclick="closeOverlay('wish-overlay')">إغلاق</button>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// ── Settings from server ──────────────────────────────────────
const SHIP_COST = {{ shipping_cost or 35 }};
const FREE_FROM = {{ free_shipping_from or 500 }};

// ── State ─────────────────────────────────────────────────────
let cart     = JSON.parse(localStorage.getItem('regal_cart')  || '[]');
let wishlist = JSON.parse(localStorage.getItem('regal_wish')  || '[]');
let orders   = JSON.parse(localStorage.getItem('regal_orders')|| '[]');
let allProducts = [];
let selSize = {};

// ── Navigation ────────────────────────────────────────────────
function showPage(n) {
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+n).classList.add('active');
  const idx={home:0,cart:1,orders:2,profile:3}[n];
  if(idx!==undefined) document.querySelectorAll('.nav-btn')[idx].classList.add('active');
  if(n==='cart')   renderCart();
  if(n==='orders') renderOrders();
}

// ── Toast ─────────────────────────────────────────────────────
function toast(msg) {
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2300);
}

// ── Cart count ────────────────────────────────────────────────
function updateCartBadge() {
  const n=cart.reduce((s,i)=>s+i.qty,0);
  const b=document.getElementById('cart-badge');
  b.textContent=n; b.style.display=n?'flex':'none';
  updateFreeBar();
}

function updateFreeBar() {
  const sub=cart.reduce((s,i)=>s+i.price*i.qty,0);
  const bar=document.getElementById('free-shipping-bar');
  const txt=document.getElementById('free-bar-text');
  const fill=document.getElementById('free-bar-fill');
  if(!bar) return;
  if(sub>0){
    bar.style.display='flex';
    if(sub>=FREE_FROM){
      txt.textContent='🎉 تهانينا! شحنك مجاني';
      fill.style.width='100%';
    } else {
      const rem=(FREE_FROM-sub).toFixed(0);
      txt.textContent=`أضف ${rem} ج لشحن مجاني`;
      fill.style.width=(sub/FREE_FROM*100)+'%';
    }
  } else { bar.style.display='none'; }
}

// ── Categories ────────────────────────────────────────────────
async function loadCategories() {
  const res=await fetch('/api/categories');
  const cats=await res.json();
  const nav=document.getElementById('cat-nav');
  const list=document.getElementById('cats-list');
  nav.innerHTML='<a class="active" onclick="filterCat(0,this);return false" href="#">الرئيسية</a>';
  cats.forEach(c=>{
    nav.innerHTML+=`<a onclick="filterCat(${c.id},this);return false" href="#">${c.icon} ${c.name}</a>`;
  });
  list.innerHTML=`<div class="cat-card active" onclick="filterCat(0,this)"><div class="cat-icon">🌟</div><div class="cat-name">الكل</div></div>`;
  cats.forEach(c=>{
    list.innerHTML+=`<div class="cat-card" onclick="filterCat(${c.id},this)"><div class="cat-icon">${c.icon}</div><div class="cat-name">${c.name}</div></div>`;
  });
}

async function filterCat(id, el) {
  document.querySelectorAll('.cat-card').forEach(c=>c.classList.remove('active'));
  document.querySelectorAll('#cat-nav a').forEach(a=>a.classList.remove('active'));
  if(el){el.classList.add('active');}
  document.getElementById('products-grid').innerHTML='<div class="spinner"></div>';
  const url=id?`/api/products?category=${id}`:'/api/products/featured';
  const res=await fetch(url);
  allProducts=await res.json();
  const title=id?(el?.querySelector('.cat-name')?.textContent||'المنتجات'):'منتجات مميزة';
  renderProducts(allProducts, title);
}

async function doSearch(q) {
  if(!q){loadFeatured();return;}
  const res=await fetch(`/api/products?search=${encodeURIComponent(q)}`);
  const prods=await res.json();
  renderProducts(prods, `نتائج: "${q}"`);
}

async function loadFeatured() {
  const res=await fetch('/api/products/featured');
  allProducts=await res.json();
  renderProducts(allProducts,'منتجات مميزة');
}

// ── Products ──────────────────────────────────────────────────
function isFav(id){return wishlist.includes(id);}

function renderProducts(products, title) {
  document.getElementById('prod-title').textContent=title||'المنتجات';
  const g=document.getElementById('products-grid');
  if(!products.length){
    g.innerHTML='<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--gray)">لا توجد منتجات</div>';
    return;
  }
  g.innerHTML=products.map(p=>{
    const sizes=(p.sizes||'S,M,L,XL').split(',');
    const badge=p.old_price?'<div class="prod-badge">خصم</div>':
                (p.featured?'<div class="prod-badge new-b">مميز</div>':'');
    const img=p.image_url?`<img src="${p.image_url}" alt="${p.name}">`:(p.icon||'👕');
    return `
    <div class="prod-card" onclick="showDetail(${p.id})">
      <div class="prod-img">
        ${badge}
        <button class="fav-btn" onclick="event.stopPropagation();toggleWish(${p.id})" id="fav-${p.id}">${isFav(p.id)?'❤️':'🤍'}</button>
        ${img}
      </div>
      <div class="prod-info">
        <div class="prod-brand">${p.cat_name||''}</div>
        <div class="prod-name">${p.name}</div>
        <div class="prod-prices">
          ${p.old_price?`<span class="prod-old">${p.old_price} ج</span>`:''}
          <span class="prod-price">${p.price} ج</span>
        </div>
        <button class="add-btn" onclick="event.stopPropagation();quickAdd(${p.id})">+ أضف للسلة</button>
      </div>
    </div>`;
  }).join('');
}

// ── Product Detail ────────────────────────────────────────────
function showDetail(id) {
  const p=allProducts.find(x=>x.id===id);
  if(!p) return;
  selSize[id]='';
  const sizes=(p.sizes||'S,M,L,XL').split(',');
  const img=p.image_url?`<img src="${p.image_url}" alt="${p.name}">`:(p.icon||'👕');
  document.getElementById('detail-sheet').innerHTML=`
    <div class="sheet-handle"></div>
    <div class="detail-img">${img}</div>
    <div style="font-size:11px;color:var(--gray);font-weight:700;letter-spacing:.5px;text-transform:uppercase;margin-bottom:3px">${p.cat_name||''}</div>
    <div style="font-size:18px;font-weight:900;margin-bottom:4px">${p.name}</div>
    <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:10px">
      ${p.old_price?`<span style="color:#bbb;font-size:13px;text-decoration:line-through">${p.old_price} ج</span>`:''}
      <span style="font-size:22px;font-weight:900;color:var(--navy)">${p.price} ج</span>
    </div>
    <div style="font-size:13px;color:var(--gray);line-height:1.7;margin-bottom:14px">${p.description||''}</div>
    <div style="font-size:13px;font-weight:700;margin-bottom:8px;color:var(--gray)">اختر المقاس:</div>
    <div class="sizes">${sizes.map(s=>`<button class="sz" onclick="selSize[${id}]='${s}';this.closest('.sizes').querySelectorAll('.sz').forEach(b=>b.classList.remove('active'));this.classList.add('active')">${s}</button>`).join('')}</div>
    <button class="submit-btn" onclick="addWithSize(${id})">🛒 أضف للسلة</button>
    <button class="cancel-btn" onclick="closeOverlay('detail-overlay')">إغلاق</button>
  `;
  document.getElementById('detail-overlay').classList.add('open');
}

function addWithSize(id) {
  const p=allProducts.find(x=>x.id===id);
  const sz=selSize[id]||(p.sizes||'S,M,L,XL').split(',')[0];
  addToCart(p.id,p.name,p.price,p.image_url||p.icon||'',sz);
  closeOverlay('detail-overlay');
}

function quickAdd(id) {
  const p=allProducts.find(x=>x.id===id);
  if(!p) return;
  addToCart(p.id,p.name,p.price,p.image_url||p.icon||'',(p.sizes||'S,M,L,XL').split(',')[0]);
}

// ── Cart ──────────────────────────────────────────────────────
function addToCart(id,name,price,imgOrEmoji,size) {
  const key=`${id}_${size}`;
  const ex=cart.find(i=>i.key===key);
  if(ex){ex.qty++;}
  else{cart.push({id,key,name,price,img:imgOrEmoji,size,qty:1});}
  saveCart(); toast('✅ تم إضافة '+name);
}

function saveCart() {
  localStorage.setItem('regal_cart',JSON.stringify(cart));
  updateCartBadge();
}

function renderCart() {
  const el=document.getElementById('cart-list');
  const tot=document.getElementById('cart-total-box');
  if(!cart.length){
    el.innerHTML='<div class="empty"><div class="empty-icon">🛒</div><p>سلتك فارغة حالياً</p></div>';
    tot.innerHTML=''; return;
  }
  el.innerHTML=cart.map(i=>{
    const isUrl=i.img&&i.img.startsWith('/');
    return `
    <div class="cart-item">
      <div class="cart-img">${isUrl?`<img src="${i.img}" alt="${i.name}">`:(i.img||'👕')}</div>
      <div class="cart-info">
        <div class="cart-name">${i.name}</div>
        <div class="cart-size">المقاس: ${i.size}</div>
        <div class="cart-price">${i.price} ج</div>
        <div class="qty-row">
          <button class="qty-btn" onclick="changeQty('${i.key}',-1)">−</button>
          <span style="font-weight:700">${i.qty}</span>
          <button class="qty-btn" onclick="changeQty('${i.key}',1)">+</button>
        </div>
      </div>
      <button class="cart-del" onclick="removeItem('${i.key}')">🗑</button>
    </div>`; }).join('');
  const sub=cart.reduce((s,i)=>s+i.price*i.qty,0);
  const shipping=sub>=FREE_FROM?0:SHIP_COST;
  tot.innerHTML=`
    <div class="cart-summary">
      <div class="sum-row"><span>المنتجات (${cart.reduce((s,i)=>s+i.qty,0)})</span><span>${sub} ج</span></div>
      <div class="sum-row"><span>الشحن</span><span>${shipping===0?'<span style="color:#1a7a3a;font-weight:700">مجاني 🎉</span>':shipping+' ج'}</span></div>
      ${shipping>0?`<div style="font-size:11px;color:var(--gray);padding:2px 0 8px">أضف ${FREE_FROM-sub} ج لشحن مجاني</div>`:''}
      <div class="sum-row final"><span>الإجمالي</span><span>${sub+shipping} ج</span></div>
      <button class="checkout-btn" onclick="openOrder()">إتمام الطلب ◀</button>
    </div>`;
}

function changeQty(key,d){
  const i=cart.find(x=>x.key===key); if(!i)return;
  i.qty+=d;
  if(i.qty<=0) cart=cart.filter(x=>x.key!==key);
  saveCart(); renderCart();
}
function removeItem(key){
  cart=cart.filter(x=>x.key!==key);
  saveCart(); renderCart();
}

// ── Order ─────────────────────────────────────────────────────
function openOrder() {
  if(!cart.length){toast('السلة فارغة!');return;}
  const sub=cart.reduce((s,i)=>s+i.price*i.qty,0);
  const shipping=sub>=FREE_FROM?0:SHIP_COST;
  document.getElementById('order-preview').innerHTML=
    cart.map(i=>`${i.name} (${i.size}) × ${i.qty} = ${i.price*i.qty} ج`).join('<br>')+
    `<hr style="border:none;border-top:1px solid #e8e5df;margin:8px 0">
     <strong>الإجمالي: ${sub+shipping} ج ${shipping===0?'(شحن مجاني 🎉)':'(شحن: '+shipping+' ج)'}</strong>`;
  document.getElementById('order-overlay').classList.add('open');
}

async function submitOrder() {
  const name   =document.getElementById('f-name').value.trim();
  const phone  =document.getElementById('f-phone').value.trim();
  const city   =document.getElementById('f-city').value;
  const address=document.getElementById('f-address').value.trim();
  const notes  =document.getElementById('f-notes').value.trim();
  if(!name||!phone||!city||!address){toast('⚠️ أكمل جميع البيانات');return;}
  const sub=cart.reduce((s,i)=>s+i.price*i.qty,0);
  const shipping=sub>=FREE_FROM?0:SHIP_COST;
  const btn=document.querySelector('.submit-btn');
  btn.disabled=true; btn.textContent='...جاري الإرسال';
  try{
    const res=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name,phone,city,address,notes,total:sub+shipping,items:cart})});
    const data=await res.json();
    if(data.success){
      orders.unshift({id:data.order_id,date:new Date().toLocaleDateString('ar-EG'),
        city,items:[...cart],total:sub+shipping,status:'جديد'});
      localStorage.setItem('regal_orders',JSON.stringify(orders));
      cart=[]; saveCart(); closeOverlay('order-overlay');
      toast('🎉 طلبك وصلنا! رقم الطلب: #'+data.order_id);
      showPage('orders');
    }
  }catch(e){toast('خطأ في الاتصال');}
  btn.disabled=false; btn.textContent='✅ تأكيد الطلب';
}

// ── Orders ────────────────────────────────────────────────────
const SC={'جديد':'s-new','قيد التنفيذ':'s-process','تم التوصيل':'s-done','ملغي':'s-cancel'};

function renderOrders() {
  const el=document.getElementById('orders-list');
  if(!orders.length){
    el.innerHTML='<div class="empty"><div class="empty-icon">📦</div><p>لا يوجد طلبات بعد</p></div>';
    return;
  }
  el.innerHTML=orders.map(o=>`
    <div class="order-card">
      <div class="order-header">
        <span class="order-num">#${o.id}</span>
        <span class="status-pill ${SC[o.status]||'s-new'}">${o.status}</span>
      </div>
      <div class="order-date">📅 ${o.date||''} | 📍 ${o.city||''}</div>
      <div class="order-items-txt">${(o.items||[]).map(i=>`${i.name} × ${i.qty}`).join(' · ')}</div>
      <div class="order-footer">
        <span style="font-weight:700;color:var(--navy)">${o.total} ج</span>
        <span style="font-size:11px;color:var(--gray)">${(o.items||[]).reduce((s,i)=>s+i.qty,0)} قطعة</span>
      </div>
    </div>`).join('');
}

// ── Wishlist ──────────────────────────────────────────────────
function toggleWish(id){
  const idx=wishlist.indexOf(id);
  if(idx>=0){wishlist.splice(idx,1);toast('تم الإزالة من المفضلة');}
  else{wishlist.push(id);toast('❤️ تم الإضافة للمفضلة');}
  localStorage.setItem('regal_wish',JSON.stringify(wishlist));
  const btn=document.getElementById('fav-'+id);
  if(btn) btn.textContent=wishlist.includes(id)?'❤️':'🤍';
}

function showWishlist(){
  const prods=allProducts.filter(p=>wishlist.includes(p.id));
  const el=document.getElementById('wish-content');
  if(!prods.length){
    el.innerHTML='<div class="empty"><div class="empty-icon">🤍</div><p>المفضلة فارغة</p></div>';
  } else {
    el.innerHTML=prods.map(p=>{
      const isUrl=p.image_url&&p.image_url.startsWith('/');
      return `
      <div class="wish-item">
        <div class="wish-img">${isUrl?`<img src="${p.image_url}" alt="${p.name}">`:( p.icon||'👕')}</div>
        <div style="flex:1">
          <div style="font-size:13px;font-weight:700">${p.name}</div>
          <div style="font-size:13px;color:var(--navy);font-weight:700;margin-top:3px">${p.price} ج</div>
        </div>
        <button class="add-btn" style="width:auto;padding:7px 14px" onclick="quickAdd(${p.id});toast('تم الإضافة للسلة')">أضف</button>
      </div>`; }).join('');
  }
  document.getElementById('wish-overlay').classList.add('open');
}

// ── Overlays ──────────────────────────────────────────────────
function closeOverlay(id){document.getElementById(id).classList.remove('open');}
document.querySelectorAll('.overlay').forEach(ov=>{
  ov.addEventListener('click',function(e){if(e.target===this)this.classList.remove('open');});
});

// ── Init ──────────────────────────────────────────────────────
updateCartBadge();
loadCategories();
loadFeatured();
</script>
</body>
</html>"""


TMPL_LOGIN = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>تسجيل الدخول - لوحة التحكم</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Cairo',sans-serif;background:linear-gradient(135deg,#0d1b2a,#1b2d42,#0d1b2a);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.box{background:#fff;border-radius:20px;padding:36px 28px;width:100%;max-width:380px;box-shadow:0 16px 48px rgba(0,0,0,.3);text-align:center}
.logo{font-size:48px;margin-bottom:8px}
h2{font-size:20px;font-weight:900;color:#0d1b2a;margin-bottom:4px}
.sub{font-size:13px;color:#888;margin-bottom:26px}
.fg{margin-bottom:15px;text-align:right}
label{display:block;font-size:12px;color:#555;margin-bottom:5px;font-weight:600}
input{width:100%;border:1.5px solid #e8e5df;border-radius:10px;padding:11px 14px;font-size:14px;font-family:'Cairo',sans-serif;outline:none;transition:.2s}
input:focus{border-color:#c9a84c}
.btn{width:100%;background:#0d1b2a;color:#fff;border:none;border-radius:12px;padding:13px;font-size:15px;font-weight:700;cursor:pointer;font-family:'Cairo',sans-serif;margin-top:6px}
.error{background:#ffebee;color:#c62828;border-radius:8px;padding:10px;font-size:13px;margin-bottom:16px}
</style>
</head>
<body>
<div class="box">
  <div class="logo">👔</div>
  <h2>ريجال — لوحة التحكم</h2>
  <p class="sub">سجّل دخولك للمتابعة</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <div class="fg"><label>اسم المستخدم</label><input name="username" placeholder="admin" required></div>
    <div class="fg"><label>كلمة المرور</label><input type="password" name="password" placeholder="••••••••" required></div>
    <button type="submit" class="btn">دخول ←</button>
  </form>
</div>
</body>
</html>"""


ADMIN_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--navy:#0d1b2a;--navy2:#1b2d42;--gold:#c9a84c;--bg:#f0f2f5;--sw:230px}
body{font-family:'Cairo',sans-serif;background:var(--bg);display:flex;min-height:100vh;font-size:14px}
.sidebar{width:var(--sw);background:var(--navy);color:#fff;position:fixed;height:100vh;overflow-y:auto;z-index:50;display:flex;flex-direction:column}
.sb-logo{padding:18px 16px;font-size:15px;font-weight:900;border-bottom:1px solid rgba(255,255,255,.1);display:flex;align-items:center;gap:8px}
.sb-logo span{font-size:22px}
.sb-sec{padding:10px 14px 4px;font-size:10px;text-transform:uppercase;color:rgba(255,255,255,.35);letter-spacing:.05em;margin-top:8px}
.sidebar a{display:flex;align-items:center;gap:9px;padding:10px 16px;color:rgba(255,255,255,.75);text-decoration:none;font-size:13px;transition:.15s;border-right:3px solid transparent}
.sidebar a:hover,.sidebar a.act{background:rgba(255,255,255,.1);color:#fff;border-right-color:var(--gold)}
.sidebar a .ic{font-size:16px;width:20px;text-align:center}
.main{margin-right:var(--sw);flex:1;padding:22px;min-width:0}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.topbar h2{font-size:18px;font-weight:700}
.stat-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}
.stat{background:#fff;border-radius:13px;padding:16px;box-shadow:0 1px 5px rgba(0,0,0,.07);border-bottom:3px solid var(--gold)}
.stat-ic{font-size:24px;margin-bottom:5px}
.stat-val{font-size:22px;font-weight:900;color:var(--navy)}
.stat-lbl{font-size:11px;color:#888;margin-top:2px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:13px;overflow:hidden;box-shadow:0 1px 5px rgba(0,0,0,.07)}
th{background:var(--navy);color:#fff;padding:11px 13px;font-size:12px;text-align:right;font-weight:600}
td{padding:10px 13px;font-size:13px;border-bottom:1px solid #f0f0f0;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#fafaf8}
.badge{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;display:inline-block}
.badge-جديد{background:#e3f2fd;color:#1565c0}
.badge-قيد\ التنفيذ{background:#fff3e0;color:#e65100}
.badge-تم\ التوصيل{background:#e8f5e9;color:#2e7d32}
.badge-ملغي{background:#ffebee;color:#c62828}
.btn{padding:7px 15px;border-radius:8px;border:none;cursor:pointer;font-size:12px;font-weight:600;text-decoration:none;display:inline-block;font-family:'Cairo',sans-serif}
.btn-navy{background:var(--navy);color:#fff}
.btn-red{background:#f44336;color:#fff}
.btn-gold{background:var(--gold);color:var(--navy)}
.btn-gray{background:#eee;color:#333}
.card{background:#fff;border-radius:13px;padding:20px;box-shadow:0 1px 5px rgba(0,0,0,.07);margin-bottom:18px}
.card-title{font-size:15px;font-weight:700;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fg{margin-bottom:12px}
.fg label{display:block;font-size:12px;color:#555;margin-bottom:4px;font-weight:600}
.fg input,.fg select,.fg textarea{width:100%;border:1.5px solid #e8e5df;border-radius:8px;padding:8px 12px;font-size:13px;font-family:'Cairo',sans-serif;outline:none;transition:.2s}
.fg input:focus,.fg select:focus{border-color:var(--gold)}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:200;justify-content:center;align-items:center}
.overlay.open{display:flex}
.modal{background:#fff;border-radius:16px;padding:24px;width:520px;max-height:88vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,.15)}
.modal-title{font-size:16px;font-weight:700;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid #eee}
.upload-zone{border:2px dashed #e0e0e0;border-radius:12px;padding:20px;text-align:center;cursor:pointer;transition:.2s;position:relative;overflow:hidden;background:#fafafa}
.upload-zone:hover{border-color:var(--gold);background:#fdf8ec}
.upload-zone.has-img{border-style:solid;border-color:var(--gold);padding:0}
.upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer}
.upload-zone img{width:100%;max-height:180px;object-fit:contain;padding:10px;display:none;border-radius:12px}
.upload-zone.has-img img{display:block}
.upload-placeholder{pointer-events:none}
.upload-zone.has-img .upload-placeholder{display:none}
.remove-img-btn{position:absolute;top:8px;left:8px;background:rgba(244,67,54,.9);color:#fff;border:none;border-radius:6px;padding:3px 10px;font-size:12px;cursor:pointer;z-index:2;display:none;font-family:'Cairo',sans-serif}
.upload-zone.has-img .remove-img-btn{display:block}
.prod-thumb{width:44px;height:44px;border-radius:8px;object-fit:contain;border:1px solid #eee;background:#f9f9f9;padding:3px}
</style>
"""

SIDEBAR = lambda active: f"""
<div class="sidebar">
  <div class="sb-logo"><span>👔</span>ريجال — إدارة</div>
  <div class="sb-sec">القائمة</div>
  <a href="/admin" class="{'act' if active=='index' else ''}"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products" class="{'act' if active=='products' else ''}"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories" class="{'act' if active=='categories' else ''}"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders" class="{'act' if active=='orders' else ''}"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers" class="{'act' if active=='customers' else ''}"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings" class="{'act' if active=='settings' else ''}"><span class="ic">⚙️</span>الإعدادات</a>
  <div class="sb-sec">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout"><span class="ic">🚪</span>خروج</a>
</div>
"""

TMPL_ADMIN_INDEX = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>لوحة التحكم</title>""" + ADMIN_STYLE + """</head>
<body>
""" + SIDEBAR('index') + """
<div class="main">
  <div class="topbar"><h2>📊 لوحة التحكم</h2><span style="color:#888;font-size:13px">مرحباً {{ session.admin }} 👋</span></div>
  <div class="stat-grid">
    <div class="stat"><div class="stat-ic">📦</div><div class="stat-val">{{ stats.products }}</div><div class="stat-lbl">المنتجات</div></div>
    <div class="stat"><div class="stat-ic">🛒</div><div class="stat-val">{{ stats.orders }}</div><div class="stat-lbl">الطلبات</div></div>
    <div class="stat"><div class="stat-ic">🔔</div><div class="stat-val">{{ stats.new_orders }}</div><div class="stat-lbl">جديدة</div></div>
    <div class="stat"><div class="stat-ic">👥</div><div class="stat-val">{{ stats.customers }}</div><div class="stat-lbl">العملاء</div></div>
    <div class="stat"><div class="stat-ic">💰</div><div class="stat-val">{{ "%.0f"|format(stats.revenue) }}</div><div class="stat-lbl">الإيرادات ج</div></div>
  </div>
  <div class="card">
    <div class="card-title">آخر الطلبات <a href="/admin/orders" class="btn btn-navy">عرض الكل</a></div>
    <table><thead><tr><th>#</th><th>العميل</th><th>الهاتف</th><th>المدينة</th><th>الإجمالي</th><th>الحالة</th><th>التاريخ</th><th>إجراء</th></tr></thead>
    <tbody>
    {% for o in orders %}
    <tr>
      <td><b>#{{ o.id }}</b></td><td>{{ o.customer_name }}</td><td>{{ o.customer_phone }}</td>
      <td>{{ o.customer_city or '—' }}</td>
      <td><b>{{ "%.2f"|format(o.total) }} ج</b></td>
      <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
      <td style="color:#888;font-size:12px">{{ o.created_at[:16] }}</td>
      <td><a href="/admin/orders/{{ o.id }}" class="btn btn-navy">عرض</a></td>
    </tr>
    {% else %}<tr><td colspan="8" style="text-align:center;padding:30px;color:#888">لا توجد طلبات</td></tr>{% endfor %}
    </tbody></table>
  </div>
</div>
</body></html>"""


TMPL_ADMIN_PRODUCTS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>المنتجات</title>""" + ADMIN_STYLE + """</head>
<body>
""" + SIDEBAR('products') + """
<div class="main">
  <div class="topbar"><h2>📦 المنتجات</h2><button class="btn btn-navy" onclick="document.getElementById('add-m').classList.add('open')">+ إضافة منتج</button></div>
  <div class="card">
  <table><thead><tr><th>#</th><th>الصورة</th><th>الاسم</th><th>التصنيف</th><th>السعر</th><th>السعر القديم</th><th>المخزون</th><th>الوحدة</th><th>المقاسات</th><th>مميز</th><th>إجراءات</th></tr></thead>
  <tbody>
  {% for p in products %}
  <tr>
    <td>{{ p.id }}</td>
    <td>{% if p.image_url %}<img src="{{ p.image_url }}" class="prod-thumb">{% else %}<div style="width:44px;height:44px;border-radius:8px;background:#eae8e2;display:flex;align-items:center;justify-content:center;font-size:22px">👕</div>{% endif %}</td>
    <td><b>{{ p.name }}</b><br><span style="font-size:11px;color:#888">{{ p.description or '' }}</span></td>
    <td>{{ p.cat_name or '—' }}</td>
    <td><b>{{ p.price }} ج</b></td>
    <td>{{ p.old_price or '—' }}</td>
    <td style="color:{% if p.stock < 10 %}#f44336{% else %}#2e7d32{% endif %}"><b>{{ p.stock }}</b></td>
    <td>{{ p.unit }}</td>
    <td style="font-size:11px;color:#888">{{ p.sizes or '' }}</td>
    <td>{% if p.featured %}⭐{% else %}—{% endif %}</td>
    <td style="display:flex;gap:5px">
      <button class="btn btn-gold" onclick="editProd({{ p.id }},'{{ p.name|replace("'","\\'") }}','{{ (p.description or '')|replace("'","\\'") }}',{{ p.price }},{{ p.old_price or 0 }},{{ p.stock }},{{ p.category_id or 0 }},'{{ p.unit }}','{{ p.sizes or "S,M,L,XL" }}',{{ p.featured }},'{{ p.image_url or "" }}')">تعديل</button>
      <a href="/admin/products/delete/{{ p.id }}" class="btn btn-red" onclick="return confirm('حذف المنتج؟')">حذف</a>
    </td>
  </tr>
  {% else %}<tr><td colspan="11" style="text-align:center;padding:30px;color:#888">لا توجد منتجات</td></tr>{% endfor %}
  </tbody></table>
  </div>
</div>

<!-- Add Modal -->
<div class="overlay" id="add-m">
  <div class="modal">
    <div class="modal-title">➕ إضافة منتج جديد</div>
    <form method="POST" action="/admin/products/add" enctype="multipart/form-data">
      <div class="form-row">
        <div class="fg"><label>اسم المنتج *</label><input name="name" required></div>
        <div class="fg"><label>التصنيف *</label><select name="category_id" required>{% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}</select></div>
      </div>
      <div class="fg"><label>الوصف</label><input name="description"></div>
      <div class="form-row">
        <div class="fg"><label>السعر *</label><input name="price" type="number" step="0.01" required></div>
        <div class="fg"><label>السعر القديم</label><input name="old_price" type="number" step="0.01"></div>
      </div>
      <div class="form-row">
        <div class="fg"><label>المخزون *</label><input name="stock" type="number" value="0" required></div>
        <div class="fg"><label>الوحدة</label><select name="unit"><option>قطعة</option><option>زوج</option><option>طقم</option></select></div>
      </div>
      <div class="fg"><label>المقاسات (مفصولة بفاصلة)</label><input name="sizes" value="S,M,L,XL" placeholder="مثال: S,M,L,XL أو 40,41,42"></div>
      <div class="fg">
        <label>📸 صورة المنتج</label>
        <div class="upload-zone" id="add-zone">
          <input type="file" name="image" accept="image/*" onchange="previewImg(this,'add-zone','add-prev')">
          <div class="upload-placeholder"><div style="font-size:28px;margin-bottom:6px">📸</div><div style="font-size:12px;color:#888">انقر لرفع صورة</div></div>
          <img id="add-prev"><button type="button" class="remove-img-btn" onclick="clearImg('add-zone','add-prev')">✕</button>
        </div>
      </div>
      <div class="fg" style="display:flex;align-items:center;gap:8px"><input type="checkbox" name="featured" id="add-feat" style="width:auto"><label for="add-feat">منتج مميز (يظهر في الرئيسية)</label></div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-navy" style="flex:1;padding:11px">حفظ</button>
        <button type="button" class="btn btn-gray" style="flex:1;padding:11px" onclick="document.getElementById('add-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<!-- Edit Modal -->
<div class="overlay" id="edit-m">
  <div class="modal">
    <div class="modal-title">✏️ تعديل المنتج</div>
    <form method="POST" id="edit-form" enctype="multipart/form-data">
      <div class="form-row">
        <div class="fg"><label>الاسم</label><input name="name" id="e-name" required></div>
        <div class="fg"><label>التصنيف</label><select name="category_id" id="e-cat">{% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}</select></div>
      </div>
      <div class="fg"><label>الوصف</label><input name="description" id="e-desc"></div>
      <div class="form-row">
        <div class="fg"><label>السعر</label><input name="price" id="e-price" type="number" step="0.01"></div>
        <div class="fg"><label>السعر القديم</label><input name="old_price" id="e-oprice" type="number" step="0.01"></div>
      </div>
      <div class="form-row">
        <div class="fg"><label>المخزون</label><input name="stock" id="e-stock" type="number"></div>
        <div class="fg"><label>الوحدة</label><select name="unit" id="e-unit"><option>قطعة</option><option>زوج</option><option>طقم</option></select></div>
      </div>
      <div class="fg"><label>المقاسات</label><input name="sizes" id="e-sizes"></div>
      <div class="fg">
        <label>صورة جديدة (اتركه فارغ للإبقاء)</label>
        <div id="curr-img-box" style="display:none;margin-bottom:8px;display:flex;align-items:center;gap:10px">
          <img id="curr-img-el" style="width:54px;height:54px;object-fit:contain;border-radius:8px;border:1px solid #eee;background:#f9f9f9;padding:3px">
          <span style="font-size:11px;color:#888">الصورة الحالية</span>
        </div>
        <div class="upload-zone" id="edit-zone">
          <input type="file" name="image" accept="image/*" onchange="previewImg(this,'edit-zone','edit-prev')">
          <div class="upload-placeholder"><div style="font-size:28px;margin-bottom:6px">📸</div><div style="font-size:12px;color:#888">انقر لتغيير الصورة</div></div>
          <img id="edit-prev"><button type="button" class="remove-img-btn" onclick="clearImg('edit-zone','edit-prev')">✕</button>
        </div>
      </div>
      <div class="fg" style="display:flex;align-items:center;gap:8px"><input type="checkbox" name="featured" id="e-feat" style="width:auto"><label for="e-feat">منتج مميز</label></div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-navy" style="flex:1;padding:11px">حفظ</button>
        <button type="button" class="btn btn-gray" style="flex:1;padding:11px" onclick="document.getElementById('edit-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<script>
function previewImg(input,zoneId,prevId){
  if(!input.files||!input.files[0])return;
  const r=new FileReader();
  r.onload=e=>{
    document.getElementById(zoneId).classList.add('has-img');
    document.getElementById(prevId).src=e.target.result;
  };
  r.readAsDataURL(input.files[0]);
}
function clearImg(zoneId,prevId){
  document.getElementById(zoneId).classList.remove('has-img');
  document.getElementById(prevId).src='';
  document.getElementById(zoneId).querySelector('input[type=file]').value='';
}
function editProd(id,name,desc,price,oprice,stock,catId,unit,sizes,featured,imageUrl){
  document.getElementById('edit-form').action='/admin/products/edit/'+id;
  document.getElementById('e-name').value=name;
  document.getElementById('e-desc').value=desc;
  document.getElementById('e-price').value=price;
  document.getElementById('e-oprice').value=oprice||'';
  document.getElementById('e-stock').value=stock;
  document.getElementById('e-cat').value=catId;
  document.getElementById('e-unit').value=unit;
  document.getElementById('e-sizes').value=sizes;
  document.getElementById('e-feat').checked=featured==1;
  const box=document.getElementById('curr-img-box');
  if(imageUrl){document.getElementById('curr-img-el').src=imageUrl;box.style.display='flex';}
  else{box.style.display='none';}
  clearImg('edit-zone','edit-prev');
  document.getElementById('edit-m').classList.add('open');
}
</script>
</body></html>"""


TMPL_ADMIN_CATS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>التصنيفات</title>""" + ADMIN_STYLE + """</head>
<body>""" + SIDEBAR('categories') + """
<div class="main">
  <div class="topbar"><h2>🗂 التصنيفات</h2><button class="btn btn-navy" onclick="document.getElementById('add-m').classList.add('open')">+ تصنيف جديد</button></div>
  <div class="card">
    <table><thead><tr><th>#</th><th>الأيقونة</th><th>الاسم</th><th>النوع</th><th>المنتجات</th><th>إجراءات</th></tr></thead>
    <tbody>
    {% for c in categories %}
    <tr>
      <td>{{ c.id }}</td><td style="font-size:24px">{{ c.icon }}</td>
      <td><b>{{ c.name }}</b></td><td>{{ c.type }}</td>
      <td>{{ c.count }} منتج</td>
      <td style="display:flex;gap:6px">
        <button class="btn btn-gold" onclick="editCat({{ c.id }},'{{ c.name }}','{{ c.icon }}','{{ c.type }}')">تعديل</button>
        <a href="/admin/categories/delete/{{ c.id }}" class="btn btn-red" onclick="return confirm('حذف؟')">حذف</a>
      </td>
    </tr>
    {% else %}<tr><td colspan="6" style="text-align:center;padding:30px;color:#888">لا توجد تصنيفات</td></tr>{% endfor %}
    </tbody></table>
  </div>
</div>

<div class="overlay" id="add-m">
  <div class="modal">
    <div class="modal-title">➕ تصنيف جديد</div>
    <form method="POST" action="/admin/categories/add">
      <div class="form-row">
        <div class="fg"><label>الاسم *</label><input name="name" required></div>
        <div class="fg"><label>الأيقونة</label><input name="icon" value="👔" maxlength="5" style="font-size:20px"></div>
      </div>
      <div class="fg"><label>النوع</label><select name="type"><option value="main">رئيسي</option><option value="promo">عروض</option></select></div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-navy" style="flex:1;padding:11px">إضافة</button>
        <button type="button" class="btn btn-gray" style="flex:1;padding:11px" onclick="document.getElementById('add-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<div class="overlay" id="edit-m">
  <div class="modal">
    <div class="modal-title">✏️ تعديل التصنيف</div>
    <form method="POST" id="edit-f">
      <div class="form-row">
        <div class="fg"><label>الاسم</label><input name="name" id="e-name" required></div>
        <div class="fg"><label>الأيقونة</label><input name="icon" id="e-icon" maxlength="5" style="font-size:20px"></div>
      </div>
      <div class="fg"><label>النوع</label><select name="type" id="e-type"><option value="main">رئيسي</option><option value="promo">عروض</option></select></div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-navy" style="flex:1;padding:11px">حفظ</button>
        <button type="button" class="btn btn-gray" style="flex:1;padding:11px" onclick="document.getElementById('edit-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>
<script>
function editCat(id,name,icon,type){
  document.getElementById('edit-f').action='/admin/categories/edit/'+id;
  document.getElementById('e-name').value=name;
  document.getElementById('e-icon').value=icon;
  document.getElementById('e-type').value=type;
  document.getElementById('edit-m').classList.add('open');
}
</script>
</body></html>"""


TMPL_ADMIN_ORDERS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>الطلبات</title>""" + ADMIN_STYLE + """</head>
<body>""" + SIDEBAR('orders') + """
<div class="main">
  <div class="topbar"><h2>🛒 الطلبات</h2></div>
  <div class="card">
    <table><thead><tr><th>#</th><th>العميل</th><th>الهاتف</th><th>المدينة</th><th>الإجمالي</th><th>الشحن</th><th>الحالة</th><th>التاريخ</th><th>تفاصيل</th></tr></thead>
    <tbody>
    {% for o in orders %}
    <tr>
      <td><b>#{{ o.id }}</b></td><td>{{ o.customer_name }}</td><td>{{ o.customer_phone }}</td>
      <td>{{ o.customer_city or '—' }}</td>
      <td><b>{{ "%.2f"|format(o.total) }} ج</b></td>
      <td>{{ o.shipping }} ج</td>
      <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
      <td style="color:#888;font-size:12px">{{ o.created_at[:16] }}</td>
      <td><a href="/admin/orders/{{ o.id }}" class="btn btn-navy">عرض</a></td>
    </tr>
    {% else %}<tr><td colspan="9" style="text-align:center;padding:30px;color:#888">لا توجد طلبات</td></tr>{% endfor %}
    </tbody></table>
  </div>
</div>
</body></html>"""


TMPL_ADMIN_ORDER_DETAIL = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>تفاصيل الطلب</title>""" + ADMIN_STYLE + """</head>
<body>""" + SIDEBAR('orders') + """
<div class="main">
  <div class="topbar"><h2>📋 الطلب #{{ order.id }}</h2><a href="/admin/orders" class="btn btn-gray">← رجوع</a></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px">
    <div class="card">
      <div class="card-title">👤 بيانات العميل</div>
      <p><b>الاسم:</b> {{ order.customer_name }}</p>
      <p style="margin-top:8px"><b>الهاتف:</b> {{ order.customer_phone }}</p>
      <p style="margin-top:8px"><b>المدينة:</b> {{ order.customer_city or '—' }}</p>
      <p style="margin-top:8px"><b>العنوان:</b> {{ order.customer_address }}</p>
      {% if order.notes %}<p style="margin-top:8px"><b>ملاحظات:</b> {{ order.notes }}</p>{% endif %}
      <p style="margin-top:8px;color:#888;font-size:12px">{{ order.created_at[:16] }}</p>
    </div>
    <div class="card">
      <div class="card-title">📊 الحالة</div>
      <span class="badge badge-{{ order.status }}" style="font-size:14px;padding:6px 16px">{{ order.status }}</span>
      <form method="POST" action="/admin/orders/status/{{ order.id }}" style="margin-top:16px">
        <div class="fg"><label>تغيير الحالة</label>
          <select name="status">
            <option {% if order.status=='جديد' %}selected{% endif %}>جديد</option>
            <option {% if order.status=='قيد التنفيذ' %}selected{% endif %}>قيد التنفيذ</option>
            <option {% if order.status=='تم التوصيل' %}selected{% endif %}>تم التوصيل</option>
            <option {% if order.status=='ملغي' %}selected{% endif %}>ملغي</option>
          </select>
        </div>
        <button type="submit" class="btn btn-navy">تحديث</button>
      </form>
    </div>
  </div>
  <div class="card">
    <div class="card-title">🛒 المنتجات</div>
    <table><thead><tr><th>المنتج</th><th>المقاس</th><th>الكمية</th><th>السعر</th><th>الإجمالي</th></tr></thead>
    <tbody>
    {% for item in items %}
    <tr>
      <td>{{ item.product_name or '—' }}</td>
      <td>{{ item.size or '—' }}</td>
      <td>{{ item.qty }}</td>
      <td>{{ item.price }} ج</td>
      <td><b>{{ "%.2f"|format(item.price * item.qty) }} ج</b></td>
    </tr>
    {% endfor %}
    <tr style="background:#f9f8f4">
      <td colspan="3"></td>
      <td><b>الشحن</b></td><td><b>{{ order.shipping }} ج</b></td>
    </tr>
    <tr style="background:#f9f8f4">
      <td colspan="3"></td>
      <td><b>الإجمالي</b></td>
      <td><b style="color:var(--navy);font-size:15px">{{ "%.2f"|format(order.total) }} ج</b></td>
    </tr>
    </tbody></table>
  </div>
</div>
</body></html>"""


TMPL_ADMIN_CUSTOMERS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>العملاء</title>""" + ADMIN_STYLE + """</head>
<body>""" + SIDEBAR('customers') + """
<div class="main">
  <div class="topbar"><h2>👥 العملاء</h2></div>
  <div class="card">
    <table><thead><tr><th>#</th><th>الاسم</th><th>الهاتف</th><th>المدينة</th><th>العنوان</th><th>التاريخ</th></tr></thead>
    <tbody>
    {% for c in customers %}
    <tr>
      <td>{{ c.id }}</td><td><b>{{ c.name }}</b></td><td>{{ c.phone }}</td>
      <td>{{ c.city or '—' }}</td><td>{{ c.address }}</td>
      <td style="color:#888;font-size:12px">{{ c.created_at[:16] }}</td>
    </tr>
    {% else %}<tr><td colspan="6" style="text-align:center;padding:30px;color:#888">لا يوجد عملاء</td></tr>{% endfor %}
    </tbody></table>
  </div>
</div>
</body></html>"""


TMPL_ADMIN_SETTINGS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>الإعدادات</title>""" + ADMIN_STYLE + """</head>
<body>""" + SIDEBAR('settings') + """
<div class="main">
  <div class="topbar"><h2>⚙️ إعدادات المتجر</h2><a href="/" target="_blank" class="btn btn-navy">معاينة المتجر ↗</a></div>

  <form method="POST" action="/admin/settings/save" enctype="multipart/form-data">

    <!-- اسم الموقع -->
    <div class="card">
      <div class="card-title">🏪 معلومات المتجر</div>
      <div class="form-row">
        <div class="fg"><label>اسم المتجر</label><input name="site_name" value="{{ settings.site_name }}"></div>
        <div class="fg"><label>الشعار الفرعي (tagline)</label><input name="site_subtitle" value="{{ settings.site_subtitle }}"></div>
      </div>
    </div>

    <!-- شحن -->
    <div class="card">
      <div class="card-title">🚚 إعدادات الشحن</div>
      <div class="form-row">
        <div class="fg"><label>تكلفة الشحن (ج)</label><input name="shipping_cost" type="number" value="{{ settings.shipping_cost }}"></div>
        <div class="fg"><label>شحن مجاني من (ج)</label><input name="free_shipping_from" type="number" value="{{ settings.free_shipping_from }}"></div>
      </div>
    </div>

    <!-- واتساب -->
    <div class="card">
      <div class="card-title">📱 تواصل</div>
      <div class="fg"><label>رقم واتساب (بدون +)</label><input name="whatsapp" value="{{ settings.whatsapp }}" placeholder="201xxxxxxxxx"></div>
    </div>

    <!-- n8n / MCP -->
    <div class="card">
      <div class="card-title">🤖 n8n & MCP Integration</div>
      <p style="font-size:12px;color:#888;margin-bottom:14px;line-height:1.7">
        📌 <b>n8n Webhook:</b> عند إتمام أي طلب، يُرسل JSON لهذا الرابط تلقائياً.<br>
        📌 <b>MCP API Endpoint:</b> متاح على <code style="background:#f4f2ee;padding:2px 6px;border-radius:4px">/api/mcp</code> — يدعم list_products, list_orders, update_order_status, add_product, stats.<br>
        📌 <b>Secret:</b> مفتاح سري اختياري لحماية MCP endpoint — أرسله في هيدر <code>X-Secret</code>.
      </p>
      <div class="fg"><label>n8n Webhook URL</label><input name="n8n_webhook" value="{{ settings.n8n_webhook }}" placeholder="https://your-n8n.com/webhook/..."></div>
      <div class="fg"><label>MCP Secret (اختياري)</label><input name="n8n_secret" value="{{ settings.n8n_secret }}" placeholder="your-secret-key"></div>
    </div>

    <!-- اللوجو -->
    <div class="card">
      <div class="card-title">🖼️ اللوجو</div>
      <div class="fg"><label>نوع اللوجو</label>
        <select name="logo_type" id="logo-type" onchange="toggleLogoType(this.value)">
          <option value="emoji" {% if settings.logo_type=='emoji' %}selected{% endif %}>إيموجي</option>
          <option value="image" {% if settings.logo_type=='image' %}selected{% endif %}>صورة</option>
        </select>
      </div>
      <div id="emoji-box" style="{% if settings.logo_type=='image' %}display:none{% endif %}">
        <div class="fg"><label>الإيموجي</label><input name="logo_emoji" value="{{ settings.logo_emoji or '👔' }}" maxlength="5" style="font-size:26px;text-align:center;width:80px"></div>
      </div>
      <div id="img-box" style="{% if settings.logo_type=='emoji' %}display:none{% endif %}">
        {% if settings.logo_image %}
        <div style="margin-bottom:12px;display:flex;align-items:center;gap:12px">
          <img src="{{ settings.logo_image }}" style="width:54px;height:54px;object-fit:contain;border-radius:8px;border:1px solid #eee;background:#f9f9f9;padding:3px">
          <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:#f44336;cursor:pointer"><input type="checkbox" name="remove_logo_image" style="width:auto"> حذف اللوجو</label>
        </div>
        {% endif %}
        <div class="upload-zone" id="logo-zone">
          <input type="file" name="logo_image" accept="image/*" onchange="previewImg(this,'logo-zone','logo-prev')">
          <div class="upload-placeholder"><div style="font-size:28px;margin-bottom:6px">🖼️</div><div style="font-size:12px;color:#888">رفع صورة لوجو</div></div>
          <img id="logo-prev"><button type="button" class="remove-img-btn" onclick="clearImg('logo-zone','logo-prev')">✕</button>
        </div>
      </div>
    </div>

    <!-- صورة البانر -->
    <div class="card">
      <div class="card-title">🎨 صورة البانر</div>
      {% if settings.banner_image %}
      <div style="margin-bottom:12px;display:flex;align-items:center;gap:12px">
        <img src="{{ settings.banner_image }}" style="width:100px;height:70px;object-fit:contain;border-radius:8px;border:1px solid #eee;background:linear-gradient(135deg,#0d1b2a,#1b2d42);padding:6px">
        <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:#f44336;cursor:pointer"><input type="checkbox" name="remove_banner" style="width:auto"> حذف البانر</label>
      </div>
      {% endif %}
      <div class="upload-zone" id="banner-zone">
        <input type="file" name="banner_image" accept="image/*" onchange="previewImg(this,'banner-zone','banner-prev')">
        <div class="upload-placeholder"><div style="font-size:28px;margin-bottom:6px">🎨</div><div style="font-size:12px;color:#888">رفع صورة بانر (PNG شفاف يفضل)</div></div>
        <img id="banner-prev"><button type="button" class="remove-img-btn" onclick="clearImg('banner-zone','banner-prev')">✕</button>
      </div>
    </div>

    <button type="submit" class="btn btn-navy" style="padding:13px 40px;font-size:15px">💾 حفظ الإعدادات</button>
  </form>
</div>

<script>
function toggleLogoType(v){
  document.getElementById('emoji-box').style.display=v==='emoji'?'':'none';
  document.getElementById('img-box').style.display=v==='image'?'':'none';
}
function previewImg(input,zoneId,prevId){
  if(!input.files||!input.files[0])return;
  const r=new FileReader();
  r.onload=e=>{
    document.getElementById(zoneId).classList.add('has-img');
    document.getElementById(prevId).src=e.target.result;
  };
  r.readAsDataURL(input.files[0]);
}
function clearImg(zoneId,prevId){
  document.getElementById(zoneId).classList.remove('has-img');
  document.getElementById(prevId).src='';
  document.getElementById(zoneId).querySelector('input[type=file]').value='';
}
</script>
</body></html>"""


if __name__ == "__main__":
    app.run(debug=True, port=5000)
