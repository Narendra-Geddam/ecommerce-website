import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const Header = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleSearch = () => {
    onSearch(searchTerm);
  };

  return (
    <header>
      <nav>
        <ul>
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/cart">Cart</Link>
          </li>
        </ul>
        <div>
          <input type="text" value={searchTerm} onChange={handleChange} />
          <button onClick={handleSearch}>Search</button>
        </div>
      </nav>
    </header>
  );
};

export default Header;
