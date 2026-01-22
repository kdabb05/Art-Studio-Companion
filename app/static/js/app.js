/**
 * Art Studio Companion - Frontend JavaScript
 */

// State
let isLoading = false;

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatContainer = document.getElementById('chat-container');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    autoResizeTextarea();
});

// ============== Chat Functions ==============

async function sendMessage(event) {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message || isLoading) return;

    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';
    resizeTextarea();

    // Show loading state
    setLoading(true);
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Remove loading message
        removeMessage(loadingId);

        if (data.success) {
            addMessage(data.response, 'assistant');

            // If the agent made tool calls, refresh relevant panels
            if (data.tool_calls && data.tool_calls.length > 0) {
                refreshDashboard();
            }
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('Sorry, I could not connect to the server. Please ensure it is running.', 'assistant');
        console.error('Chat error:', error);
    }

    setLoading(false);
}

function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = `msg-${Date.now()}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Parse markdown-like content
    const formattedContent = formatMessageContent(content);
    contentDiv.innerHTML = formattedContent;

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return messageDiv.id;
}

function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = `loading-${Date.now()}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="loading"></div> Thinking...';

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    chatContainer.scrollTop = chatContainer.scrollHeight;

    return messageDiv.id;
}

function removeMessage(id) {
    const message = document.getElementById(id);
    if (message) {
        message.remove();
    }
}

function formatMessageContent(content) {
    // Simple markdown-like formatting
    let formatted = content;

    // Handle line breaks
    formatted = formatted.replace(/\n/g, '<br>');

    // Handle bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Handle bullet points
    formatted = formatted.replace(/^- (.*?)(<br>|$)/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');

    // Handle numbered lists
    formatted = formatted.replace(/^\d+\. (.*?)(<br>|$)/gm, '<li>$1</li>');

    return formatted;
}

function setLoading(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    chatInput.disabled = loading;
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        document.getElementById('chat-form').dispatchEvent(new Event('submit'));
    }
}

function autoResizeTextarea() {
    chatInput.addEventListener('input', resizeTextarea);
}

function resizeTextarea() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}

// ============== Quick Actions ==============

function quickAction(action) {
    switch (action) {
        case 'scan':
            openModal('scan-modal');
            break;
        case 'new-project':
            openModal('project-modal');
            break;
        case 'low-stock':
            showLowStock();
            break;
        case 'inspiration':
            chatInput.value = 'I need some art inspiration. What should I paint today?';
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
            break;
    }
}

async function showLowStock() {
    setLoading(true);
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('/api/quick-action/check-supplies');
        const data = await response.json();

        removeMessage(loadingId);

        if (data.success) {
            let message = data.message;

            if (data.shopping_list && data.shopping_list.length > 0) {
                message += '\n\n**Shopping List:**\n';
                data.shopping_list.forEach(item => {
                    message += `- ${item.item}${item.brand ? ` (${item.brand})` : ''}\n`;
                });
            }

            addMessage(message, 'assistant');
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('Could not check supplies. Please try again.', 'assistant');
    }

    setLoading(false);
}

async function submitProjectIdea() {
    const idea = document.getElementById('project-idea').value.trim();
    if (!idea) return;

    closeModal('project-modal');

    // Send as chat message
    chatInput.value = `I want to create: ${idea}`;
    document.getElementById('chat-form').dispatchEvent(new Event('submit'));

    // Clear the modal input
    document.getElementById('project-idea').value = '';
}

async function scanSupplies(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('photo', file);

    closeModal('scan-modal');
    setLoading(true);
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('/api/supplies/scan', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        removeMessage(loadingId);

        if (data.success) {
            addMessage(data.message + '\n\nPlease describe what supplies you see in the photo.', 'assistant');
        } else {
            addMessage('Could not process the photo. Please try again.', 'assistant');
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('Could not upload the photo. Please try again.', 'assistant');
    }

    setLoading(false);
    event.target.value = ''; // Reset file input
}

async function uploadArtwork(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch('/api/portfolio/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Ask the agent to help add it to portfolio
            chatInput.value = `I just uploaded a new artwork. Please help me add it to my portfolio. The image is at: ${data.image_path}`;
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
        }
    } catch (error) {
        console.error('Upload error:', error);
    }

    event.target.value = ''; // Reset file input
}

// ============== Modal Functions ==============

function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// ============== Dashboard Functions ==============

async function loadDashboard() {
    refreshSupplies();
    refreshProjects();
    refreshPortfolio();
}

async function refreshDashboard() {
    loadDashboard();
}

async function refreshSupplies() {
    try {
        const response = await fetch('/api/supplies');
        const data = await response.json();

        if (data.success) {
            // Update summary counts
            document.getElementById('supply-plenty').textContent = data.summary?.plenty || 0;
            document.getElementById('supply-low').textContent = data.summary?.low || 0;
            document.getElementById('supply-empty').textContent = data.summary?.empty || 0;

            // Update low stock list
            const lowStockList = document.getElementById('low-stock-list');
            const lowItems = [...(data.by_status?.yellow || []), ...(data.by_status?.red || [])];

            if (lowItems.length > 0) {
                lowStockList.innerHTML = lowItems.slice(0, 5).map(item => `
                    <div class="list-item">
                        <div class="list-item-title">${item.name}</div>
                        <div class="list-item-subtitle">${item.brand || item.category || ''}</div>
                    </div>
                `).join('');
            } else {
                lowStockList.innerHTML = '<div class="empty-state"><small>All supplies well stocked</small></div>';
            }
        }
    } catch (error) {
        console.error('Failed to refresh supplies:', error);
    }
}

async function refreshProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();

        if (data.success) {
            const projectsList = document.getElementById('projects-list');

            if (data.projects && data.projects.length > 0) {
                projectsList.innerHTML = data.projects.slice(0, 5).map(project => `
                    <div class="list-item" onclick="loadProject(${project.id})">
                        <div class="list-item-title">${project.title}</div>
                        <div class="list-item-subtitle">${project.status} - ${project.medium || 'Mixed'}</div>
                    </div>
                `).join('');
            } else {
                projectsList.innerHTML = '<div class="empty-state"><small>No projects yet</small></div>';
            }
        }
    } catch (error) {
        console.error('Failed to refresh projects:', error);
    }
}

async function refreshPortfolio() {
    try {
        const [portfolioRes, statsRes] = await Promise.all([
            fetch('/api/portfolio'),
            fetch('/api/portfolio/stats')
        ]);

        const portfolioData = await portfolioRes.json();
        const statsData = await statsRes.json();

        if (statsData.success && statsData.stats) {
            document.getElementById('portfolio-completed').textContent = statsData.stats.by_status?.completed || 0;
            document.getElementById('portfolio-wip').textContent = statsData.stats.by_status?.wip || 0;
            document.getElementById('portfolio-sketches').textContent = statsData.stats.by_status?.sketch || 0;
        }

        if (portfolioData.success) {
            const grid = document.getElementById('portfolio-grid');

            if (portfolioData.pieces && portfolioData.pieces.length > 0) {
                grid.innerHTML = portfolioData.pieces.slice(0, 6).map(piece => `
                    <div class="gallery-item" onclick="viewPiece(${piece.id})" title="${piece.title}">
                        ${piece.image_path ?
                            `<img src="${piece.image_path}" alt="${piece.title}">` :
                            `<div style="display:flex;align-items:center;justify-content:center;height:100%;background:var(--surface-dark)">${piece.title.charAt(0)}</div>`
                        }
                    </div>
                `).join('');
            } else {
                grid.innerHTML = '<div class="empty-state"><p>No artwork yet</p><small>Start a project to add to your portfolio</small></div>';
            }
        }
    } catch (error) {
        console.error('Failed to refresh portfolio:', error);
    }
}

function loadProject(projectId) {
    chatInput.value = `Tell me about project #${projectId} and what I need to continue working on it.`;
    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
}

function viewPiece(pieceId) {
    chatInput.value = `Show me details about portfolio piece #${pieceId}.`;
    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
}
