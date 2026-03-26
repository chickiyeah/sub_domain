// 모든 통신에서 JWT 토큰을 자동으로 실어 보냅니다.
const API = {
    async post(url, data, auth = false) {
        const headers = { 'Content-Type': 'application/json' };
        if (auth) {
            const token = localStorage.getItem('access_token');
            if (!token) {
                location.href = '/';
                return;
            }
            headers['Authorization'] = `Bearer ${token}`;
        }

        const res = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });
        return res.json();
    }
};