import { generateCodeVerifier, generateCodeChallenge } from '../utils/pkce';

// Kakao Developer App Configuration
const KAKAO_CLIENT_ID = 'YOUR_KAKAO_REST_API_KEY'; // Replace with your Kakao REST API Key
const KAKAO_REDIRECT_URI = 'http://localhost:8006/api/auth/kakao/callback'; // Replace with your backend redirect URI
// In production, ensure this matches the URI configured in your Kakao Developer Console
// and is accessible via your Ingress/API Gateway.

// Kakao Authorization Endpoint
const KAKAO_AUTH_URL = '[https://kauth.kakao.com/oauth/authorize](https://kauth.kakao.com/oauth/authorize)';

export const initiateKakaoLogin = async () => {
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = await generateCodeChallenge(codeVerifier);

  // Store code_verifier and state securely (e.g., in sessionStorage)
  // State is used to prevent CSRF attacks
  const state = Math.random().toString(36).substring(2); // Simple random state
  sessionStorage.setItem('code_verifier', codeVerifier);
  sessionStorage.setItem('oauth_state', state);

  // Construct the authorization URL
  const authUrl = new URL(KAKAO_AUTH_URL);
  authUrl.searchParams.append('client_id', KAKAO_CLIENT_ID);
  authUrl.searchParams.append('redirect_uri', KAKAO_REDIRECT_URI);
  authUrl.searchParams.append('response_type', 'code');
  authUrl.searchParams.append('scope', 'openid profile account_email'); // Request necessary scopes
  authUrl.searchParams.append('code_challenge', codeChallenge);
  authUrl.searchParams.append('code_challenge_method', 'S256'); // PKCE method
  authUrl.searchParams.append('state', state);

  // Redirect the user's browser
  window.location.href = authUrl.toString();
};

// Function to handle API calls with the token
// This assumes your backend issues its own token after Kakao auth
export const callAuthenticatedApi = async (url, options = {}) => {
  const token = sessionStorage.getItem('backend_auth_token'); // Retrieve token from storage

  if (!token) {
    // User is not authenticated, redirect to login or show error
    console.error('User not authenticated. Redirecting to login.');
    // TODO: Implement actual redirect to login page
    // window.location.href = '/login'; // Example redirect
    throw new Error('User not authenticated');
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`, // Include the token in the Authorization header
  };

  try {
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        console.error('Authentication or Authorization failed for API call.');
        // TODO: Handle unauthorized - clear token, redirect to login
        sessionStorage.removeItem('backend_auth_token');
        // window.location.href = '/login'; // Example redirect
      }
      // Handle other HTTP errors
      const errorBody = await response.text();
      throw new Error(`API call failed: ${response.status} ${response.statusText} - ${errorBody}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
};

// TODO: Implement logic to handle the redirect URI and token exchange if frontend does it
// This is less secure for SPAs compared to backend exchange, but possible depending on API Gateway setup.
// If backend handles token exchange, the frontend just needs to land on the redirect URI page.
