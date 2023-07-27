import React from 'react';

const ShoppingCart = ({ cartItems, onRemoveFromCart }) => {
  const handleRemoveFromCart = (productId) => {
    onRemoveFromCart(productId);
  };

  const getTotalCost = () => {
    const totalCost = cartItems.reduce((total, item) => total + item.price, 0);
    return totalCost.toFixed(2); // To display the total with two decimal places
  };

  return (
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
          <p>Total: ${getTotalCost()}</p>
        </div>
      )}
    </div>
  );
};

export default ShoppingCart;
