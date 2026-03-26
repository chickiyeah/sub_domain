let currentMode = 'login'; // 기본값은 로그인 모드

const loginTab = document.getElementById('loginTab');
const signupTab = document.getElementById('signupTab');
const submitBtn = document.getElementById('submitBtn');
const authForm = document.getElementById('authForm');


// 공통 탭 스타일 클래스 정의 (Tailwind)
const activeClasses = ['border-b-2', 'border-indigo-500', 'text-white'];
const inactiveClasses = ['text-slate-400'];

// 1. 탭 전환 로직
// 로그인 탭 클릭 시
loginTab.addEventListener('click', () => {
    currentMode = 'login';
    
    // 로그인 탭 활성화
    loginTab.classList.add(...activeClasses);
    loginTab.classList.remove(...inactiveClasses);
    
    // 회원가입 탭 비활성화
    signupTab.classList.remove(...activeClasses);
    signupTab.classList.add(...inactiveClasses);
    
    submitBtn.innerText = '로그인';
});

// 회원가입 탭 클릭 시
signupTab.addEventListener('click', () => {
    currentMode = 'signup';
    
    // 회원가입 탭 활성화
    signupTab.classList.add(...activeClasses);
    signupTab.classList.remove(...inactiveClasses);
    
    // 로그인 탭 비활성화
    loginTab.classList.remove(...activeClasses);
    loginTab.classList.add(...inactiveClasses);
    
    submitBtn.innerText = '회원가입';
});
// 2. 폼 제출 로직
authForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // 페이지 새로고침 방지

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (currentMode === 'signup') {
        // 회원가입 처리
        try {
            const res = await fetch('/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            if (res.ok) {
                alert("회원가입 성공! 이제 로그인해주세요.");
                loginTab.click(); // 로그인 탭으로 자동 이동
            } else {
                alert("가입 실패: " + data.detail);
            }
        } catch (err) {
            alert("서버 연결 실패");
        }
    } else {
        // 로그인 처리
        try {
            // OAuth2PasswordRequestForm 형식에 맞게 FormData 사용
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch('/auth/login', {
                method: 'POST',
                body: formData // JSON이 아니라 FormData로 보냄
            });
            const data = await res.json();

            if (res.ok) {
                localStorage.setItem('access_token', data.access_token);
                location.href = "/dashboard"; // 대시보드로 이동
            } else {
                alert("로그인 실패: " + data.detail);
            }
        } catch (err) {
            alert("서버 연결 실패");
        }
    }
});