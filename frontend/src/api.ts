import axios from 'axios';
// Set the backend API URL and authorization token from environment variables
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const authToken = process.env.NEXT_PUBLIC_BACKEND_PW || 'kk';

/**
 * Searches documents using either precision or generic search based on the precision flag
 * This will be kept temporarily for backward compatibility
 */
export const searchDocuments = async (
  query: string,
  top_k: number,
  precision: boolean,
  country: string,
  organization: string,
  region: string
) => {
  try {
    // Use the new endpoint based on precision flag
    const endpoint = precision ? '/search/precision' : '/search/generic';

    // Make the POST request to the appropriate search endpoint
    const response = await axios.post(
      `${backendUrl}${endpoint}`,
      {
        query,
        country: country || undefined,
        organization: organization || undefined,
        region: region || undefined,
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

/**
 * Performs a generic search that returns document chunks with context
 */
export const searchGeneric = async (
  query: string,
  country?: string,
  organization?: string,
  region?: string
) => {
  try {
    const response = await axios.post(
      `${backendUrl}/search/generic`,
      {
        query,
        country: country || undefined,
        organization: organization || undefined,
        region: region || undefined,
      },
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        timeout: 25000,
      }
    );

    return response.data.results || [];
  } catch (error) {
    console.error('Error fetching generic search results:', error);
    throw new Error('Search request timed out or failed. Please try again.');
  }
};

/**
 * Performs a precision search that returns specific QA pairs
 */
export const searchPrecision = async (
  query: string,
  country?: string,
  organization?: string,
  region?: string
) => {
  try {
    const response = await axios.post(
      `${backendUrl}/search/precision`,
      {
        query,
        country: country || undefined,
        organization: organization || undefined,
        region: region || undefined,
      },
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        timeout: 25000,
      }
    );

    return response.data.results || [];
  } catch (error) {
    console.error('Error fetching precision search results:', error);
    throw new Error('Search request timed out or failed. Please try again.');
  }
};
