// This function runs when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    
    // Select the form and results section from the DOM
    const searchForm = document.getElementById('drug-search-form');
    const resultsSection = document.getElementById('results-section');
    const resultDrugName = document.getElementById('result-drug-name');
    const sideEffectsList = document.getElementById('side-effects-list');

    // Make sure the form exists on the page before adding an event listener
    if (searchForm) {
        searchForm.addEventListener('submit', (event) => {
            // Prevent the default form submission which reloads the page
            event.preventDefault(); 
            
            // Get the drug name from the input field
            const drugNameInput = document.getElementById('drug-name');
            const drugName = drugNameInput.value.trim();

            if (drugName === "") {
                alert("Please enter a drug name.");
                return;
            }

            // --- THIS IS WHERE YOU'LL CALL YOUR ML MODEL API ---
            
            // For demonstration, we'll use dummy data
            // In a real application, you would use fetch() to send drugName to your backend
            console.log(`Searching for side effects of: ${drugName}`);
            
            // Display the results section
            displayResults(drugName, getDummySideEffects(drugName));

            // Clear the input field
            drugNameInput.value = "";
        });
    }

    /**
     * A function to display the results in the UI
     * @param {string} drugName - The name of the drug searched.
     * @param {string[]} effects - An array of side effects.
     */
    function displayResults(drugName, effects) {
        // Update the drug name in the results title
        resultDrugName.textContent = drugName;
        
        // Clear any previous results
        sideEffectsList.innerHTML = '';

        // Check if there are any side effects to display
        if (effects.length > 0) {
            effects.forEach(effect => {
                const li = document.createElement('li');
                li.textContent = effect;
                sideEffectsList.appendChild(li);
            });
        } else {
            const p = document.createElement('p');
            p.textContent = "No common side effects found or drug not recognized.";
            sideEffectsList.appendChild(p);
        }

        // Make the results section visible
        resultsSection.classList.remove('hidden');
    }

    /**
     * A function to generate dummy side effects for demonstration
     * @param {string} drugName - The name of the drug.
     * @returns {string[]} An array of dummy side effects.
     */
    function getDummySideEffects(drugName) {
        // Simple logic to return different results based on input
        const lowerCaseDrug = drugName.toLowerCase();
        if (lowerCaseDrug.includes('paracetamol')) {
            return ['Nausea', 'Allergic reactions', 'Skin rashes', 'Liver damage (in case of overdose)'];
        } else if (lowerCaseDrug.includes('ibuprofen')) {
            return ['Stomach pain', 'Heartburn', 'Headache', 'Dizziness'];
        } else {
            return ['Dry mouth', 'Drowsiness', 'Constipation', 'Blurred vision'];
        }
    }
});