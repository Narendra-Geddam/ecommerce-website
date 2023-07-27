import React from 'react';

const ShoppingCart = ({ cartItems, onRemoveFromCart }) => {
  const cartTotal = cartItems.reduce((total, item) => total + item.price, 0);

  return (
    <div>
      <h2>Shopping Cart</h2>
      {cartItems.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <div>
          {cartItems.map((item) => (
            <div key={item.id}>
              <h3>{item.title}</h3>
              <p>${item.price}</p>
              <button onClick={() => onRemoveFromCart(item.id)}>Remove</button>
            </div>
          ))}
          <p>Total: ${cartTotal.toFixed(2)}</p>
        </div>
      )}
    </div>
  );
};

export default ShoppingCart;
