import React, { useState } from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import Header from './components/Header';
import ProductList from './components/ProductList';
import ProductDetails from './components/ProductDetails';
import ShoppingCart from './components/ShoppingCart';
import Checkout from './components/Checkout';
import NotFound from './components/NotFound';
import './styles/main.min.css';

const App = () => {
  const [cartItems, setCartItems] = useState([]);

  const handleAddToCart = (product) => {
    setCartItems((prevCartItems) => [...prevCartItems, product]);
  };

  return (
    <Router>
      <Header cartItems={cartItems} />
      <Switch>
        <Route exact path="/">
          <ProductList handleAddToCart={handleAddToCart} />
        </Route>
        <Route path="/product/:id" component={ProductDetails} />
        <Route path="/cart">
          <ShoppingCart cartItems={cartItems} />
        </Route>
        <Route path="/checkout">
          <Checkout cartItems={cartItems} />
        </Route>
        <Route component={NotFound} />
      </Switch>
    </Router>
  );
};

export default App;
