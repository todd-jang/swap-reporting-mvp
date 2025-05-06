// pkceUtils.js

// 무작위 문자열 생성 (code_verifier, state 용)
export function generateRandomString(length) { // export 추가
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let randomString = '';
  for (let i = 0; i < length; i++) {
    randomString += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return randomString;
}

// SHA256 해시 함수 (code_challenge용)
async function sha256(plain) {
  const encoder = new TextEncoder();
  const data = encoder.encode(plain);
  const hash = await window.crypto.subtle.digest('SHA-256', data);
  return hash;
}

// Base64 URL 인코딩 (code_challenge용)
function base64UrlEncode(input) {
  return btoa(String.fromCharCode(...new Uint8Array(input)))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

// code_verifier 길이 (43자 이상 128자 이하 권장)
const codeVerifierLength = 64;
// state 길이 (충분히 길게 생성하여 예측 어렵게 함)
const stateLength = 32; // 예시 길이

export async function generatePkceCodes() {
  const code_verifier = generateRandomString(codeVerifierLength);
  const code_challenge = await generateCodeChallenge(code_verifier);
  return { code_verifier, code_challenge };
}

async function generateCodeChallenge(code_verifier) {
    const hashed = await sha256(code_verifier);
    const code_challenge = base64UrlEncode(hashed);
    return code_challenge;
}

// state 생성 함수 (새로 추가)
export function generateState() {
    return generateRandomString(stateLength);
}
