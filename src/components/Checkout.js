import React, { useState } from 'react';

const Checkout = () => {
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [contactNumber, setContactNumber] = useState('');
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Perform any additional logic or API calls here if needed
    setIsSubmitted(true);
  };

  const handleChange = (e) => {
    setAddress(e.target.value);
  };

  const handleNameChange = (e) => {
    setName(e.target.value);
  };

  const handleContactNumberChange = (e) => {
    setContactNumber(e.target.value);
  };

  const handleChangeEmail = (e) => {
    setEmail(e.target.value);
  };

  return (
    <div className="checkout-container">
      {isSubmitted ? (
        <div className="submitted-details">
          <p>Your order will be delivered soon. Details:</p>
          <p>Name: {name}</p>
          <p>Address: {address}</p>
          <p>Contact Number: {contactNumber}</p>
          <p>Email: {email}</p>
        </div>
      ) : (
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
