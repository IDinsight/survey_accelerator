import axios from 'axios';
// Set the backend API URL and authorization token from environment variables
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const authToken = process.env.NEXT_PUBLIC_BACKEND_PW || 'kk';

export const searchDocuments = async (
  query: string,
  top_k: number,
  precision: boolean,
  country: string,
  organization: string,
  region: string
) => {
  try {
    // Make the POST request to the search endpoint with headers and data
    const response = await axios.post(
      `${backendUrl}/search/`,
      {
        query,
        top_k,
        precision,
        country,
        organization,
        region,
      },
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        timeout: 25000, // Set timeout of 25 seconds
      }
    );

    // Return results data or an empty array if not present
    return response.data.results || [];
  } catch (error) {
    console.error('Error fetching search results:', error);
    throw new Error('Search request timed out or failed. Please try again.');
  }
};
