import axios from 'axios';

// Set the backend API URL and authorization token from environment variables
const backendApiUrl = process.env.REACT_APP_BACKEND_API_URL || 'http://localhost:8000';
const authToken = process.env.REACT_APP_AUTH_TOKEN || 'kk';

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
      `${backendApiUrl}/search`,
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
      }
    );

    // Return results data or an empty array if not present
    return response.data.results || [];
  } catch (error) {
    console.error('Error fetching search results:', error);
    return [];
  }
};
