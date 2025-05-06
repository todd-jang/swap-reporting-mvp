// AuthHandler.jsx
import React, { useEffect, useState, useContext } from 'react'; // useContext import
import { useLocation, useNavigate } from 'react-router-dom';
import { generatePkceCodes } from './pkceUtils';

// TODO: Context API를 사용하여 인증 상태를 관리하는 경우 import
// import { AuthContext } from './AuthContext';

// OAuth 설정 (실제 값으로 대체 필요)
const OAUTH_CONFIG = {
  clientId: 'YOUR_CLIENT_ID',
  redirectUri: 'YOUR_REDIRECT_URI', // 예: 'http://localhost:3000/callback'
  authorizationEndpoint: 'YOUR_AUTH_SERVER_AUTHORIZATION_ENDPOINT',
  tokenEndpoint: 'YOUR_AUTH_SERVER_TOKEN_ENDPOINT',
  scope: 'openid profile email offline_access', // Refresh Token을 받으려면 'offline_access' 스코프 요청 필요
};

// 토큰 저장을 위한 sessionStorage 키
const PKCE_VERIFIER_STORAGE_KEY = 'pkce_code_verifier';
const OAUTH_STATE_STORAGE_KEY = 'oauth_state';
const ACCESS_TOKEN_STORAGE_KEY = 'access_token';
const ID_TOKEN_STORAGE_KEY = 'id_token';
const REFRESH_TOKEN_STORAGE_KEY = 'refresh_token';


function AuthHandler() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // TODO: Context API를 사용하는 경우
  // const { setTokens, clearTokens } = useContext(AuthContext);


  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const errorParam = params.get('error');
    const receivedState = params.get('state');

    // 리디렉션 처리
    if (location.pathname === new URL(OAUTH_CONFIG.redirectUri).pathname) {
        if (code) {
          console.log('Authorization Code Received:', code);

          // 1. state 검증
          const storedState = sessionStorage.getItem(OAUTH_STATE_STORAGE_KEY);
          sessionStorage.removeItem(OAUTH_STATE_STORAGE_KEY);

          if (!storedState || receivedState !== storedState) {
            console.error('State mismatch. Potential CSRF attack.');
            setError('로그인 요청이 유효하지 않습니다. 다시 시도해주세요.');
            setIsLoading(false);
            navigate('/error?message=State mismatch', { replace: true });
            return;
          }

          // state 검증 통과
          // 2. code_verifier 가져오기
          const code_verifier = sessionStorage.getItem(PKCE_VERIFIER_STORAGE_KEY);
          sessionStorage.removeItem(PKCE_VERIFIER_STORAGE_KEY);

          if (!code_verifier) {
            console.error('code_verifier not found in storage.');
             setError('보안 정보가 누락되었습니다. 다시 로그인해주세요.');
             setIsLoading(false);
            navigate('/error?message=PKCE verifier missing', { replace: true });
            return;
          }

          // 3. Token Exchange Request 수행
          exchangeCodeForTokens(code, code_verifier);

        } else if (errorParam) {
          console.error('OAuth Error:', errorParam);
          setError(`로그인 중 오류가 발생했습니다: ${errorParam}`);
          setIsLoading(false);
          navigate(`/error?message=${errorParam}`, { replace: true });
        } else {
             console.log('Redirected to callback without code or error.');
             setError('유효하지 않은 접근입니다.');
             setIsLoading(false);
             navigate('/', { replace: true });
        }
    } else {
        // 콜백 경로가 아닌 경우 (예: 초기 로딩 또는 다른 페이지 접근)
        setIsLoading(false); // 로딩 상태 해제
        // TODO: 여기서는 토큰이 있는지 확인하고, 유효하면 세션을 유지하거나
        //       필요하다면 Refresh Token으로 갱신을 시도하는 로직을 추가할 수 있습니다.
        //       예: checkAndRefreshToken();
    }

  }, [location, navigate]);

  // Token Exchange Request 함수 (기존 코드)
  const exchangeCodeForTokens = async (code, code_verifier) => {
      // ... (이전 코드와 동일)
      try {
          // ... fetch 요청 ...
          const tokenData = await response.json();

          // 4. 받은 토큰 저장 (Refresh Token 포함)
          storeTokens(tokenData); // storeTokens 함수 호출

          // 5. 로그인 성공 후 리디렉션
          setIsLoading(false);
          navigate('/home', { replace: true });

      } catch (err) {
          // ... 에러 처리 ...
      }
  };

  // 토큰 저장 함수 (Refresh Token 저장 로직 포함)
  const storeTokens = (tokenData) => {
      sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, tokenData.access_token);
      sessionStorage.setItem(ID_TOKEN_STORAGE_KEY, tokenData.id_token);
      if (tokenData.refresh_token) {
         sessionStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, tokenData.refresh_token);
      }
      // TODO: Context API를 사용하는 경우 setTokens(tokenData); 호출
      // TODO: 토큰 만료 시간을 계산하여 함께 저장 (Optional, 하지만 권장)
      // 예: const expiresInMs = tokenData.expires_in * 1000;
      //     const expiresAt = Date.now() + expiresInMs;
      //     sessionStorage.setItem('access_token_expires_at', expiresAt.toString());
  };

  // 토큰 삭제 함수
  const clearTokens = () => {
      sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
      sessionStorage.removeItem(ID_TOKEN_STORAGE_KEY);
      sessionStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
      // TODO: Context API를 사용하는 경우 clearTokens() 호출
      // TODO: 만료 시간 관련 정보도 삭제
      // sessionStorage.removeItem('access_token_expires_at');
  };


  // Access Token 갱신 함수 (새로 추가)
  const refreshToken = async () => {
      console.log('Attempting to refresh token...');
      const currentRefreshToken = sessionStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);

      if (!currentRefreshToken) {
          console.log('No refresh token available. User needs to re-authenticate.');
          clearTokens(); // 혹시 모를 잔여 토큰 정리
          navigate('/login', { replace: true }); // 로그인 페이지로 리디렉션
          return null; // 갱신 실패
      }

      const tokenParams = new URLSearchParams();
      tokenParams.append('grant_type', 'refresh_token');
      tokenParams.append('client_id', OAUTH_CONFIG.clientId);
      tokenParams.append('refresh_token', currentRefreshToken);
      // NOTE: Refresh Token Grant에는 PKCE code_verifier가 필요 없습니다.
      // tokenParams.append('scope', OAUTH_CONFIG.scope); // Optional: 갱신 시 스코프 재지정 (일반적으로는 원래 스코프 사용)

      try {
          const response = await fetch(OAUTH_CONFIG.tokenEndpoint, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/x-www-form-urlencoded',
              },
              body: tokenParams.toString(),
          });

          if (!response.ok) {
              // Refresh Token 갱신 실패 (예: Refresh Token 만료 또는 취소)
              const errorData = await response.json();
              console.error('Refresh token failed:', errorData);
              setError(`세션 만료: ${errorData.error_description || errorData.error || '다시 로그인해주세요.'}`);
              clearTokens(); // 모든 토큰 삭제
              navigate('/login', { replace: true }); // 로그인 페이지로 리디렉션
              return null; // 갱신 실패
          }

          const tokenData = await response.json();
          console.log('Tokens refreshed:', tokenData);

          // 새로운 토큰 저장 (새 Refresh Token이 올 수도 있으므로 업데이트)
          storeTokens(tokenData); // storeTokens 재사용

          console.log('Token refresh successful.');
          return tokenData.access_token; // 갱신된 Access Token 반환

      } catch (err) {
          console.error('Error during token refresh:', err);
          setError(`세션 갱신 중 네트워크 오류: ${err.message}. 다시 로그인해주세요.`);
          clearTokens();
          navigate('/login', { replace: true });
          return null; // 갱신 실패
      }
  };

  // TODO: 이 refreshToken 함수는 API 호출 로직에서 Access Token이 만료되었을 때 호출되도록 연결해야 합니다.
  //       예를 들어, API 요청을 보내는 axios interceptor 또는 fetch 래퍼 함수에서 401 에러를 감지하면 refreshToken 함수를 호출하고,
  //       성공 시 원래 요청을 새로운 Access Token으로 재시도하는 로직을 구현합니다.


  return (
    <div>
      {isLoading && <p>로그인 처리 중...</p>}
      {error && (
        <div style={{ color: 'red' }}>
          <p>{error}</p>
          <button onClick={() => { setError(null); navigate('/login'); }}>다시 로그인</button> {/* 다시 로그인 버튼 추가 */}
        </div>
      )}
      {/* 다른 경로에서의 상태 표시 (필요하다면) */}
      {!isLoading && !error && location.pathname !== new URL(OAUTH_CONFIG.redirectUri).pathname && (
          <p>인증 상태 확인 중...</p>
      )}
    </div>
  );
}

export default AuthHandler;
