/* GxP Chromatography Platform Frontend Engine with 21 CFR Part 11 RBAC */

let cyInstance = null;
let currentRecords = [];
let currentFilter = 'ALL';
let activeRecordForApproval = null;
let activeTokenForMapping = null;

// User Session State (Default Scientist/Analyst)
let currentUser = {
    id: 'Dr. Jane Analyst',
    role: 'ANALYST' // 'ANALYST' or 'QA_QC'
};

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    updateUserSessionUI();
    await refreshData();
}

function updateUserSessionUI() {
    document.getElementById('session-user-id').textContent = currentUser.id;
    const badge = document.getElementById('session-role-badge');
    if (currentUser.role === 'QA_QC') {
        badge.textContent = 'QA/QC Lead (Admin)';
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/20 text-amber-400 border border-amber-500/30';
    } else {
        badge.textContent = 'Scientist/Analyst';
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-sky-500/20 text-sky-400 border border-sky-500/30';
    }
}

function setupEventListeners() {
    // Role selection in Login Modal
    const roleAnalystBtn = document.getElementById('role-analyst');
    const roleQaBtn = document.getElementById('role-qa');
    const loginUserIdInput = document.getElementById('login-user-id');

    let selectedRole = 'ANALYST';

    roleAnalystBtn.addEventListener('click', () => {
        selectedRole = 'ANALYST';
        roleAnalystBtn.className = 'btn-role-select bg-sky-600 border border-sky-400 text-white p-3 rounded-lg text-left flex flex-col justify-between hover:bg-sky-500 transition';
        roleQaBtn.className = 'btn-role-select bg-slate-800 border border-slate-700 text-slate-400 p-3 rounded-lg text-left flex flex-col justify-between hover:bg-slate-700 transition';
        loginUserIdInput.value = 'Dr. Jane Analyst';
    });

    roleQaBtn.addEventListener('click', () => {
        selectedRole = 'QA_QC';
        roleQaBtn.className = 'btn-role-select bg-amber-600 border border-amber-400 text-white p-3 rounded-lg text-left flex flex-col justify-between hover:bg-amber-500 transition';
        roleAnalystBtn.className = 'btn-role-select bg-slate-800 border border-slate-700 text-slate-400 p-3 rounded-lg text-left flex flex-col justify-between hover:bg-slate-700 transition';
        loginUserIdInput.value = 'QA_Manager_Smith';
    });

    document.getElementById('btn-login-submit').addEventListener('click', () => {
        const uid = loginUserIdInput.value.trim() || (selectedRole === 'QA_QC' ? 'QA_Manager_Smith' : 'Dr. Jane Analyst');
        currentUser = {
            id: uid,
            role: selectedRole
        };
        updateUserSessionUI();
        document.getElementById('login-modal').classList.add('hidden');
        renderGrid();
        fetchResiduals();
    });

    document.getElementById('btn-switch-user').addEventListener('click', () => {
        document.getElementById('login-modal').classList.remove('hidden');
    });

    // Dropzone & File Input
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-sky-400', 'bg-slate-800');
    });
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-sky-400', 'bg-slate-800');
    });
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-sky-400', 'bg-slate-800');
        if (e.dataTransfer.files.length) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            uploadFile(e.target.files[0]);
        }
    });

    // Buttons
    document.getElementById('btn-sync-gcs').addEventListener('click', async () => {
        await fetch('/api/seed', { method: 'POST' });
        await refreshData();
    });

    document.getElementById('btn-reseed').addEventListener('click', async () => {
        await fetch('/api/seed', { method: 'POST' });
        await refreshData();
    });

    document.getElementById('btn-relayout-graph').addEventListener('click', () => {
        if (cyInstance) {
            cyInstance.elements().removeClass('dimmed').removeClass('highlighted');
            cyInstance.layout({ name: 'cose', animate: true }).run();
        }
    });

    // Filters
    document.querySelectorAll('.btn-filter').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-filter').forEach(b => {
                b.classList.remove('bg-sky-500', 'text-white');
                b.classList.add('text-slate-400');
            });
            e.target.classList.remove('text-slate-400');
            e.target.classList.add('bg-sky-500', 'text-white');
            currentFilter = e.target.dataset.filter;
            renderGrid();
        });
    });

    // Search
    document.getElementById('grid-search').addEventListener('input', () => {
        renderGrid();
    });

    // Modal Approval Events
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-cancel-btn').addEventListener('click', closeModal);
    document.getElementById('modal-submit-btn').addEventListener('click', submitApproval);

    // Modal Residual Map Events
    document.getElementById('modal-map-close').addEventListener('click', closeMapModal);
    document.getElementById('modal-map-cancel').addEventListener('click', closeMapModal);
    document.getElementById('modal-map-submit').addEventListener('click', submitResidualMap);

    // Chat Events
    document.getElementById('chat-send').addEventListener('click', sendChatMessage);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
    document.getElementById('chat-header').addEventListener('click', () => {
        const body = document.getElementById('chat-body');
        const footer = document.getElementById('chat-footer');
        const isHidden = body.classList.contains('hidden');
        body.classList.toggle('hidden', !isHidden);
        footer.classList.toggle('hidden', !isHidden);
    });
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/extract', {
            method: 'POST',
            body: formData
        });
        if (res.ok) {
            await refreshData();
        } else {
            alert('Extraction failed. Check file format.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function refreshData() {
    await Promise.all([
        fetchRecords(),
        fetchAuditLog(),
        fetchResiduals(),
        fetchGraph()
    ]);
}

async function fetchRecords() {
    const res = await fetch('/api/records');
    currentRecords = await res.json();
    renderGrid();
    updateStats();
}

function renderGrid() {
    const tbody = document.getElementById('grid-body');
    tbody.innerHTML = '';

    const searchTerm = document.getElementById('grid-search').value.toLowerCase();

    const filtered = currentRecords.filter(rec => {
        const statusMatch = currentFilter === 'ALL' || rec.verification_status === currentFilter;
        const data = rec.data || {};
        const textMatch = (data.Sample_ID || '').toLowerCase().includes(searchTerm) ||
                          (data.Analyte_Name || '').toLowerCase().includes(searchTerm) ||
                          (data.Equipment_Vendor || '').toLowerCase().includes(searchTerm);
        return statusMatch && textMatch;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" class="py-6 text-center text-slate-500 italic">No matching chromatography records found.</td></tr>`;
        return;
    }

    filtered.forEach(rec => {
        const d = rec.data || {};
        const status = rec.verification_status;
        const detector = d.detector || {};
        const detType = detector.Detector_Type || 'UV-VIS';
        
        let badgeClass = 'badge-passed';
        if (status === 'QUARANTINED') badgeClass = 'badge-quarantined';
        else if (status === 'FLAGGED') badgeClass = 'badge-flagged';
        else if (status === 'REVIEWED_APPROVED') badgeClass = 'badge-approved';

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-800/80 transition cursor-pointer';
        tr.innerHTML = `
            <td class="py-2.5 px-3 font-mono">
                <div class="font-bold text-sky-400">${rec.record_id}</div>
                <div class="text-[10px] text-slate-400">${d.Equipment_Vendor || 'Generic'} <span class="text-amber-400">(${detType})</span></div>
            </td>
            <td class="py-2.5 px-3 font-semibold text-slate-200">${d.Sample_ID}</td>
            <td class="py-2.5 px-3 font-medium text-emerald-400">${d.Analyte_Name}</td>
            <td class="py-2.5 px-3 font-mono">${d.Retention_Time} min</td>
            <td class="py-2.5 px-3 font-mono">${d.Peak_Area}</td>
            <td class="py-2.5 px-3 font-mono">${d.Tailing_Factor}</td>
            <td class="py-2.5 px-3 font-mono">${d.Plate_Count}</td>
            <td class="py-2.5 px-3 font-mono font-bold ${d.Percent_RSD > 2.0 ? 'text-rose-400' : 'text-slate-300'}">${d.Percent_RSD}%</td>
            <td class="py-2.5 px-3">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${badgeClass}">
                    ${status}
                </span>
            </td>
            <td class="py-2.5 px-3 text-right">
                ${(status === 'QUARANTINED' || status === 'FLAGGED') ? `
                    <button onclick="handleQaReviewClick('${rec.record_id}')" class="bg-amber-600 hover:bg-amber-500 text-white px-2.5 py-1 rounded text-[10px] font-bold transition flex items-center gap-1 ml-auto">
                        <i class="fa-solid fa-user-shield text-[9px]"></i> QA Review
                    </button>
                ` : `<span class="text-slate-500 text-[10px]"><i class="fa-solid fa-check text-emerald-400"></i> Released</span>`}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function handleQaReviewClick(recordId) {
    if (currentUser.role !== 'QA_QC') {
        alert("21 CFR Part 11 Access Control Violation:\n\nOnly users authenticated with the QA/QC Quality Lead role can authorize quarantined records.\n\nPlease click 'Switch User' in the top bar to switch session.");
        return;
    }
    openApprovalModal(recordId);
}

function updateStats() {
    const passed = currentRecords.filter(r => r.verification_status === 'PASSED' || r.verification_status === 'REVIEWED_APPROVED').length;
    const quarantined = currentRecords.filter(r => r.verification_status === 'QUARANTINED' || r.verification_status === 'FLAGGED').length;
    
    document.getElementById('stat-passed').textContent = passed;
    document.getElementById('stat-quarantined').textContent = quarantined;
    document.getElementById('stat-total').textContent = currentRecords.length;
}

async function fetchAuditLog() {
    const res = await fetch('/api/audit');
    const logs = await res.json();
    document.getElementById('stat-audit-count').textContent = `${logs.length} events`;

    const ul = document.getElementById('audit-log-list');
    ul.innerHTML = '';
    logs.slice().reverse().forEach(log => {
        const li = document.createElement('li');
        li.className = 'py-1.5 text-slate-300 space-y-0.5';
        const isQaAction = (log.event_type || '').includes('HITL') || (log.event_type || '').includes('QA');
        
        li.innerHTML = `
            <div class="flex items-center justify-between text-slate-400">
                <span class="font-bold ${isQaAction ? 'text-amber-400' : 'text-sky-400'}">[${log.event_type}]</span>
                <span class="text-[10px] text-slate-500 font-mono">${(log.timestamp || '').substring(11, 19)} UTC</span>
            </div>
            <div class="text-[10px] text-slate-300 font-mono flex items-center justify-between">
                <span>User: <strong class="text-slate-200">${log.user_id || 'System'}</strong> (${log.user_role || 'System'})</span>
                <span class="text-slate-500 truncate max-w-[150px]">Sig: ${(log.digital_signature_hash || '').substring(0, 10)}...</span>
            </div>
            ${log.reason_for_change ? `<div class="text-[10px] text-slate-400 italic">Reason: "${log.reason_for_change}"</div>` : ''}
        `;
        ul.appendChild(li);
    });
}

async function fetchResiduals() {
    const res = await fetch('/api/residuals');
    const resLogs = await res.json();

    const ul = document.getElementById('residual-log-list');
    ul.innerHTML = '';
    
    let totalUnmapped = 0;

    resLogs.forEach(entry => {
        if (!entry.unmapped_lines || entry.unmapped_lines.length === 0) return;
        totalUnmapped += entry.unmapped_lines.length;

        entry.unmapped_lines.forEach(token => {
            const li = document.createElement('li');
            li.className = 'py-1.5 text-slate-300 flex items-center justify-between gap-2';
            
            const isQaUser = currentUser.role === 'QA_QC';

            li.innerHTML = `
                <div class="truncate">
                    <span class="text-purple-400 font-bold">${token}</span>
                    <span class="text-[10px] text-slate-500 block truncate">Source: ${entry.filename} (${entry.vendor})</span>
                </div>
                <div>
                    ${isQaUser ? `
                        <button onclick="openMapModal('${token.replace(/'/g, "\\'")}')" class="bg-purple-600 hover:bg-purple-500 text-white px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1">
                            <i class="fa-solid fa-wrench text-[9px]"></i> Map Token
                        </button>
                    ` : `
                        <span class="text-[9px] bg-slate-800 text-slate-500 border border-slate-700 px-1.5 py-0.5 rounded italic">
                            🔒 QA/QC Admin Required
                        </span>
                    `}
                </div>
            `;
            ul.appendChild(li);
        });
    });

    if (totalUnmapped === 0) {
        ul.innerHTML = '<li class="text-slate-500 italic py-2 text-center">No unmapped residual tokens captured. Schema is fully aligned.</li>';
    }
}

async function fetchGraph() {
    const res = await fetch('/api/graph');
    const graphData = await res.json();

    if (!cyInstance) {
        cyInstance = cytoscape({
            container: document.getElementById('cytoscape-canvas'),
            elements: [...graphData.nodes, ...graphData.edges],
            style: [
                {
                    selector: 'node[type = "analyte_central"], node[type = "sample_analyte_central"], node[type = "sample_central"]',
                    style: {
                        'background-color': '#f97316',
                        'label': 'data(label)',
                        'color': '#ffedd5',
                        'font-size': '12px',
                        'font-weight': 'bold',
                        'text-valign': 'bottom',
                        'text-margin-y': 4,
                        'width': 36,
                        'height': 36,
                        'border-width': 3,
                        'border-color': '#ffedd5',
                        'transition-property': 'opacity, border-width, border-color',
                        'transition-duration': '0.2s'
                    }
                },
                {
                    selector: 'node',
                    style: {
                        'background-color': 'data(color)',
                        'label': 'data(label)',
                        'color': '#f8fafc',
                        'font-size': '10px',
                        'text-valign': 'bottom',
                        'text-margin-y': 4,
                        'width': 22,
                        'height': 22,
                        'transition-property': 'opacity, border-width, border-color',
                        'transition-duration': '0.2s'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 1.5,
                        'line-color': '#334155',
                        'target-arrow-color': '#334155',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '8px',
                        'color': '#64748b',
                        'transition-property': 'opacity, line-color',
                        'transition-duration': '0.2s'
                    }
                },
                {
                    selector: '.dimmed',
                    style: {
                        'opacity': 0.15
                    }
                },
                {
                    selector: '.highlighted',
                    style: {
                        'opacity': 1.0,
                        'border-width': 3,
                        'border-color': '#38bdf8',
                        'line-color': '#38bdf8',
                        'target-arrow-color': '#38bdf8'
                    }
                }
            ],
            layout: {
                name: 'cose',
                animate: false
            }
        });

        // Tap on node -> Hover connected data & show full hierarchy
        cyInstance.on('tap', 'node', (evt) => {
            const node = evt.target;
            const data = node.data();

            cyInstance.batch(() => {
                cyInstance.elements().addClass('dimmed').removeClass('highlighted');
                node.removeClass('dimmed').addClass('highlighted');
                node.neighborhood().removeClass('dimmed').addClass('highlighted');
            });

            const inspector = document.getElementById('node-inspector-content');

            // -------------------------------------------------------------
            // CENTRAL SAMPLE NODE VISUALIZER
            // -------------------------------------------------------------
            if (data.type === 'analyte_central' || data.type === 'sample_analyte_central' || data.type === 'sample_central') {
                const sampleName = data.sample_name || data.label;
                const connectedRuns = node.neighborhood('node[type = "peak_run"]').map(n => n.data());
                
                inspector.innerHTML = `
                    <div class="space-y-3">
                        <div class="bg-orange-950/40 p-3 rounded-lg border border-orange-500/50">
                            <p class="text-[10px] text-orange-400 font-bold uppercase tracking-wider mb-1 flex items-center justify-between">
                                <span><i class="fa-solid fa-vial-circle-check text-orange-300"></i> Central Analyte Visualizer</span>
                                <button onclick="resetGraphHighlight()" class="text-[9px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">
                                    Reset View
                                </button>
                            </p>
                            <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                                <span class="text-orange-400 font-mono">${sampleName}</span>
                            </h3>
                            <p class="text-[10px] text-slate-400 mt-1">Analyte Node behavior across different chromatographic systems and conditions.</p>
                        </div>

                        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-700">
                            <p class="text-[10px] text-slate-300 font-bold uppercase mb-2 flex items-center justify-between">
                                <span>Multi-System Behavior Summary</span>
                                <span class="text-amber-400 font-mono font-bold">${connectedRuns.length} Runs</span>
                            </p>
                            <div class="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                                ${connectedRuns.length > 0 ? connectedRuns.map(run => `
                                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-[11px] font-mono space-y-1">
                                        <div class="flex items-center justify-between text-slate-200">
                                            <span class="font-bold text-sky-400">${run.vendor || 'Generic'} (${run.det_type || 'UV-Vis'})</span>
                                            <span class="text-amber-400 font-bold text-[10px]">${run.rec_id}</span>
                                        </div>
                                        <div class="grid grid-cols-2 gap-1 text-[10px] text-slate-400">
                                            <div>Retention Time: <strong class="text-emerald-400">${run.rt || 'N/A'}m</strong></div>
                                            <div>Plates (N): <strong class="text-slate-300">${run.plates || 'N/A'}</strong></div>
                                            <div>Wavelength: <strong class="text-cyan-400">${run.wavelength || 'N/A'}nm</strong></div>
                                            <div>Temp: <strong class="text-purple-400">${run.col_temp || '30'}°C</strong></div>
                                        </div>
                                        <div class="text-[9px] text-slate-500 truncate">Column: ${run.col_model || 'C18 Reverse Phase'}</div>
                                    </div>
                                `).join('') : `<p class="text-slate-500 italic text-[11px]">No system runs linked yet.</p>`}
                            </div>
                        </div>
                    </div>
                `;
                return;
            }

            let parentComponent = 'Data System';
            if (data.type === 'field_detector' || data.id === 'comp_detector') parentComponent = 'Detector';
            else if (data.type === 'field_pump' || data.id === 'comp_pump') parentComponent = 'Pump';
            else if (data.type === 'field_autoinjector' || data.id === 'comp_autoinjector') parentComponent = 'Auto-Injector';
            else if (data.type === 'field_column' || data.id === 'comp_column') parentComponent = 'Column';
            else if (data.type === 'equipment_class') parentComponent = 'Root Hierarchy';

            inspector.innerHTML = `
                <div class="space-y-3">
                    <div class="bg-slate-900/90 p-3 rounded-lg border border-sky-500/40">
                        <p class="text-[10px] text-sky-400 font-bold uppercase tracking-wider mb-1 flex items-center justify-between">
                            <span><i class="fa-solid fa-sitemap"></i> Equipment Class Hierarchy</span>
                            <button onclick="resetGraphHighlight()" class="text-[9px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">
                                Reset View
                            </button>
                        </p>
                        <div class="font-mono text-xs text-slate-200 mt-2 space-y-1">
                            <div class="text-blue-400 font-bold"><i class="fa-solid fa-folder-open"></i> Class: Chromatography</div>
                            <div class="pl-2 border-l border-slate-700">
                                <div class="text-amber-400 font-semibold"><i class="fa-solid fa-cube"></i> Component: ${parentComponent}</div>
                                <div class="pl-4 border-l border-slate-700 mt-1 space-y-0.5 text-[11px]">
                                    <div class="text-emerald-400 font-bold">└── Entity: ${data.label}</div>
                                    <div class="text-slate-300">├── Type: <span class="uppercase font-mono text-sky-300">${data.type}</span></div>
                                    ${data.status ? `<div class="text-rose-400 font-bold">└── Verification: ${data.status}</div>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-700">
                        <p class="text-[10px] text-slate-400 font-bold uppercase mb-1">Entity Attributes</p>
                        <div class="space-y-1 text-[11px] text-slate-300 font-mono max-h-[160px] overflow-y-auto pr-1">
                            ${Object.entries(data).map(([k, v]) => `
                                <div class="flex items-center justify-between border-b border-slate-800 py-0.5">
                                    <span class="text-slate-500">${k}:</span>
                                    <span class="text-slate-200 font-medium text-right">${v}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        });

        cyInstance.on('tap', (evt) => {
            if (evt.target === cyInstance) {
                resetGraphHighlight();
            }
        });

    } else {
        cyInstance.elements().remove();
        cyInstance.add([...graphData.nodes, ...graphData.edges]);
        cyInstance.layout({ name: 'cose', animate: true }).run();
    }
}

function resetGraphHighlight() {
    if (cyInstance) {
        cyInstance.elements().removeClass('dimmed').removeClass('highlighted');
    }
}

function openApprovalModal(recordId) {
    activeRecordForApproval = recordId;
    document.getElementById('modal-rec-id').textContent = recordId;
    document.getElementById('qa-user-input').value = `${currentUser.id} (QA/QC Lead)`;
    document.getElementById('modal-approve').classList.remove('hidden');
}

function closeModal() {
    activeRecordForApproval = null;
    document.getElementById('modal-approve').classList.add('hidden');
}

async function submitApproval() {
    if (!activeRecordForApproval) return;
    
    const comment = document.getElementById('qa-comment-input').value || 'Approved via 21 CFR Part 11 QA HITL UI.';

    try {
        const res = await fetch('/api/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                record_id: activeRecordForApproval,
                qa_user: currentUser.id,
                user_role: currentUser.role,
                comment: comment
            })
        });

        if (res.ok) {
            closeModal();
            await refreshData();
        } else {
            const err = await res.json();
            alert(`Approval Failed: ${err.detail || 'Access Denied'}`);
        }
    } catch (err) {
        console.error(err);
    }
}

function openMapModal(token) {
    if (currentUser.role !== 'QA_QC') {
        alert("21 CFR Part 11 Access Control Violation:\n\nOnly users authenticated with the QA/QC Quality Lead role can map residual tokens.");
        return;
    }
    activeTokenForMapping = token;
    document.getElementById('map-target-token').textContent = token;
    document.getElementById('modal-map-residual').classList.remove('hidden');
}

function closeMapModal() {
    activeTokenForMapping = null;
    document.getElementById('modal-map-residual').classList.add('hidden');
}

async function submitResidualMap() {
    if (!activeTokenForMapping) return;

    const targetField = document.getElementById('map-ontology-select').value;
    const reason = document.getElementById('map-reason-input').value || 'QA/QC manual ontology mapping';

    try {
        const res = await fetch('/api/residuals/map', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                token: activeTokenForMapping,
                target_field: targetField,
                user_id: currentUser.id,
                user_role: currentUser.role,
                reason: reason
            })
        });

        if (res.ok) {
            closeMapModal();
            await refreshData();
        } else {
            const err = await res.json();
            alert(`Ontology Mapping Failed: ${err.detail || 'Access Denied'}`);
        }
    } catch (err) {
        console.error(err);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    const chatBody = document.getElementById('chat-body');
    
    const userDiv = document.createElement('div');
    userDiv.className = 'bg-sky-600/80 text-white p-2 rounded-lg ml-auto max-w-[85%] text-xs font-medium';
    userDiv.textContent = msg;
    chatBody.appendChild(userDiv);
    input.value = '';

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();

        const botDiv = document.createElement('div');
        botDiv.className = 'bg-slate-800/80 p-2 rounded-lg text-slate-300 max-w-[85%] border border-slate-700 text-xs';
        botDiv.textContent = data.response;
        chatBody.appendChild(botDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    } catch (err) {
        console.error(err);
    }
}
