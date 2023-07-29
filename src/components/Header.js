import React, { useState } from 'react';
import { Link } from 'react-router-dom';

// Importing Logo Image to Header
import logoImage from '../assets/images/logo.png';
import cartImage from '../assets/images/carts.png';

// importing StyleSheet and View for adding elements
import { StyleSheet, View } from '@react-pdf/renderer';

const styles = StyleSheet.create({
  header: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    padding: '20px 10px',
    borderBottom: '1px solid #ccc',
  },
  logoSection: {
    display: 'flex',
    alignItems: 'center',
  },
  logo: {
    width: 65,
    height: 50,
    marginRight: 30,
  },

  cart: {
    width: 50,
    height: 50,
    marginRight: 30,
  },

  brandName: {
    fontSize: 28,
    fontWeight: 700,
    fontFamily: 'Arial, sans-serif',
  },
  navItems: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    fontSize: 24,
  },
  ul: {
    display: 'flex',
    alignItems: 'center',
    listStyle: 'none',
    margin: 0,
    padding: 0,
  },
  li: {
    marginLeft: '20px', // Use margin-left instead of margin-right for spacing
  },
  searchSort: {
    display: 'flex',
    alignItems: 'center',
  },
  searchBar: {
    marginLeft: '20px', // Adjust the margin as needed
    display: 'flex',
    alignItems: 'center',
  },
  searchInput: {
    fontSize: 16,
    border: '1px solid #ccc',
    borderRadius: 5,
    backgroundColor: '#ffffff',
    padding: '8px 12px',
    minWidth: 250,
  },
  searchButton: {
    marginLeft: '10px',
    padding: '8px 12px',
    background: '#007bff',
    color: '#fff',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '16px',
    transition: 'background-color 0.3s ease-in-out',
  },
  searchButtonHover: {
    background: '#0056b3',
  },
  sortOption: {
    marginLeft: '20px', // Adjust the margin as needed
    display: 'flex',
    alignItems: 'center',
  },
  select: {
    fontSize: 16,
    border: '1px solid #ccc',
    padding: '8px 12px',
  },
  link: {
    textDecoration: 'none',
    color: '#333',
  },
});

const Header = ({ onSearch, cartItemCount, onSortChange }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOption, setSortOption] = useState('asc');

  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleSearch = () => {
    onSearch(searchTerm);
  };

  const handleSortChange = (event) => {
    setSortOption(event.target.value);
    onSortChange(event.target.value);
  };

  // Add state to handle the button hover effect
  const [isButtonHovered, setButtonHovered] = useState(false);

  return (
    <header style={styles.header}>
      <View style={styles.logoSection}>
        {/* Logo component */}
        <img src={logoImage} alt="Logo" style={styles.logo} />
        <div style={styles.brandName}>SuperMartX</div>
      </View>
      <nav style={styles.navItems}>

        {/* Search and Sort option */}
        <View style={styles.searchSort}>
          <View style={styles.searchBar}>
            <input
              style={styles.searchInput}
              type="text"
              value={searchTerm}
              onChange={handleChange}
            />
            <button
              style={{ ...styles.searchButton, ...(isButtonHovered && styles.searchButtonHover) }}
              onClick={handleSearch}
              onMouseEnter={() => setButtonHovered(true)}
              onMouseLeave={() => setButtonHovered(false)}
            >
              Search
            </button>
          </View>

          <View style={styles.sortOption}>
            {/* Add the sorting select element */}
            <select style={styles.select} value={sortOption} onChange={handleSortChange}>
              <option value="asc">High to Low</option>
              <option value="desc">Low to High</option>
            </select>
          </View>
        </View>

        <ul style={styles.ul}>
          <li style={styles.li}>
            <Link style={styles.link} to="/">Home</Link>
          </li>
          <li style={styles.li}>
            <Link style={styles.link} to="/cart">
              <img src={cartImage} alt="Cart" style={styles.cart} /> ({cartItemCount})
            </Link>
          </li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;
