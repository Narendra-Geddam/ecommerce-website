//! OG Creator - @narendra

// import useState and useEffect for state of cart and products

import React, { useState, useEffect } from 'react';

//  import router and route and switch for site no reload 

import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';

// importing components from components directory



import Header from './components/Header';
import ProductList from './components/ProductList';
import ProductDetails from './components/ProductDetails';
import ShoppingCart from './components/ShoppingCart';
import Checkout from './components/Checkout';
import NotFound from './components/NotFound';
import { fetchProducts } from './data/products';
import { StyleSheet, View } from '@react-pdf/renderer';


const styles = StyleSheet.create({
  bodyFStyle:{
    fontFamily: 'Arial, sans-serif',
    color: '#333',
  }
});

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

  const handleSortChange = (sortOption) => {
    // Sort the products based on the selected sorting option
    const sortedProducts = [...filteredProducts];
    if (sortOption === 'desc') {
      sortedProducts.sort((a, b) => b.id - a.id);
    } else {
      sortedProducts.sort((a, b) => a.id - b.id);
    }
    setFilteredProducts(sortedProducts);
  };

  return (
    <Router>
   <View style={styles.bodyFStyle}>
      <Header onSearch={handleSearch} cartItemCount={cart.length} onSortChange={handleSortChange} />
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
    </View>
    </Router>
  );
};

export default App;
