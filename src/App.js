//! OG Creator - @narendra

// Import necessary modules from React and React Router
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';

// Import custom components from the components directory
import Header from './components/Header';
import ProductList from './components/ProductList';
import ProductDetails from './components/ProductDetails';
import ShoppingCart from './components/ShoppingCart';
import Checkout from './components/Checkout';
import NotFound from './components/NotFound';

// Import the fetchProducts function from the products data file
import { fetchProducts } from './data/products';

// Import StyleSheet and View from react-pdf/renderer (if using react-pdf)
import { StyleSheet, View } from '@react-pdf/renderer';

// Create a stylesheet (only if using react-pdf)
const styles = StyleSheet.create({
  bodyFStyle:{
    fontFamily: 'Arial, sans-serif',
    color: '#333',
  }
});

// Define the main App component
const App = () => {
  // State variables using React Hooks to manage the cart, products, and filteredProducts
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);

  // useEffect hook to fetch products from the data file when the component mounts
  useEffect(() => {
    fetchProducts().then((data) => {
      setProducts(data);
      setFilteredProducts(data);
    });
  }, []);

  // Function to handle adding a product to the cart
  const handleAddToCart = (product) => {
    setCart((prevCart) => [...prevCart, product]);
  };

  // Function to handle removing a product from the cart based on its productId
  const handleRemoveFromCart = (productId) => {
    setCart((prevCart) => prevCart.filter((item) => item.id !== productId));
  };

  // Function to handle searching for products based on a searchText
  const handleSearch = (searchText) => {
    if (!searchText) {
      // If searchText is empty, reset filteredProducts to all products
      setFilteredProducts(products);
    } else {
      // Filter products based on the searchText (case-insensitive)
      const filtered = products.filter((product) =>
        product.title.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredProducts(filtered);
    }
  };

  // Function to handle sorting the products based on a sortOption ('asc' or 'desc')
  const handleSortChange = (sortOption) => {
    // Sort the products based on the selected sorting option
    const sortedProducts = [...filteredProducts];
    if (sortOption === 'desc') {
      sortedProducts.sort((a, b) => b.id - a.id); // Descending order by product id
    } else {
      sortedProducts.sort((a, b) => a.id - b.id); // Ascending order by product id
    }
    setFilteredProducts(sortedProducts);
  };

  // Render the JSX content of the App component
  return (
    <Router>
      {/* If using react-pdf, wrap the entire content with View and apply styles */}
      <View style={styles.bodyFStyle}>
        {/* Header component with search, cartItemCount, and sorting props */}
        <Header onSearch={handleSearch} cartItemCount={cart.length} onSortChange={handleSortChange} />

        {/* Switch to handle routing based on the URL */}
        <Switch>
          {/* Route for the homepage */}
          <Route exact path="/">
            {/* Render the ProductList component with filtered products and addToCart handler */}
            <ProductList products={filteredProducts} onAddToCart={handleAddToCart} />
          </Route>

          {/* Route for displaying the details of a single product */}
          <Route path="/product/:id" component={ProductDetails} />

          {/* Route for the shopping cart */}
          <Route path="/cart">
            {/* Render the ShoppingCart component with cartItems and removeFromCart handler */}
            <ShoppingCart cartItems={cart} onRemoveFromCart={handleRemoveFromCart} />
          </Route>

          {/* Route for the checkout page */}
          <Route path="/checkout" component={Checkout} />

          {/* If none of the above routes match, display the NotFound component */}
          <Route component={NotFound} />
        </Switch>
      </View>
    </Router>
  );
};

// Export the App component as the default export of this module
export default App;