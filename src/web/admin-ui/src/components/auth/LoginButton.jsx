// LoginButton.jsx
import React from 'react';
// generateRandomString 대신 generateState 함수를 import 하거나 generateRandomString을 직접 사용
import { generatePkceCodes, generateState, generateRandomString } from './pkceUtils'; // generateState 추가

// OAuth 설정 (AuthHandler.jsx의 OAUTH_CONFIG와 동일해야 함)
const OAUTH_CONFIG = {
    clientId: 'YOUR_CLIENT_ID',
    redirectUri: 'YOUR_REDIRECT_URI', // 예: 'http://localhost:3000/callback'
    authorizationEndpoint: 'YOUR_AUTH_SERVER_AUTHORIZATION_ENDPOINT',
    scope: 'openid profile email', // 필요한 스코프 설정
    // state 값은 동적으로 생성하여 사용하므로 여기서는 더 이상 필요 없습니다.
    // state: 'random_state_string', // 제거
};

// code_verifier 저장을 위한 sessionStorage 키
const PKCE_VERIFIER_STORAGE_KEY = 'pkce_code_verifier';
const OAUTH_STATE_STORAGE_KEY = 'oauth_state'; // state 저장을 위한 키


async function handleLogin() {
  // 1. PKCE 코드 생성
  const { code_verifier, code_challenge } = await generatePkceCodes();

  // 2. state 값 동적 생성
  const state = generateState(); // 또는 generateRandomString(32); 사용

  // 3. code_verifier와 state 저장
  sessionStorage.setItem(PKCE_VERIFIER_STORAGE_KEY, code_verifier);
  sessionStorage.setItem(OAUTH_STATE_STORAGE_KEY, state); // 동적으로 생성된 state 저장

  // 4. Authorization URL 생성
  const authUrl = new URL(OAUTH_CONFIG.authorizationEndpoint);
  authUrl.searchParams.append('client_id', OAUTH_CONFIG.clientId);
  authUrl.searchParams.append('redirect_uri', OAUTH_CONFIG.redirectUri);
  authUrl.searchParams.append('response_type', 'code'); // Authorization Code Flow
  authUrl.searchParams.append('scope', OAUTH_CONFIG.scope);
  authUrl.searchParams.append('state', state); // 동적으로 생성된 state 사용
  authUrl.searchParams.append('code_challenge', code_challenge); // PKCE 파라미터
  authUrl.searchParams.append('code_challenge_method', 'S256'); // SHA256 사용 명시

  // 5. Authorization Server로 리디렉션
  window.location.replace(authUrl.toString());
}

function LoginButton() {
  return (
    <button onClick={handleLogin}>
      Login with OAuth 2.0
    </button>
  );
}

export default LoginButton;
