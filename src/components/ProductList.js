import React, { useState, useEffect } from 'react';
import { fetchProducts } from '../data/products';

const ProductList = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetchProducts()
      .then((data) => setProducts(data))
      .catch((error) => console.error('Error fetching products:', error));
  }, []);

  const handleAddToCart = (product) => {
    // Implement the logic to add the product to the cart here
    console.log('Product added to cart:', product);
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
