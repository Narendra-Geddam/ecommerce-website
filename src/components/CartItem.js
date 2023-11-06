// Importing the React library, which allows us to use React components.
import React from 'react';

//! OG Creator - @narendra
// Functional component named CartItem, which takes two props: 'item' and 'handleRemoveFromCart'.
const CartItem = ({ item, handleRemoveFromCart }) => {
  return (
    <div>
      {/* Displaying the name of the item */}
      <h3>{item.name}</h3>

      {/* Displaying the quantity of the item */}
      <p>Quantity: {item.quantity}</p>

      {/* Displaying the price of the item */}
      <p>Price: ${item.price}</p>

      {/* Button to remove the item from the cart */}
      <button onClick={() => handleRemoveFromCart(item.id)}>Remove</button>
    </div>
  );
};

// Exporting the CartItem component to make it available for other parts of the application.
export default CartItem;
