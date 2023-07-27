import React from 'react';
import CartItem from './CartItem';

const ShoppingCart = ({ cartItems, handleRemoveFromCart }) => {
  const calculateTotalPrice = () => {
    return cartItems.reduce((total, item) => total + item.price * item.quantity, 0);
  };

  return (
    <div>
      <h2>Shopping Cart</h2>
      {cartItems.length === 0 ? (
        <p>Cart is empty</p>
      ) : (
        <div>
          {cartItems.map((item) => (
            <CartItem key={item.id} item={item} handleRemoveFromCart={handleRemoveFromCart} />
          ))}
          <h3>Total Price: ${calculateTotalPrice().toFixed(2)}</h3>
        </div>
      )}
    </div>
  );
};

export default ShoppingCart;
