// This function runs when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    
    // --- Autocomplete Logic ---

    // 1. Define promises to fetch all JSON files
    const pChemicals = fetch('/static/js/active_chemicals.json').then(res => res.json());
    const pIndications = fetch('/static/js/indications.json').then(res => res.json());
    const pRoutes = fetch('/static/js/routes.json').then(res => res.json());
    const pCountries = fetch('/static/js/countries.json').then(res => res.json());

    /**
     * Reusable function to create an autocomplete search box
     * @param {string} inputId - The id of the <input> element
     * @param {string} suggestionsId - The id of the <div> for suggestions
     * @param {string[]} sourceList - The array of all possible values (from JSON)
     */
    function setupAutocomplete(inputId, suggestionsId, sourceList) {
        const input = document.getElementById(inputId);
        const suggestionsBox = document.getElementById(suggestionsId);

        if (!input) {
            console.error(`Autocomplete input with id "${inputId}" not found.`);
            return;
        }
        if (!suggestionsBox) {
            console.error(`Suggestion box with id "${suggestionsId}" not found.`);
            return;
        }

        input.addEventListener('input', () => {
            const query = input.value.toUpperCase();
            suggestionsBox.innerHTML = ''; // Clear old suggestions

            if (query.length < 1) { 
                suggestionsBox.style.display = 'none';
                return;
            }

            // Filter the sourceList (which is now guaranteed to be loaded)
            const matchingItems = sourceList.filter(item => 
                item.toUpperCase().includes(query)
            ).slice(0, 50); // Show max 50 results

            if (matchingItems.length > 0) {
                matchingItems.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    div.textContent = item;
                    div.addEventListener('click', () => {
                        input.value = item; // Fill input on click
                        suggestionsBox.style.display = 'none'; // Hide box
                        suggestionsBox.innerHTML = '';
                    });
                    suggestionsBox.appendChild(div);
                });
                suggestionsBox.style.display = 'block';
            } else {
                suggestionsBox.style.display = 'none';
            }
        });

        // Hide suggestions when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (e.target.id !== inputId) {
                suggestionsBox.style.display = 'none';
            }
        });
    }

    // 2. Wait for ALL promises to resolve
    Promise.all([pChemicals, pIndications, pRoutes, pCountries])
        .then(([allChemicals, allIndications, allRoutes, allCountries]) => {
            
            // 3. NOW, set up the autocomplete functions
            console.log("All JSON files loaded. Setting up autocomplete.");
            setupAutocomplete('active_chemical', 'chemical_suggestions', allChemicals);
            setupAutocomplete('indication_for_use', 'indication_suggestions', allIndications);
            setupAutocomplete('route', 'route_suggestions', allRoutes);
            setupAutocomplete('country', 'country_suggestions', allCountries);
        })
        .catch(error => {
            console.error("Fatal Error: Could not load one or more JSON files for autocomplete.", error);
            // You could show a user-facing error here if you want
        });

    // --- End of Autocomplete Logic ---


    // --- Form Submission Logic (This part is unchanged) ---
    const searchForm = document.getElementById('drug-search-form');
    const resultsSection = document.getElementById('results-section');
    const riskList = document.getElementById('risk-profile-list');
    const sideEffectsList = document.getElementById('side-effects-list');
    
    if (searchForm) {
        searchForm.addEventListener('submit', async (event) => {
            event.preventDefault(); 
            
            // --- 1. Collect all inputs ---
            const age_grp = document.getElementById('age_grp').value;
            const sex = document.getElementById('sex').value;
            const is_hcp = document.getElementById('is_hcp').value === 'True';
            const country_input = document.getElementById('country').value.toUpperCase();

            // --- 2. Build the drug_profile_joined string ---
            const active_chemical = document.getElementById('active_chemical').value.toUpperCase();
            const drug_role = document.getElementById('drug_role').value;
            const route = document.getElementById('route').value;
            const indication = document.getElementById('indication_for_use').value;
            const dechallenge = document.getElementById('dechallenge').value;

            const drug_profile_joined = 
                `${active_chemical}_ROLE_${drug_role}_ROUTE_${route}_IND_${indication}_DECHAL_${dechallenge}`;

            // --- 3. Create the JSON payload for the API ---
            const data = {
                age_grp: age_grp,
                sex: sex,
                reporter_country: country_input, // Use single country for both
                occr_country: country_input,     // Use single country for both
                is_hcp: is_hcp,
                drug_profile_joined: drug_profile_joined
            };

            console.log("Sending data to API:", data);

            // --- 4. Call your /predict endpoint ---
            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Network response was not ok');
                }

                const results = await response.json();
                
                // --- 5. Display both results ---
                displayResults(results.risk_profile, results.side_effects);

            } catch (error) {
                console.error("Error fetching prediction:", error);
                displayResults([`Error: ${error.message}`], []);
            }
        });
    }

    /**
     * A function to display the results in the UI
     * @param {string[]} risks - An array of predicted risks.
     * @param {string[]} effects - An array of side effects.
     */
    function displayResults(risks, effects) {
        // Clear previous results
        riskList.innerHTML = '';
        sideEffectsList.innerHTML = '';

        // Populate Risk Profile
        if (risks && risks.length > 0) {
            risks.forEach(risk => {
                const li = document.createElement('li');
                li.textContent = risk;
                riskList.appendChild(li);
            });
        } else {
            riskList.innerHTML = '<p>No specific risks predicted.</p>';
        }

        // Populate Side Effects
        if (effects && effects.length > 0) {
            effects.forEach(effect => {
                const li = document.createElement('li');
                li.textContent = effect;
                sideEffectsList.appendChild(li);
            });
        } else {
            sideEffectsList.innerHTML = '<p>No common side effects predicted.</p>';
        }

        // Make the results section visible
        resultsSection.classList.remove('hidden');
    }
});