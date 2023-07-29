import React, { useState } from 'react';

const Checkout = () => {
  const [address, setAddress] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Perform any additional logic or API calls here if needed
    setIsSubmitted(true);
  };

  const handleChange = (e) => {
    setAddress(e.target.value);
  };

  return (
    <div>
      {isSubmitted ? (
        <div>
          <p>Your order will be delivered soon to:</p>
          <p>{address}</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <label>
            Address:
            <input type="text" value={address} onChange={handleChange} />
          </label>
          <br />
          <button type="submit">Submit</button>
        </form>
      )}
    </div>
  );
};

export default Checkout;
