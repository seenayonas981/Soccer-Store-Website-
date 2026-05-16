// server.js - Main API file
const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Create Express app
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Database connection pool
const pool = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    port: process.env.DB_PORT || 3306,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// Promise wrapper
const promisePool = pool.promise();

// Test database connection
async function testConnection() {
    try {
        const [rows] = await promisePool.query('SELECT 1 + 1 AS result');
        console.log('✅ Database connected successfully!');
        console.log('📊 Database:', process.env.DB_NAME);
        console.log('🔌 Host:', process.env.DB_HOST);
    } catch (error) {
        console.error('❌ Database connection failed:', error.message);
        console.log('Please check your .env file settings');
    }
}
testConnection();

// ============================================
// HOME ROUTE
// ============================================
app.get('/', (req, res) => {
    res.json({
        message: 'Soccer Store API is running!',
        endpoints: {
            products: '/api/products',
            product_by_id: '/api/products/:id',
            categories: '/api/categories',
            customers: '/api/customers',
            orders: '/api/orders',
            order_by_id: '/api/orders/:id',
            cart: '/api/cart',
            reviews: '/api/reviews'
        }
    });
});

// ============================================
// PRODUCT ROUTES
// ============================================

// GET all products
app.get('/api/products', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT p.*, c.CategoryName 
            FROM Product p
            JOIN Category c ON p.CategoryID = c.CategoryID
            WHERE p.IsActive = 1
            ORDER BY p.ProductName
        `);
        res.json(rows);
    } catch (error) {
        console.error('Error fetching products:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// GET single product by ID
app.get('/api/products/:id', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT p.*, c.CategoryName 
            FROM Product p
            JOIN Category c ON p.CategoryID = c.CategoryID
            WHERE p.ProductID = ? AND p.IsActive = 1
        `, [req.params.id]);

        if (rows.length === 0) {
            return res.status(404).json({ error: 'Product not found' });
        }
        res.json(rows[0]);
    } catch (error) {
        console.error('Error fetching product:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ============================================
// CATEGORY ROUTES
// ============================================

// GET all categories
app.get('/api/categories', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT * FROM Category ORDER BY CategoryName
        `);
        res.json(rows);
    } catch (error) {
        console.error('Error fetching categories:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ============================================
// CUSTOMER ROUTES
// ============================================

// GET all customers (for admin)
app.get('/api/customers', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT CustomerID, FirstName, LastName, Email, Phone, Address, RegistrationDate, IsActive
            FROM Customer
            ORDER BY LastName, FirstName
        `);
        res.json(rows);
    } catch (error) {
        console.error('Error fetching customers:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// GET single customer by ID
app.get('/api/customers/:id', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT CustomerID, FirstName, LastName, Email, Phone, Address, RegistrationDate, IsActive
            FROM Customer
            WHERE CustomerID = ?
        `, [req.params.id]);

        if (rows.length === 0) {
            return res.status(404).json({ error: 'Customer not found' });
        }
        res.json(rows[0]);
    } catch (error) {
        console.error('Error fetching customer:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ============================================
// ORDER ROUTES
// ============================================

// GET all orders (for admin)
app.get('/api/orders', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT o.*, c.FirstName, c.LastName, c.Email
            FROM \`Order\` o
            JOIN Customer c ON o.CustomerID = c.CustomerID
            ORDER BY o.OrderDate DESC
        `);
        res.json(rows);
    } catch (error) {
        console.error('Error fetching orders:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// GET order by ID with details
app.get('/api/orders/:id', async (req, res) => {
    try {
        // Get order header
        const [orderRows] = await promisePool.query(`
            SELECT o.*, c.FirstName, c.LastName, c.Email, c.Phone, c.Address
            FROM \`Order\` o
            JOIN Customer c ON o.CustomerID = c.CustomerID
            WHERE o.OrderID = ?
        `, [req.params.id]);

        if (orderRows.length === 0) {
            return res.status(404).json({ error: 'Order not found' });
        }

        // Get order details
        const [detailRows] = await promisePool.query(`
            SELECT od.*, p.ProductName, p.ImageURL
            FROM Order_Details od
            JOIN Product p ON od.ProductID = p.ProductID
            WHERE od.OrderID = ?
        `, [req.params.id]);

        const order = orderRows[0];
        order.items = detailRows;

        res.json(order);
    } catch (error) {
        console.error('Error fetching order:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ============================================
// CART ROUTES
// ============================================

// GET cart for a customer
app.get('/api/cart/:customerId', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT c.CartID, c.ProductID, c.Quantity, c.AddedDate,
                   p.ProductName, p.Price, p.ImageURL, p.StockQuantity
            FROM Cart c
            JOIN Product p ON c.ProductID = p.ProductID
            WHERE c.CustomerID = ?
            ORDER BY c.AddedDate DESC
        `, [req.params.customerId]);

        // Calculate total
        let total = 0;
        rows.forEach(item => {
            total += item.Price * item.Quantity;
        });

        res.json({
            items: rows,
            total: total,
            itemCount: rows.length
        });
    } catch (error) {
        console.error('Error fetching cart:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ADD to cart
app.post('/api/cart', async (req, res) => {
    const { customerId, productId, quantity } = req.body;

    if (!customerId || !productId || !quantity || quantity < 1) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    try {
        // Check if item already in cart
        const [existing] = await promisePool.query(
            'SELECT * FROM Cart WHERE CustomerID = ? AND ProductID = ?',
            [customerId, productId]
        );

        if (existing.length > 0) {
            // Update quantity
            await promisePool.query(
                'UPDATE Cart SET Quantity = Quantity + ? WHERE CustomerID = ? AND ProductID = ?',
                [quantity, customerId, productId]
            );
        } else {
            // Insert new item
            await promisePool.query(
                'INSERT INTO Cart (CustomerID, ProductID, Quantity) VALUES (?, ?, ?)',
                [customerId, productId, quantity]
            );
        }

        res.json({ success: true, message: 'Item added to cart' });
    } catch (error) {
        console.error('Error adding to cart:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// UPDATE cart item quantity
app.put('/api/cart/:cartId', async (req, res) => {
    const { quantity } = req.body;

    if (!quantity || quantity < 1) {
        return res.status(400).json({ error: 'Quantity must be at least 1' });
    }

    try {
        await promisePool.query(
            'UPDATE Cart SET Quantity = ? WHERE CartID = ?',
            [quantity, req.params.cartId]
        );
        res.json({ success: true, message: 'Cart updated' });
    } catch (error) {
        console.error('Error updating cart:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// REMOVE from cart
app.delete('/api/cart/:cartId', async (req, res) => {
    try {
        await promisePool.query('DELETE FROM Cart WHERE CartID = ?', [req.params.cartId]);
        res.json({ success: true, message: 'Item removed from cart' });
    } catch (error) {
        console.error('Error removing from cart:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ============================================
// REVIEW ROUTES
// ============================================

// GET reviews for a product
app.get('/api/reviews/product/:productId', async (req, res) => {
    try {
        const [rows] = await promisePool.query(`
            SELECT r.*, c.FirstName, c.LastName
            FROM Review r
            JOIN Customer c ON r.CustomerID = c.CustomerID
            WHERE r.ProductID = ?
            ORDER BY r.ReviewDate DESC
        `, [req.params.productId]);

        // Calculate average rating
        let avgRating = 0;
        if (rows.length > 0) {
            const sum = rows.reduce((acc, r) => acc + r.Rating, 0);
            avgRating = sum / rows.length;
        }

        res.json({
            reviews: rows,
            averageRating: avgRating,
            totalReviews: rows.length
        });
    } catch (error) {
        console.error('Error fetching reviews:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ADD a review
app.post('/api/reviews', async (req, res) => {
    const { productId, customerId, rating, comment } = req.body;

    if (!productId || !customerId || !rating) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    if (rating < 1 || rating > 5) {
        return res.status(400).json({ error: 'Rating must be between 1 and 5' });
    }

    try {
        await promisePool.query(
            'INSERT INTO Review (ProductID, CustomerID, Rating, Comment) VALUES (?, ?, ?, ?)',
            [productId, customerId, rating, comment || null]
        );
        res.json({ success: true, message: 'Review added' });
    } catch (error) {
        console.error('Error adding review:', error);
        res.status(500).json({ error: 'Database error' });
    }
});

// ============================================
// START SERVER
// ============================================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
});