import React from 'react';
import productsData from '../data/products';

const ProductDetails = ({ match }) => {
  const productId = parseInt(match.params.id);
  const product = productsData.find((p) => p.id === productId);

  if (!product) {
    return <div>Product not found</div>;
  }

  const { name, price, description, image } = product;

  return (
    <div className="product-details">
      <img src={image} alt={name} />
      <h2>{name}</h2>
      <p>${price}</p>
      <p>{description}</p>
    </div>
  );
};

export default ProductDetails;
