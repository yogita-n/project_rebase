// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const analyzeForm = document.getElementById('analyzeForm');
const repoInput = document.getElementById('repoInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const resultsSection = document.getElementById('resultsSection');

// Summary elements
const totalDepsEl = document.getElementById('totalDeps');
const breakingChangesEl = document.getElementById('breakingChanges');
const outdatedPkgsEl = document.getElementById('outdatedPkgs');
const uptodatePkgsEl = document.getElementById('uptodatePkgs');
const repoPathEl = document.getElementById('repoPath');
const packagesListEl = document.getElementById('packagesList');

// Example buttons
const exampleBtns = document.querySelectorAll('.example-btn');

// Event Listeners
analyzeForm.addEventListener('submit', handleAnalyze);

exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        repoInput.value = btn.dataset.url;
    });
});

// Main analyze function
async function handleAnalyze(e) {
    e.preventDefault();

    const repoUrl = repoInput.value.trim();
    if (!repoUrl) return;

    // Show loading state
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ repo_url: repoUrl })
        });

        const result = await response.json();

        if (result.status === 'success') {
            displayResults(result.data);
        } else {
            showError(result.message || 'Analysis failed');
        }
    } catch (error) {
        showError(`Network error: ${error.message}. Make sure the server is running.`);
    }
}

// Display results
function displayResults(data) {
    // Hide loading and error states
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');

    // Show results section
    resultsSection.classList.remove('hidden');

    // Update summary cards
    totalDepsEl.textContent = data.total_dependencies || 0;
    breakingChangesEl.textContent = data.breaking_changes || 0;
    outdatedPkgsEl.textContent = data.outdated_packages || 0;

    const uptodate = (data.total_updates || 0) - (data.breaking_changes || 0) - (data.outdated_packages || 0);
    uptodatePkgsEl.textContent = Math.max(0, uptodate);

    // Update repository path
    repoPathEl.textContent = data.repository || 'Unknown';

    // Display packages
    displayPackages(data.results || []);

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Display package list
function displayPackages(packages) {
    packagesListEl.innerHTML = '';

    if (packages.length === 0) {
        packagesListEl.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No packages found</p>';
        return;
    }

    // Sort: breaking first, then outdated, then up-to-date
    const sortedPackages = packages.sort((a, b) => {
        const statusOrder = { breaking: 0, outdated: 1, 'up-to-date': 2 };
        return (statusOrder[a.status] || 3) - (statusOrder[b.status] || 3);
    });

    sortedPackages.forEach(pkg => {
        const card = createPackageCard(pkg);
        packagesListEl.appendChild(card);
    });
}

// Create package card
function createPackageCard(pkg) {
    const card = document.createElement('div');
    card.className = `package-card ${pkg.status}`;

    // Header
    const header = document.createElement('div');
    header.className = 'package-header';

    const name = document.createElement('div');
    name.className = 'package-name';
    name.textContent = pkg.package;

    const status = document.createElement('span');
    status.className = `package-status ${pkg.status}`;
    status.textContent = pkg.status;

    header.appendChild(name);
    header.appendChild(status);
    card.appendChild(header);

    // Versions
    const versions = document.createElement('div');
    versions.className = 'package-versions';

    const currentVersion = document.createElement('div');
    currentVersion.className = 'version-badge';
    currentVersion.innerHTML = `
        <span class="version-label">Current:</span>
        <span class="version-value">${pkg.current_version}</span>
    `;

    const latestVersion = document.createElement('div');
    latestVersion.className = 'version-badge';
    latestVersion.innerHTML = `
        <span class="version-label">Latest:</span>
        <span class="version-value">${pkg.latest_version}</span>
    `;

    versions.appendChild(currentVersion);
    versions.appendChild(latestVersion);
    card.appendChild(versions);

    // Impacts (if breaking)
    if (pkg.status === 'breaking' && pkg.impacted_files && pkg.impacted_files.length > 0) {
        const impactsSection = document.createElement('div');
        impactsSection.className = 'impacts-section';

        const impactsTitle = document.createElement('h4');
        impactsTitle.className = 'impacts-title';
        impactsTitle.textContent = `⚠️ Impacted Files (${pkg.impacted_files.length})`;
        impactsSection.appendChild(impactsTitle);

        pkg.impacted_files.forEach(fileImpact => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'impact-file';

            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = `📄 ${fileImpact.file}`;
            fileDiv.appendChild(fileName);

            fileImpact.impacts.forEach(impact => {
                const impactItem = document.createElement('div');
                impactItem.className = 'impact-item';
                impactItem.innerHTML = `
                    <span class="line-number">Line ${impact.line}:</span>
                    <span class="code-context">${escapeHtml(impact.context)}</span>
                `;
                fileDiv.appendChild(impactItem);
            });

            impactsSection.appendChild(fileDiv);
        });

        card.appendChild(impactsSection);

        // Add Fix Suggestions Section
        const fixSection = createFixSection(pkg, pkg.impacted_files[0]);
        card.appendChild(fixSection);
    }

    return card;
}

// Create fix suggestions section
function createFixSection(pkg, fileImpact) {
    const fixSection = document.createElement('div');
    fixSection.className = 'fix-section';

    // Fix header (collapsible)
    const fixHeader = document.createElement('div');
    fixHeader.className = 'fix-header';

    const fixTitle = document.createElement('div');
    fixTitle.className = 'fix-title';
    fixTitle.innerHTML = '💡 How to Fix This Breaking Change';

    const fixToggle = document.createElement('span');
    fixToggle.className = 'fix-toggle';
    fixToggle.textContent = '▼';

    fixHeader.appendChild(fixTitle);
    fixHeader.appendChild(fixToggle);
    fixSection.appendChild(fixHeader);

    // Fix content (initially hidden)
    const fixContent = document.createElement('div');
    fixContent.className = 'fix-content hidden';

    // Check if AI fix is available
    if (fileImpact.ai_fix) {
        const aiFix = fileImpact.ai_fix;

        // Confidence badge
        const confidenceLevel = aiFix.confidence > 0.7 ? 'high' : aiFix.confidence > 0.4 ? 'medium' : 'low';
        const confidenceBadge = document.createElement('div');
        confidenceBadge.className = `confidence-badge ${confidenceLevel}`;
        confidenceBadge.innerHTML = `
            <span>AI Confidence: ${(aiFix.confidence * 100).toFixed(0)}%</span>
        `;
        fixContent.appendChild(confidenceBadge);

        // Explanation
        const explanation = document.createElement('div');
        explanation.className = 'fix-explanation';
        explanation.innerHTML = `
            <h5>📋 What Changed</h5>
            <p>${escapeHtml(aiFix.explanation)}</p>
        `;
        fixContent.appendChild(explanation);

        // Fixed code
        if (aiFix.fixed_code) {
            const fixedCode = document.createElement('div');
            fixedCode.className = 'fix-code';
            fixedCode.innerHTML = `
                <h5>✅ Suggested Fix</h5>
                <div class="code-block"><pre>${escapeHtml(aiFix.fixed_code)}</pre></div>
            `;
            fixContent.appendChild(fixedCode);
        }

        // Migration notes
        if (aiFix.migration_notes) {
            const migrationNotes = document.createElement('div');
            migrationNotes.className = 'fix-steps';
            migrationNotes.innerHTML = `<h5>📝 Migration Steps</h5>`;

            const notesParagraph = document.createElement('p');
            notesParagraph.style.color = 'var(--text-secondary)';
            notesParagraph.style.marginTop = 'var(--spacing-sm)';
            notesParagraph.textContent = aiFix.migration_notes;
            migrationNotes.appendChild(notesParagraph);

            fixContent.appendChild(migrationNotes);
        }
    } else {
        // Manual fix instructions
        fixContent.appendChild(createManualFixInstructions(pkg));
    }

    fixSection.appendChild(fixContent);

    // Toggle functionality
    fixHeader.addEventListener('click', () => {
        fixContent.classList.toggle('hidden');
        fixToggle.classList.toggle('expanded');
    });

    return fixSection;
}

// Create manual fix instructions
function createManualFixInstructions(pkg) {
    const manualFix = document.createElement('div');
    manualFix.className = 'fix-steps';
    manualFix.innerHTML = `
        <h5>🔧 Manual Fix Steps</h5>
        <ol class="step-list">
            <li class="step-item">
                Check the official changelog for ${pkg.package} version ${pkg.latest_version}:
                <div class="code-block" style="margin-top: 0.5rem;">
                    <pre>https://pypi.org/project/${pkg.package}/${pkg.latest_version}/</pre>
                </div>
            </li>
            <li class="step-item">
                Review breaking changes in the documentation
            </li>
            <li class="step-item">
                Update your code to use the new API
            </li>
            <li class="step-item">
                Update requirements.txt:
                <div class="code-block" style="margin-top: 0.5rem;">
                    <pre>${pkg.package}==${pkg.latest_version}</pre>
                </div>
            </li>
            <li class="step-item">
                Test thoroughly before deploying
            </li>
        </ol>
    `;
    return manualFix;
}

// Show loading state
function showLoading() {
    loadingState.classList.remove('hidden');
    errorState.classList.add('hidden');
    resultsSection.classList.add('hidden');
    analyzeBtn.disabled = true;
}

// Show error state
function showError(message) {
    loadingState.classList.add('hidden');
    errorState.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    errorMessage.textContent = message;
    analyzeBtn.disabled = false;
}

// Reset form
function resetForm() {
    errorState.classList.add('hidden');
    analyzeBtn.disabled = false;
    repoInput.focus();
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Check server health on load
async function checkServerHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('Server status:', data);
    } catch (error) {
        console.warn('Server not reachable. Make sure to run: python web_server.py');
    }
}

// Initialize
checkServerHealth();
