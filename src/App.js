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
  const [filteredProducts, setFilteredProducts] = useState([]); // New state for filtered products

  useEffect(() => {
    fetchProducts().then((data) => {
      setProducts(data);
      setFilteredProducts(data); // Initialize filtered products with all products
    });
  }, []);

  const handleAddToCart = (product) => {
    setCart((prevCart) => [...prevCart, product]);
  };

  const handleRemoveFromCart = (productId) => {
    setCart((prevCart) => prevCart.filter((item) => item.id !== productId));
  };

  const handleSearch = (searchTerm) => {
    if (searchTerm.trim() === '') {
      // If the search term is empty, reset the filtered products list to all products
      setFilteredProducts(products);
    } else {
      // If the search term is not empty, filter the products based on the search term
      const filteredProducts = products.filter((product) =>
        product.title.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredProducts(filteredProducts);
    }
  };

  return (
    <Router>
      <Header onSearch={handleSearch} />
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
