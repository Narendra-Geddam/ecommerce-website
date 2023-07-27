import React from 'react';
import { Link } from 'react-router-dom';

const ProductCard = ({ product }) => {
  const { id, name, price, image } = product;

  return (
    <div className="product-card">
      <img src={image} alt={name} />
      <h3>{name}</h3>
      <p>${price}</p>
      <Link to={`/product/${id}`}>View Details</Link>
    </div>
  );
};

export default ProductCard;
