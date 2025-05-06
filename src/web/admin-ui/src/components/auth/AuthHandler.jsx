// AuthHandler.jsx
import React, { useEffect, useState } from 'react'; // useState import
import { useLocation, useNavigate } from 'react-router-dom';
import { generatePkceCodes } from './pkceUtils'; // generatePkceCodes만 필요

// OAuth 설정 (실제 값으로 대체 필요)
const OAUTH_CONFIG = {
  clientId: 'YOUR_CLIENT_ID',
  redirectUri: 'YOUR_REDIRECT_URI', // 예: 'http://localhost:3000/callback'
  authorizationEndpoint: 'YOUR_AUTH_SERVER_AUTHORIZATION_ENDPOINT',
  tokenEndpoint: 'YOUR_AUTH_SERVER_TOKEN_ENDPOINT',
  scope: 'openid profile email', // 필요한 스코프 설정
};

// code_verifier 저장을 위한 sessionStorage 키
const PKCE_VERIFIER_STORAGE_KEY = 'pkce_code_verifier';
const OAUTH_STATE_STORAGE_KEY = 'oauth_state'; // state 저장을 위한 키
const ACCESS_TOKEN_STORAGE_KEY = 'access_token'; // 토큰 저장을 위한 키 (예시)
const ID_TOKEN_STORAGE_KEY = 'id_token';
const REFRESH_TOKEN_STORAGE_KEY = 'refresh_token';


function AuthHandler() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true); // 로딩 상태 관리
  const [error, setError] = useState(null); // 에러 상태 관리

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const errorParam = params.get('error'); // error 변수명 변경
    const receivedState = params.get('state');

    // 리디렉션 처리
    if (location.pathname === new URL(OAUTH_CONFIG.redirectUri).pathname) {
        if (code) {
          console.log('Authorization Code Received:', code);

          // 1. state 검증
          const storedState = sessionStorage.getItem(OAUTH_STATE_STORAGE_KEY);
          sessionStorage.removeItem(OAUTH_STATE_STORAGE_KEY); // 사용 후 삭제 (성공/실패 상관없이)

          if (!storedState || receivedState !== storedState) {
            console.error('State mismatch. Potential CSRF attack.');
            setError('로그인 요청이 유효하지 않습니다. 다시 시도해주세요.'); // 사용자에게 보여줄 메시지
            setIsLoading(false);
            // 에러 처리 로직 (예: 에러 페이지로 이동)
            navigate('/error?message=State mismatch', { replace: true }); // replace 옵션 추가
            return;
          }

          // state 검증 통과
          // 2. code_verifier 가져오기
          const code_verifier = sessionStorage.getItem(PKCE_VERIFIER_STORAGE_KEY);
          sessionStorage.removeItem(PKCE_VERIFIER_STORAGE_KEY); // 사용 후 삭제

          if (!code_verifier) {
            console.error('code_verifier not found in storage.');
             setError('보안 정보가 누락되었습니다. 다시 로그인해주세요.');
             setIsLoading(false);
            // 에러 처리 로직
            navigate('/error?message=PKCE verifier missing', { replace: true });
            return;
          }

          // 3. Token Exchange Request 수행
          exchangeCodeForTokens(code, code_verifier);

        } else if (errorParam) { // 에러 파라미터가 있는 경우
          console.error('OAuth Error:', errorParam);
          // 에러 처리 로직
          setError(`로그인 중 오류가 발생했습니다: ${errorParam}`);
          setIsLoading(false);
          navigate(`/error?message=${errorParam}`, { replace: true });
        } else {
            // 코드나 에러 파라미터 없이 리디렉션된 경우 (예: 그냥 콜백 URL로 접근)
             console.log('Redirected to callback without code or error.');
             setError('유효하지 않은 접근입니다.');
             setIsLoading(false);
             navigate('/', { replace: true }); // 홈으로 리디렉션 또는 에러 페이지
        }
    } else {
        // 콜백 경로가 아닌 다른 경로에서의 AuthHandler 처리 (선택 사항)
        // 예: 이미 로그인되어 있는지 확인하고 리디렉션 등
        console.log('AuthHandler mounted on a non-callback path.');
        setIsLoading(false); // 로딩 상태 해제
        // TODO: 여기에 이미 토큰이 있는지 확인하는 로직 등을 추가할 수 있습니다.
    }

  }, [location, navigate]); // location 또는 navigate 변경 시 effect 재실행

  // Token Exchange Request 함수
  const exchangeCodeForTokens = async (code, code_verifier) => {
    setIsLoading(true); // 토큰 교환 시작 시 로딩 상태 설정
    setError(null); // 이전 에러 초기화

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
        setError(`토큰 교환 실패: ${errorData.error_description || errorData.error || '알 수 없는 오류'}`);
        setIsLoading(false);
        navigate('/error?message=Token exchange failed', { replace: true });
        return;
      }

      const tokenData = await response.json();
      console.log('Tokens received:', tokenData);

      // 4. 받은 토큰 저장 (sessionStorage 또는 다른 안전한 저장소)
      // 이 부분은 아래 "토큰 관리" 섹션에서 더 자세히 다룹니다.
      sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, tokenData.access_token);
      sessionStorage.setItem(ID_TOKEN_STORAGE_KEY, tokenData.id_token); // ID Token 저장
      if (tokenData.refresh_token) {
         sessionStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, tokenData.refresh_token); // Refresh Token 저장
      }
      // TODO: 토큰 만료 시간 등도 함께 저장하고 관리 필요

      // 5. 로그인 성공 후 리디렉션 (예: 홈 페이지)
      setIsLoading(false); // 로딩 상태 해제
      navigate('/home', { replace: true }); // 토큰 저장 후 이동할 경로

    } catch (err) { // 네트워크 에러 등 예외 발생 시 처리
      console.error('Error during token exchange:', err);
      setError(`네트워크 오류 발생: ${err.message}`);
      setIsLoading(false);
      navigate('/error?message=Network error during token exchange', { replace: true });
    }
  };

const [isLoading, setIsLoading] = useState(true); // 로딩 상태 관리
const [error, setError] = useState(null); // 에러 상태 관리

  // ... (effect 및 exchangeCodeForTokens 함수 내에서 상태 업데이트)

  return (
    <div>
      {isLoading && <p>로그인 처리 중...</p>} {/* 로딩 상태 표시 */}
      {error && (
        <div style={{ color: 'red' }}>
          <p>{error}</p> {/* 에러 메시지 표시 */}
          {/* 사용자가 다시 시도할 수 있도록 로그인 버튼 등을 표시할 수 있습니다. */}
          {/* 에러 발생 시 로그인 버튼을 다시 표시하려면, error 상태일 때 LoginButton 컴포넌트를 렌더링하도록 설정합니다. */}
          <button onClick={() => navigate('/')}>홈으로 돌아가기</button>
          {/* 또는 <LoginButton /> 컴포넌트 렌더링 */}
        </div>
      )}
      {/* 로딩 중도 아니고 에러도 아닐 때, 콜백 경로가 아닌 경우에 대한 처리 */}
      {!isLoading && !error && location.pathname !== new URL(OAUTH_CONFIG.redirectUri).pathname && (
          // 이 컴포넌트가 다른 경로에서도 사용된다면, 여기에 로그인 필요 메시지나 로그인 버튼을 표시할 수 있습니다.
          // 또는 단순히 아무것도 렌더링하지 않고 다른 라우트에서 로그인 상태를 확인하도록 합니다.
          <p>로그인 상태 확인 중...</p>
      )}
      {/* 콜백 경로에서 처리 완료 후에는 이 컴포넌트가 자동으로 사라지거나, 다음 페이지로 리디렉션되므로 추가적인 UI 요소는 필요 없을 수 있습니다. */}
    </div>
  );
    
  
async function callProtectedApi() {
  const accessToken = sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (!accessToken) {
    console.log('Access Token not found. User not logged in.');
    // 로그인 페이지로 리디렉션 또는 에러 처리
    return;
  }

  try {
    const response = await fetch('YOUR_PROTECTED_API_ENDPOINT', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
        if (response.status === 401) {
            console.log('Access Token expired or invalid. Need to refresh or re-authenticate.');
            // TODO: Refresh Token을 사용하여 Access Token 갱신 로직 호출
        }
        throw new Error(`API request failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('API Response:', data);
    // API 응답 처리
  } catch (error) {
    console.error('Error calling protected API:', error);
    // 에러 처리 (예: 사용자에게 메시지 표시)
  }
}

// 예: 컴포넌트 마운트 시 API 호출
// useEffect(() => {
//   callProtectedApi();
// }, []);  
  

export default AuthHandler;
