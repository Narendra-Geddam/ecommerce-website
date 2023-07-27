import React, { useState, useEffect } from 'react';

const fetchProducts = () => {
  return fetch('https://fakestoreapi.com/products')
    .then((res) => res.json())
    .then((data) => data);
};

const ProductList = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetchProducts()
      .then((data) => setProducts(data))
      .catch((error) => console.error('Error fetching products:', error));
  }, []);

  const handleAddToCart = (product) => {
    // Add product to cart logic here (You can implement this logic in the App component or create a separate cart state)
    console.log('Product added to cart:', product);
  };

  return (
    <div>
      {products.length > 0 ? (
        products.map((product) => (
          <div key={product.id}>
            <h2>{product.title}</h2>
            <p>{product.price}</p>
            <p>{product.category}</p>
            <p>{product.description}</p>
            <img src={product.image} alt={product.title} />
            <button onClick={() => handleAddToCart(product)}>Add to Cart</button>
          </div>
        ))
      ) : (
        <p>No products available.</p>
      )}
    </div>
  );
};

export default ProductList;
