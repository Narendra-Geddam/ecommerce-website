//! OG Creator - @narendra
import React, { useState } from 'react';

// Checkout component that allows users to submit their details for order processing.
const Checkout = () => {
  // State variables to hold form field values and submitted status.
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [contactNumber, setContactNumber] = useState('');
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  // Function to handle form submission.
  const handleSubmit = (e) => {
    e.preventDefault();

    // Set the submitted status to true to display the order details.
    setIsSubmitted(true);
  };

  // Function to handle address field change.
  const handleChange = (e) => {
    setAddress(e.target.value);
  };

  // Function to handle name field change.
  const handleNameChange = (e) => {
    setName(e.target.value);
  };

  // Function to handle contact number field change.
  const handleContactNumberChange = (e) => {
    setContactNumber(e.target.value);
  };

  // Function to handle email field change.
  const handleChangeEmail = (e) => {
    setEmail(e.target.value);
  };

  return (
    <div className="checkout-container">
      {/* Display the order details after submission */}
      {isSubmitted ? (
        <div className="submitted-details">
          <p>Your order will be delivered soon. Details:</p>
          <p>Name: {name}</p>
          <p>Address: {address}</p>
          <p>Contact Number: {contactNumber}</p>
          <p>Email: {email}</p>
        </div>
      ) : (
        /* Display the form for user input if not submitted */
        <form onSubmit={handleSubmit} className="checkout-form">
          <label>
            Name:
            <input type="text" value={name} onChange={handleNameChange} />
          </label>
          <br />
          <label>
            Address:
            <input type="text" value={address} onChange={handleChange} />
          </label>
          <br />
          <label>
            Contact Number:
            <input type="text" value={contactNumber} onChange={handleContactNumberChange} />
          </label>
          <br />
          <label>
            Email:
            <input type="text" value={email} onChange={handleChangeEmail} />
          </label>
          <br />
          <button type="submit">Submit</button>
        </form>
      )}
    </div>
  );
};

export default Checkout;
