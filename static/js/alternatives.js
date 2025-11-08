document.addEventListener('DOMContentLoaded', () => {
    
    // --- Autocomplete Setup (Reused) ---
    const pIndications = fetch('/static/js/alternatives_indications.json').then(res => res.json());
    const pChemicals = fetch('/static/js/alternatives_drugs.json').then(res => res.json());

    function setupAutocomplete(inputId, suggestionsId, sourceList) {
        const input = document.getElementById(inputId);
        const suggestionsBox = document.getElementById(suggestionsId);
        if (!input || !suggestionsBox) return;

        input.addEventListener('input', () => {
            const query = input.value.toUpperCase();
            suggestionsBox.innerHTML = '';
            if (query.length < 1) { suggestionsBox.style.display = 'none'; return; }
            
            const matching = sourceList.filter(item => item.toUpperCase().includes(query)).slice(0, 50);
            if (matching.length > 0) {
                matching.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    div.textContent = item;
                    div.addEventListener('click', () => {
                        input.value = item;
                        suggestionsBox.style.display = 'none';
                    });
                    suggestionsBox.appendChild(div);
                });
                suggestionsBox.style.display = 'block';
            } else { suggestionsBox.style.display = 'none'; }
        });
        document.addEventListener('click', (e) => { if (e.target.id !== inputId) suggestionsBox.style.display = 'none'; });
    }

    Promise.all([pIndications, pChemicals]).then(([indications, chemicals]) => {
        setupAutocomplete('search-indication', 'indication_suggestions', indications);
        setupAutocomplete('search-drug', 'drug_suggestions', chemicals);
    });

    // --- SEARCH LOGIC ---
    const drugForm = document.getElementById('drug-search-form');
    const indicationForm = document.getElementById('indication-search-form');
    const resultsSection = document.getElementById('results-section');
    const primaryDrugInfo = document.getElementById('primary-drug-info');
    const primaryDrugCard = document.getElementById('primary-drug-card');
    const primaryDrugIndication = document.getElementById('primary-drug-indication');
    const alternativesList = document.getElementById('alternatives-list');
    const alternativesTitle = document.getElementById('alternatives-title');

    // Helper function to create a drug card HTML
    function createDrugCard(drugName, sideEffects) {
        const card = document.createElement('div');
        card.className = 'drug-card';
        
        const nameEl = document.createElement('div');
        nameEl.className = 'drug-name';
        nameEl.textContent = drugName;
        card.appendChild(nameEl);

        const effectsLabel = document.createElement('strong');
        effectsLabel.textContent = 'Reported Side Effects:';
        card.appendChild(effectsLabel);

        const ul = document.createElement('ul');
        ul.className = 'side-effects-list';
        if (sideEffects && sideEffects.length > 0) {
            // Show top 5 effects to keep card size reasonable
            sideEffects.slice(0, 5).forEach(effect => {
                const li = document.createElement('li');
                li.textContent = effect;
                ul.appendChild(li);
            });
            if (sideEffects.length > 5) {
                const li = document.createElement('li');
                li.textContent = `...and ${sideEffects.length - 5} more`;
                li.style.fontStyle = 'italic';
                ul.appendChild(li);
            }
        } else {
            const li = document.createElement('li');
            li.textContent = 'None reported in this dataset';
            ul.appendChild(li);
        }
        card.appendChild(ul);

        return card;
    }

    // Define performSearch as an async function
    async function performSearch(payload) {
        // Clear and show loading
        resultsSection.classList.add('hidden');
        primaryDrugInfo.classList.add('hidden');
        alternativesList.innerHTML = '<p>Loading results...</p>';
        resultsSection.classList.remove('hidden');

        try {
            // Updated URL to point to the new specific endpoint
            const response = await fetch('/alternatives/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                alternativesList.innerHTML = ''; // Clear loading

                // CASE 1: Drug Search Result
                if (data.search_type === 'drug') {
                    if (data.primary_drug) {
                        // Show primary drug info
                        primaryDrugCard.innerHTML = '';
                        primaryDrugCard.appendChild(createDrugCard(data.primary_drug.name, data.primary_drug.effects));
                        primaryDrugIndication.textContent = data.primary_drug.primary_indication || "Unknown Indication";
                        primaryDrugInfo.classList.remove('hidden');
                        alternativesTitle.textContent = "Alternative Medicines";
                    } else {
                         alternativesList.innerHTML = `<p>Drug "${data.query}" not found in our alternatives database.</p>`;
                         return;
                    }
                } 
                // CASE 2: Indication Search Result
                else {
                    primaryDrugInfo.classList.add('hidden');
                    alternativesTitle.textContent = `Medicines for: ${data.query}`;
                }

                // Show list of alternatives (common for both cases)
                if (data.alternatives && data.alternatives.length > 0) {
                    // Limit to top 20 for performance if list is huge
                    data.alternatives.slice(0, 20).forEach(drug => {
                        alternativesList.appendChild(createDrugCard(drug.name, drug.effects));
                    });
                } else {
                    alternativesList.innerHTML = '<p>No other medicines found for this condition.</p>';
                }

            } else {
                alternativesList.innerHTML = '<p>Error fetching results.</p>';
            }
        } catch (error) {
            console.error(error);
            alternativesList.innerHTML = '<p>Network error.</p>';
        }
    }

    // Event Listeners for both forms
    drugForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await performSearch({ drug_name: document.getElementById('search-drug').value });
    });

    indicationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await performSearch({ indication: document.getElementById('search-indication').value });
    });
});