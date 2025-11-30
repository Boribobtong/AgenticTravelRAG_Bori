````markdown
# 🐙 Git 명령어 치트시트 (Git Cheat Sheet)

자주 사용하는 Git 명령어 모음입니다.

## 🚀 기본 워크플로우 (Basic Workflow)

가장 많이 사용하는 반복 작업 순서입니다.

````


1. **상태 확인**
   ```bash
   git status
   ```

      - 현재 변경된 파일, 스테이징된 파일 목록을 확인합니다.

<!-- end list -->

2.  **변경 사항 스테이징 (Add)**

    ```bash
    git add .
    ```

      - 현재 디렉토리의 모든 변경 사항을 스테이징 영역(Staging Area)에 올립니다.
      - 특정 파일만 올리려면: `git add 파일명`

3.  **커밋 (Commit)**

    ```bash
    git commit -m "커밋 메시지 작성"
    ```

      - 스테이징된 변경 사항을 로컬 저장소에 저장합니다.
      - 메시지는 명확하고 간결하게 작성합니다 (예: `feat: 로그인 기능 추가`).

4.  **푸시 (Push)**

    ```bash
    git push origin <브랜치명>
    ```

      - 로컬 커밋을 원격 저장소(GitHub)에 업로드합니다.
      - 예: `git push origin develop`

5.  **풀 (Pull)**

    ```bash
    git pull origin <브랜치명>
    ```

      - 원격 저장소의 최신 변경 사항을 가져와 로컬에 병합합니다.
      - 작업 시작 전에 실행하는 것이 좋습니다.

-----

## 🌿 브랜치 작업 (Branching)

1.  **브랜치 목록 확인**

    ```bash
    git branch
    ```

2.  **새 브랜치 생성 및 이동**

    ```bash
    git checkout -b <새로운_브랜치명>
    ```

      - 예: `git checkout -b feature/login`

3.  **브랜치 이동**

    ```bash
    git checkout <브랜치명>
    # 또는
    git switch <브랜치명>
    ```

4.  **브랜치 병합 (Merge)**

    ```bash
    # (예: feature 브랜치를 develop에 병합하려는 경우)
    git checkout develop
    git merge <feature_브랜치명>
    ```

-----

## 🛠️ 문제 해결 및 유용한 팁 (Troubleshooting)

### 변경 사항이 감지되지 않을 때 (Working tree clean 문제)

파일을 수정했는데 `git status`나 `git add`가 반응하지 않을 때 캐시를 새로고침합니다.

```bash
git update-index --refresh
```

### 마지막 커밋 메시지 수정하기

아직 푸시하지 않은 마지막 커밋의 메시지를 수정합니다.

```bash
git commit --amend -m "수정할 메시지"
```

### 로그 확인하기

커밋 히스토리를 확인합니다.

```bash
git log --oneline --graph --all
```