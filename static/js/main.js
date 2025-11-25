// Shopping cart related functions
let cart = {};

// Initialize after page load
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
    loadCart();
});

// Add to cart
function addToCart(productId, quantity = 1, event = null, variant = '') {
    if (!isLoggedIn()) {
        alert('Please login first');
        return;
    }

    // Get the button that triggered the event
    let addButton = null;
    let productCard = null;
    let productImage = null;
    
    if (event && event.target) {
        // If event is provided, try to find the button and product card
        addButton = event.target.closest('.btn-add-cart') || event.target.closest('button');
        productCard = addButton ? addButton.closest('.product-card') : null;
        productImage = productCard ? productCard.querySelector('.product-image') : null;
    } else {
        // Fallback: try to find button by product ID or use window.event
        if (window.event) {
            addButton = window.event.target.closest('button');
            productCard = addButton ? addButton.closest('.product-card') : null;
            productImage = productCard ? productCard.querySelector('.product-image') : null;
        }
        // If still not found, try to find product image on product detail page
        if (!productImage) {
            productImage = document.querySelector('.card img.img-fluid');
            addButton = document.querySelector('button[onclick*="addToCart"]');
        }
    }

    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: parseInt(quantity) || 1,
            variant: variant || ''
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Added to cart', 'success');
            updateCartCount();
            loadCart();
            // Trigger fly to cart animation
            if (productImage && addButton) {
                createFlyToCartAnimation(productImage, addButton, parseInt(quantity) || 1);
            }
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Failed to add, please try again', 'error');
    });
}

// Update cart count display
function updateCartCount() {
    fetch('/get_cart')
    .then(response => response.json())
    .then(data => {
        const count = data.items.reduce((sum, item) => sum + item.quantity, 0);
        document.getElementById('cart-count').textContent = count;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Load cart content
function loadCart() {
    fetch('/get_cart')
    .then(response => response.json())
    .then(data => {
        displayCartItems(data.items);
        document.getElementById('cart-total').textContent = formatNumber(data.total);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Display cart items
function displayCartItems(items) {
    const cartItemsContainer = document.getElementById('cart-items');
    
    if (items.length === 0) {
        cartItemsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-shopping-cart"></i>
                <h5>Cart is empty</h5>
                <p>Go add some products!</p>
            </div>
        `;
        return;
    }

    cartItemsContainer.innerHTML = items.map(item => `
        <div class="cart-item d-flex align-items-center">
            <img src="${item.image ? '/static/uploads/' + item.image : '/static/images/no-image.svg'}" 
                 class="cart-item-image me-3" alt="${item.name}">
            <div class="flex-grow-1">
                <h6 class="mb-1">${item.name}${item.variant ? ' <span class="badge bg-info">' + item.variant + '</span>' : ''}</h6>
                <p class="mb-0 text-muted">${formatNumber(item.price)} Ks</p>
            </div>
            <div class="quantity-controls">
                <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity - 1}, '${item.variant || ''}')">
                    <i class="fas fa-minus"></i>
                </button>
                <input type="number" class="quantity-input" value="${item.quantity}" 
                       min="1" onchange="updateQuantity(${item.id}, this.value, '${item.variant || ''}')">
                <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity + 1}, '${item.variant || ''}')">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
            <div class="ms-3">
                <h6 class="mb-0">${formatNumber(item.total)} Ks</h6>
            </div>
            <button class="btn btn-sm btn-outline-danger ms-2" onclick="removeFromCart(${item.id}, '${item.variant || ''}')">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// Update product quantity
function updateQuantity(productId, quantity, variant = '') {
    if (quantity < 0) quantity = 0;
    
    fetch('/update_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity,
            variant: variant || ''
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount();
            loadCart();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Remove product from cart
function removeFromCart(productId, variant = '') {
    if (confirm('Are you sure you want to remove this product from cart?')) {
        updateQuantity(productId, 0, variant);
    }
}

// Clear cart
function clearCart() {
    if (!confirm('Are you sure you want to clear the cart?')) {
        return;
    }
    
    fetch('/clear_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Cart cleared', 'success');
            updateCartCount();
            loadCart();
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Failed to clear, please try again', 'error');
    });
}

// Show cart
function showCart() {
    if (!isLoggedIn()) {
        alert('Please login first');
        return;
    }
    
    loadCart();
    const cartModal = new bootstrap.Modal(document.getElementById('cartModal'));
    cartModal.show();
}

// Quick buy - Add product to cart and open checkout (don't clear existing cart items)
function quickBuy(productId, quantity = 1, variant = '') {
    if (!isLoggedIn()) {
        alert('Please login first');
        return;
    }

    // Store quick buy info in session storage (for reference)
    sessionStorage.setItem('quickBuy', JSON.stringify({productId, quantity, variant}));
    
    // Add product to cart (without clearing existing items)
    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity,
            variant: variant || ''
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // After adding product successfully, update cart display and open checkout page
            showMessage('Product added to cart', 'success');
            updateCartCount();
            loadCart();
            
            // Open checkout page directly
            setTimeout(function() {
                const checkoutModal = new bootstrap.Modal(document.getElementById('checkoutModal'));
                checkoutModal.show();
            }, 300); // Small delay to ensure cart is updated
        } else {
            throw new Error(data.message || 'Failed to add product');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Quick buy failed, please try again', 'error');
    });
}

// Checkout
function checkout() {
    if (!isLoggedIn()) {
        alert('Please login first');
        return;
    }
    
    const checkoutModal = new bootstrap.Modal(document.getElementById('checkoutModal'));
    checkoutModal.show();
}

// Submit order
function submitOrder() {
    const contactInfo = document.getElementById('contact-info').value.trim();
    
    if (!contactInfo) {
        alert('Please fill in contact information');
        return;
    }

    const submitBtn = event.target;
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="loading"></span> Submitting...';
    submitBtn.disabled = true;

    fetch('/submit_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            contact_info: contactInfo
        })
    })
    .then(async response => {
        // Check if response is ok
        if (!response.ok) {
            // Try to parse error response as JSON
            let errorMessage = `Server error: ${response.status} ${response.statusText}`;
            try {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    errorMessage = data.message || errorMessage;
                } else {
                    // If not JSON, try to get text
                    const text = await response.text();
                    console.error('Server returned non-JSON response:', text.substring(0, 200));
                }
            } catch (parseError) {
                console.error('Error parsing error response:', parseError);
            }
            throw new Error(errorMessage);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showMessage(`Order submitted successfully! Order number: ${data.order_number}`, 'success');
            
            // Close modals
            const checkoutModal = bootstrap.Modal.getInstance(document.getElementById('checkoutModal'));
            const cartModal = bootstrap.Modal.getInstance(document.getElementById('cartModal'));
            if (checkoutModal) checkoutModal.hide();
            if (cartModal) cartModal.hide();
            
            // Clear contact information
            document.getElementById('contact-info').value = '';
            
            // Update cart
            updateCartCount();
            loadCart();
            
            // If on admin order management page, refresh to show new order
            if (window.location.pathname === '/admin' || window.location.pathname.includes('/admin')) {
                setTimeout(() => {
                    location.reload();
                }, 1000); // Wait 1 second to show success message, then refresh
            }
        } else {
            showMessage(data.message || 'Submission failed', 'error');
        }
    })
    .catch(error => {
        console.error('Error submitting order:', error);
        const errorMsg = error.message || 'Submission failed, please try again';
        showMessage(errorMsg, 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Check if logged in
function isLoggedIn() {
    // Check if username dropdown menu or cart link exists
    return document.querySelector('.navbar-nav .dropdown-toggle') !== null || 
           document.querySelector('.navbar-nav .fa-shopping-cart') !== null;
}

// Show message notification
function showMessage(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 'alert-info';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto disappear after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// Admin function: update order status
function updateOrderStatus(orderId, status) {
    if (!confirm('Are you sure you want to update the order status?')) {
        return;
    }

    fetch('/admin/update_order_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            order_id: orderId,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Order status updated successfully', 'success');
            location.reload();
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Update failed, please try again', 'error');
    });
}

// Image preview function
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('image-preview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    for (let input of inputs) {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            return false;
        } else {
            input.classList.remove('is-invalid');
        }
    }
    
    return true;
}

// Number formatting
function formatNumber(num) {
    return parseFloat(num).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Date formatting
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US');
}

// Create fly to cart animation
function createFlyToCartAnimation(productImage, addButton, quantity = 1) {
    // Get product image position
    const imageRect = productImage.getBoundingClientRect();
    
    // Get cart button position
    const cartButton = document.querySelector('.navbar-nav .nav-link[onclick="showCart()"]');
    if (!cartButton) {
        console.log('Cart button not found');
        return;
    }
    
    const cartRect = cartButton.getBoundingClientRect();
    
    // Set target position to cart button center
    const targetX = cartRect.left + cartRect.width / 2 - 20; // Subtract half of image width
    const targetY = cartRect.top + cartRect.height / 2 - 20; // Subtract half of image height
    
    // Create fly animation element - using product image
    const flyElement = document.createElement('div');
    flyElement.className = 'fly-to-cart';
    
    // Get product image src
    const productImageSrc = productImage.src;
    flyElement.innerHTML = `<img src="${productImageSrc}" class="fly-product-image" alt="Product Image">`;
    
    // Set initial position (product image position)
    flyElement.style.left = imageRect.left + imageRect.width / 2 - 20 + 'px';
    flyElement.style.top = imageRect.top + imageRect.height / 2 - 20 + 'px';
    
    document.body.appendChild(flyElement);
    
    // Force browser repaint to ensure initial position is set
    flyElement.offsetHeight; 
    
    // Set target position (cart button)
    flyElement.style.left = targetX + 'px';
    flyElement.style.top = targetY + 'px';
    flyElement.classList.add('animate');
    
    // Add cart button bounce animation
    cartButton.classList.add('cart-icon-bounce');
    setTimeout(() => {
        cartButton.classList.remove('cart-icon-bounce');
    }, 600);
    
    // Remove element after animation ends
    setTimeout(() => {
        flyElement.remove();
    }, 1200); // Increase animation time to make flight slower
}

// Show add success message
function showAddSuccessMessage() {
    // Remove existing success message
    const existingMessage = document.querySelector('.add-success');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create new success message
    const successMessage = document.createElement('div');
    successMessage.className = 'add-success';
    successMessage.innerHTML = '<i class="fas fa-check"></i> Added to cart';
    
    // Add to page
    document.body.appendChild(successMessage);
    
    // Show animation
    setTimeout(() => {
        successMessage.classList.add('show');
    }, 100);
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        successMessage.classList.remove('show');
        setTimeout(() => {
            if (successMessage.parentNode) {
                successMessage.parentNode.removeChild(successMessage);
            }
        }, 300);
    }, 3000);
}
