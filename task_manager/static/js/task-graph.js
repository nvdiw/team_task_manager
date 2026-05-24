// Task Graph – With persistent positions and toggle dependency
const TaskGraph = (function() {
    // ---------- Private state ----------
    let config = {
        apiUrl: null,
        projectUrl: null,
        nodes: [],
        edges: [],
        nodePositions: [],
        zoom: 1,
        panX: 0,
        panY: 0,
        isPanning: false,
        dragStartX: 0,
        dragStartY: 0,
        colors: {
            'TODO': '#ef4444',
            'IN_PROGRESS': '#f59e0b',
            'DONE': '#10b981'
        }
    };

    let canvas = null;
    let ctx = null;
    let tooltipDiv = null;
    let hoveredNodeId = null;

    // Drag & drop state
    let draggedNode = null;
    let dragOffsetX = 0, dragOffsetY = 0;

    // Connection state (right‑click)
    let isConnecting = false;
    let connectionSourceId = null;

    // Message container (instead of alert)
    let messageDiv = null;

    // ---------- Helper functions ----------
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showMessage(text, isError = false) {
        if (!messageDiv) {
            messageDiv = document.createElement('div');
            messageDiv.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #1e293b;
                color: white;
                padding: 10px 20px;
                border-radius: 30px;
                font-size: 14px;
                z-index: 2000;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                backdrop-filter: blur(4px);
                border-left: 4px solid #6366f1;
                pointer-events: none;
                transition: opacity 0.3s;
                opacity: 0;
            `;
            document.body.appendChild(messageDiv);
        }
        if (isError) {
            messageDiv.style.borderLeftColor = '#ef4444';
            messageDiv.style.background = '#2d1a1a';
        } else {
            messageDiv.style.borderLeftColor = '#6366f1';
            messageDiv.style.background = '#1e293b';
        }
        messageDiv.textContent = text;
        messageDiv.style.opacity = '1';
        setTimeout(() => {
            if (messageDiv) messageDiv.style.opacity = '0';
        }, 3000);
    }

    // Save node position to backend
    function saveNodePosition(taskId, x, y) {
        fetch('/api/tasks/save-node-position/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin',
            body: JSON.stringify({ task_id: taskId, x: x, y: y })
        }).catch(err => console.warn('Failed to save position:', err));
    }

    // Check if a dependency already exists between two nodes
    function dependencyExists(sourceId, targetId) {
        return config.edges.some(edge => edge.data.source === sourceId && edge.data.target === targetId);
    }

    function screenToWorld(screenX, screenY) {
        const rect = canvas.getBoundingClientRect();
        const canvasX = (screenX - rect.left) * (canvas.width / rect.width);
        const canvasY = (screenY - rect.top) * (canvas.height / rect.height);
        const worldX = (canvasX / config.zoom) - config.panX;
        const worldY = (canvasY / config.zoom) - config.panY;
        return { x: worldX, y: worldY };
    }

    function drawArrow(ctx, fromX, fromY, toX, toY) {
        const angle = Math.atan2(toY - fromY, toX - fromX);
        const arrowSize = 12;
        const arrowX = toX - arrowSize * 0.7 * Math.cos(angle);
        const arrowY = toY - arrowSize * 0.7 * Math.sin(angle);
        ctx.beginPath();
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(arrowX - arrowSize * 0.5 * Math.sin(angle), arrowY + arrowSize * 0.5 * Math.cos(angle));
        ctx.lineTo(arrowX + arrowSize * 0.5 * Math.sin(angle), arrowY - arrowSize * 0.5 * Math.cos(angle));
        ctx.fillStyle = '#64748b';
        ctx.fill();
    }

    function drawGrid() {
        if (!ctx) return;
        ctx.save();
        ctx.scale(config.zoom, config.zoom);
        ctx.translate(config.panX, config.panY);
        const w = canvas.width / config.zoom;
        const h = canvas.height / config.zoom;
        const step = 50;
        ctx.beginPath();
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 0.5;
        for (let x = -config.panX % step; x < w; x += step) {
            ctx.moveTo(x, -config.panY);
            ctx.lineTo(x, h - config.panY);
            ctx.stroke();
        }
        for (let y = -config.panY % step; y < h; y += step) {
            ctx.moveTo(-config.panX, y);
            ctx.lineTo(w - config.panX, y);
            ctx.stroke();
        }
        ctx.restore();
    }

    function drawEdges() {
        if (!ctx) return;
        ctx.save();
        ctx.scale(config.zoom, config.zoom);
        ctx.translate(config.panX, config.panY);
        ctx.lineWidth = 2.5 / config.zoom;
        ctx.strokeStyle = '#94a3b8';
        for (const edge of config.edges) {
            const source = config.nodePositions.find(n => n.id === edge.data.source);
            const target = config.nodePositions.find(n => n.id === edge.data.target);
            if (source && target) {
                ctx.beginPath();
                ctx.moveTo(source.x, source.y);
                ctx.lineTo(target.x, target.y);
                ctx.stroke();
                drawArrow(ctx, source.x, source.y, target.x, target.y);
            }
        }
        ctx.restore();
    }

    function drawNodes() {
        if (!ctx) return;
        ctx.save();
        ctx.scale(config.zoom, config.zoom);
        ctx.translate(config.panX, config.panY);
        for (const node of config.nodePositions) {
            const x = node.x - node.width/2;
            const y = node.y - node.height/2;
            const color = config.colors[node.status] || '#6366f1';
            const isHovered = (hoveredNodeId === node.id);
            ctx.shadowBlur = isHovered ? 12 : 5;
            ctx.shadowColor = 'rgba(0,0,0,0.2)';
            ctx.fillStyle = color;
            ctx.beginPath();
            const r = 8;
            ctx.moveTo(x + r, y);
            ctx.lineTo(x + node.width - r, y);
            ctx.quadraticCurveTo(x + node.width, y, x + node.width, y + r);
            ctx.lineTo(x + node.width, y + node.height - r);
            ctx.quadraticCurveTo(x + node.width, y + node.height, x + node.width - r, y + node.height);
            ctx.lineTo(x + r, y + node.height);
            ctx.quadraticCurveTo(x, y + node.height, x, y + node.height - r);
            ctx.lineTo(x, y + r);
            ctx.quadraticCurveTo(x, y, x + r, y);
            ctx.fill();
            if (isHovered) {
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2.5 / config.zoom;
                ctx.stroke();
            }
            ctx.fillStyle = '#fff';
            ctx.font = `bold ${12 / config.zoom}px "Segoe UI", sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            let label = node.label;
            if (label.length > 20) label = label.slice(0, 18) + '...';
            ctx.fillText(label, node.x, node.y);
        }
        ctx.restore();
    }

    function render() {
        if (!canvas || !ctx) return;
        canvas.width = canvas.width; // clear
        drawGrid();
        drawEdges();
        drawNodes();
    }

    // ---------- Node positions (circular layout with saved positions) ----------
    function calculateNodePositions(savedPositions = {}) {
        const w = canvas.width;
        const h = canvas.height;
        const centerX = w / 2;
        const centerY = h / 2;
        const radius = Math.min(w, h) / 3;
        const total = config.nodes.length;
        config.nodePositions = [];
        config.nodes.forEach((node, idx) => {
            let x, y;
            const saved = savedPositions[node.data.id];
            if (saved && typeof saved.x === 'number' && typeof saved.y === 'number') {
                x = saved.x;
                y = saved.y;
            } else {
                const angle = (idx / total) * Math.PI * 2;
                x = centerX + radius * Math.cos(angle);
                y = centerY + radius * Math.sin(angle);
            }
            config.nodePositions.push({
                id: node.data.id,
                x: x,
                y: y,
                label: node.data.label,
                status: node.data.status,
                priority: node.data.priority,
                width: 120,
                height: 40
            });
        });
    }

    // ---------- Tooltip ----------
    function createTooltip() {
        const div = document.createElement('div');
        div.className = 'graph-tooltip';
        div.style.cssText = `
            position: fixed;
            background: rgba(30,41,59,0.95);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 260px;
            backdrop-filter: blur(4px);
            border-left: 3px solid #6366f1;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        document.body.appendChild(div);
        return div;
    }

    function showTooltip(node, mouseX, mouseY) {
        if (!tooltipDiv) return;
        const task = config.nodes.find(n => n.data.id === node.id);
        if (!task) return;
        const statusText = node.status === 'TODO' ? '📋 To Do' : (node.status === 'IN_PROGRESS' ? '⚙️ In Progress' : '✅ Done');
        const priorityText = (node.priority || 'NONE').toLowerCase();
        const priorityLabel = { low: 'Low', medium: 'Medium', high: 'High', urgent: 'Urgent' }[priorityText] || 'None';
        let desc = task.data.description || '';
        if (desc.length > 100) desc = desc.slice(0, 100) + '…';
        tooltipDiv.innerHTML = `
            <strong>${node.label}</strong><br>
            <span style="font-size: 10px;">Status: ${statusText}</span><br>
            <span style="font-size: 10px;">Priority: ${priorityLabel}</span>
            ${desc ? `<br><span style="font-size: 10px; color:#cbd5e1;">${desc}</span>` : ''}
        `;
        tooltipDiv.style.left = (mouseX + 15) + 'px';
        tooltipDiv.style.top = (mouseY + 15) + 'px';
        tooltipDiv.style.opacity = '1';
    }

    function hideTooltip() {
        if (tooltipDiv) tooltipDiv.style.opacity = '0';
    }

    // ---------- Event handlers ----------
    function onMouseMove(e) {
        if (draggedNode) return;
        const world = screenToWorld(e.clientX, e.clientY);
        let hovered = null;
        for (const node of config.nodePositions) {
            const left = node.x - node.width/2;
            const right = node.x + node.width/2;
            const top = node.y - node.height/2;
            const bottom = node.y + node.height/2;
            if (world.x >= left && world.x <= right && world.y >= top && world.y <= bottom) {
                hovered = node;
                break;
            }
        }
        if (hovered) {
            if (hoveredNodeId !== hovered.id) {
                hoveredNodeId = hovered.id;
                showTooltip(hovered, e.clientX, e.clientY);
                render();
            } else {
                if (tooltipDiv) {
                    tooltipDiv.style.left = (e.clientX + 15) + 'px';
                    tooltipDiv.style.top = (e.clientY + 15) + 'px';
                }
            }
        } else if (hoveredNodeId !== null) {
            hoveredNodeId = null;
            hideTooltip();
            render();
        }
    }

    function onCanvasMouseDown(e) {
        const world = screenToWorld(e.clientX, e.clientY);
        if (e.button === 0) {
            for (const node of config.nodePositions) {
                const left = node.x - node.width/2;
                const right = node.x + node.width/2;
                const top = node.y - node.height/2;
                const bottom = node.y + node.height/2;
                if (world.x >= left && world.x <= right && world.y >= top && world.y <= bottom) {
                    draggedNode = node;
                    dragOffsetX = node.x - world.x;
                    dragOffsetY = node.y - world.y;
                    canvas.style.cursor = 'grabbing';
                    e.preventDefault();
                    break;
                }
            }
            if (!draggedNode) {
                config.isPanning = true;
                config.dragStartX = e.clientX;
                config.dragStartY = e.clientY;
                canvas.style.cursor = 'grabbing';
            }
        }
    }

    function onGlobalMouseMove(e) {
        if (draggedNode) {
            const world = screenToWorld(e.clientX, e.clientY);
            draggedNode.x = world.x + dragOffsetX;
            draggedNode.y = world.y + dragOffsetY;
            render();
        } else if (config.isPanning) {
            const dx = e.clientX - config.dragStartX;
            const dy = e.clientY - config.dragStartY;
            config.panX += dx;
            config.panY += dy;
            config.dragStartX = e.clientX;
            config.dragStartY = e.clientY;
            render();
        } else {
            onMouseMove(e);
        }
    }

    function onGlobalMouseUp(e) {
        if (draggedNode) {
            // Save position after drag
            saveNodePosition(draggedNode.id, draggedNode.x, draggedNode.y);
            draggedNode = null;
        }
        config.isPanning = false;
        if (canvas) canvas.style.cursor = 'grab';
    }

    // Right‑click connection logic (toggle create/delete)
    function onCanvasContextMenu(e) {
        e.preventDefault();
        const world = screenToWorld(e.clientX, e.clientY);
        let clickedNode = null;
        for (const node of config.nodePositions) {
            const left = node.x - node.width/2;
            const right = node.x + node.width/2;
            const top = node.y - node.height/2;
            const bottom = node.y + node.height/2;
            if (world.x >= left && world.x <= right && world.y >= top && world.y <= bottom) {
                clickedNode = node;
                break;
            }
        }
        if (clickedNode) {
            if (!isConnecting) {
                isConnecting = true;
                connectionSourceId = clickedNode.id;
                canvas.style.cursor = 'crosshair';
                showMessage(`🔗 Connecting from "${clickedNode.label}". Now right‑click on another task.`);
            } else {
                const targetId = clickedNode.id;
                if (connectionSourceId !== targetId) {
                    const exists = dependencyExists(connectionSourceId, targetId);
                    const url = exists ? '/api/tasks/dependency/delete/' : '/api/tasks/dependency/create/';
                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        credentials: 'same-origin',
                        body: JSON.stringify({
                            source_id: connectionSourceId,
                            target_id: targetId
                        })
                    })
                    .then(async response => {
                        const text = await response.text();
                        try {
                            const data = JSON.parse(text);
                            if (data.success) {
                                showMessage(exists ? '❌ Dependency removed! Reloading...' : '✅ Dependency created! Reloading...');
                                setTimeout(() => location.reload(), 800);
                            } else {
                                showMessage('❌ Error: ' + (data.error || 'Unknown error'), true);
                            }
                        } catch (err) {
                            console.error('Invalid JSON response:', text);
                            showMessage('❌ Server error. Check console.', true);
                        }
                    })
                    .catch(err => {
                        console.error('Fetch error:', err);
                        showMessage('❌ Network error: ' + err.message, true);
                    });
                } else {
                    showMessage('❌ Cannot connect a task to itself.', true);
                }
                isConnecting = false;
                connectionSourceId = null;
                canvas.style.cursor = 'grab';
            }
        } else if (isConnecting) {
            isConnecting = false;
            connectionSourceId = null;
            canvas.style.cursor = 'grab';
            showMessage('Connection cancelled.');
        }
    }

    function attachCanvasEvents() {
        if (!canvas) return;
        canvas.addEventListener('mousedown', onCanvasMouseDown);
        canvas.addEventListener('contextmenu', onCanvasContextMenu);
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            config.zoom = Math.min(3, Math.max(0.5, config.zoom * delta));
            render();
        });
        window.addEventListener('mousemove', onGlobalMouseMove);
        window.addEventListener('mouseup', onGlobalMouseUp);
        window.addEventListener('resize', () => {
            if (canvas) {
                const container = canvas.parentElement;
                canvas.width = container.clientWidth;
                canvas.height = 550;
                // Recalculate positions using existing saved positions (not resetting)
                render();
            }
        });
    }

    // ---------- Data loading & initialization ----------
    function fetchData(apiUrl) {
        const container = document.getElementById('graphContainer');
        container.innerHTML = '<div style="text-align:center; padding:2rem;">Loading graph...</div>';
        fetch(apiUrl)
            .then(res => res.json())
            .then(data => {
                config.nodes = data.nodes || [];
                config.edges = data.edges || [];
                document.getElementById('totalTasks').innerText = config.nodes.length;
                document.getElementById('totalDeps').innerText = config.edges.length;
                const connected = new Set();
                config.edges.forEach(e => { connected.add(e.data.source); connected.add(e.data.target); });
                document.getElementById('connectedTasks').innerText = connected.size;

                container.innerHTML = '<canvas id="taskGraphCanvas" style="width:100%; height:550px; display:block; background:#fff; border-radius:12px; cursor:grab;"></canvas>';
                canvas = document.getElementById('taskGraphCanvas');
                ctx = canvas.getContext('2d');
                tooltipDiv = createTooltip();
                const rect = container.parentElement.getBoundingClientRect();
                canvas.width = rect.width;
                canvas.height = 550;
                // Use saved positions from backend
                calculateNodePositions(data.saved_positions || {});
                attachCanvasEvents();
                render();
            })
            .catch(err => {
                console.error(err);
                container.innerHTML = '<div style="color:red; text-align:center; padding:2rem;">Failed to load graph. Refresh page.</div>';
            });
    }

    // Button handlers (Reset button removed)
    function setupButtons() {
        document.getElementById('btn-zoom-in')?.addEventListener('click', () => {
            config.zoom = Math.min(3, config.zoom * 1.2);
            render();
        });
        document.getElementById('btn-zoom-out')?.addEventListener('click', () => {
            config.zoom = Math.max(0.5, config.zoom / 1.2);
            render();
        });
        document.getElementById('btn-fit')?.addEventListener('click', () => {
            config.zoom = 1;
            config.panX = 0;
            config.panY = 0;
            render();
        });
        // No btn-reset listener
    }

    // Public API
    return {
        init: function(projectId, apiUrl, projectUrl) {
            config.apiUrl = apiUrl;
            config.projectUrl = projectUrl;
            fetchData(apiUrl);
            setupButtons();
        }
    };
})();