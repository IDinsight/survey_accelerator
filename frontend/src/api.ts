import axios from "axios"

const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000"
const authToken = process.env.NEXT_PUBLIC_BACKEND_PW || "kk"

export const searchDocuments = async (
  query: string,
  country: string,
  organization: string,
  region: string,
  resultsCount = 25,
) => {
  try {
    const endpoint = "/search/generic"
    const token = localStorage.getItem("token")

    if (!token) {
      throw new Error("Authentication token not found")
    }

    const response = await axios.post(
      `${backendUrl}${endpoint}`,
      {
        query,
        country: country || undefined,
        organization: organization || undefined,
        region: region || undefined,
        limit: resultsCount,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        timeout: 40000, // 40 seconds timeout
      },
    )
    return response.data.results || []
  } catch (error) {
    console.error("Error fetching search results:", error)
    throw new Error("Search request timed out or failed.")
  }
}

// Also update the getHighlightedPdf function to use the user's token
export const getHighlightedPdf = async (pdfUrl: string, searchTerm: string): Promise<string> => {
  try {
    const token = localStorage.getItem("token")

    if (!token) {
      throw new Error("Authentication token not found")
    }

    const response = await axios.get(`${backendUrl}/api/highlight-pdf`, {
      params: {
        pdf_url: pdfUrl,
        search_term: searchTerm,
      },
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      timeout: 40000, // 40 seconds for PDF processing
    })
    return response.data.highlighted_pdf_url
  } catch (error) {
    console.error("Error getting highlighted PDF:", error)
    throw new Error("Failed to get highlighted PDF.")
  }
}

export const login = async (email: string, password: string): Promise<any> => {
  const body = new URLSearchParams()
  body.append("username", email)
  body.append("password", password)

  const response = await fetch(`${backendUrl}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || "Incorrect email or password.")
  }
  return response.json()
}

export const resetPassword = async (email: string): Promise<any> => {
  try {
    const response = await axios.post(`${backendUrl}/users/password-reset`, null, {
      params: { email },
      headers: {
        Authorization: `Bearer ${authToken}`,
        "Content-Type": "application/json",
      },
      timeout: 25000,
    })
    return response.data
  } catch (error) {
    console.error("Error sending password reset email:", error)
    throw new Error("Failed to send reset email. Please check your email and try again.")
  }
}

export const registerUser = async (email: string, password: string, organization: string, role: string) => {
  try {
    const response = await axios.post(
      `${backendUrl}/users/create`,
      { email, password, organization, role },
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
        timeout: 25000,
      },
    )
    return response.data
  } catch (error: any) {
    console.error("Registration error:", error)
    throw new Error(error.message || "Registration failed. Please try again.")
  }
}

// New function for changing password
export const changePassword = async (currentPassword: string, newPassword: string): Promise<any> => {
  try {
    const token = localStorage.getItem("token")
    if (!token) {
      throw new Error("Authentication token not found")
    }

    const response = await axios.post(
      `${backendUrl}/users/change-password`,
      {
        current_password: currentPassword,
        new_password: newPassword,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        timeout: 25000,
      },
    )
    return response.data
  } catch (error: any) {
    console.error("Password change error:", error)

    // Handle validation errors
    if (error.response && error.response.status === 422) {
      const validationErrors = error.response.data.detail
        .map((err: any) => {
          const field = err.loc[err.loc.length - 1]
          return `${field}: ${err.msg}`
        })
        .join(", ")
      throw new Error(`Validation error: ${validationErrors}`)
    }

    // Handle other errors
    if (error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail)
    }

    throw new Error(error.message || "Failed to change password")
  }
}

// New function for updating results count preference
export const updateResultsCountPreference = async (numResults: number): Promise<any> => {
  try {
    const token = localStorage.getItem("token")
    if (!token) {
      throw new Error("Authentication token not found")
    }

    const response = await axios.post(`${backendUrl}/users/update-num-results-preference`, null, {
      params: { num_results: numResults },
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      timeout: 25000,
    })
    return response.data
  } catch (error: any) {
    console.error("Update results count error:", error)

    if (error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail)
    }

    throw new Error(error.message || "Failed to update results count preference")
  }
}


// New function to fetch documents grouped by organization
export const fetchDocumentsByOrganization = async () => {
  try {
    const token = localStorage.getItem("token")

    if (!token) {
      throw new Error("Authentication token not found")
    }

    const response = await axios.get(`${backendUrl}/ingestion/view-ingested-documents`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      timeout: 30000, // 30 seconds timeout
    })

    return response.data || []
  } catch (error) {
    console.error("Error fetching documents by organization:", error)
    throw new Error("Failed to fetch documents by organization.")
  }
}
