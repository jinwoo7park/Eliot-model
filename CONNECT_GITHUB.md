# GitHub 저장소 연결 가이드

이미 생성된 GitHub 저장소 [https://github.com/jinwoo7park/Eliot-model](https://github.com/jinwoo7park/Eliot-model)와 연결하는 방법입니다.

## 현재 디렉토리에서 실행할 명령어

프로젝트 루트 디렉토리에서 다음 명령어를 순서대로 실행하세요:

```bash
# 1. Git 저장소 초기화 (이미 되어있다면 생략 가능)
git init

# 2. 모든 파일 추가
git add .

# 3. 첫 커밋
git commit -m "Initial commit: Python port of MATLAB Elliot fitting code"

# 4. GitHub 저장소 연결
git remote add origin https://github.com/jinwoo7park/Eliot-model.git

# 5. 기본 브랜치를 main으로 설정
git branch -M main

# 6. GitHub에 푸시
git push -u origin main
```

## 이미 Git이 초기화되어 있다면

만약 이미 `git init`을 실행했거나 원격 저장소가 설정되어 있다면:

```bash
# 원격 저장소 확인
git remote -v

# 기존 원격 저장소가 있다면 제거 후 재설정
git remote remove origin
git remote add origin https://github.com/jinwoo7park/Eliot-model.git

# 또는 기존 원격 저장소 URL 변경
git remote set-url origin https://github.com/jinwoo7park/Eliot-model.git
```

## 문제 해결

### 인증 오류가 발생하는 경우

1. **Personal Access Token 사용** (권장):
   - GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
   - 새 토큰 생성 (repo 권한 필요)
   - 푸시 시 비밀번호 대신 토큰 사용

2. **SSH 키 사용**:
   ```bash
   git remote set-url origin git@github.com:jinwoo7park/Eliot-model.git
   ```

### 저장소가 비어있지 않은 경우

GitHub 저장소에 이미 파일이 있다면:

```bash
# 원격 저장소의 내용 가져오기
git pull origin main --allow-unrelated-histories

# 충돌 해결 후
git add .
git commit -m "Merge with remote repository"
git push origin main
```

## 업로드 후 확인

1. https://github.com/jinwoo7park/Eliot-model 에서 파일이 업로드되었는지 확인
2. README.md가 제대로 표시되는지 확인
3. 파일 구조가 올바른지 확인

## 다음 단계

- [ ] 코드 업로드 확인
- [ ] README.md가 제대로 표시되는지 확인
- [ ] Issues 활성화 (Settings > Features)
- [ ] 첫 번째 릴리스 생성 (Releases > Create a new release)


