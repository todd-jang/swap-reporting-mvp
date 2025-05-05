import React from 'react';
import { initiateKakaoLogin } from '../auth/kakaoAuth';

function LoginPage() {
  const handleLoginClick = () => {
    initiateKakaoLogin();
  };

  return (
    <div className="card" style={{ maxWidth: '400px', margin: '5rem auto', textAlign: 'center' }}>
      <div className="card-header">Admin Login</div>
      <p>Please log in to access the Admin UI.</p>
      <button onClick={handleLoginClick} className="button">Login with Kakao</button>
      {/* TODO: Add error message display if login fails */}
    </div>
  );
}

export default LoginPage;
