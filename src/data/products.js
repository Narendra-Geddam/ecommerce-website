//! OG Creator - @narendra

// Define the base URL for the API endpoint
const API_BASE_URL = 'https://fakestoreapi.com/products';

// Export a function called fetchProducts
export const fetchProducts = async () => {
  try {
    // Use the fetch API to make a GET request to the API endpoint
    const response = await fetch(API_BASE_URL);

    // Check if the response status is not OK (status code >= 400)
    if (!response.ok) {
      throw new Error('Network response was not ok.');
    }

    // Parse the response data as JSON
    const data = await response.json();

    // Return the fetched data (an array of products)
    return data;
  } catch (error) {
    // If an error occurs during the fetch process, handle the error
    console.error('Error fetching products:', error);

    // Return an empty array to indicate that no products were fetched
    return [];
  }
};
