// src/api.ts
import axios from 'axios';

export const searchDocuments = async (
  query: string,
  top_k: number,
  precision: boolean,
  country: string,
  organization: string,
  region: string
) => {
  try {
    const response = await axios.post('http://localhost:8000/search/', {
      query,
      top_k,
      precision,
      country,
      organization,
      region,
    }, {
      headers: {
        'Authorization': `Bearer kk`,
        'Content-Type': 'application/json',
      },
    });

    // Return response data, handle any errors upstream
    return response.data.results || [];
  } catch (error) {
    console.error('Error fetching search results:', error);
    return [];
  }
};
