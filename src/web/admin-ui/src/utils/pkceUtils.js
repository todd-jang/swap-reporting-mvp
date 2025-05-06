// pkceUtils.js

// 무작위 문자열 생성 (code_verifier용)
function generateRandomString(length) {
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let randomString = '';
  for (let i = 0; i < length; i++) {
    randomString += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return randomString;
}

// SHA256 해시 함수 (code_challenge용)
// Web Cryptography API 사용
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

// code_challenge 생성 함수
async function generateCodeChallenge(code_verifier) {
  const hashed = await sha256(code_verifier);
  const code_challenge = base64UrlEncode(hashed);
  return code_challenge;
}

// code_verifier 길이는 43자 이상 128자 이하 권장
const codeVerifierLength = 64;

export async function generatePkceCodes() {
  const code_verifier = generateRandomString(codeVerifierLength);
  const code_challenge = await generateCodeChallenge(code_verifier);
  return { code_verifier, code_challenge };
}
