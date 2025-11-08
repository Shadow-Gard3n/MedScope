// This function runs when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    
    // --- Autocomplete Logic (Lines 6-107) ---
    let allChemicals = [];
    let allIndications = [];
    let allRoutes = [];
    let allCountries = []; // This will now be an array of objects

    // 1. Define promises to fetch all JSON files
    const pChemicals = fetch('/static/js/active_chemicals.json').then(res => res.json());
    const pIndications = fetch('/static/js/indications.json').then(res => res.json());
    const pRoutes = fetch('/static/js/routes.json').then(res => res.json());
    const pCountries = fetch('/static/js/countries.json').then(res => res.json());

    /**
     * Reusable function to create an autocomplete search box
     * @param {string} inputId - The id of the <input> element
     * @param {string} suggestionsId - The id of the <div> for suggestions
     * @param {Array<string> | Array<object>} sourceList - The data source (string array or object array)
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
        
        // Check if the source is the special country list
        const isCountrySearch = (inputId === 'country');

        input.addEventListener('input', () => {
            const query = input.value.toUpperCase();
            suggestionsBox.innerHTML = ''; // Clear old suggestions

            if (query.length < 1) { 
                suggestionsBox.style.display = 'none';
                return;
            }

            let matchingItems = [];

            if (isCountrySearch) {
                // Search by both name and code
                matchingItems = sourceList.filter(item => 
                    item.name.toUpperCase().includes(query) ||
                    item.code.toUpperCase().includes(query)
                ).slice(0, 50);
            } else {
                // Standard search for simple string arrays
                matchingItems = sourceList.filter(item => 
                    item.toUpperCase().includes(query)
                ).slice(0, 50);
            }

            if (matchingItems.length > 0) {
                matchingItems.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';

                    if (isCountrySearch) {
                        // Display: "United States (US)"
                        div.textContent = `${item.name} (${item.code})`;
                        div.addEventListener('click', () => {
                            input.value = item.code; // Set input value to the CODE
                            suggestionsBox.style.display = 'none';
                            suggestionsBox.innerHTML = '';
                        });
                    } else {
                        // Display: "IBUPROFEN"
                        div.textContent = item;
                        div.addEventListener('click', () => {
                            input.value = item; // Set input value to the item
                            suggestionsBox.style.display = 'none';
                            suggestionsBox.innerHTML = '';
                        });
                    }
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
        .then(([chemicals, indications, routes, countries]) => {
            
            // 3. NOW, set up the autocomplete functions
            console.log("All JSON files loaded. Setting up autocomplete.");
            // Store fetched data in the global-like variables
            allChemicals = chemicals;
            allIndications = indications;
            allRoutes = routes;
            allCountries = countries;

            // Setup autocomplete with the fetched data
            setupAutocomplete('active_chemical', 'chemical_suggestions', allChemicals);
            setupAutocomplete('indication_for_use', 'indication_suggestions', allIndications);
            setupAutocomplete('route', 'route_suggestions', allRoutes);
            setupAutocomplete('country', 'country_suggestions', allCountries); 
        })
        .catch(error => {
            console.error("Fatal Error: Could not load one or more JSON files for autocomplete.", error);
        });
    // --- End of Autocomplete Logic ---


    // --- Form Submission Logic (SINGLE, CORRECT VERSION) ---
    const searchForm = document.getElementById('drug-search-form');
    const resultsSection = document.getElementById('results-section');
    
    // Get all result list elements
    const riskList = document.getElementById('risk-profile-list');
    const sideEffectsList = document.getElementById('side-effects-list');
    
    // Get new alternative elements
    const alternativesBox = document.getElementById('alternatives-box');
    const alternativesList = document.getElementById('alternatives-list');
    const altIndicationEl = document.getElementById('alt-indication');
    
    if (searchForm) {
        searchForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // <-- THIS WILL NOW RUN
            
            // --- 1. Clear all previous results and hide ---
            riskList.innerHTML = '';
            sideEffectsList.innerHTML = '';
            alternativesList.innerHTML = '';
            if (alternativesBox) alternativesBox.style.display = 'none';
            resultsSection.classList.add('hidden');

            // --- 2. Collect all inputs ---
            const age_grp = document.getElementById('age_grp').value;
            const sex = document.getElementById('sex').value;
            const is_hcp = document.getElementById('is_hcp').value === 'True';
            const country_input = document.getElementById('country').value.toUpperCase();

            // --- 3. Build the drug_profile_joined string ---
            const active_chemical = document.getElementById('active_chemical').value.toUpperCase();
            const drug_role = document.getElementById('drug_role').value;
            const route = document.getElementById('route').value;
            const indication = document.getElementById('indication_for_use').value; // Get indication here
            const dechallenge = document.getElementById('dechallenge').value;

            const drug_profile_joined = 
                `${active_chemical}_ROLE_${drug_role}_ROUTE_${route}_IND_${indication}_DECHAL_${dechallenge}`;

            // --- 4. Create the JSON payload for the /predict API ---
            const predictionPayload = {
                age_grp: age_grp,
                sex: sex,
                reporter_country: country_input,
                occr_country: country_input,
                is_hcp: is_hcp,
                drug_profile_joined: drug_profile_joined
            };

            console.log("Sending data to /predict:", predictionPayload);

            try {
                // --- 5. Call your /predict endpoint ---
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(predictionPayload)
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Network response was not ok');
                }

                const predictionData = await response.json();
                
                // --- 6. Display Prediction results ---
                if (predictionData.risk_profile && predictionData.risk_profile.length > 0) {
                    predictionData.risk_profile.forEach(risk => {
                        const li = document.createElement('li');
                        li.textContent = risk;
                        riskList.appendChild(li);
                    });
                } else {
                    riskList.innerHTML = '<p>No specific risks predicted.</p>';
                }

                if (predictionData.side_effects && predictionData.side_effects.length > 0) {
                    predictionData.side_effects.forEach(effect => {
                        const li = document.createElement('li');
                        li.textContent = effect;
                        sideEffectsList.appendChild(li);
                    });
                } else {
                    sideEffectsList.innerHTML = '<p>No common side effects predicted.</p>';
                }

                // --- 7. Call /alternatives endpoint (UPDATED LOGIC) ---
                const predictedEffects = predictionData.side_effects;
                
                // Only try to find alternatives if an indication was provided
                if (indication && indication.toLowerCase() !== 'unknown') {
                    
                    // --- 'if/else' BLOCK ---
                    // Check if there are actually side effects to avoid
                    if (predictedEffects && predictedEffects.length > 0) {
                        // Case 1: Side effects WERE predicted. Find alternatives.
                        const alternativesPayload = {
                            indication: indication,
                            avoid_side_effects: predictedEffects,
                            original_drug_name: active_chemical
                        };
                        
                        console.log("Sending data to /alternatives:", alternativesPayload);

                        try {
                            const altResponse = await fetch('/alternatives/avoid', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(alternativesPayload)
                            });

                            if (altResponse.ok) {
                                const altData = await altResponse.json();
                                altIndicationEl.textContent = altData.indication; 
                                if (altData.alternatives && altData.alternatives.length > 0) {
                                    const ul = document.createElement('ul');
                                    altData.alternatives.slice(0, 10).forEach(alt => {
                                        const li = document.createElement('li');
                                        li.textContent = alt;
                                        ul.appendChild(li);
                                    });
                                    alternativesList.appendChild(ul);
                                } else {
                                    alternativesList.innerHTML = '<p>No alternatives found for this indication without those side effects.</p>';
                                }
                            } else {
                                alternativesList.innerHTML = '<p>Could not check for alternatives.</p>';
                            }
                        
                        } catch (altError) {
                            console.error("Error fetching alternatives:", altError);
                            alternativesList.innerHTML = '<p>An error occurred while fetching alternatives.</p>';
                        }

                    } else {
                        // Case 2: NO side effects were predicted. Display a message.
                        console.log("No side effects predicted, skipping alternative search.");
                        altIndicationEl.textContent = indication; // Show what we searched for
                        alternativesList.innerHTML = '<p>No side effects were predicted for this drug.</p>';
                    }
                    
                    // This line is now run for BOTH cases
                    alternativesBox.style.display = 'block';
                }

            } catch (error) {
                // This catch handles errors from the /predict call
                console.error("Error fetching prediction:", error);
                riskList.innerHTML = `<p>Error: ${error.message}</p>`;
            }

            // --- 8. Make the results section visible ---
            resultsSection.classList.remove('hidden');
        });
    }
});

//  // This function runs when the DOM is fully loaded
// document.addEventListener('DOMContentLoaded', () => {
    
//     // --- Autocomplete Logic ---
//     let allChemicals = [];
//     let allIndications = [];
//     let allRoutes = [];
//     let allCountries = []; // This will now be an array of objects

//     // 1. Define promises to fetch all JSON files
//     const pChemicals = fetch('/static/js/active_chemicals.json').then(res => res.json());
//     const pIndications = fetch('/static/js/indications.json').then(res => res.json());
//     const pRoutes = fetch('/static/js/routes.json').then(res => res.json());
//     const pCountries = fetch('/static/js/countries.json').then(res => res.json());

//     /**
//      * Reusable function to create an autocomplete search box
//      * @param {string} inputId - The id of the <input> element
//      * @param {string} suggestionsId - The id of the <div> for suggestions
//      * @param {Array<string> | Array<object>} sourceList - The data source (string array or object array)
//      */
//     function setupAutocomplete(inputId, suggestionsId, sourceList) {
//         const input = document.getElementById(inputId);
//         const suggestionsBox = document.getElementById(suggestionsId);

//         if (!input) {
//             console.error(`Autocomplete input with id "${inputId}" not found.`);
//             return;
//         }
//         if (!suggestionsBox) {
//             console.error(`Suggestion box with id "${suggestionsId}" not found.`);
//             return;
//         }
        
//         // Check if the source is the special country list
//         const isCountrySearch = (inputId === 'country');

//         input.addEventListener('input', () => {
//             const query = input.value.toUpperCase();
//             suggestionsBox.innerHTML = ''; // Clear old suggestions

//             if (query.length < 1) { 
//                 suggestionsBox.style.display = 'none';
//                 return;
//             }

//             let matchingItems = [];

//             if (isCountrySearch) {
//                 // Search by both name and code
//                 matchingItems = sourceList.filter(item => 
//                     item.name.toUpperCase().includes(query) ||
//                     item.code.toUpperCase().includes(query)
//                 ).slice(0, 50);
//             } else {
//                 // Standard search for simple string arrays
//                 matchingItems = sourceList.filter(item => 
//                     item.toUpperCase().includes(query)
//                 ).slice(0, 50);
//             }

//             if (matchingItems.length > 0) {
//                 matchingItems.forEach(item => {
//                     const div = document.createElement('div');
//                     div.className = 'suggestion-item';

//                     if (isCountrySearch) {
//                         // Display: "United States (US)"
//                         div.textContent = `${item.name} (${item.code})`;
//                         div.addEventListener('click', () => {
//                             input.value = item.code; // Set input value to the CODE
//                             suggestionsBox.style.display = 'none';
//                             suggestionsBox.innerHTML = '';
//                         });
//                     } else {
//                         // Display: "IBUPROFEN"
//                         div.textContent = item;
//                         div.addEventListener('click', () => {
//                             input.value = item; // Set input value to the item
//                             suggestionsBox.style.display = 'none';
//                             suggestionsBox.innerHTML = '';
//                         });
//                     }
//                     suggestionsBox.appendChild(div);
//                 });
//                 suggestionsBox.style.display = 'block';
//             } else {
//                 suggestionsBox.style.display = 'none';
//             }
//         });

//         // Hide suggestions when clicking elsewhere
//         document.addEventListener('click', (e) => {
//             if (e.target.id !== inputId) {
//                 suggestionsBox.style.display = 'none';
//             }
//         });
//     }

//     // 2. Wait for ALL promises to resolve
//     Promise.all([pChemicals, pIndications, pRoutes, pCountries])
//         .then(([allChemicals, allIndications, allRoutes, allCountries]) => {
            
//             // 3. NOW, set up the autocomplete functions
//             console.log("All JSON files loaded. Setting up autocomplete.");
//             setupAutocomplete('active_chemical', 'chemical_suggestions', allChemicals);
//             setupAutocomplete('indication_for_use', 'indication_suggestions', allIndications);
//             setupAutocomplete('route', 'route_suggestions', allRoutes);
//             setupAutocomplete('country', 'country_suggestions', allCountries); // This will now use the new logic
//         })
//         .catch(error => {
//             console.error("Fatal Error: Could not load one or more JSON files for autocomplete.", error);
//         });
//     // --- End of Autocomplete Logic ---


//     // --- Form Submission Logic (This part is unchanged) ---
//     const searchForm = document.getElementById('drug-search-form');
//     const resultsSection = document.getElementById('results-section');
//     const riskList = document.getElementById('risk-profile-list');
//     const sideEffectsList = document.getElementById('side-effects-list');
    
//     if (searchForm) {
//         searchForm.addEventListener('submit', async (event) => {
//             event.preventDefault(); 
            
//             // --- 1. Collect all inputs ---
//             const age_grp = document.getElementById('age_grp').value;
//             const sex = document.getElementById('sex').value;
//             const is_hcp = document.getElementById('is_hcp').value === 'True';
//             const country_input = document.getElementById('country').value.toUpperCase();

//             // --- 2. Build the drug_profile_joined string ---
//             const active_chemical = document.getElementById('active_chemical').value.toUpperCase();
//             const drug_role = document.getElementById('drug_role').value;
//             const route = document.getElementById('route').value;
//             const indication = document.getElementById('indication_for_use').value;
//             const dechallenge = document.getElementById('dechallenge').value;

//             const drug_profile_joined = 
//                 `${active_chemical}_ROLE_${drug_role}_ROUTE_${route}_IND_${indication}_DECHAL_${dechallenge}`;

//             // --- 3. Create the JSON payload for the API ---
//             const data = {
//                 age_grp: age_grp,
//                 sex: sex,
//                 reporter_country: country_input, // Use single country for both
//                 occr_country: country_input,     // Use single country for both
//                 is_hcp: is_hcp,
//                 drug_profile_joined: drug_profile_joined
//             };

//             console.log("Sending data to API:", data);

//             // --- 4. Call your /predict endpoint ---
//             try {
//                 const response = await fetch('/predict', {
//                     method: 'POST',
//                     headers: {
//                         'Content-Type': 'application/json'
//                     },
//                     body: JSON.stringify(data)
//                 });

//                 if (!response.ok) {
//                     const err = await response.json();
//                     throw new Error(err.detail || 'Network response was not ok');
//                 }

//                 const results = await response.json();
                
//                 // --- 5. Display both results ---
//                 displayResults(results.risk_profile, results.side_effects);

//             } catch (error) {
//                 console.error("Error fetching prediction:", error);
//                 displayResults([`Error: ${error.message}`], []);
//             }
//         });
//     }

//     /**
//      * A function to display the results in the UI
//      * @param {string[]} risks - An array of predicted risks.
//      * @param {string[]} effects - An array of side effects.
//      */
//     function displayResults(risks, effects) {
//         // Clear previous results
//         riskList.innerHTML = '';
//         sideEffectsList.innerHTML = '';

//         // Populate Risk Profile
//         if (risks && risks.length > 0) {
//             risks.forEach(risk => {
//                 const li = document.createElement('li');
//                 li.textContent = risk;
//                 riskList.appendChild(li);
//             });
//         } else {
//             riskList.innerHTML = '<p>No specific risks predicted.</p>';
//         }

//         // Populate Side Effects
//         if (effects && effects.length > 0) {
//             effects.forEach(effect => {
//                 const li = document.createElement('li');
//                 li.textContent = effect;
//                 sideEffectsList.appendChild(li);
//             });
//         } else {
//             sideEffectsList.innerHTML = '<p>No common side effects predicted.</p>';
//         }

//         // Make the results section visible
//         resultsSection.classList.remove('hidden');
//     }
// });