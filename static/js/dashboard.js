let currentDomains = []; // 전역 변수로 도메인 목록 보관

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
        location.href = "/";
        return;
    }
    loadDomains();
});

// 타입별 색상 지정 유틸리티
function getTypeColor(type) {
    switch(type) {
        case 'A': return 'bg-blue-500/20 text-blue-400';
        case 'AAAA': return 'bg-purple-500/20 text-purple-400';
        case 'CNAME': return 'bg-green-500/20 text-green-400';
        case 'MX': return 'bg-orange-500/20 text-orange-400';
        case 'TXT': return 'bg-slate-500/20 text-slate-300';
        default: return 'bg-indigo-500/20 text-indigo-400';
    }
}
// 1. 목록 로드
async function loadDomains() {
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch('/dns/my-domains', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.status === 401) logout();
        
        currentDomains = await res.json();
        const container = document.getElementById('domainList');
        container.innerHTML = '';

        if (currentDomains.length === 0) {
            container.innerHTML = '<p class="text-slate-500 col-span-full text-center py-20">등록된 도메인이 없습니다.</p>';
            return;
        }

        // --- 1. 데이터 그룹화 (subdomain 기준) ---
        const grouped = currentDomains.reduce((acc, domain) => {
            const key = domain.subdomain;
            if (!acc[key]) acc[key] = [];
            acc[key].push(domain);
            return acc;
        }, {});

        // --- 2. 그룹별로 카드 생성 ---
        for (const [subdomain, records] of Object.entries(grouped)) {
            // 카드 상단 (도메인 이름)
            let cardHtml = `
                <div class="bg-slate-800/80 rounded-2xl border border-slate-700 shadow-xl overflow-hidden mb-4">
                    <div class="bg-slate-700/30 px-6 py-4 border-b border-slate-700">
                        <h3 class="font-bold text-lg text-indigo-300">${subdomain}.decodns.org</h3>
                    </div>
                    <div class="p-2">
            `;

            // 카드 내부 (레코드 리스트)
            records.forEach(d => {
    const displayValue = d.content || d.ip || "";
    cardHtml += `
        <div class="flex justify-between items-center p-4 hover:bg-slate-700/40 rounded-xl transition-all group mb-1 cursor-pointer" onclick="prepareEdit(${d.id})">
            <div class="flex items-center gap-4">
                <span class="w-12 ${getTypeColor(d.type)} text-center px-2 py-0.5 bg-indigo-500/10 text-indigo-400 text-[10px] font-bold rounded border border-indigo-500/20 uppercase">
                    ${d.type}
                </span>
                <div class="flex flex-col">
                    <span class="text-sm text-slate-200 font-mono">${displayValue}</span>
                    ${d.priority ? `<span class="text-[10px] text-slate-500">우선순위: ${d.priority}</span>` : ''}
                </div>
            </div>

            <button onclick="event.stopPropagation(); handleDelete(${d.id})" 
                    class="text-slate-500 hover:text-red-400 p-3 bg-slate-700/20 hover:bg-red-500/10 rounded-lg transition-all ml-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
            </button>
        </div>
    `;
});

            cardHtml += `</div></div>`;
            container.innerHTML += cardHtml;
        }
    } catch (err) {
        console.error("로딩 실패:", err);
    }
}

// 2. 등록
async function handleRegister() {
    const type = document.getElementById('recordType').value;
    const subdomain = document.getElementById('subdomain').value;
    const content = document.getElementById('targetContent').value;
    const priority = document.getElementById('priority').value;
    const token = localStorage.getItem('access_token');

    const res = await fetch('/dns/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ 
            subdomain, 
            type, 
            content, 
            priority: type === 'MX' ? parseInt(priority) : null 
        })
    });

    if (res.ok) {
        alert("등록 성공!");
        location.reload();
    } else {
        const data = await res.json();
        alert("실패: " + (data.detail || "오류 발생"));
    }
}

// 수정 전용 변수 (처음 열었을 때의 타입을 기억함)
let originalType = "";

function prepareEdit(id) {
    const domain = currentDomains.find(d => d.id === id);
    if (!domain) return;

    originalType = domain.type; // 원래 타입을 저장해둠!
    
    document.getElementById('editId').value = domain.id;
    document.getElementById('editType').value = domain.type || "A";
    document.getElementById('editSubdomain').value = domain.subdomain || "";
    document.getElementById('editContent').value = domain.content || domain.ip || "";
    document.getElementById('editPriority').value = domain.priority || "";

    updateEditModalUI();
    document.getElementById('editModal').classList.remove('hidden');
}

async function submitEdit() {
    const id = document.getElementById('editId').value;
    const currentType = document.getElementById('editType').value;
    const token = localStorage.getItem('access_token');

    const payload = {
        subdomain: document.getElementById('editSubdomain').value,
        type: currentType,
        content: document.getElementById('editContent').value,
        priority: currentType === 'MX' ? parseInt(document.getElementById('editPriority').value) : null
    };

    // [핵심 로직] 타입이 처음과 달라졌다면? -> "추가(POST)"로 취급!
    if (currentType !== originalType) {
        if (!confirm(`타입이 ${originalType}에서 ${currentType}으로 변경되었습니다. 기존 레코드는 유지하고 새 레코드로 추가할까요?`)) {
            // 취소를 누르면 그냥 기존 레코드를 수정(PUT)하게 내버려두거나 중단할 수 있습니다.
            // 여기서는 "기존 건 두고 새로 추가"하는 것을 기본으로 합니다.
        } else {
            // 새로 추가 (POST)
            const res = await fetch('/dns/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(payload)
            });
            if (res.ok) { alert("새로운 레코드 타입이 추가되었습니다!"); location.reload(); }
            return;
        }
    }

    // 타입이 같거나, 사용자가 수정을 원할 경우 (PUT)
    const res = await fetch(`/dns/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("레코드가 수정되었습니다!");
        location.reload();
    } else {
        const data = await res.json();
        alert("오류: " + data.detail);
    }
}

// 5. 삭제
async function handleDelete(id) {
    if (!confirm("정말 삭제할까요?")) return;
    const res = await fetch(`/dns/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    });
    if (res.ok) {
        loadDomains();
    }
}

// UI 유틸리티
function closeModal() { document.getElementById('editModal').classList.add('hidden'); }

function updateNewRecordUI() {
    const type = document.getElementById('recordType').value;
    document.getElementById('priority').classList.toggle('hidden', type !== 'MX');
}

// 수정 모달에서 타입을 변경할 때 호출되는 함수
function updateEditModalUI() {
    const selectedType = document.getElementById('editType').value;
    const currentSub = document.getElementById('editSubdomain').value;
    const priorityGroup = document.getElementById('editPriorityGroup');
    const warningBox = document.getElementById('typeWarning'); // HTML에 이 ID를 가진 div가 필요합니다.

    // 같은 서브도메인을 쓰는 다른 레코드가 있는지 체크
    const hasOtherRecords = currentDomains.some(d => d.subdomain === currentSub && d.type !== selectedType);

    // CNAME 선택 시 위험 안내
    if (selectedType === 'CNAME' && hasOtherRecords) {
        warningBox.innerHTML = "🚫 <b>주의:</b> 이 호스트 이름으로 다른 레코드가 존재합니다. CNAME으로 변경 시 충돌이 발생합니다.";
        warningBox.classList.remove('hidden');
    } else {
        warningBox.classList.add('hidden');
    }

    // 1. 현재 목록(currentDomains)에서 [같은 호스트 이름 && 선택한 타입]이 있는지 검색
    const existingRecord = currentDomains.find(d => 
        d.subdomain === currentSub && d.type === selectedType
    );

    if (existingRecord) {
        // [케이스 A] 이미 해당 타입으로 등록된 데이터가 있는 경우 -> 채워줌
        document.getElementById('editContent').value = existingRecord.content || existingRecord.ip || "";
        if (selectedType === 'MX') {
            document.getElementById('editPriority').value = existingRecord.priority || 10;
        }
        // (팁) 이미 있는 레코드를 수정하는 것이므로 ID도 해당 레코드의 ID로 바꿔주면 더 정확합니다.
        document.getElementById('editId').value = existingRecord.id;
    } else {
        // [케이스 B] 해당 타입으로 등록된 적이 없는 경우 -> 빈칸으로 비워줌
        document.getElementById('editContent').value = "";
        document.getElementById('editPriority').value = selectedType === 'MX' ? 10 : "";
    }

    // 2. MX 타입일 때만 우선순위 입력창 표시 (UI 토글)
    priorityGroup.classList.toggle('hidden', selectedType !== 'MX');
}

function logout() {
    localStorage.removeItem('access_token');
    location.href = "/";
}