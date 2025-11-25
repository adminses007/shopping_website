# Shopping Website Project Overview

## Project Purpose
A complete e-commerce website system with frontend display, shopping cart, order management, and admin backend functionality.

## Tech Stack
- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5 + CSS3 + JavaScript + Bootstrap 5
- **Authentication**: Flask-Login
- **File Upload**: Werkzeug

## Key Features
### Frontend Features
- Product display pages with images, prices, descriptions, and stock
- Shopping cart functionality (add/remove items, quantity adjustment, total calculation)
- User system (registration, login, logout)
- Order submission with contact information

### Backend Features
- User management (registration, login, permission control)
- Product management (add/modify product information)
- Order management (order creation, status tracking)
- Admin backend (order status management, product management)

## Database Design
- **users table**: username, password, email, phone, admin permissions
- **products table**: product name, price, stock, image, description
- **orders table**: order number, user, total price, status, contact info
- **order_items table**: order item details (product, quantity, price)

## Project Structure
```
shopping_website/
├── app.py                 # Main Flask application file
├── config.py             # Configuration file
├── run.py                # Startup script
├── requirements.txt      # Dependencies list
├── README.md            # Documentation
├── templates/           # HTML templates
├── static/              # Static files (CSS, JS, images, uploads)
└── shopping_website.db  # SQLite database (generated after running)
```