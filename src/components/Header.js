import React, { useState } from 'react';
import { Link } from 'react-router-dom';

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
    <header>
      <nav>
        <ul>
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/cart">Cart ({cartItemCount})</Link>
          </li>
        </ul>
        <div>
          {/* Add the sorting select element */}
          <select value={sortOption} onChange={handleSortChange}>
            <option value="asc">High to Low</option>
            <option value="desc">Low to High</option>
          </select>

          <input type="text" value={searchTerm} onChange={handleChange} />
          <button onClick={handleSearch}>Search</button>
        </div>
      </nav>
    </header>
  );
};

export default Header;
