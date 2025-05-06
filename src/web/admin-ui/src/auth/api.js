// api.js (axios 인스턴스 및 interceptor 설정 예시)
import axios from 'axios';
import { refreshToken } from './AuthHandler'; // AuthHandler에서 refreshToken 함수 import
import { ACCESS_TOKEN_STORAGE_KEY } from './AuthHandler'; // 토큰 키 import

const apiClient = axios.create({
  baseURL: 'YOUR_API_BASE_URL',
});

// 요청 인터셉터: Access Token을 요청 헤더에 추가
apiClient.interceptors.request.use(config => {
  const accessToken = sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// 응답 인터셉터: 401 에러 발생 시 토큰 갱신 및 요청 재시도
apiClient.interceptors.response.use(response => {
  return response;
}, async error => {
  const originalRequest = error.config;

  // 401 에러이고, 이미 재시도한 요청이 아니며, 토큰 갱신 중이 아닌 경우
  if (error.response.status === 401 && !originalRequest._retry) {
    originalRequest._retry = true; // 재시도 플래그 설정

    try {
      const newAccessToken = await refreshToken(); // 토큰 갱신 시도
      if (newAccessToken) {
        // 갱신 성공 시 새로운 Access Token으로 헤더 업데이트
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        // 원래 요청 재시도
        return apiClient(originalRequest);
      }
    } catch (refreshError) {
      // Refresh Token 갱신 실패 시 (refreshToken 함수 내에서 로그인 페이지로 리디렉션 이미 처리)
      console.error('Failed to refresh token and retry original request:', refreshError);
      return Promise.reject(refreshError); // 에러 전파
    }
  }

  // 401 에러가 아니거나, 이미 재시도했거나, Refresh Token 갱신에 실패한 경우
  return Promise.reject(error);
});

export default apiClient;
