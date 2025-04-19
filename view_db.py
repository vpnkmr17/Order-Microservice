from app import app, db, Order, Product

# Function to display all orders and their products
def view_all_orders():
    print("\n=== All Orders ===")
    orders = Order.query.all()
    
    if not orders:
        print("No orders found in the database.")
        return
    
    for order in orders:
        print(f"\nOrder Number: {order.order_number}")
        print(f"Order Date: {order.order_date}")
        print(f"Total: ${order.total}")
        print(f"Sub-Total: ${order.sub_total}")
        print("\nProducts:")
        
        if not order.products:
            print("  No products in this order.")
        else:
            for product in order.products:
                print(f"  - {product.product_name}: ${product.price} x {product.quantity}")

# Function to display all products
def view_all_products():
    print("\n=== All Products ===")
    products = Product.query.all()
    
    if not products:
        print("No products found in the database.")
        return
    
    for product in products:
        print(f"Product: {product.product_name}, Price: ${product.price}, Quantity: {product.quantity}, Order ID: {product.order_id}")

if __name__ == "__main__":
    with app.app_context():
        view_all_orders()
        view_all_products() 