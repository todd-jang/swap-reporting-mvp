// AuthHandler.jsx
import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom'; // react-router-dom 사용 가정
import { generatePkceCodes } from './pkceUtils';

// OAuth 설정 (실제 값으로 대체 필요)
const OAUTH_CONFIG = {
  clientId: 'YOUR_CLIENT_ID',
  redirectUri: 'YOUR_REDIRECT_URI', // 예: 'http://localhost:3000/callback'
  authorizationEndpoint: 'YOUR_AUTH_SERVER_AUTHORIZATION_ENDPOINT',
  tokenEndpoint: 'YOUR_AUTH_SERVER_TOKEN_ENDPOINT',
  scope: 'openid profile email', // 필요한 스코프 설정
  // state 값은 CSRF 방지를 위해 요청마다 고유하게 생성하고 저장 후 검증 필요
  // 여기서는 간단히 예시로 'random_state_string' 사용
  // 실제 앱에서는 generateRandomString 등으로 생성하고 sessionStorage에 저장 후 리디렉션 시 검증해야 함
  state: 'random_state_string',
};

// code_verifier 저장을 위한 sessionStorage 키
const PKCE_VERIFIER_STORAGE_KEY = 'pkce_code_verifier';
const OAUTH_STATE_STORAGE_KEY = 'oauth_state'; // state 저장을 위한 키

function AuthHandler() {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const error = params.get('error');
    const receivedState = params.get('state');

    // 리디렉션 처리
    if (code) {
      console.log('Authorization Code Received:', code);

      // 1. state 검증
      const storedState = sessionStorage.getItem(OAUTH_STATE_STORAGE_KEY);
      sessionStorage.removeItem(OAUTH_STATE_STORAGE_KEY); // 사용 후 삭제
      if (receivedState !== storedState) {
        console.error('State mismatch. Potential CSRF attack.');
        // 에러 처리 로직 (예: 에러 페이지로 이동)
        navigate('/error?message=State mismatch');
        return;
      }

      // 2. code_verifier 가져오기
      const code_verifier = sessionStorage.getItem(PKCE_VERIFIER_STORAGE_KEY);
      sessionStorage.removeItem(PKCE_VERIFIER_STORAGE_KEY); // 사용 후 삭제

      if (!code_verifier) {
        console.error('code_verifier not found in storage.');
        // 에러 처리 로직
        navigate('/error?message=PKCE verifier missing');
        return;
      }

      // 3. Token Exchange Request 수행
      exchangeCodeForTokens(code, code_verifier);

    } else if (error) {
      console.error('OAuth Error:', error);
      // 에러 처리 로직
      navigate('/error?message=' + error);
    }
    // TODO: 토큰이 이미 있는 경우 처리 로직 추가
    // TODO: 경로가 '/callback'이 아닌 다른 경로일 때의 초기 로딩 로직 추가
  }, [location, navigate]); // location 또는 navigate 변경 시 effect 재실행

  // Token Exchange Request 함수
  const exchangeCodeForTokens = async (code, code_verifier) => {
    const tokenParams = new URLSearchParams();
    tokenParams.append('grant_type', 'authorization_code');
    tokenParams.append('client_id', OAUTH_CONFIG.clientId);
    tokenParams.append('redirect_uri', OAUTH_CONFIG.redirectUri);
    tokenParams.append('code', code);
    tokenParams.append('code_verifier', code_verifier); // PKCE 핵심 파라미터

    try {
      const response = await fetch(OAUTH_CONFIG.tokenEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: tokenParams.toString(),
      });

      if (!response.ok) {
        // 에러 응답 처리
        const errorData = await response.json();
        console.error('Token exchange failed:', errorData);
        navigate('/error?message=Token exchange failed');
        return;
      }

      const tokenData = await response.json();
      console.log('Tokens received:', tokenData);

      // 4. 받은 토큰 저장 (localStorage 또는 sessionStorage)
      // 실제 앱에서는 보안 고려하여 적절한 저장소 선택 및 관리 필요
      sessionStorage.setItem('access_token', tokenData.access_token);
      sessionStorage.setItem('id_token', tokenData.id_token);
      if (tokenData.refresh_token) {
         sessionStorage.setItem('refresh_token', tokenData.refresh_token);
      }

      // 5. 로그인 성공 후 리디렉션 (예: 홈 페이지)
      navigate('/home'); // 토큰 저장 후 이동할 경로

    } catch (error) {
      console.error('Error during token exchange:', error);
      navigate('/error?message=Network error during token exchange');
    }
  };


  return (
    <div>
      {/* 로딩 스피너 등을 여기에 표시할 수 있습니다. */}
      {location.pathname === new URL(OAUTH_CONFIG.redirectUri).pathname ? (
        <p>로그인 처리 중...</p>
      ) : (
        <p>로그인 대기 중...</p> // 로그인 버튼 등을 표시할 컴포넌트
      )}
    </div>
  );
}

export default AuthHandler;
