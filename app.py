from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import time
from datetime import datetime, timedelta
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 添加自定义过滤器
@app.template_filter('format_currency')
def format_currency(value):
    """Format currency with thousand separators"""
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return "0.00"

@app.template_filter('from_json')
def from_json(value):
    """Parse JSON string to list"""
    if not value:
        return []
    try:
        import json
        return json.loads(value)
    except (ValueError, TypeError, json.JSONDecodeError):
        return []

@app.template_filter('get_first_image')
def get_first_image(value):
    """Get first image from product image field (supports both old and new format)"""
    if not value:
        return None
    try:
        import json
        images = json.loads(value)
        if isinstance(images, list) and len(images) > 0:
            return images[0]
        elif isinstance(images, str):
            return images
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    # Old format or not JSON: return as is
    return value if isinstance(value, str) else None

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login first'

# Favicon route to avoid 404 errors
@app.route('/favicon.ico')
def favicon():
    """Return favicon to avoid 404 errors"""
    return redirect(url_for('static', filename='images/favicon.svg'))

@app.route('/static/images/favicon.ico')
def favicon_ico():
    """Return SVG favicon as ICO to avoid 404 errors"""
    # Return SVG file with appropriate content type
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'),
        'favicon.svg',
        mimetype='image/svg+xml'
    )

# 创建上传文件夹
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 登录失败跟踪字典
# 格式: {identifier: {'count': 失败次数, 'lock_time': 锁定时间戳}}
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5分钟（秒）

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(200))
    variants = db.Column(db.Text)  # JSON string storing variant options like ["XL", "2XL", "3XL"]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), nullable=False, index=True)  # Removed unique constraint to allow multiple items per order
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    variant = db.Column(db.String(50))  # Selected variant like "XL", "2XL", etc.
    total_price = db.Column(db.Float, nullable=False)
    contact_info = db.Column(db.Text)  # Contact information provided by user during checkout
    status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    product = db.relationship('Product', backref=db.backref('orders', lazy=True))

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # 关联
    order = db.relationship('Order', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))

class OrderRecord(db.Model):
    """订单记录：存储付款凭证、收据、发货凭证等图片"""
    __tablename__ = 'order_records'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), nullable=False, index=True)  # 订单号
    record_type = db.Column(db.String(20), nullable=False)  # 'payment' (付款凭证), 'receipt' (收据), 'shipped' (发货凭证)
    image_path = db.Column(db.String(500), nullable=False)  # 图片路径
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 上传者
    description = db.Column(db.Text)  # 描述信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    uploader = db.relationship('User', backref=db.backref('order_records', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    # 每次请求时从数据库重新加载用户，确保权限信息是最新的
    user = User.query.get(int(user_id))
    if user:
        # 强制刷新用户对象，确保获取最新的is_admin状态
        db.session.refresh(user)
    return user

# 路由
@app.route('/')
def index():
    products = Product.query.filter(Product.stock > 0).all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    # Get related products (exclude current product, stock > 0, max 4)
    related_products = Product.query.filter(
        Product.id != product_id,
        Product.stock > 0
    ).limit(4).all()
    
    return render_template('product_detail.html', product=product, related_products=related_products)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 获取客户端IP地址
        client_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
        identifier = f"{client_ip}:{username}"
        
        # 检查是否被锁定
        if identifier in login_attempts:
            attempt_info = login_attempts[identifier]
            if attempt_info['count'] >= MAX_LOGIN_ATTEMPTS:
                lock_time = attempt_info.get('lock_time')
                if lock_time:
                    elapsed = time.time() - lock_time
                    if elapsed < LOCKOUT_DURATION:
                        remaining_minutes = int((LOCKOUT_DURATION - elapsed) / 60)
                        remaining_seconds = int((LOCKOUT_DURATION - elapsed) % 60)
                        flash(f'Too many failed login attempts. Please wait {remaining_minutes} minutes and {remaining_seconds} seconds before trying again.')
                        return render_template('login.html', lockout_remaining=LOCKOUT_DURATION - elapsed)
                    else:
                        # 锁定时间已过，清除记录
                        del login_attempts[identifier]
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # 登录成功，清除失败记录
            if identifier in login_attempts:
                del login_attempts[identifier]
            login_user(user)
            return redirect(url_for('index'))
        else:
            # 登录失败，增加失败计数
            if identifier not in login_attempts:
                login_attempts[identifier] = {'count': 0, 'lock_time': None}
            
            login_attempts[identifier]['count'] += 1
            
            # 如果达到最大尝试次数，设置锁定时间
            if login_attempts[identifier]['count'] >= MAX_LOGIN_ATTEMPTS:
                login_attempts[identifier]['lock_time'] = time.time()
                flash(f'Too many failed login attempts. Your account has been locked for 5 minutes.')
            else:
                remaining_attempts = MAX_LOGIN_ATTEMPTS - login_attempts[identifier]['count']
                flash(f'Invalid username or password. {remaining_attempts} attempt(s) remaining.')
    
    # 清理过期的锁定记录
    current_time = time.time()
    expired_keys = [key for key, info in login_attempts.items() 
                    if info.get('lock_time') and (current_time - info['lock_time']) >= LOCKOUT_DURATION]
    for key in expired_keys:
        del login_attempts[key]
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful, please login')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)
    variant = request.json.get('variant', '')  # Get selected variant
    
    # Ensure quantity is integer type
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1
    
    product = Product.query.get_or_404(product_id)
    
    # Check variant stock if variant is provided
    if variant and product.variants:
        import json
        try:
            variants_list = json.loads(product.variants)
            variant_stock = None
            for v in variants_list:
                if isinstance(v, dict) and v.get('name') == variant:
                    variant_stock = v.get('stock', 0)
                    break
                elif isinstance(v, str) and v == variant:
                    # Old format: use product stock
                    variant_stock = product.stock
                    break
            
            if variant_stock is not None and variant_stock < quantity:
                return jsonify({'success': False, 'message': f'Insufficient stock for variant {variant}. Available: {variant_stock}'})
        except (json.JSONDecodeError, ValueError, TypeError):
            # If parsing fails, fall back to product stock
            if product.stock < quantity:
                return jsonify({'success': False, 'message': 'Insufficient stock'})
    else:
        # No variant, check product stock
        if product.stock < quantity:
            return jsonify({'success': False, 'message': 'Insufficient stock'})
    
    # Use session to store cart with variant info
    # Cart structure: {product_id: {'quantity': qty, 'variant': variant}}
    cart = session.get('cart', {})
    cart_key = str(product_id)
    
    # If variant is provided, use product_id:variant as key
    if variant:
        cart_key = f"{product_id}:{variant}"
    
    if cart_key in cart:
        if isinstance(cart[cart_key], dict):
            cart[cart_key]['quantity'] += quantity
        else:
            # Migrate old format to new format
            cart[cart_key] = {'quantity': cart[cart_key] + quantity, 'variant': variant}
    else:
        cart[cart_key] = {'quantity': quantity, 'variant': variant}
    
    session['cart'] = cart
    return jsonify({'success': True, 'message': 'Added to cart'})

@app.route('/get_cart')
@login_required
def get_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for cart_key, cart_data in cart.items():
        # Handle both old format (quantity as int) and new format (dict with quantity and variant)
        if isinstance(cart_data, dict):
            quantity = cart_data.get('quantity', 1)
            variant = cart_data.get('variant', '')
        else:
            # Old format: just quantity
            quantity = cart_data
            variant = ''
        
        # Extract product_id from cart_key (format: "product_id" or "product_id:variant")
        try:
            if ':' in cart_key:
                product_id = int(cart_key.split(':')[0])
            else:
                product_id = int(cart_key)
        except (ValueError, TypeError):
            continue  # Skip invalid product IDs
        
        product = Product.query.get(product_id)
        if product:
            # Ensure quantity is integer
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                quantity = 1
            
            item_total = product.price * quantity
            # Get first image (support both old and new format)
            import json
            first_image = None
            if product.image:
                try:
                    images = json.loads(product.image)
                    if isinstance(images, list) and len(images) > 0:
                        first_image = images[0]
                    elif isinstance(images, str):
                        first_image = images
                except (json.JSONDecodeError, ValueError, TypeError):
                    first_image = product.image if isinstance(product.image, str) else None
            
            cart_items.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'variant': variant,
                'total': item_total,
                'image': first_image
            })
            total += item_total
    
    return jsonify({'items': cart_items, 'total': total})

@app.route('/update_cart', methods=['POST'])
@login_required
def update_cart():
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')
    variant = request.json.get('variant', '')
    
    cart = session.get('cart', {})
    
    # Build cart key (same format as add_to_cart)
    cart_key = str(product_id)
    if variant:
        cart_key = f"{product_id}:{variant}"
    
    if quantity <= 0:
        cart.pop(cart_key, None)
    else:
        # Update or create cart item with variant info
        if cart_key in cart:
            if isinstance(cart[cart_key], dict):
                cart[cart_key]['quantity'] = quantity
            else:
                # Migrate old format
                cart[cart_key] = {'quantity': quantity, 'variant': variant}
        else:
            cart[cart_key] = {'quantity': quantity, 'variant': variant}
    
    session['cart'] = cart
    return jsonify({'success': True})

@app.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    session.pop('cart', None)
    return jsonify({'success': True, 'message': 'Cart cleared'})

@app.route('/submit_order', methods=['POST'])
@login_required
def submit_order():
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
        
        if request.json is None:
            return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400
        
        contact_info = request.json.get('contact_info')
        cart = session.get('cart', {})
        
        app.logger.info(f'Submit order: User {current_user.id}, Cart items: {cart}, Cart type: {type(cart)}')
        
        if not cart:
            app.logger.warning(f'Submit order failed: Cart is empty for user {current_user.id}')
            return jsonify({'success': False, 'message': 'Cart is empty'})
        
        # Generate unique order number with better uniqueness
        # Use timestamp with microseconds + longer UUID + user_id for better uniqueness
        max_attempts = 20
        order_number = None
        
        for attempt in range(max_attempts):
            # Use microseconds for better time precision
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]  # Include milliseconds
            # Use longer UUID (12 chars instead of 6) + user_id for extra uniqueness
            unique_id = f"{uuid.uuid4().hex[:12].upper()}{current_user.id:04d}"
            order_number = f"ORD{timestamp}{unique_id}"
            
            # Check if order number already exists
            existing_order = Order.query.filter_by(order_number=order_number).first()
            if not existing_order:
                break
            
            # If exists, wait a tiny bit and try again
            if attempt < max_attempts - 1:
                time.sleep(0.001)  # 1ms delay
            else:
                return jsonify({'success': False, 'message': 'Failed to generate unique order number after multiple attempts'}), 500
        
        # Create separate order for each product (match database structure)
        orders_created = []
        app.logger.info(f'Processing {len(cart)} items in cart')
        for cart_key, cart_data in cart.items():
            # Handle both old format (quantity as int) and new format (dict with quantity and variant)
            if isinstance(cart_data, dict):
                quantity = cart_data.get('quantity', 1)
                variant = cart_data.get('variant', '')
            else:
                # Old format: just quantity
                quantity = cart_data
                variant = ''
            
            # Extract product_id from cart_key (format: "product_id" or "product_id:variant")
            if ':' in cart_key:
                product_id_str = cart_key.split(':')[0]
            else:
                product_id_str = cart_key
            
            app.logger.info(f'Processing cart item: product_id={product_id_str}, quantity={quantity}, variant={variant}')
            # Convert string product_id to integer
            try:
                product_id = int(product_id_str)
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Invalid product ID: {product_id_str}'}), 400
            
            # Ensure quantity is integer
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    db.session.rollback()
                    return jsonify({'success': False, 'message': f'Invalid quantity for product {product_id_str}'}), 400
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Invalid quantity format for product {product_id_str}'}), 400
            
            product = Product.query.get(product_id)
            if not product:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Product {product_id} not found'}), 404
            
            # Check variant stock if variant is provided
            if variant and product.variants:
                import json
                try:
                    variants_list = json.loads(product.variants)
                    variant_stock = None
                    for v in variants_list:
                        if isinstance(v, dict) and v.get('name') == variant:
                            variant_stock = v.get('stock', 0)
                            break
                        elif isinstance(v, str) and v == variant:
                            # Old format: use product stock
                            variant_stock = product.stock
                            break
                    
                    if variant_stock is not None and variant_stock < quantity:
                        db.session.rollback()
                        return jsonify({'success': False, 'message': f'Variant {variant} of {product.name} has insufficient stock. Available: {variant_stock}, Requested: {quantity}'}), 400
                except (json.JSONDecodeError, ValueError, TypeError):
                    # If parsing fails, fall back to product stock
                    if product.stock < quantity:
                        db.session.rollback()
                        return jsonify({'success': False, 'message': f'Product {product.name} has insufficient stock. Available: {product.stock}, Requested: {quantity}'}), 400
            else:
                # No variant, check product stock
                if product.stock < quantity:
                    db.session.rollback()
                    return jsonify({'success': False, 'message': f'Product {product.name} has insufficient stock. Available: {product.stock}, Requested: {quantity}'}), 400
            
            # Create order
            try:
                # Store original stock for logging
                original_stock = product.stock
                
                order = Order(
                    order_number=order_number,
                    user_id=current_user.id,
                    product_id=product.id,
                    quantity=quantity,
                    variant=variant,  # Save selected variant
                    total_price=product.price * quantity,
                    contact_info=contact_info  # Save contact information
                )
                db.session.add(order)
                orders_created.append(order)
                
                # Reduce stock (variant stock if variant is provided, otherwise product stock)
                if variant and product.variants:
                    import json
                    try:
                        variants_list = json.loads(product.variants)
                        for v in variants_list:
                            if isinstance(v, dict) and v.get('name') == variant:
                                # Reduce variant stock
                                v['stock'] = max(0, v.get('stock', 0) - quantity)
                                product.variants = json.dumps(variants_list)
                                app.logger.info(f'Order item prepared: Product {product.id} ({product.name}), Variant: {variant}, Qty: {quantity}, Variant Stock: {v["stock"] + quantity} -> {v["stock"]}')
                                break
                        else:
                            # Variant not found in list, reduce product stock as fallback
                            product.stock -= quantity
                            app.logger.info(f'Order item prepared: Product {product.id} ({product.name}), Variant not found, using product stock. Qty: {quantity}, Stock: {original_stock} -> {product.stock}')
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # If parsing fails, reduce product stock
                        product.stock -= quantity
                        app.logger.info(f'Order item prepared: Product {product.id} ({product.name}), Parse error, using product stock. Qty: {quantity}, Stock: {original_stock} -> {product.stock}')
                else:
                    # No variant, reduce product stock
                    product.stock -= quantity
                    app.logger.info(f'Order item prepared: Product {product.id} ({product.name}), Qty: {quantity}, Stock: {original_stock} -> {product.stock}')
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Error creating order: {str(e)}', exc_info=True)
                return jsonify({'success': False, 'message': f'Error creating order: {str(e)}'}), 500
        
        # Commit all changes
        try:
            db.session.commit()
            app.logger.info(f'Order committed successfully: {order_number}, Orders created: {len(orders_created)}')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Database commit error: {str(e)}', exc_info=True)
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
        
        # Verify orders were actually saved and stock was updated
        saved_orders = Order.query.filter_by(order_number=order_number).all()
        app.logger.info(f'Verification: Found {len(saved_orders)} orders with order_number {order_number}')
        
        # Verify stock was updated for all products in the order
        for order in saved_orders:
            product = Product.query.get(order.product_id)
            if product:
                app.logger.info(f'Stock verification for Product {product.id} ({product.name}): Current stock = {product.stock}')
        
        # Clear cart only after successful commit
        session.pop('cart', None)
        
        return jsonify({'success': True, 'order_number': order_number})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Unexpected error in submit_order: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': f'Error submitting order: {str(e)}'}), 500

# 用户订单查看路由
@app.route('/my_orders')
@login_required
def my_orders():
    """用户查看自己的订单"""
    # Get all orders for current user, grouped by order_number
    all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Group orders by order_number
    from collections import defaultdict
    orders_by_number = defaultdict(list)
    for order in all_orders:
        orders_by_number[order.order_number].append(order)
    
    # Convert to list of order groups, each group represents one order with potentially multiple items
    order_groups = []
    for order_number, orders in orders_by_number.items():
        # Sort orders in group by created_at to get the first one as primary
        orders_sorted = sorted(orders, key=lambda x: x.created_at)
        order_groups.append({
            'order_number': order_number,
            'primary_order': orders_sorted[0],  # First order as primary for display
            'all_orders': orders_sorted,  # All orders with this order number
            'total_amount': sum(o.total_price for o in orders_sorted),
            'total_items': len(orders_sorted),
            'created_at': orders_sorted[0].created_at,
            'contact_info': orders_sorted[0].contact_info,  # Contact information from first order
            'status': orders_sorted[0].status  # Use first order's status
        })
    
    # Sort order groups by creation time (most recent first)
    order_groups.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Get order records for each order group
    for group in order_groups:
        records = OrderRecord.query.filter_by(order_number=group['order_number']).order_by(OrderRecord.created_at.desc()).all()
        group['records'] = records
    
    app.logger.info(f'My orders page: Found {len(all_orders)} order records, {len(order_groups)} unique orders for user {current_user.username}')
    return render_template('my_orders.html', order_groups=order_groups, total_orders=len(all_orders))

@app.route('/delete_order', methods=['POST'])
@login_required
def delete_my_order():
    """用户删除自己的已完成订单"""
    order_number = request.json.get('order_number')
    if not order_number:
        return jsonify({'success': False, 'message': 'Order number required'})
    
    try:
        # Get all orders with this order number
        orders = Order.query.filter_by(order_number=order_number).all()
        
        if not orders:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Verify that all orders belong to the current user
        for order in orders:
            if order.user_id != current_user.id:
                return jsonify({'success': False, 'message': 'You can only delete your own orders'})
        
        # Check if all orders are completed
        for order in orders:
            if order.status != 'completed':
                return jsonify({'success': False, 'message': 'Only completed orders can be deleted'})
        
        # Delete all orders with this order number
        for order in orders:
            db.session.delete(order)
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Order {order_number} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting order {order_number} for user {current_user.id}: {str(e)}')
        return jsonify({'success': False, 'message': f'Failed to delete order: {str(e)}'})

# 管理员路由
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Insufficient permissions')
        return redirect(url_for('index'))
    
    # Get all orders grouped by order_number
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Group orders by order_number
    from collections import defaultdict
    orders_by_number = defaultdict(list)
    for order in all_orders:
        orders_by_number[order.order_number].append(order)
    
    # Convert to list of order groups, each group represents one order with potentially multiple items
    order_groups = []
    for order_number, orders in orders_by_number.items():
        # Sort orders in group by created_at to get the first one as primary
        orders_sorted = sorted(orders, key=lambda x: x.created_at)
        order_groups.append({
            'order_number': order_number,
            'primary_order': orders_sorted[0],  # First order as primary for display
            'all_orders': orders_sorted,  # All orders with this order number
            'total_amount': sum(o.total_price for o in orders_sorted),
            'total_items': len(orders_sorted),
            'created_at': orders_sorted[0].created_at,
            'user': orders_sorted[0].user,
            'contact_info': orders_sorted[0].contact_info,  # Contact information from first order
            'status': orders_sorted[0].status  # Use first order's status
        })
    
    # Sort order groups by creation time (most recent first)
    order_groups.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Get order records for each order group
    for group in order_groups:
        records = OrderRecord.query.filter_by(order_number=group['order_number']).order_by(OrderRecord.created_at.desc()).all()
        group['records'] = records
    
    app.logger.info(f'Admin page: Found {len(all_orders)} order records, {len(order_groups)} unique orders for user {current_user.username}')
    return render_template('admin.html', order_groups=order_groups, total_orders=len(all_orders))

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Insufficient permissions')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        flash('Insufficient permissions')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        variants_text = request.form.get('variants', '').strip()
        
        # Parse variants (JSON array of objects with name and stock)
        variants = None
        if variants_text:
            import json
            try:
                # Try to parse as JSON (new format: [{"name": "XL", "stock": 10}, ...])
                variant_list = json.loads(variants_text)
                if isinstance(variant_list, list) and len(variant_list) > 0:
                    # Validate and clean variant data
                    cleaned_variants = []
                    for v in variant_list:
                        if isinstance(v, dict) and 'name' in v:
                            cleaned_variants.append({
                                'name': str(v['name']).strip(),
                                'stock': int(v.get('stock', 0))
                            })
                    if cleaned_variants:
                        variants = json.dumps(cleaned_variants)
            except (json.JSONDecodeError, ValueError, TypeError):
                # Fallback to old format (comma-separated string)
                variant_list = [v.strip() for v in variants_text.split(',') if v.strip()]
                if variant_list:
                    # Convert old format to new format
                    cleaned_variants = [{'name': v, 'stock': 0} for v in variant_list]
                    variants = json.dumps(cleaned_variants)
        
        # Handle images upload (support multiple images, max 6)
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filename = f"{uuid.uuid4().hex}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    images.append(filename)
                    # Limit to 6 images
                    if len(images) >= 6:
                        break
        
        # Store images as JSON array (compatible with old single image format)
        import json
        if images:
            image = json.dumps(images) if len(images) > 1 else images[0]
        else:
            image = None
        
        product = Product(
            name=name,
            price=price,
            description=description,
            stock=stock,
            image=image,
            variants=variants
        )
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully')
        return redirect(url_for('admin_products'))
    
    return render_template('add_product.html')

@app.route('/admin/get_orders_by_number')
@login_required
def get_orders_by_number():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Insufficient permissions'})
    
    order_number = request.args.get('order_number')
    if not order_number:
        return jsonify({'success': False, 'message': 'Order number required'})
    
    orders = Order.query.filter_by(order_number=order_number).all()
    order_ids = [order.id for order in orders]
    
    return jsonify({'success': True, 'order_ids': order_ids})

@app.route('/admin/update_order_status', methods=['POST'])
@login_required
def update_order_status():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Insufficient permissions'})
    
    order_id = request.json.get('order_id')
    status = request.json.get('status')
    
    order = Order.query.get_or_404(order_id)
    order.status = status
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/delete_order', methods=['POST'])
@login_required
def delete_order():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Insufficient permissions'})
    
    order_number = request.json.get('order_number')
    if not order_number:
        return jsonify({'success': False, 'message': 'Order number required'})
    
    try:
        # Get all orders with this order number
        orders = Order.query.filter_by(order_number=order_number).all()
        
        if not orders:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Check if all orders are completed
        for order in orders:
            if order.status != 'completed':
                return jsonify({'success': False, 'message': 'Only completed orders can be deleted'})
        
        # Delete all orders with this order number
        for order in orders:
            db.session.delete(order)
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Order {order_number} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting order {order_number}: {str(e)}')
        return jsonify({'success': False, 'message': f'Failed to delete order: {str(e)}'})

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('Insufficient permissions')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.description = request.form['description']
        product.stock = int(request.form['stock'])
        variants_text = request.form.get('variants', '').strip()
        
        # Parse variants (JSON array of objects with name and stock)
        if variants_text:
            import json
            try:
                # Try to parse as JSON (new format: [{"name": "XL", "stock": 10}, ...])
                variant_list = json.loads(variants_text)
                if isinstance(variant_list, list) and len(variant_list) > 0:
                    # Validate and clean variant data
                    cleaned_variants = []
                    for v in variant_list:
                        if isinstance(v, dict) and 'name' in v:
                            cleaned_variants.append({
                                'name': str(v['name']).strip(),
                                'stock': int(v.get('stock', 0))
                            })
                    if cleaned_variants:
                        product.variants = json.dumps(cleaned_variants)
                    else:
                        product.variants = None
                else:
                    product.variants = None
            except (json.JSONDecodeError, ValueError, TypeError):
                # Fallback to old format (comma-separated string)
                variant_list = [v.strip() for v in variants_text.split(',') if v.strip()]
                if variant_list:
                    # Convert old format to new format
                    cleaned_variants = [{'name': v, 'stock': 0} for v in variant_list]
                    product.variants = json.dumps(cleaned_variants)
                else:
                    product.variants = None
        else:
            product.variants = None
        
        # Handle images upload (support multiple images, max 6)
        if 'images' in request.files:
            files = request.files.getlist('images')
            if files and any(f.filename for f in files):
                # Delete old images
                if product.image:
                    import json
                    try:
                        # Try to parse as JSON array (new format)
                        old_images = json.loads(product.image)
                        if isinstance(old_images, list):
                            for old_img in old_images:
                                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_img)
                                if os.path.exists(old_image_path):
                                    os.remove(old_image_path)
                        else:
                            # Old format: single image string
                            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # Old format: single image string
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                
                # Save new images
                new_images = []
                for file in files:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        filename = f"{uuid.uuid4().hex}_{filename}"
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        new_images.append(filename)
                        # Limit to 6 images
                        if len(new_images) >= 6:
                            break
                
                # Store images as JSON array (compatible with old single image format)
                if new_images:
                    product.image = json.dumps(new_images) if len(new_images) > 1 else new_images[0]
        
        db.session.commit()
        flash('Product updated successfully')
        return redirect(url_for('admin_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/admin/delete_product', methods=['POST'])
@login_required
def delete_product():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Insufficient permissions'})
    
    product_id = request.json.get('product_id')
    product = Product.query.get_or_404(product_id)
    
    try:
        # Delete related order items first (query then delete individually)
        order_items = OrderItem.query.filter_by(product_id=product_id).all()
        for item in order_items:
            db.session.delete(item)
        
        # Delete related orders (query then delete individually)
        orders = Order.query.filter_by(product_id=product_id).all()
        for order in orders:
            db.session.delete(order)
        
        # Flush to ensure deletions are processed before deleting product
        db.session.flush()
        
        # Delete product images
        if product.image:
            import json
            try:
                # Try to parse as JSON array (new format)
                images = json.loads(product.image)
                if isinstance(images, list):
                    # Multiple images
                    for img in images:
                        image_path = os.path.join(app.config['UPLOAD_FOLDER'], img)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                else:
                    # Old format: single image string
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
            except (json.JSONDecodeError, ValueError, TypeError):
                # Old format: single image string
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
        
        # Delete product
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting product {product_id}: {str(e)}')
        return jsonify({'success': False, 'message': f'Failed to delete product: {str(e)}'})

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Insufficient permissions')
        return redirect(url_for('index'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users, current_user=current_user)

@app.route('/admin/toggle_admin', methods=['POST'])
@login_required
def toggle_admin():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Insufficient permissions'})
    
    user_id = request.json.get('user_id')
    is_admin = request.json.get('is_admin')
    
    # Cannot modify own admin permissions
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot modify own admin permissions'})
    
    user = User.query.get_or_404(user_id)
    user.is_admin = is_admin
    db.session.commit()
    
    action = 'set as admin' if is_admin else 'remove admin privileges'
    return jsonify({'success': True, 'message': f'Successfully {action}'})

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """允许所有登录用户修改自己的密码"""
    try:
        user_id = request.json.get('user_id')
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')
        
        # Validate input
        if not user_id or not old_password or not new_password:
            return jsonify({'success': False, 'message': '所有字段都是必填的'})
        
        # Can only change own password
        if int(user_id) != current_user.id:
            return jsonify({'success': False, 'message': '您只能修改自己的密码'})
        
        # Validate new password length
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '密码必须至少6个字符'})
        
        # Verify old password
        if not current_user.check_password(old_password):
            return jsonify({'success': False, 'message': '当前密码不正确'})
        
        # Check if new password is different from old password
        if current_user.check_password(new_password):
            return jsonify({'success': False, 'message': '新密码必须与当前密码不同'})
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '密码修改成功'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'修改密码失败: {str(e)}'})

# 保留旧路由以兼容管理员菜单
@app.route('/admin/change_password', methods=['POST'])
@login_required
def admin_change_password():
    """管理员修改密码（重定向到通用修改密码接口）"""
    return change_password()

# 订单记录相关路由
@app.route('/upload_order_record', methods=['POST'])
@login_required
def upload_order_record():
    """上传订单记录（付款凭证、收据、发货凭证）"""
    try:
        order_number = request.form.get('order_number')
        record_type = request.form.get('record_type')  # 'payment', 'receipt', 'shipped'
        description = request.form.get('description', '')
        
        if not order_number or not record_type:
            return jsonify({'success': False, 'message': '订单号和记录类型是必填的'})
        
        # 验证订单号是否存在
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'})
        
        # 验证权限：普通用户只能上传自己订单的付款凭证，管理员可以上传所有类型的记录
        if not current_user.is_admin:
            if order.user_id != current_user.id:
                return jsonify({'success': False, 'message': '您只能为自己的订单上传记录'})
            if record_type != 'payment':
                return jsonify({'success': False, 'message': '普通用户只能上传付款凭证'})
        
        # 验证记录类型
        if record_type not in ['payment', 'receipt', 'shipped']:
            return jsonify({'success': False, 'message': '无效的记录类型'})
        
        # 处理文件上传
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': '请选择要上传的图片'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': '请选择要上传的图片'})
        
        # 验证文件类型
        if file and file.filename:
            filename = secure_filename(file.filename)
            if '.' in filename:
                ext = filename.rsplit('.', 1)[1].lower()
                if ext not in app.config['ALLOWED_EXTENSIONS']:
                    return jsonify({'success': False, 'message': '不支持的文件类型，只支持 PNG, JPG, JPEG, GIF'})
            else:
                return jsonify({'success': False, 'message': '文件必须包含扩展名'})
            
            # 生成唯一文件名
            filename = f"order_record_{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 创建订单记录
            order_record = OrderRecord(
                order_number=order_number,
                record_type=record_type,
                image_path=filename,
                uploaded_by=current_user.id,
                description=description
            )
            db.session.add(order_record)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': '记录上传成功',
                'record': {
                    'id': order_record.id,
                    'record_type': order_record.record_type,
                    'image_path': order_record.image_path,
                    'description': order_record.description,
                    'created_at': order_record.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        else:
            return jsonify({'success': False, 'message': '文件上传失败'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error uploading order record: {str(e)}')
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'})

@app.route('/get_order_records', methods=['GET'])
@login_required
def get_order_records():
    """获取订单记录"""
    try:
        order_number = request.args.get('order_number')
        if not order_number:
            return jsonify({'success': False, 'message': '订单号是必填的'})
        
        # 验证订单号是否存在
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'})
        
        # 验证权限：普通用户只能查看自己订单的记录
        if not current_user.is_admin:
            if order.user_id != current_user.id:
                return jsonify({'success': False, 'message': '您只能查看自己订单的记录'})
        
        # 获取订单记录
        records = OrderRecord.query.filter_by(order_number=order_number).order_by(OrderRecord.created_at.desc()).all()
        
        records_data = []
        for record in records:
            records_data.append({
                'id': record.id,
                'record_type': record.record_type,
                'image_path': record.image_path,
                'description': record.description,
                'uploaded_by': record.uploader.username if record.uploader else 'Unknown',
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({'success': True, 'records': records_data})
    
    except Exception as e:
        app.logger.error(f'Error getting order records: {str(e)}')
        return jsonify({'success': False, 'message': f'获取记录失败: {str(e)}'})

@app.route('/delete_order_record', methods=['POST'])
@login_required
def delete_order_record():
    """删除订单记录"""
    try:
        record_id = request.json.get('record_id')
        if not record_id:
            return jsonify({'success': False, 'message': '记录ID是必填的'})
        
        record = OrderRecord.query.get_or_404(record_id)
        
        # 验证权限：只能删除自己上传的记录，或管理员可以删除任何记录
        if not current_user.is_admin:
            if record.uploaded_by != current_user.id:
                return jsonify({'success': False, 'message': '您只能删除自己上传的记录'})
        
        # 删除图片文件
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], record.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # 删除记录
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '记录删除成功'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting order record: {str(e)}')
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

if __name__ == '__main__':
    with app.app_context():
        # Create admin account (if not exists)
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', phone='1234567890', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin account created: admin / admin123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
