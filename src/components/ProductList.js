import React from 'react';
import productsData from '../data/products';
import ProductCard from './ProductCard';

const ProductList = () => {
  return (
    <div className="product-list">
      {productsData.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
};

export default ProductList;
