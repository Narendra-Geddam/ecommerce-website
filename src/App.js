import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import Header from './components/Header';
import ProductList from './components/ProductList';
import ProductDetails from './components/ProductDetails';
import ShoppingCart from './components/ShoppingCart';
import Checkout from './components/Checkout';
import NotFound from './components/NotFound';
import { fetchProducts } from './data/products';

const App = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);

  useEffect(() => {
    fetchProducts().then((data) => {
      setProducts(data);
      setFilteredProducts(data);
    });
  }, []);

  const handleAddToCart = (product) => {
    setCart((prevCart) => [...prevCart, product]);
  };

  const handleRemoveFromCart = (productId) => {
    setCart((prevCart) => prevCart.filter((item) => item.id !== productId));
  };

  const handleSearch = (searchText) => {
    if (!searchText) {
      setFilteredProducts(products);
    } else {
      const filtered = products.filter((product) =>
        product.title.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredProducts(filtered);
    }
  };

  return (
    <Router>
      <Header onSearch={handleSearch} cartItemCount={cart.length} />
      <Switch>
        <Route exact path="/">
          <ProductList products={filteredProducts} onAddToCart={handleAddToCart} />
        </Route>
        <Route path="/product/:id" component={ProductDetails} />
        <Route path="/cart">
          <ShoppingCart cartItems={cart} onRemoveFromCart={handleRemoveFromCart} />
        </Route>
        <Route path="/checkout" component={Checkout} />
        <Route component={NotFound} />
      </Switch>
    </Router>
  );
};

export default App;
