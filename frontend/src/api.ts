import axios from 'axios';
// Set the backend API URL and authorization token from environment variables
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const authToken = process.env.NEXT_PUBLIC_BACKEND_PW || 'kk';

export const searchDocuments = async (
  query: string,
  country: string,
  organization: string,
  region: string
) => {
  try {
    const endpoint = '/search/generic';

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
 * Gets a highlighted version of a PDF with the search term pre-highlighted.
 * This calls the backend to process the PDF and add highlights.
 */
export const getHighlightedPdf = async (
  pdfUrl: string, 
  searchTerm: string
): Promise<string> => {
  try {
    const response = await axios.get(
      `${backendUrl}/api/highlight-pdf`,
      {
        params: {
          pdf_url: pdfUrl,
          search_term: searchTerm
        },
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        timeout: 30000, // Allow 30 seconds for PDF processing
      }
    );
    
    // The response should contain the URL to the highlighted PDF
    return response.data.highlighted_pdf_url;
  } catch (error) {
    console.error('Error getting highlighted PDF:', error);
    throw new Error('Failed to get highlighted PDF. Please try again.');
  }
};

export const login = async (email: string, password: string): Promise<any> => {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: body.toString()
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Incorrect email or password.');
  }

  return response.json();
}

export const resetPassword = async (email: string): Promise<any> => {
  try {
    const response = await axios.post(
      `${backendUrl}/users/password-reset`,
      null,
      {
        params: { email },
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        timeout: 25000,
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error sending password reset email:', error);
    throw new Error('Failed to send reset email. Please check your email and try again.');
  }
};
