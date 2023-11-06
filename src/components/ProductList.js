//! OG Creator - @narendra
import React from 'react';

const ProductList = ({ products, onAddToCart }) => {
  const handleAddToCart = (product) => {
    onAddToCart(product);
  };

  return (
    <div className="product-grid">
      {products.map((product) => (
        <div key={product.id} className="product-item">
          <img src={product.image} alt={product.title} className="product-image" />
          <h2 className="product-title">{product.title}</h2>
          <p className="product-price">${product.price}</p>
          <button className="add-to-cart-button" onClick={() => handleAddToCart(product)}>
            Add to Cart
          </button>
        </div>
      ))}
    </div>
  );
};

export default ProductList;
