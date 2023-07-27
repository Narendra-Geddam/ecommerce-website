import React from 'react';

const CartItem = ({ item, handleRemoveFromCart }) => {
  return (
    <div>
      <h3>{item.name}</h3>
      <p>Quantity: {item.quantity}</p>
      <p>Price: ${item.price}</p>
      <button onClick={() => handleRemoveFromCart(item.id)}>Remove</button>
    </div>
  );
};

export default CartItem;
