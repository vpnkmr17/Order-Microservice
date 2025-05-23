from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime
import os
import sys

app = Flask(__name__)

# Try multiple options for database URL to resolve the environment variable issues
try:
    # First attempt - directly set SQLite for simplicity
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print(f"Using database: sqlite:///orders.db")
    
    db = SQLAlchemy(app)
    
    # Test connection
    with app.app_context():
        db.engine.connect()
    
    print("Successfully connected to SQLite database")
    
except Exception as e:
    print(f"SQLite connection failed: {str(e)}", file=sys.stderr)
    print("Attempting to use backup database configuration...")
    
    try:
        # Fallback to PostgreSQL with hardcoded credentials as a last resort
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/postgres'
        db = SQLAlchemy(app)
        
        # Test connection
        with app.app_context():
            db.engine.connect()
            
        print("Successfully connected to PostgreSQL database")
        
    except Exception as e2:
        print(f"PostgreSQL connection also failed: {str(e2)}", file=sys.stderr)
        sys.exit(1)

# Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Float, nullable=False)
    sub_total = db.Column(db.Float, nullable=False)
    products = db.relationship('Product', backref='order', lazy=True, cascade="all, delete-orphan")
    
# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "<p>Order Management API</p>"

@app.route("/api/v1/orders", methods=["GET"])
def get_all_orders():
    try:
        orders = Order.query.all()
        result = []
        
        for order in orders:
            products = []
            for product in order.products:
                products.append({
                    "product_name": product.product_name,
                    "price": product.price,
                    "quantity": product.quantity
                })
            
            result.append({
                "order_number": order.order_number,
                "order_date": order.order_date.strftime('%Y-%m-%d'),
                "total": order.total,
                "sub_total": order.sub_total,
                "products": products
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/orders/<string:order_number>", methods=["GET"])
def get_order_by_number(order_number):
    try:
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            return jsonify({"error": "Order not found"}), 404
            
        products = []
        for product in order.products:
            products.append({
                "product_name": product.product_name,
                "price": product.price,
                "quantity": product.quantity
            })
        
        result = {
            "order_number": order.order_number,
            "order_date": order.order_date.strftime('%Y-%m-%d'),
            "total": order.total,
            "sub_total": order.sub_total,
            "products": products
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/orders", methods=["POST"])
def create_new_order():
    try:
        data = request.json
        
        # Validate required fields
        if not all(k in data for k in ['order_date', 'total', 'sub_total', 'products']):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Format the date
        try:
            order_date = datetime.strptime(data['order_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Generate unique order number
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Create order
        new_order = Order(
            order_number=order_number,
            order_date=order_date,
            total=data['total'],
            sub_total=data['sub_total']
        )
        
        # Add products
        for product_data in data['products']:
            if not all(k in product_data for k in ['product_name', 'price', 'quantity']):
                return jsonify({"error": "Product missing required fields"}), 400
                
            product = Product(
                product_name=product_data['product_name'],
                price=product_data['price'],
                quantity=product_data['quantity'],
                order=new_order
            )
            db.session.add(product)
        
        db.session.add(new_order)
        db.session.commit()
        
        return jsonify({
            "message": "Order created successfully",
            "order_number": order_number
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)


