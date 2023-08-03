//! OG Creator - @narendra

import React from 'react';
import Checkout from './Checkout';


const ShoppingCart = ({ cartItems, onRemoveFromCart }) => {
  const handleRemoveFromCart = (productId) => {
    onRemoveFromCart(productId);
  };

  const getTotalCost = () => {
    const totalCost = cartItems.reduce((total, item) => total + item.price, 0);
    return totalCost.toFixed(2); // To display the total with two decimal places
  };

  return (
    <div className="page-container">
      <div className="cart">
        <h2>Shopping Cart</h2>
        {cartItems.length === 0 ? (
          <p>Your cart is empty.</p>
        ) : (
          <div>
            <ul>
              {cartItems.map((item) => (
                <li key={item.id}>
                  <h3>{item.title}</h3>
                  <p>Price: ${item.price}</p>
                  <button onClick={() => handleRemoveFromCart(item.id)}>Remove</button>
                </li>
              ))}
            </ul>
            <h3 className="total">Total: ${getTotalCost()}</h3>
            <Checkout />
          </div>
        )}
      </div>
    </div>
  );
};

export default ShoppingCart;
