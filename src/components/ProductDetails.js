//! OG Creator - @narendra
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { fetchProducts } from '../data/products'; // Import the fetchProducts function

const ProductDetails = ({ handleAddToCart }) => {
  const { id } = useParams();
  const [product, setProduct] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const data = await fetchProducts();
      const productData = data.find((item) => item.id === parseInt(id));
      setProduct(productData);
    };
    fetchData();
  }, [id]);

  if (!product) {
    return <div>Product not found.</div>;
  }

  return (
    <div>
      <h2>{product.title}</h2>
      <p>{product.price}</p>
      <button onClick={() => handleAddToCart(product)}>Add to Cart</button>
    </div>
  );
};

export default ProductDetails;
