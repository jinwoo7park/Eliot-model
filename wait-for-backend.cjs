#!/usr/bin/env node

/**
 * 백엔드 서버가 시작될 때까지 기다리는 스크립트
 */
const http = require('http');

const BACKEND_URL = 'http://localhost:8000/api/health';
const MAX_ATTEMPTS = 30;
const DELAY_MS = 1000;

function checkBackend() {
  return new Promise((resolve, reject) => {
    const req = http.get(BACKEND_URL, (res) => {
      if (res.statusCode === 200) {
        resolve(true);
      } else {
        reject(new Error(`Backend returned status ${res.statusCode}`));
      }
    });

    req.on('error', (err) => {
      reject(err);
    });

    req.setTimeout(2000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

async function waitForBackend() {
  console.log('⏳ 백엔드 서버 시작 대기 중...');

  for (let i = 0; i < MAX_ATTEMPTS; i++) {
    try {
      await checkBackend();
      console.log('✅ 백엔드 서버가 준비되었습니다!');
      process.exit(0);
    } catch (err) {
      if (i < MAX_ATTEMPTS - 1) {
        process.stdout.write('.');
        await new Promise(resolve => setTimeout(resolve, DELAY_MS));
      } else {
        console.error('\n❌ 백엔드 서버가 시작되지 않았습니다.');
        console.error('백엔드 서버를 수동으로 확인하세요: python3 -m api.index');
        process.exit(1);
      }
    }
  }
}

waitForBackend();
