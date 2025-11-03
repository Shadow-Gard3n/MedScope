// This function runs when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    
    // Select the form and new results lists from the DOM
    const searchForm = document.getElementById('drug-search-form');
    const resultsSection = document.getElementById('results-section');
    const riskList = document.getElementById('risk-profile-list');
    const sideEffectsList = document.getElementById('side-effects-list');

    // Make sure the form exists on the page before adding an event listener
    if (searchForm) {
        searchForm.addEventListener('submit', async (event) => {
            // Prevent the default form submission which reloads the page
            event.preventDefault(); 
            
            // --- 1. Collect all inputs from the new form ---
            const age_in_years = parseFloat(document.getElementById('age_in_years').value);
            const sex = document.getElementById('sex').value;
            const is_hcp = document.getElementById('is_hcp').value === 'True';
            const reporter_country = document.getElementById('reporter_country').value.toUpperCase();
            
            // From our model logic, occr_country is usually the same
            const occr_country = reporter_country;

            // Determine age_grp from age_in_years
            // (This matches the logic in your data cleaning notebook)
            let age_grp;
            if (age_in_years < (1/12)) age_grp = 'Neonate';
            else if (age_in_years < 2) age_grp = 'Infant';
            else if (age_in_years < 12) age_grp = 'Child';
            else if (age_in_years < 18) age_grp = 'Adolescent';
            else if (age_in_years <= 65) age_grp = 'Adult';
            else age_grp = 'Elderly';

            // --- 2. Build the drug_profile_joined string ---
            // This MUST match the format from your training notebook
            const active_chemical = document.getElementById('active_chemical').value.toUpperCase();
            const drug_role = document.getElementById('drug_role').value;
            const route = document.getElementById('route').value;
            const indication = document.getElementById('indication_for_use').value;
            const dechallenge = document.getElementById('dechallenge').value;

            // Build the string: e.g., "DIDANOSINE_ROLE_PS_ROUTE_Oral_IND_Headache_DECHAL_Unknown"
            const drug_profile_joined = 
                `${active_chemical}_ROLE_${drug_role}_ROUTE_${route}_IND_${indication}_DECHAL_${dechallenge}`;

            // --- 3. Create the JSON payload for the API ---
            const data = {
                age_grp: age_grp,
                sex: sex,
                reporter_country: reporter_country,
                occr_country: occr_country,
                is_hcp: is_hcp,
                age_in_years: age_in_years,
                drug_profile_joined: drug_profile_joined
            };

            console.log("Sending data to API:", data);

            // --- 4. Call your new /predict endpoint ---
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