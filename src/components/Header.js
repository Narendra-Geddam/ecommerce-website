//! OG Creator - @narendra

import React, { useState } from 'react';
import { Link } from 'react-router-dom';

// Importing Logo Image to Header
import logoImage from '../assets/images/logo.png';

// importing StyleSheet and View for adding elements
import { StyleSheet, View,} from '@react-pdf/renderer';
const styles = StyleSheet.create({

  headerStyle :{
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    padding: '10px',
  },

  logoSection:{
    display: 'flex',
    alignItems: 'center',
  },

  logoStyle : {
    flex: 1,
    padding: '5px',
    width:50,
    height:50,
    marginRight:30,
  },

  brandName:{
    fontSize:32,
    fontWeight:800,
    marginLeft:30,
  },

  navItemsStyle : {
    flex: 3,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    fontSize:24,
  },

  ulStyle : {
    listStyle: 'none',
    margin: 0,
    padding: 0,
  },

  liStyle : {
    display: 'inline',
    marginRight: '20px',
  },

  searchSortStyle : {
    display: 'flex',
    alignItems: 'center',
  },

  searchBar:{
    marginLeft:100,
  },

  searchBarStyle:{
    fontStyle:16,
    border:'1px solid #ccc',
    borderRadius:'50%',
    backgroundColor:'#f0f0f0'
  },

  sortOption:{

  },

  selectStyle : {
    marginRight: '10px',
    fontSize:16,
  },

  linkStyle:{
    textDecoration:'none'
  }


});

const Header = ({ onSearch, cartItemCount, onSortChange }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOption, setSortOption] = useState('asc'); // State for sorting

  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleSearch = () => {
    onSearch(searchTerm);
  };

  const handleSortChange = (event) => {
    setSortOption(event.target.value);
    onSortChange(event.target.value); // Call the parent component's sort function
  };

  return (
    <header style={styles.headerStyle}>
      <View style={styles.logoSection}>
        <View style={styles.logoStyle}>
          {/* logo component  */}
          <img src={logoImage} alt="Logo" style={styles.logoStyle} />
        </View>
        <View style={styles.brandName}>
        SuperMartX
        </View>
      </View>
      <nav style={styles.navItemsStyle}>

         {/* Search and Sort option */}
        <View style={styles.searchSortStyle}>
          <View style={styles.searchBar}>
            <input style={styles.searchBarStyle} type="text" value={searchTerm} onChange={handleChange} />
            <button onClick={handleSearch}>Search</button>
          </View>

          <View style={styles.sortOption}>
            {/* Add the sorting select element */}
            <select style={styles.selectStyle} value={sortOption} onChange={handleSortChange}>
              <option value="asc">High to Low</option>
              <option value="desc">Low to High</option>
            </select>
          </View>
        </View>

        <ul style={styles.ulStyle}>
          <li style={styles.liStyle}>
            <Link style={styles.linkStyle} to="/">Home</Link>
          </li>
          <li style={styles.liStyle}>
            <Link style={styles.linkStyle} to="/cart">Cart ({cartItemCount})</Link>
          </li>
        </ul>
      </nav>
    </header>
  
  );
};

export default Header;
