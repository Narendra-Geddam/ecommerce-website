import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import Header from './components/Header';
import ProductList from './components/ProductList';
import ProductDetails from './components/ProductDetails';
import ShoppingCart from './components/ShoppingCart';
import NotFound from './components/NotFound';
import { fetchProducts } from './data/products';

import './styles/main.min.css';

const App = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const data = await fetchProducts();
      setProducts(data);
    };
    fetchData();
  }, []);

  const handleAddToCart = (product) => {
    setCart((prevCart) => {
      const existingItem = prevCart.find((item) => item.id === product.id);
      if (existingItem) {
        return prevCart.map((item) =>
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      } else {
        return [...prevCart, { ...product, quantity: 1 }];
      }
    });
  };

  const handleRemoveFromCart = (productId) => {
    setCart((prevCart) => prevCart.filter((item) => item.id !== productId));
  };

  return (
    <Router>
      <Header cartItems={cart} />
      <Switch>
        <Route exact path="/">
          <ProductList products={products} handleAddToCart={handleAddToCart} />
        </Route>
        <Route path="/product/:id">
          <ProductDetails handleAddToCart={handleAddToCart} />
        </Route>
        <Route path="/cart">
          <ShoppingCart cartItems={cart} handleRemoveFromCart={handleRemoveFromCart} />
        </Route>
        <Route component={NotFound} />
      </Switch>
    </Router>
  );
};

export default App;
