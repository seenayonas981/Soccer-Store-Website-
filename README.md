# Soccer Store API

Backend API for Soccer Equipment Online Store.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | Get all products |
| GET | `/api/products/:id` | Get single product |
| GET | `/api/categories` | Get all categories |
| GET | `/api/customers` | Get all customers |
| GET | `/api/customers/:id` | Get single customer |
| GET | `/api/orders` | Get all orders |
| GET | `/api/orders/:id` | Get order details |
| GET | `/api/cart/:customerId` | Get user cart |
| POST | `/api/cart` | Add to cart |
| PUT | `/api/cart/:cartId` | Update cart item |
| DELETE | `/api/cart/:cartId` | Remove from cart |
| GET | `/api/reviews/product/:productId` | Get product reviews |
| POST | `/api/reviews` | Add a review |

## Deployment

This API is deployed on Render.com