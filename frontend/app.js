/**
 * CivicScheme AI - Production Frontend
 * JWT-Authenticated Government Schemes Finder
 */

// ============== Configuration ==============
const API_BASE = '/api';
const ANIMATION_DURATION = 300;

// ============== Initialization ==============
window.addEventListener('DOMContentLoaded', () => {
    const preloader = document.getElementById('preloader');

    // We use DOMContentLoaded for faster start, but still wait for load for completion
    window.addEventListener('load', () => {
        setTimeout(() => {
            if (preloader) {
                preloader.classList.add('fade-out');
            }
        }, 2000); // Reduced to 2s for better UX
    });
});

// ============== State Management ==============
// (AuthManager removed)

// ============== State Management ==============
class AppState {
    constructor() {
        this.language = 'en'; // Force English
        this.theme = localStorage.getItem('theme') || 'dark';
        this.profile = {};
        this.savedSchemes = [];
        this.applications = [];
        this.familyMembers = [];
        this.isTyping = false;
        this.isListening = false;
        this.lastRecommendations = [];
    }
}

class ProfileManager {
    constructor() {
        this.profiles = JSON.parse(localStorage.getItem('profiles')) || [];
        this.currentProfileId = localStorage.getItem('session_id');
    }

    createNewProfile(name = 'New Profile') {
        const id = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        const newProfile = { id, name };
        this.profiles.push(newProfile);
        this.save();
        this.switchProfile(id);
        return newProfile;
    }

    switchProfile(id) {
        this.currentProfileId = id;
        if (id) {
            localStorage.setItem('session_id', id);
        } else {
            localStorage.removeItem('session_id');
        }
        this.save();
        // Trigger page reload to reset state and load new profile
        window.location.reload();
    }

    updateProfileName(id, name) {
        const profile = this.profiles.find(p => p.id === id);
        if (profile) {
            profile.name = name;
            this.save();
        }
    }

    deleteProfile(id) {
        this.profiles = this.profiles.filter(p => p.id !== id);
        if (this.currentProfileId === id) {
            this.switchProfile(this.profiles.length > 0 ? this.profiles[0].id : null);
        } else {
            this.save();
        }
    }

    save() {
        localStorage.setItem('profiles', JSON.stringify(this.profiles));
    }

    getCurrentProfile() {
        return this.profiles.find(p => p.id === this.currentProfileId) || { name: 'Guest' };
    }
}

const state = new AppState();
const profileManager = new ProfileManager();

// ============== DOM Elements ==============
const elements = {
    // Chat
    chatMessages: document.getElementById('chatMessages'),
    userInput: document.getElementById('userInput'),
    sendBtn: document.getElementById('sendBtn'),
    voiceBtn: document.getElementById('voiceBtn'),
    voiceStatus: document.getElementById('voiceStatus'),
    voiceIndicator: document.getElementById('voiceIndicator'),

    // Profile Modal
    profileModal: document.getElementById('profileModal'),
    profileForm: document.getElementById('profileForm'),
    profileBtn: document.getElementById('profileBtn'),
    profileSwitcher: document.getElementById('profileSwitcher'),
    profileDropdown: document.getElementById('profileDropdown'),
    profileList: document.getElementById('profileList'),
    addNewProfileBtn: document.getElementById('addNewProfileBtnInDropdown'),
    editProfileAction: document.getElementById('editProfileAction'),
    currentProfileName: document.getElementById('currentProfileName'),
    closeProfileModal: document.getElementById('closeProfileModal'),
    saveProfileBtn: document.getElementById('saveProfileBtn'),
    clearProfileBtn: document.getElementById('clearProfileBtn'),
    editProfileBtn: document.getElementById('editProfileBtn'),
    startProfileBtn: document.getElementById('startProfileBtn'),

    // Profile Card
    profileCard: document.getElementById('profileCard'),
    profileCardBody: document.getElementById('profileCardBody'),
    completenessBar: document.getElementById('completenessBar'),
    completenessText: document.getElementById('completenessText'),

    // Family
    familyCard: document.getElementById('familyCard'),
    familyList: document.getElementById('familyList'),
    addFamilyBtn: document.getElementById('addFamilyBtn'),
    familyModal: document.getElementById('familyModal'),
    closeFamilyModal: document.getElementById('closeFamilyModal'),
    saveFamilyBtn: document.getElementById('saveFamilyBtn'),
    cancelFamilyBtn: document.getElementById('cancelFamilyBtn'),

    // Saved Schemes
    savedSchemesList: document.getElementById('savedSchemesList'),
    savedCount: document.getElementById('savedCount'),
    savedActions: document.getElementById('savedActions'),
    compareBtn: document.getElementById('compareBtn'),
    checklistBtn: document.getElementById('checklistBtn'),

    // Tracker
    trackerList: document.getElementById('trackerList'),
    trackerCount: document.getElementById('trackerCount'),

    // Comparison Modal
    compareModal: document.getElementById('compareModal'),
    closeCompareModal: document.getElementById('closeCompareModal'),
    comparisonTable: document.getElementById('comparisonTable'),
    exportCompareBtn: document.getElementById('exportCompareBtn'),

    // Checklist Modal
    checklistModal: document.getElementById('checklistModal'),
    closeChecklistModal: document.getElementById('closeChecklistModal'),
    checklistContent: document.getElementById('checklistContent'),
    printChecklistBtn: document.getElementById('printChecklistBtn'),
    shareChecklistBtn: document.getElementById('shareChecklistBtn'),

    // Status Modal
    statusModal: document.getElementById('statusModal'),
    closeStatusModal: document.getElementById('closeStatusModal'),
    statusSchemeName: document.getElementById('statusSchemeName'),
    appStatus: document.getElementById('appStatus'),
    appNotes: document.getElementById('appNotes'),
    updateStatusBtn: document.getElementById('updateStatusBtn'),

    // Controls
    themeToggle: document.getElementById('themeToggle'),

    // Toast
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toastMessage'),
};

// ============== API Calls ==============
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);

        if (response.status === 401) {
            // auth.logout();
            return null;
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showToast('Connection error. Please try again.', 'error');
        return null;
    }
}

// ============== Toast Notifications ==============
function showToast(message, type = 'success') {
    const toast = elements.toast;
    const toastIcon = toast.querySelector('.toast-icon');

    elements.toastMessage.textContent = message;

    if (type === 'success') {
        toastIcon.textContent = '✓';
        toastIcon.style.background = 'var(--success)';
    } else if (type === 'error') {
        toastIcon.textContent = '✕';
        toastIcon.style.background = 'var(--error)';
    } else if (type === 'info') {
        toastIcon.textContent = 'ℹ';
        toastIcon.style.background = 'var(--primary)';
    }

    toast.classList.add('active');
    setTimeout(() => toast.classList.remove('active'), 3000);
}

// ============== Profile Functions ==============
function openProfileModal() {
    elements.profileModal.classList.add('active');
    document.body.style.overflow = 'hidden';
    populateFormFromProfile();
}

function closeProfileModal() {
    elements.profileModal.classList.remove('active');
    document.body.style.overflow = '';
}

function populateFormFromProfile() {
    const p = state.profile;
    const setField = (id, value) => {
        const el = document.getElementById(id);
        if (el && value) el.value = value;
    };

    setField('fullName', p.full_name);
    setField('dob', p.dob);
    setField('gender', p.gender);
    setField('community', p.community);
    setField('state', p.location); // Note: backend uses 'location' for state
    setField('areaType', p.area_type);
    setField('occupation', p.occupation);
    setField('income', p.income || p.annual_income);
    setField('familySize', p.family_size);
    setField('children', p.children_count);

    document.getElementById('isBPL').checked = p.is_bpl || false;
    document.getElementById('isDisabled').checked = p.is_disabled || false;
    document.getElementById('isWidow').checked = p.is_widow || false;
    document.getElementById('isSenior').checked = p.is_senior_citizen || false;
    document.getElementById('hasGirlChild').checked = p.has_girl_child || false;
}

function gatherFormData() {
    const getValue = (id) => document.getElementById(id)?.value || '';
    const getChecked = (id) => document.getElementById(id)?.checked || false;

    const dob = getValue('dob');
    let age = null;
    if (dob) {
        const birthDate = new Date(dob);
        const today = new Date();
        age = today.getFullYear() - birthDate.getFullYear();
    }

    return {
        full_name: getValue('fullName'),
        age: age,
        gender: getValue('gender'),
        community: getValue('community'),
        location: getValue('state'), // Backend expects 'location'
        area_type: getValue('areaType'),
        occupation: getValue('occupation'),
        annual_income: getValue('income') ? parseInt(getValue('income')) : null,
        family_size: getValue('familySize') ? parseInt(getValue('familySize')) : null,
        children_count: getValue('children') ? parseInt(getValue('children')) : null,
        is_bpl: getChecked('isBPL'),
        is_disabled: getChecked('isDisabled'),
        is_widow: getChecked('isWidow'),
        is_senior_citizen: getChecked('isSenior'),
        has_girl_child: getChecked('hasGirlChild'),
        language: state.language
    };
}

async function saveProfile() {
    const profile = gatherFormData();

    // Call backend API
    const result = await apiCall('/profile', 'POST', {
        session_id: getSessionId(),
        ...profile
    });

    if (result) {
        state.profile = profile;
        showToast('Profile saved successfully! 🎉');
        closeProfileModal();
        updateProfileCard();

        // Update profile name in manager and switcher if full_name exists
        if (profile.full_name) {
            updateProfileNameInList(profile.full_name);
            renderProfileList(); // Refresh the list
        }

        // CLEAR the welcome message - remove it completely
        const welcomeMsg = document.querySelector('.welcome-msg');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        // Build personalized sector suggestions based on profile
        const sectors = getSuggestedSectors(profile);
        showSectorSuggestions(sectors);
    } else {
        showToast('Failed to save profile. Please try again.', 'error');
    }
}

function getSuggestedSectors(profile) {
    const sectors = [];

    // Always add general welfare
    sectors.push({ name: 'Welfare Schemes', query: 'welfare schemes for my profile', icon: '🏛️' });

    // Add based on occupation
    if (profile.occupation === 'Farmer') {
        sectors.push({ name: 'Agriculture', query: 'agriculture and farming schemes', icon: '🌾' });
    }
    if (profile.occupation === 'Student') {
        sectors.push({ name: 'Education', query: 'scholarship and education schemes for students', icon: '📚' });
    }
    if (profile.occupation === 'Business') {
        sectors.push({ name: 'Business Loans', query: 'business loan and MUDRA schemes', icon: '💼' });
    }

    // Add based on income
    if (profile.annual_income && profile.annual_income < 300000) {
        sectors.push({ name: 'Financial Aid', query: 'financial assistance for low income families', icon: '💰' });
    }

    // Add based on special conditions
    if (profile.is_bpl) {
        sectors.push({ name: 'BPL Benefits', query: 'schemes for BPL families', icon: '📋' });
    }
    if (profile.has_girl_child) {
        sectors.push({ name: 'Girl Child', query: 'schemes for girl child education and savings', icon: '👧' });
    }
    if (profile.is_senior_citizen) {
        sectors.push({ name: 'Senior Citizen', query: 'pension and senior citizen schemes', icon: '👴' });
    }

    // Add health always
    sectors.push({ name: 'Healthcare', query: 'health insurance schemes', icon: '🏥' });

    // Add housing if low/middle income
    if (!profile.annual_income || profile.annual_income < 500000) {
        sectors.push({ name: 'Housing', query: 'housing schemes and PMAY', icon: '🏠' });
    }

    // Return top 5 unique sectors
    return sectors.slice(0, 5);
}

function showSectorSuggestions(sectors) {
    addBotMessage("Great! I've saved your profile. Based on your details, here are some scheme categories you might be interested in:", true, true);

    // Create sector chips container
    const chipsContainer = document.createElement('div');
    chipsContainer.className = 'sector-chips';
    chipsContainer.innerHTML = sectors.map(sector => `
        <button class="sector-chip" onclick="searchSector('${sector.query}')">
            <span class="chip-icon">${sector.icon}</span>
            <span class="chip-text">${sector.name}</span>
        </button>
    `).join('');

    elements.chatMessages.appendChild(chipsContainer);
    scrollToBottom();
}

function searchSector(query) {
    sendMessage(query);
}

async function loadProfile() {
    const sessionId = getSessionId();
    const result = await apiCall(`/profile/${sessionId}`, 'GET');
    
    if (result && result.profile) {
        state.profile = result.profile;
        updateProfileCard();
        
        // If profile is mostly complete, hide welcome message
        const isComplete = result.is_complete;
        if (isComplete) {
            const welcomeMsg = document.querySelector('.welcome-msg');
            if (welcomeMsg) welcomeMsg.remove();
            
            // Show suggestions for existing user
            const sectors = getSuggestedSectors(state.profile);
            showSectorSuggestions(sectors);
        }
    }
}

function updateProfileCard() {
    const p = state.profile;
    const body = elements.profileCardBody;

    if (!p || !p.full_name) {
        body.innerHTML = '<p class="no-profile">Complete your profile to get personalized recommendations</p>';
        updateCompletenessBar(0);
        return;
    }

    // Calculate completeness
    const fields = ['full_name', 'age', 'gender', 'location', 'occupation', 'income'];
    const filled = fields.filter(f => p[f] || p['annual_income']).length;
    const percentage = Math.round((filled / fields.length) * 100);

    // Display profile summary
    body.innerHTML = `
            <div class="profile-info">
                <p><strong>👤 Name:</strong> ${p.full_name || 'Not set'}</p>
                <p><strong>📍 Location:</strong> ${p.location || 'Not set'}</p>
                <p><strong>💼 Occupation:</strong> ${p.occupation || 'Not set'}</p>
                ${(p.income || p.annual_income) ? `<p><strong>💰 Income:</strong> ₹${(p.income || p.annual_income).toLocaleString()}</p>` : ''}
            </div>
        `;

    updateCompletenessBar(percentage);
}

function updateCompletenessBar(percentage) {
    elements.completenessBar.style.width = `${percentage}%`;
    elements.completenessText.textContent = `${percentage}% Complete`;
}

// ============== Profile Switcher UI ==============
function setupProfileSwitcher() {
    if (!elements.profileBtn || !elements.profileDropdown) return;

    // Toggle dropdown
    elements.profileBtn.onclick = (e) => {
        e.stopPropagation();
        elements.profileDropdown.classList.toggle('active');
    };

    // Close on click outside
    document.addEventListener('click', () => {
        elements.profileDropdown.classList.remove('active');
    });

    // Add new profile
    if (elements.addNewProfileBtn) {
        elements.addNewProfileBtn.onclick = () => {
            profileManager.createNewProfile('New Profile');
        };
    }

    // Edit current profile
    if (elements.editProfileAction) {
        elements.editProfileAction.onclick = () => {
            openProfileModal();
            elements.profileDropdown.classList.remove('active');
        };
    }

    renderProfileList();
}

function renderProfileList() {
    if (!elements.profileList) return;

    const currentProfile = profileManager.getCurrentProfile();
    if (elements.currentProfileName) {
        elements.currentProfileName.textContent = currentProfile.name;
    }

    elements.profileList.innerHTML = profileManager.profiles.map(p => `
        <div class="profile-item ${p.id === profileManager.currentProfileId ? 'active' : ''}" 
             onclick="profileManager.switchProfile('${p.id}')">
            <span>${p.name}</span>
            <div style="display: flex; align-items: center; gap: 8px;">
                ${p.id === profileManager.currentProfileId ? '<div class="active-indicator"></div>' : ''}
                <button class="remove-profile-btn" onclick="event.stopPropagation(); if(confirm('Delete this profile?')) { profileManager.deleteProfile('${p.id}'); renderProfileList(); }">✕</button>
            </div>
        </div>
    `).join('');
}

function clearProfile() {
    if (confirm('Are you sure you want to clear your profile?')) {
        elements.profileForm.reset();
        showToast('Profile cleared');
    }
}

function getSessionId() {
    if (!profileManager.currentProfileId) {
        // use a persistent guest session for this page load
        if (!window.guestSessionId) {
            window.guestSessionId = 'guest_' + Date.now();
        }
        return window.guestSessionId;
    }
    return profileManager.currentProfileId;
}

function updateProfileNameInList(name) {
    profileManager.updateProfileName(getSessionId(), name);
    if (elements.currentProfileName) {
        elements.currentProfileName.textContent = name;
    }
}

// ============== Chat Functions ==============
async function sendMessage(message) {
    if (!message || !message.trim()) return;

    // Add user message to chat
    addUserMessage(message);
    elements.userInput.value = '';
    autoResizeTextarea();

    // Remove welcome message if it exists
    const welcomeMsg = document.querySelector('.welcome-msg');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Show typing indicator
    showTypingIndicator();

    // Prepare context from profile
    const context = {
        age: state.profile.age,
        gender: state.profile.gender,
        location: state.profile.location,
        occupation: state.profile.occupation,
        annual_income: state.profile.annual_income,
        community: state.profile.community,
        is_bpl: state.profile.is_bpl,
        is_disabled: state.profile.is_disabled,
        is_widow: state.profile.is_widow,
        is_senior_citizen: state.profile.is_senior_citizen,
        has_girl_child: state.profile.has_girl_child,
        language: state.language
    };

    // Send to backend
    const result = await apiCall('/chat', 'POST', {
        message: message,
        session_id: getSessionId(),
        language: state.language,
        context: context
    });

    hideTypingIndicator();

    if (result) {
        addBotMessage(result.response, true, true);

        // Store and display recommendations if available
        if (result.recommendations && result.recommendations.length > 0) {
            state.lastRecommendations = result.recommendations;
            // addSchemeCards(result.recommendations); // Disabled as per user request
        }
    } else {
        addBotMessage("Sorry, I couldn't process your request. Please try again.", false, true);
    }
}

function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-bubble">${escapeHtml(text)}</div>
            </div>
            <div class="message-avatar">👤</div>
        `;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text, animated = true, scroll = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';

    if (animated) {
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(10px)';
    }

    // Use formatMessage for bot responses to support Markdown
    messageDiv.innerHTML = `
            <div class="message-avatar">✦</div>
            <div class="message-content">
                <div class="message-bubble">${formatMessage(text)}</div>
            </div>
        `;

    elements.chatMessages.appendChild(messageDiv);

    if (animated) {
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 50);
    }

    if (scroll) scrollToBottom();
}

function addSchemeCards(schemes) {
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'scheme-cards-container';

    schemes.forEach((scheme, index) => {
        const card = document.createElement('div');
        card.className = 'scheme-card';
        // Removed Save and Track buttons as per user request
        card.innerHTML = `
                <div class="scheme-card-header">
                    <h4>${escapeHtml(scheme.name)}</h4>
                    <span class="scheme-category">${escapeHtml(scheme.category || 'General')}</span>
                </div>
                <p class="scheme-description">${escapeHtml(scheme.description || 'No description available')}</p>
            `;
        cardsContainer.appendChild(card);
    });

    elements.chatMessages.appendChild(cardsContainer);
    scrollToBottom();
}

// Removed saveSchemeFromIndex and trackApplicationFromIndex

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message bot typing-indicator';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
            <div class="message-avatar">✦</div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
    elements.chatMessages.appendChild(indicator);
    scrollToBottom();
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

function scrollToBottom() {
    setTimeout(() => {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }, 100);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Simple Markdown-like formatter for chat messages
 * Supports: **bold**, *italic*, - lists, 1. ordered lists, headers, newlines
 */
function formatMessage(text) {
    if (!text) return '';

    // Check if the text contains HTML tags (basic logic)
    if (/<[a-z][\s\S]*>/i.test(text)) {
        // If it looks like HTML, sanitize it (minimal/safe tags only) or escape it
        // For now, we assume LLM output is text-based markdown
    }

    let html = escapeHtml(text); // Start by escaping HTML entities to prevent XSS

    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Lists: - item or • item
    html = html.replace(/^\s*[\-•]\s+(.*)$/gm, '<li>$1</li>');

    // Ordered Lists: 1. item
    html = html.replace(/^\s*\d+\.\s+(.*)$/gm, '<li class="ordered">$1</li>');

    // Wrap lists (consecutive lis)
    // specific replacing for unordered
    html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

    // Fix ordered lists (class="ordered" is a hack to identify them)
    html = html.replace(/<ul>((?:<li class="ordered">.*<\/li>\n?)+)<\/ul>/g, function (match, inner) {
        return '<ol>' + inner.replace(/class="ordered"/g, '') + '</ol>';
    });

    // Headings: # Heading or ## Heading
    html = html.replace(/^#\s+(.*)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.*)$/gm, '<h4>$1</h4>');
    html = html.replace(/^###\s+(.*)$/gm, '<h5>$1</h5>');

    // Create paragraphs from double newlines
    html = html.replace(/\n\n/g, '<br><br>');

    // Handle single newlines that aren't inside lists
    // (We replaced list items above, so we don't want to break those)
    // This is a bit tricky with Regex only, so we'll rely on CSS white-space for most
    // but explicit <br> for distinct line breaks is good.
    html = html.replace(/([^\n])\n([^\n])/g, '$1<br>$2');

    return html;
}

// ============== Saved Schemes ==============
async function loadSavedSchemes() {
    // Disabled
    state.savedSchemes = [];
    updateSavedSchemesList();
}

function updateSavedSchemesList() {
    const list = elements.savedSchemesList;
    const count = elements.savedCount;

    count.textContent = state.savedSchemes.length;

    if (state.savedSchemes.length === 0) {
        list.innerHTML = '<p class="no-saved">No schemes saved yet</p>';
        elements.savedActions.style.display = 'none';
        return;
    }

    elements.savedActions.style.display = 'flex';

    list.innerHTML = state.savedSchemes.map(scheme => `
            <div class="saved-scheme-item">
                <div class="saved-scheme-info">
                    <h4>${escapeHtml(scheme.scheme_name)}</h4>
                    <span class="scheme-category-small">${escapeHtml(scheme.category || 'General')}</span>
                </div>
                <button class="remove-btn" onclick="removeSavedScheme(${scheme.id})">×</button>
            </div>
        `).join('');
}

async function removeSavedScheme(schemeId) {
    if (!confirm('Remove this scheme from saved?')) return;

    const result = await apiCall(`/profile/saved-schemes/${schemeId}`, 'DELETE');
    if (result) {
        showToast('Scheme removed');
        loadSavedSchemes();
    }
}

// ============== Application Tracking ==============
async function loadApplications() {
    // Disabled
    state.applications = [];
    updateApplicationsList();
}

function updateApplicationsList() {
    const list = elements.trackerList;
    const count = elements.trackerCount;

    count.textContent = state.applications.length;

    if (state.applications.length === 0) {
        list.innerHTML = '<p class="no-apps">No applications yet</p>';
        return;
    }

    list.innerHTML = state.applications.map(app => {
        const statusEmoji = {
            'not_started': '📝',
            'documents_ready': '📄',
            'applied': '📬',
            'under_review': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }[app.status] || '📝';

        return `
                <div class="tracker-item" onclick="openStatusModal(${app.id})">
                    <div class="tracker-info">
                        <h4>${escapeHtml(app.scheme_name)}</h4>
                        <span class="tracker-status">${statusEmoji} ${app.status.replace('_', ' ')}</span>
                    </div>
                </div>
            `;
    }).join('');
}

function openStatusModal(appId) {
    const app = state.applications.find(a => a.id === appId);
    if (!app) return;

    elements.statusSchemeName.textContent = app.scheme_name;
    elements.appStatus.value = app.status;
    elements.appNotes.value = app.notes || '';

    elements.statusModal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Store current app ID for update
    elements.updateStatusBtn.dataset.appId = appId;
}

function closeStatusModal() {
    elements.statusModal.classList.remove('active');
    document.body.style.overflow = '';
}

async function updateApplicationStatus() {
    const appId = elements.updateStatusBtn.dataset.appId;
    const status = elements.appStatus.value;
    const notes = elements.appNotes.value;

    const result = await apiCall(`/tracking/applications/${appId}`, 'PUT', {
        status: status,
        notes: notes
    });

    if (result) {
        showToast('Status updated! 📊');
        closeStatusModal();
        loadApplications();
    }
}

// ============== UI Translations ==============
const translations = {
    en: {
        app_name: "CivicScheme AI",
        app_tagline: "Government Benefits Finder",
        my_profile: "My Profile",
        your_profile: "👤 Your Profile",
        edit: "✏️ Edit",
        complete_profile_msg: "Complete your profile to get personalized recommendations",
        find_csc: "📍 Find CSC Center",
        welcome_title: "Welcome to CivicScheme AI",
        welcome_subtitle: "I help you discover government schemes you're eligible for.",
        step_1: "Complete your profile",
        step_2: "Get personalized recommendations",
        step_3: "Save, compare & track applications",
        complete_profile_btn: "Complete Your Profile",
        chat_placeholder: "Ask me about government schemes...",
        tap_mic: "🎤 Tap mic to speak",
        listening: "🎤 Listening...",
        supports_lang: "Supports all Indian languages"
    },
    hi: {
        app_name: "योजना एआई",
        app_tagline: "सरकारी लाभ खोजक",
        my_profile: "मेरी प्रोफाइल",
        your_profile: "👤 आपकी प्रोफाइल",
        edit: "✏️ संपादित करें",
        complete_profile_msg: "व्यक्तिगत सिफारिशें प्राप्त करने के लिए अपनी प्रोफाइल पूरी करें",
        find_csc: "📍 सीएससी केंद्र खोजें",
        welcome_title: "योजना एआई में आपका स्वागत है",
        welcome_subtitle: "मैं आपको वे सरकारी योजनाएँ खोजने में मदद करता हूँ जिनके लिए आप पात्र हैं।",
        step_1: "अपनी प्रोफाइल पूरी करें",
        step_2: "व्यक्तिगत सिफारिशें प्राप्त करें",
        step_3: "सहेजें, तुलना करें और आवेदन ट्रैक करें",
        complete_profile_btn: "अपनी प्रोफाइल पूरी करें",
        chat_placeholder: "मुझसे सरकारी योजनाओं के बारे में पूछें...",
        tap_mic: "🎤 बोलने के लिए माइक दबाएं",
        listening: "🎤 सुन रहा हूँ...",
        supports_lang: "सभी भारतीय भाषाओं का समर्थन करता है"
    },
    ta: {
        app_name: "திட்டங்கள் AI",
        app_tagline: "அரசு சலுகைகள் கண்டுபிடிப்பான்",
        my_profile: "என் சுயவிவரம்",
        your_profile: "👤 உங்கள் சுயவிவரம்",
        edit: "✏️ திருத்து",
        complete_profile_msg: "பரிந்துரைகளைப் பெற உங்கள் சுயவிவரத்தை பூர்த்தி செய்யவும்",
        find_csc: "📍 CSC மையத்தை கண்டுபிடி",
        welcome_title: "திட்டங்கள் AI-க்கு வருக",
        welcome_subtitle: "உங்களுக்கு தகுதியான அரசு திட்டங்களைக் கண்டறிய உதவுகிறேன்.",
        step_1: "சுயவிவரத்தை பூர்த்தி செய்யவும்",
        step_2: "பரிந்துரைகளைப் பெறவும்",
        step_3: "சேமிக்கவும் & கண்காணிக்கவும்",
        complete_profile_btn: "சுயவிவரத்தை பூர்த்தி செய்",
        chat_placeholder: "அரசு திட்டங்கள் பற்றி கேளுங்கள்...",
        tap_mic: "🎤 பேச மைக் அழுத்தவும்",
        listening: "🎤 கேட்கிறது...",
        supports_lang: "அனைத்து இந்திய மொழிகளுக்கும் ஆதரவு"
    },
    te: {
        app_name: "పథకాలు AI",
        app_tagline: "ప్రభుత్వ ప్రయోజనాల ఫైండర్",
        my_profile: "నా ప్రొఫైల్",
        your_profile: "👤 మీ ప్రొఫైల్",
        edit: "✏️ సవరించండి",
        complete_profile_msg: "సిఫార్సులను పొందడానికి మీ ప్రొఫైల్ను పూర్తి చేయండి",
        find_csc: "📍 CSC కేంద్రాన్ని కనుగొనండి",
        welcome_title: "పథకాలు AI కి స్వాగతం",
        welcome_subtitle: "మీరు అర్హత కలిగిన ప్రభుత్వ పథకాలను కనుగొనడంలో నేను సహాయపడతాను.",
        step_1: "మీ ప్రొఫైల్ పూర్తి చేయండి",
        step_2: "వ్యక్తిగతీకరించిన సిఫార్సులను పొందండి",
        step_3: "సేవ్ చేయండి, సరిపోల్చండి & ట్రాక్ చేయండి",
        complete_profile_btn: "మీ ప్రొఫైల్ పూర్తి చేయండి",
        chat_placeholder: "ప్రభుత్వ పథకాల గురించి నన్ను అడగండి...",
        tap_mic: "🎤 మాట్లాడటానికి మైక్ నొక్కండి",
        listening: "🎤 వింటున్నాను...",
        supports_lang: "అన్ని భారతీయ భాషలకు మద్దతు ఇస్తుంది"
    },
    kn: {
        app_name: "ಯೋಜನೆಗಳು AI",
        app_tagline: "ಸರ್ಕಾರಿ ಸೌಲಭ್ಯ ಶೋಧಕ",
        my_profile: "ನನ್ನ ಪ್ರೊಫೈಲ್",
        your_profile: "👤 ನಿಮ್ಮ ಪ್ರೊಫೈಲ್",
        edit: "✏️ ಸಂಪಾದಿಸಿ",
        complete_profile_msg: "ಶಿಫಾರಸುಗಳನ್ನು ಪಡೆಯಲು ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಪೂರ್ಣಗೊಳಿಸಿ",
        find_csc: "📍 CSC ಕೇಂದ್ರವನ್ನು ಹುಡುಕಿ",
        welcome_title: "ಯೋಜನೆಗಳು AI ಗೆ ಸ್ವಾಗತ",
        welcome_subtitle: "ನೀವು ಅರ್ಹರಾಗಿರುವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ನಾನು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
        step_1: "ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಪೂರ್ಣಗೊಳಿಸಿ",
        step_2: "ವೈಯಕ್ತೀಕರಿಸಿದ ಶಿಫಾರಸುಗಳನ್ನು ಪಡೆಯಿರಿ",
        step_3: "ಉಳಿಸಿ, ಹೋಲಿಸಿ ಮತ್ತು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ",
        complete_profile_btn: "ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಪೂರ್ಣಗೊಳಿಸಿ",
        chat_placeholder: "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ಕೇಳಿ...",
        tap_mic: "🎤 ಮಾತನಾಡಲು ಮೈಕ್ ಟ್ಯಾಪ್ ಮಾಡಿ",
        listening: "🎤 ಆಲಿಸಲಾಗುತ್ತಿದೆ...",
        supports_lang: "ಎಲ್ಲಾ ಭಾರತೀಯ ಭಾಷೆಗಳನ್ನು ಬೆಂಬಲಿಸುತ್ತದೆ"
    },
    ml: {
        app_name: "പദ്ധതികൾ AI",
        app_tagline: "സർക്കാർ ആനുകൂല്യങ്ങൾ കണ്ടെത്താം",
        my_profile: "എന്റെ പ്രൊഫൈൽ",
        your_profile: "👤 നിങ്ങളുടെ പ്രൊഫൈൽ",
        edit: "✏️ എഡിറ്റ്",
        complete_profile_msg: "ശുപാർശകൾ ലഭിക്കാൻ പ്രൊഫൈൽ പൂർത്തിയാക്കുക",
        find_csc: "📍 CSC കേന്ദ്രം കണ്ടെത്തുക",
        welcome_title: "പദ്ധതികൾ AI-ലേക്ക് സ്വാഗതം",
        welcome_subtitle: "നിങ്ങൾക്ക് അർഹതയുള്ള സർക്കാർ പദ്ധതികൾ കണ്ടെത്താൻ ഞാൻ സഹായിക്കും.",
        step_1: "പ്രൊഫൈൽ പൂർത്തിയാക്കുക",
        step_2: "വ്യക്തിഗത ശുപാർശകൾ നേടുക",
        step_3: "സംരക്ഷിക്കുക & ട്രാക്ക് ചെയ്യുക",
        complete_profile_btn: "പ്രൊഫൈൽ പൂർത്തിയാക്കുക",
        chat_placeholder: "സർക്കാർ പദ്ധതികളെക്കുറിച്ച് ചോദിക്കൂ...",
        tap_mic: "🎤 സംസാരിക്കാൻ മൈക്ക് അമർത്തുക",
        listening: "🎤 കേൾക്കുന്നു...",
        supports_lang: "എല്ലാ ഇന്ത്യൻ ഭാഷകളെയും പിന്തുണയ്ക്കുന്നു"
    },
    bn: {
        app_name: "স্কিম এআই",
        app_tagline: "সরকারি সুবিধা অনুসন্ধানকারী",
        my_profile: "আমার প্রোফাইল",
        your_profile: "👤 আপনার প্রোফাইল",
        edit: "✏️ সম্পাদনা",
        complete_profile_msg: "সুপারিশ পেতে আপনার প্রোফাইল সম্পূর্ণ করুন",
        find_csc: "📍 সিএসসি কেন্দ্র খুঁজুন",
        welcome_title: "স্কিম এআই-তে স্বাগতম",
        welcome_subtitle: "আমি আপনাকে সরকারি স্কিমগুলি খুঁজে পেতে সাহায্য করি।",
        step_1: "প্রোফাইল সম্পূর্ণ করুন",
        step_2: "ব্যক্তিগত সুপারিশ পান",
        step_3: "সংরক্ষণ ও ট্র্যাক করুন",
        complete_profile_btn: "প্রোফাইল সম্পূর্ণ করুন",
        chat_placeholder: "সরকারি স্কিম সম্পর্কে জিজ্ঞাসা করুন...",
        tap_mic: "🎤 কথা বলতে মাইক আলতো চাপুন",
        listening: "🎤 শুনছি...",
        supports_lang: "সমস্ত ভারতীয় ভাষা সমর্থন করে"
    },
    gu: {
        app_name: "યોજના AI",
        app_tagline: "સરકારી લાભ શોધક",
        my_profile: "મારી પ્રોફાઇલ",
        your_profile: "👤 તમારી પ્રોફાઇલ",
        edit: "✏️ સંપાદિત કરો",
        complete_profile_msg: "ભલામણો મેળવવા માટે તમારી પ્રોફાઇલ પૂર્ણ કરો",
        find_csc: "📍 CSC કેન્દ્ર શોધો",
        welcome_title: "યોજના AI માં આપનું સ્વાગત છે",
        welcome_subtitle: "તમે પાત્ર છો તેવી સરકારી યોજનાઓ શોધવામાં હું મદદ કરું છું.",
        step_1: "તમારી પ્રોફાઇલ પૂર્ણ કરો",
        step_2: "વ્યક્તિગત ભલામણો મેળવો",
        step_3: "સાચવો અને ટ્રેક કરો",
        complete_profile_btn: "પ્રોફાઇલ પૂર્ણ કરો",
        chat_placeholder: "સરકારી યોજનાઓ વિશે પૂછો...",
        tap_mic: "🎤 બોલવા માટે માઇક ટેપ કરો",
        listening: "🎤 સાંભળી રહ્યો છું...",
        supports_lang: "બધી ભારતીય ભાષાઓને સપોર્ટ કરે છે"
    },
    mr: {
        app_name: "योजना AI",
        app_tagline: "सरकारी लाभ शोधक",
        my_profile: "माझी प्रोफाइल",
        your_profile: "👤 तुमची प्रोफाइल",
        edit: "✏️ संपादित करा",
        complete_profile_msg: "शिफारसी मिळवण्यासाठी तुमची प्रोफाइल पूर्ण करा",
        find_csc: "📍 CSC केंद्र शोधा",
        welcome_title: "योजना AI मध्ये आपले स्वागत आहे",
        welcome_subtitle: "मी तुम्हाला पात्र असलेल्या सरकारी योजना शोधण्यात मदत करतो.",
        step_1: "तुमची प्रोफाइल पूर्ण करा",
        step_2: "वैयक्तिकृत शिफारसी मिळवा",
        step_3: "जतन करा आणि ट्रॅक करा",
        complete_profile_btn: "तुमची प्रोफाइल पूर्ण करा",
        chat_placeholder: "सरकारी योजनांबद्दल विचारा...",
        tap_mic: "🎤 बोलण्यासाठी माइक टॅप करा",
        listening: "🎤 ऐकत आहे...",
        supports_lang: "सर्व भारतीय भाषांना समर्थन देते"
    },
    pa: {
        app_name: "ਸਕੀਮਾਂ AI",
        app_tagline: "ਸਰਕਾਰੀ ਲਾਭ ਖੋਜਕਰਤਾ",
        my_profile: "ਮੇਰੀ ਪ੍ਰੋਫਾਈਲ",
        your_profile: "👤 ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ",
        edit: "✏️ ਸੰਪਾਦਿਤ ਕਰੋ",
        complete_profile_msg: "ਸਿਫਾਰਸ਼ਾਂ ਪ੍ਰਾਪਤ ਕਰਨ ਲਈ ਆਪਣੀ ਪ੍ਰੋਫਾਈਲ ਪੂਰੀ ਕਰੋ",
        find_csc: "📍 CSC ਕੇਂਦਰ ਲੱਭੋ",
        welcome_title: "ਸਕੀਮਾਂ AI ਵਿੱਚ ਜੀ ਆਇਆਂ ਨੂੰ",
        welcome_subtitle: "ਮੈਂ ਤੁਹਾਨੂੰ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਲੱਭਣ ਵਿੱਚ ਮਦਦ ਕਰਦਾ ਹਾਂ।",
        step_1: "ਆਪਣੀ ਪ੍ਰੋਫਾਈਲ ਪੂਰੀ ਕਰੋ",
        step_2: "ਨਿੱਜੀ ਸਿਫਾਰਸ਼ਾਂ ਪ੍ਰਾਪਤ ਕਰੋ",
        step_3: "ਸੇਵ ਕਰੋ ਅਤੇ ਟ੍ਰੈਕ ਕਰੋ",
        complete_profile_btn: "ਪ੍ਰੋਫਾਈਲ ਪੂਰੀ ਕਰੋ",
        chat_placeholder: "ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਬਾਰੇ ਪੁੱਛੋ...",
        tap_mic: "🎤 ਬੋਲਣ ਲਈ ਮਾਈਕ ਦਬਾਓ",
        listening: "🎤 ਸੁਣ ਰਿਹਾ ਹੈ...",
        supports_lang: "ਸਾਰੀਆਂ ਭਾਰਤੀ ਭਾਸ਼ਾਵਾਂ ਦਾ ਸਮਰਥਨ ਕਰਦਾ ਹੈ"
    },
    or: {
        app_name: "ଯୋଜନା AI",
        app_tagline: "ସରକାରୀ ଲାଭ ଅନୁସନ୍ଧାନକାରୀ",
        my_profile: "ମୋର ପ୍ରୋଫାଇଲ୍",
        your_profile: "👤 ଆପଣଙ୍କର ପ୍ରୋଫାଇଲ୍",
        edit: "✏️ ସମ୍ପାଦନ କରନ୍ତୁ",
        complete_profile_msg: "ସୁପାରିଶ ପାଇବାକୁ ଆପଣଙ୍କର ପ୍ରୋଫାଇଲ୍ ପୂରଣ କରନ୍ତୁ",
        find_csc: "📍 CSC କେନ୍ଦ୍ର ଖୋଜନ୍ତୁ",
        welcome_title: "ଯୋଜନା AI କୁ ସ୍ୱାଗତ",
        welcome_subtitle: "ମୁଁ ଆପଣଙ୍କୁ ସରକାରୀ ଯୋଜନା ଖୋଜିବାରେ ସାହାଯ୍ୟ କରେ |",
        step_1: "ଆପଣଙ୍କର ପ୍ରୋଫାଇଲ୍ ପୂରଣ କରନ୍ତୁ",
        step_2: "ବ୍ୟକ୍ତିଗତ ସୁପାରିଶ ପାଆନ୍ତୁ",
        step_3: "ସଞ୍ଚୟ କରନ୍ତୁ ଏବଂ ଟ୍ରାକ୍ କରନ୍ତୁ",
        complete_profile_btn: "ପ୍ରୋଫାଇଲ୍ ପୂରଣ କରନ୍ତୁ",
        chat_placeholder: "ସରକାରୀ ଯୋଜନା ବିଷୟରେ ପଚାରନ୍ତୁ...",
        tap_mic: "🎤 କହିବା ପାଇଁ ମାଇକ୍ ଦବାନ୍ତୁ",
        listening: "🎤 ଶୁଣୁଛି...",
        supports_lang: "ସମସ୍ତ ଭାରତୀୟ ଭାଷାକୁ ସମର୍ଥନ କରେ"
    }
};

function updateUIText(lang) {
    // Default to 'en' if translation missing
    // or if lang is not in translations (fallback)
    const t = translations[lang] || translations['en'];

    // Update simple text elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            el.textContent = t[key];
        }
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (t[key]) {
            el.placeholder = t[key];
        }
    });
}

// ============== Voice Recognition ==============
let recognition = null;

function initVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        updateVoiceLanguage();

        recognition.onstart = () => {
            state.isListening = true;
            elements.voiceBtn.classList.add('listening');
            elements.voiceIndicator.classList.add('active');

            const t = translations[state.language] || translations['en'];
            elements.voiceStatus.textContent = t['listening'];
        };

        recognition.onend = () => {
            state.isListening = false;
            elements.voiceBtn.classList.remove('listening');
            elements.voiceIndicator.classList.remove('active');

            const t = translations[state.language] || translations['en'];
            elements.voiceStatus.textContent = t['tap_mic'];
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            elements.userInput.value = transcript;
            elements.userInput.focus();
            // Automatically send after a short delay?
            setTimeout(() => sendMessage(transcript), 800);
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            let msg = 'Voice error: ' + event.error;
            if (event.error === 'not-allowed') msg = 'Microphone access denied';
            else if (event.error === 'no-speech') msg = 'No speech detected';
            else if (event.error === 'network') msg = 'Network error (Try Chrome/Edge, Brave block)';

            showToast(msg, 'error');
            state.isListening = false;
            elements.voiceBtn.classList.remove('listening');
            elements.voiceIndicator.classList.remove('active');

            const t = translations[state.language] || translations['en'];
            elements.voiceStatus.textContent = t['tap_mic'];
        };

        return true;
    } else {
        console.warn("Speech Synthesis API not supported in this browser");
        elements.voiceBtn.style.display = 'none'; // Hide if not supported
        return false;
    }
}

function updateVoiceLanguage() {
    if (recognition) {
        const langMap = {
            'en': 'en-IN', 'hi': 'hi-IN', 'ta': 'ta-IN', 'te': 'te-IN',
            'kn': 'kn-IN', 'ml': 'ml-IN', 'bn': 'bn-IN', 'gu': 'gu-IN',
            'mr': 'mr-IN', 'pa': 'pa-IN', 'or': 'or-IN'
        };
        recognition.lang = langMap[state.language] || 'en-IN';
    }
}

function toggleVoice() {
    if (!recognition) {
        showToast('Voice input not supported in this browser', 'error');
        return;
    }

    if (state.isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

// ============== Theme & Language ==============
function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('theme', state.theme);
}

function changeLanguage(lang) {
    state.language = lang;
    updateVoiceLanguage();
    if (typeof updateUIText === 'function') {
        updateUIText(lang);
    }
    showToast(`Language changed to ${lang.toUpperCase()}`);
}

// ============== Textarea Auto-resize ==============
function autoResizeTextarea() {
    const textarea = elements.userInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// ============== Event Listeners ==============
function setupEventListeners() {
    // Chat
    elements.sendBtn.addEventListener('click', () => {
        sendMessage(elements.userInput.value);
    });

    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(elements.userInput.value);
        }
    });

    elements.userInput.addEventListener('input', autoResizeTextarea);

    elements.voiceBtn.addEventListener('click', toggleVoice);

    // Profile
    if (elements.editProfileBtn) elements.editProfileBtn.addEventListener('click', openProfileModal);
    if (elements.startProfileBtn) elements.startProfileBtn.addEventListener('click', openProfileModal);
    if (elements.closeProfileModal) elements.closeProfileModal.addEventListener('click', closeProfileModal);
    if (elements.saveProfileBtn) elements.saveProfileBtn.addEventListener('click', saveProfile);
    if (elements.clearProfileBtn) elements.clearProfileBtn.addEventListener('click', clearProfile);

    // Status Modal
    if (elements.closeStatusModal) elements.closeStatusModal.addEventListener('click', closeStatusModal);
    if (elements.updateStatusBtn) elements.updateStatusBtn.addEventListener('click', updateApplicationStatus);

    // Theme
    if (elements.themeToggle) elements.themeToggle.addEventListener('click', toggleTheme);

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });

    // Add logout button functionality (if exists in header)
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to logout?')) {
                auth.logout();
            }
        });
    }
}

// ============== Initialization ==============
async function init() {
    // Setup Profile Switcher
    setupProfileSwitcher();

    // Setup event listeners
    setupEventListeners();

    // Initialize UI Text
    if (typeof updateUIText === 'function') {
        updateUIText(state.language);
    }

    // Initialize voice recognition
    initVoiceRecognition();

    // Set theme
    document.documentElement.setAttribute('data-theme', state.theme);

    // Load user data
    await loadProfile();
    await loadSavedSchemes();
    await loadApplications();

    console.log('Schemes AI initialized successfully!');

    console.log('Schemes AI initialized successfully!');
}

// Start the app
init();
