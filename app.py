#########################################################
# Soccer Store API - Python Version
# Connects to local XAMPP MariaDB database
#########################################################

# Module Imports
import mariadb
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ========================================================
# DATABASE CONNECTION
# ========================================================

def get_db_connection():
    """Create and return a database connection to local XAMPP"""
    try:
        conn = mariadb.connect(
            user="root",
            password="root123",
            host="127.0.0.1",
            port=3306,
            database="soccershop_db"
        )
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None

# Test connection on startup
print("=" * 50)
print("SOCCER STORE API - Starting...")
print("=" * 50)

test_conn = get_db_connection()
if test_conn:
    print("✅ Database connected successfully!")
    print("📊 Database: soccershop_db")
    print("🔌 Host: 127.0.0.1")
    test_conn.close()
else:
    print("❌ Database connection failed!")
    print("Make sure XAMPP MySQL is running")
    sys.exit(1)

# ========================================================
# API HANDLER
# ========================================================

class SoccerStoreHandler(BaseHTTPRequestHandler):
    
    def send_json(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def send_error_response(self, message, status=400):
        """Send error response"""
        self.send_json({"error": message}, status)
    
    def serve_html_file(self, filename):
        """Serve an HTML file"""
        try:
            with open(filename, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
            return True
        except FileNotFoundError:
            return False
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"REQUESTED PATH: {self.path}")  # DEBUG - shows what URL is being requested
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # ============================================
        # SERVE HTML FILES (MUST BE FIRST!)
        # ============================================
        
        # Serve soccer-store.html when root is requested
        if path == '/' or path == '/soccer-store.html':
            if self.serve_html_file('soccer-store.html'):
                return
            else:
                self.send_error_response("soccer-store.html not found", 404)
                return
        
        # Serve admin.html
        if path == '/admin.html':
            if self.serve_html_file('admin.html'):
                return
            else:
                self.send_error_response("admin.html not found", 404)
                return
        
        # ============================================
        # API ROUTES
        # ============================================
        
        # Home API route
        if path == '/api/':
            self.send_json({
                "message": "Soccer Store API is running!",
                "endpoints": {
                    "products": "/api/products",
                    "product_by_id": "/api/products/:id",
                    "categories": "/api/categories",
                    "customers": "/api/customers",
                    "orders": "/api/orders",
                    "cart": "/api/cart/:customerId"
                }
            })
        
        # GET all products
        elif path == '/api/products':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("""
                SELECT p.*, c.CategoryName 
                FROM Product p
                JOIN Category c ON p.CategoryID = c.CategoryID
                WHERE p.IsActive = 1
                ORDER BY p.ProductName
            """)
            
            products = []
            for row in cur:
                products.append({
                    "ProductID": row[0],
                    "ProductName": row[1],
                    "Description": row[2],
                    "Price": float(row[3]),
                    "StockQuantity": row[4],
                    "IsActive": row[5],
                    "CategoryID": row[6],
                    "ImageURL": row[7],
                    "CategoryName": row[8]
                })
            
            cur.close()
            conn.close()
            self.send_json(products)
        
        # GET single product by ID
        elif path.startswith('/api/products/'):
            product_id = path.split('/')[-1]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("""
                SELECT p.*, c.CategoryName 
                FROM Product p
                JOIN Category c ON p.CategoryID = c.CategoryID
                WHERE p.ProductID = ? AND p.IsActive = 1
            """, (product_id,))
            
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row:
                self.send_json({
                    "ProductID": row[0],
                    "ProductName": row[1],
                    "Description": row[2],
                    "Price": float(row[3]),
                    "StockQuantity": row[4],
                    "IsActive": row[5],
                    "CategoryID": row[6],
                    "ImageURL": row[7],
                    "CategoryName": row[8]
                })
            else:
                self.send_error_response("Product not found", 404)
        
        # GET all categories
        elif path == '/api/categories':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("SELECT * FROM Category ORDER BY CategoryName")
            
            categories = []
            for row in cur:
                categories.append({
                    "CategoryID": row[0],
                    "CategoryName": row[1],
                    "Description": row[2]
                })
            
            cur.close()
            conn.close()
            self.send_json(categories)
        
        # GET all customers
        elif path == '/api/customers':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("""
                SELECT CustomerID, FirstName, LastName, Email, Phone, Address, RegistrationDate, IsActive
                FROM Customer
                ORDER BY LastName, FirstName
            """)
            
            customers = []
            for row in cur:
                customers.append({
                    "CustomerID": row[0],
                    "FirstName": row[1],
                    "LastName": row[2],
                    "Email": row[3],
                    "Phone": row[4],
                    "Address": row[5],
                    "RegistrationDate": str(row[6]),
                    "IsActive": row[7]
                })
            
            cur.close()
            conn.close()
            self.send_json(customers)
        
        # GET all orders
        elif path == '/api/orders':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("""
                SELECT o.*, c.FirstName, c.LastName, c.Email
                FROM `Order` o
                JOIN Customer c ON o.CustomerID = c.CustomerID
                ORDER BY o.OrderDate DESC
            """)
            
            orders = []
            for row in cur:
                orders.append({
                    "OrderID": row[0],
                    "OrderDate": str(row[1]),
                    "TotalAmount": float(row[2]),
                    "Status": row[3],
                    "CustomerID": row[4],
                    "ShippingAddress": row[5],
                    "TrackingNumber": row[6],
                    "CustomerFirstName": row[7],
                    "CustomerLastName": row[8],
                    "CustomerEmail": row[9]
                })
            
            cur.close()
            conn.close()
            self.send_json(orders)
        
        # GET single order by ID with details
        elif path.startswith('/api/orders/') and len(path.split('/')) == 4:
            order_id = path.split('/')[-1]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("""
                SELECT o.*, c.FirstName, c.LastName, c.Email, c.Phone, c.Address
                FROM `Order` o
                JOIN Customer c ON o.CustomerID = c.CustomerID
                WHERE o.OrderID = ?
            """, (order_id,))
            
            order_row = cur.fetchone()
            
            if not order_row:
                self.send_error_response("Order not found", 404)
                cur.close()
                conn.close()
                return
            
            cur.execute("""
                SELECT od.*, p.ProductName
                FROM Order_Details od
                JOIN Product p ON od.ProductID = p.ProductID
                WHERE od.OrderID = ?
            """, (order_id,))
            
            items = []
            for row in cur:
                items.append({
                    "ProductID": row[1],
                    "ProductName": row[4],
                    "Quantity": row[2],
                    "UnitPrice": float(row[3])
                })
            
            cur.close()
            conn.close()
            
            self.send_json({
                "OrderID": order_row[0],
                "OrderDate": str(order_row[1]),
                "TotalAmount": float(order_row[2]),
                "Status": order_row[3],
                "CustomerID": order_row[4],
                "ShippingAddress": order_row[5],
                "TrackingNumber": order_row[6],
                "CustomerFirstName": order_row[7],
                "CustomerLastName": order_row[8],
                "CustomerEmail": order_row[9],
                "CustomerPhone": order_row[10],
                "CustomerAddress": order_row[11],
                "items": items
            })
        
        # GET cart for a customer
        elif path.startswith('/api/cart/'):
            customer_id = path.split('/')[-1]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("""
                SELECT c.CartID, c.ProductID, c.Quantity, c.AddedDate,
                       p.ProductName, p.Price, p.ImageURL, p.StockQuantity
                FROM Cart c
                JOIN Product p ON c.ProductID = p.ProductID
                WHERE c.CustomerID = ?
                ORDER BY c.AddedDate DESC
            """, (customer_id,))
            
            items = []
            total = 0
            for row in cur:
                subtotal = float(row[5]) * row[2]
                total += subtotal
                items.append({
                    "CartID": row[0],
                    "ProductID": row[1],
                    "Quantity": row[2],
                    "AddedDate": str(row[3]),
                    "ProductName": row[4],
                    "Price": float(row[5]),
                    "ImageURL": row[6],
                    "StockQuantity": row[7]
                })
            
            cur.close()
            conn.close()
            
            self.send_json({
                "items": items,
                "total": total,
                "itemCount": len(items)
            })
        
        else:
            self.send_error_response("Endpoint not found", 404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
        except:
            self.send_error_response("Invalid JSON", 400)
            return
        
        # REGISTER - /api/customers
        if path == '/api/customers':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO Customer (FirstName, LastName, Email, Phone, Address, PasswordHash, RegistrationDate, IsActive)
                    VALUES (?, ?, ?, ?, ?, ?, NOW(), 1)
                """, (data['firstName'], data['lastName'], data['email'], 
                      data.get('phone', ''), data['address'], data['password']))
                
                conn.commit()
                self.send_json({"success": True}, 201)
            except mariadb.Error as e:
                self.send_error_response(str(e), 400)
            finally:
                cur.close()
                conn.close()
            return
        
        # LOGIN - /api/customers/login
        elif path == '/api/customers/login':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("""
                SELECT CustomerID, FirstName, LastName, Email, Phone, Address, PasswordHash
                FROM Customer
                WHERE Email = ? AND IsActive = 1
            """, (data['email'],))
            
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row and row[6] == data['password']:
                self.send_json({
                    "CustomerID": row[0],
                    "FirstName": row[1],
                    "LastName": row[2],
                    "Email": row[3],
                    "Phone": row[4],
                    "Address": row[5]
                })
            else:
                self.send_error_response("Invalid credentials", 401)
            return
        
        # ADD TO CART - /api/cart
        elif path == '/api/cart':
            customer_id = data.get('customerId')
            product_id = data.get('productId')
            quantity = data.get('quantity')
            
            if not all([customer_id, product_id, quantity]):
                self.send_error_response("Missing required fields", 400)
                return
            
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            
            # Check if item already in cart
            cur.execute("""
                SELECT * FROM Cart WHERE CustomerID = ? AND ProductID = ?
            """, (customer_id, product_id))
            
            existing = cur.fetchone()
            
            if existing:
                cur.execute("""
                    UPDATE Cart SET Quantity = Quantity + ? 
                    WHERE CustomerID = ? AND ProductID = ?
                """, (quantity, customer_id, product_id))
            else:
                cur.execute("""
                    INSERT INTO Cart (CustomerID, ProductID, Quantity) 
                    VALUES (?, ?, ?)
                """, (customer_id, product_id, quantity))
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.send_json({"success": True, "message": "Item added to cart"})
            return
        
        # CREATE ORDER - /api/orders (UPDATED with payment)
        elif path == '/api/orders':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                # Insert order with shipping address
                cur.execute("""
                    INSERT INTO `Order` (CustomerID, TotalAmount, Status, OrderDate, ShippingAddress)
                    VALUES (?, ?, 'Processing', NOW(), ?)
                """, (data['customerId'], data['totalAmount'], data.get('shippingAddress', '')))
                
                order_id = cur.lastrowid
                
                # Insert order details and update stock
                for item in data['items']:
                    cur.execute("""
                        INSERT INTO Order_Details (OrderID, ProductID, Quantity, UnitPrice)
                        VALUES (?, ?, ?, ?)
                    """, (order_id, item['productId'], item['quantity'], item['price']))
                    
                    cur.execute("""
                        UPDATE Product SET StockQuantity = StockQuantity - ?
                        WHERE ProductID = ?
                    """, (item['quantity'], item['productId']))
                
                # Insert payment record
                cur.execute("""
                    INSERT INTO Payment (OrderID, Amount, PaymentMethod, PaymentDate, Status)
                    VALUES (?, ?, ?, NOW(), 'Completed')
                """, (order_id, data['totalAmount'], data.get('paymentMethod', 'Credit Card')))
                
                conn.commit()
                self.send_json({"success": True, "orderId": order_id}, 201)
            except mariadb.Error as e:
                conn.rollback()
                self.send_error_response(str(e), 500)
            finally:
                cur.close()
                conn.close()
            return
        
        # CREATE PRODUCT - /api/products
        elif path == '/api/products':
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO Product (ProductName, Description, Price, StockQuantity, IsActive, CategoryID, ImageURL)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data.get('productName'), data.get('description'), data.get('price'), 
                      data.get('stockQuantity'), data.get('isActive'), data.get('categoryId'), 
                      data.get('imageURL')))
                conn.commit()
                self.send_json({"success": True, "productId": cur.lastrowid}, 201)
            except mariadb.Error as e:
                self.send_error_response(str(e), 500)
            finally:
                cur.close()
                conn.close()
            return
        
        # UPDATE ORDER STATUS - /api/orders/:id/status
        elif '/api/orders/' in path and '/status' in path:
            parts = path.split('/')
            order_id = parts[3]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE `Order` SET Status=? WHERE OrderID=?
                """, (data.get('status'), order_id))
                conn.commit()
                self.send_json({"success": True})
            except mariadb.Error as e:
                self.send_error_response(str(e), 500)
            finally:
                cur.close()
                conn.close()
            return
        
        # UPDATE PRODUCT - /api/products/:id
        elif path.startswith('/api/products/'):
            product_id = path.split('/')[-1]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE Product 
                    SET ProductName=?, Description=?, Price=?, StockQuantity=?, IsActive=?, CategoryID=?, ImageURL=?
                    WHERE ProductID=?
                """, (data.get('productName'), data.get('description'), data.get('price'), 
                      data.get('stockQuantity'), data.get('isActive'), data.get('categoryId'), 
                      data.get('imageURL'), product_id))
                conn.commit()
                self.send_json({"success": True})
            except mariadb.Error as e:
                self.send_error_response(str(e), 500)
            finally:
                cur.close()
                conn.close()
            return
        
        # If no match
        else:
            self.send_error_response("Endpoint not found", 404)
    
    def do_PUT(self):
        """Handle PUT requests (for admin functions)"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
        except:
            self.send_error_response("Invalid JSON", 400)
            return
        
        # UPDATE ORDER STATUS - /api/orders/:id/status
        if '/api/orders/' in path and '/status' in path:
            parts = path.split('/')
            order_id = parts[3]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE `Order` SET Status=? WHERE OrderID=?
                """, (data.get('status'), order_id))
                conn.commit()
                self.send_json({"success": True})
            except mariadb.Error as e:
                self.send_error_response(str(e), 500)
            finally:
                cur.close()
                conn.close()
            return
        
        # UPDATE PRODUCT - /api/products/:id
        elif path.startswith('/api/products/'):
            product_id = path.split('/')[-1]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE Product 
                    SET ProductName=?, Description=?, Price=?, StockQuantity=?, IsActive=?, CategoryID=?, ImageURL=?
                    WHERE ProductID=?
                """, (data.get('productName'), data.get('description'), data.get('price'), 
                      data.get('stockQuantity'), data.get('isActive'), data.get('categoryId'), 
                      data.get('imageURL'), product_id))
                conn.commit()
                self.send_json({"success": True})
            except mariadb.Error as e:
                self.send_error_response(str(e), 500)
            finally:
                cur.close()
                conn.close()
            return
        
        else:
            self.send_error_response("Endpoint not found", 404)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # DELETE PRODUCT - /api/products/:id
        if path.startswith('/api/products/'):
            product_id = path.split('/')[-1]
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM Product WHERE ProductID = ?", (product_id,))
                conn.commit()
                self.send_json({"success": True})
            except mariadb.Error as e:
                self.send_error_response(str(e), 500)
            finally:
                cur.close()
                conn.close()
            return
        
        # REMOVE from cart
        elif path.startswith('/api/cart/'):
            cart_id = path.split('/')[-1]
            
            conn = get_db_connection()
            if not conn:
                self.send_error_response("Database connection failed", 500)
                return
            
            cur = conn.cursor()
            cur.execute("DELETE FROM Cart WHERE CartID = ?", (cart_id,))
            conn.commit()
            
            cur.close()
            conn.close()
            
            self.send_json({"success": True, "message": "Item removed from cart"})
        
        else:
            self.send_error_response("Endpoint not found", 404)
    
    def log_message(self, format, *args):
        """Override to suppress default logging"""
        print(f"{self.address_string()} - {format % args}")

# ========================================================
# START SERVER
# ========================================================

def run_server(port=3000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SoccerStoreHandler)
    print(f"\n🚀 Server running on port {port}")
    print(f"📍 Visit: http://localhost:{port}")
    print("\nAvailable endpoints:")
    print("  GET  / (serves soccer-store.html)")
    print("  GET  /admin.html (serves admin dashboard)")
    print("  GET  /api/products")
    print("  GET  /api/products/{id}")
    print("  GET  /api/categories")
    print("  GET  /api/customers")
    print("  GET  /api/orders")
    print("  GET  /api/orders/{id}")
    print("  GET  /api/cart/{customerId}")
    print("  POST /api/customers (register)")
    print("  POST /api/customers/login")
    print("  POST /api/cart (add to cart)")
    print("  POST /api/orders (checkout)")
    print("  POST /api/products (add product - admin)")
    print("  PUT /api/products/{id} (update product - admin)")
    print("  PUT /api/orders/{id}/status (update order - admin)")
    print("  DELETE /api/products/{id} (delete product - admin)")
    print("  DELETE /api/cart/{cartId}")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()