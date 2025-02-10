const API_URL = 'http://localhost:8000';

// DOMContentLoaded: Initialize event listeners and components.
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded: Starting...");
    setupEventListeners();
    loadIngredients();
    initializeWeightSliders();
    initializeTooltips();
});

// Set up event listeners for form submission and other input elements
function setupEventListeners() {
    console.log("Setting up event listeners.");
    // Form submission event
    const recipeForm = document.getElementById('recipe-form');
    recipeForm.addEventListener('submit', handleFormSubmit);

    // Results number slider
    const numResultsSlider = document.getElementById('num-results');
    const numResultsValue = document.getElementById('num-results-value');
    numResultsSlider.addEventListener('input', () => {
        numResultsValue.textContent = `${numResultsSlider.value} recipes`;
        console.log("Results number slider updated:", numResultsSlider.value);
    });

    // Real-time validation for required select fields
    const requiredSelects = document.querySelectorAll('select[required]');
    requiredSelects.forEach(select => {
        select.addEventListener('change', () => {
            validateSelect(select);
            console.log("Select changed:", select.id, select.value);
        });
    });
}

// Initialize weight sliders (e.g., cooking_method, cuisine_region, etc.)
function initializeWeightSliders() {
    console.log("Initializing weight sliders.");
    const weightSliders = [
        { id: 'weight-cooking', label: 'cooking_method' },
        { id: 'weight-cuisine', label: 'cuisine_region' },
        { id: 'weight-diet', label: 'diet_types' },
        { id: 'weight-ingredients', label: 'ingredients' },
        { id: 'weight-nutrition', label: 'nutrition' }
    ];

    weightSliders.forEach(({ id, label }) => {
        const slider = document.getElementById(id);
        const value = document.getElementById(`${id}-value`);
        if (slider && value) {
            slider.addEventListener('input', () => {
                value.textContent = parseFloat(slider.value).toFixed(1);
                console.log(`Slider ${id} updated:`, slider.value);
            });
        }
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    console.log("Initializing tooltips.");
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
}

// Load ingredients from the API and add them to the corresponding select element
async function loadIngredients() {
    console.log("Loading ingredients from API...");
    try {
        const response = await fetch(`${API_URL}/unique_ingredients`);
        if (!response.ok) {
            throw new Error('Ingredients could not be retrieved');
        }
        const ingredients = await response.json();
        console.log("Ingredients retrieved:", ingredients);

        const select = document.getElementById('ingredients');
        select.innerHTML = ''; // Clear existing options

        // Sort and format each ingredient option
        ingredients.sort().forEach(ingredient => {
            const option = document.createElement('option');
            option.value = ingredient;
            option.textContent = ingredient.toLowerCase()
                .split(',')
                .map(word => word.trim())
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(', ');
            select.appendChild(option);
        });

        // Enable search functionality for ingredient selection
        enableIngredientSearch();
    } catch (error) {
        console.error('Error while loading ingredients:', error);
        showToast('Ingredients could not be loaded. Please try again later.', 'error');
    }
}

// Enable search functionality in the select element for ingredients
function enableIngredientSearch() {
    console.log("Enabling ingredient search.");
    const ingredientSelect = document.getElementById('ingredients');
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control mb-2';
    searchInput.placeholder = 'Search ingredients...';

    ingredientSelect.parentNode.insertBefore(searchInput, ingredientSelect);

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const options = ingredientSelect.options;
        for (let option of options) {
            const text = option.text.toLowerCase();
            option.style.display = text.includes(searchTerm) ? '' : 'none';
        }
        console.log("Search term:", searchTerm);
    });
}

// When the form is submitted
async function handleFormSubmit(event) {
    event.preventDefault();
    console.log("Form submitted. Collecting form data...");

    // Show loading state on the submit button
    const submitButton = event.target.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    submitButton.innerHTML = '<span class="loading"></span> Finding Recipes...';
    submitButton.disabled = true;

    try {
        const formData = getFormData();
        console.log("Form data:", formData);

        // Check if at least one search criterion is provided
        if (!validateFormData(formData)) {
            throw new Error('Please fill in at least one search criterion');
        }

        const recipes = await getRecommendations(formData);
        console.log("Retrieved recipe IDs:", recipes);
        displayResults(recipes);

        // Scroll to the results section
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error while retrieving recommendations:', error);
        showToast(error.message, 'error');
    } finally {
        // Restore the submit button to its original state
        submitButton.textContent = originalButtonText;
        submitButton.disabled = false;
    }
}

// Check if the form data is valid
function validateFormData(formData) {
    const valid = (
        formData.cooking_method ||
        formData.servings_bin ||
        formData.diet_types.length > 0 ||
        formData.meal_type.length > 0 ||
        formData.cook_time ||
        formData.health_types.length > 0 ||
        formData.cuisine_region ||
        formData.ingredients.length > 0
    );
    console.log("Are the form data valid?:", valid);
    return valid;
}

// Collect form data
function getFormData() {
    return {
        cooking_method: getSelectedValues('cooking-method')[0] || '',
        servings_bin: document.getElementById('servings').value,
        diet_types: getSelectedValues('diet-types'),
        meal_type: getSelectedValues('meal-types'),
        cook_time: document.getElementById('cook-time').value,
        health_types: [
            ...getSelectedValues('protein-level'),
            ...getSelectedValues('carb-level'),
            ...getSelectedValues('fat-level'),
            ...getSelectedValues('calorie-level'),
            ...getSelectedValues('cholesterol-level'),
            ...getSelectedValues('sugar-level')
        ],
        cuisine_region: getSelectedValues('cuisine-region')[0] || '',
        ingredients: getSelectedValues('ingredients'),
        weights: {
            cooking_method: parseFloat(document.getElementById('weight-cooking').value),
            cuisine_region: parseFloat(document.getElementById('weight-cuisine').value),
            diet_types: parseFloat(document.getElementById('weight-diet').value),
            ingredients: parseFloat(document.getElementById('weight-ingredients').value),
            nutrition: parseFloat(document.getElementById('weight-nutrition')?.value || 1.0)
        },
        top_k: parseInt(document.getElementById('num-results').value),
        flexible: document.getElementById('flexible-matching').checked
    };
}

// Get the selected values from a given select element
function getSelectedValues(elementId) {
    const element = document.getElementById(elementId);
    return element ? Array.from(element.selectedOptions).map(option => option.value) : [];
}

// Request recommended recipes based on form data
async function getRecommendations(formData) {
    console.log("Requesting recommendations. Form data:", formData);
    const response = await fetch(`${API_URL}/recommend`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("Recommendation API error response:", errorData);
        throw new Error(errorData.detail || 'Recommendations could not be retrieved');
    }

    const data = await response.json();
    console.log("Recommendation data received:", data);
    return data;
}

// Display recipe results
function displayResults(recipeIds) {
    console.log("Displaying recipe results:", recipeIds);
    const resultsSection = document.getElementById('results-section');
    const recipeList = document.getElementById('recipe-list');

    recipeList.innerHTML = ''; // Clear previous results

    if (recipeIds.length === 0) {
        recipeList.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                No recipes match your criteria. Please adjust your filters.
            </div>
        `;
        resultsSection.style.display = 'block';
        return;
    }

    recipeIds.forEach((id, index) => {
        const item = document.createElement('button');
        item.className = 'list-group-item list-group-item-action recipe-item';
        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <strong>Recipe #${id}</strong>
                <span class="badge bg-primary rounded-pill">${index + 1}</span>
            </div>
        `;
        item.addEventListener('click', () => {
            console.log("Recipe clicked. ID:", id);
            showRecipeDetails(id);
        });
        recipeList.appendChild(item);
    });

    resultsSection.style.display = 'block';
}

// Fetch details for the specified recipe ID and display in a modal
async function showRecipeDetails(recipeId) {
    console.log("Fetching details. Recipe ID:", recipeId);
    try {
        const response = await fetch(`${API_URL}/recipe/${recipeId}`);
        if (!response.ok) {
            throw new Error('Recipe details could not be retrieved');
        }
        const recipe = await response.json();
        console.log("Recipe details retrieved:", recipe);
        displayRecipeModal(recipe);
    } catch (error) {
        console.error('Error while fetching recipe details:', error);
        showToast('Recipe details could not be loaded. Please try again.', 'error');
    }
}

// Render the ingredient list (supports string or array format)
function renderIngredientList(ingredientData, delimiter = ',') {
    if (!ingredientData) {
        return '<li class="list-group-item">No ingredients listed</li>';
    }
    let ingredients = [];
    if (Array.isArray(ingredientData)) {
        ingredients = ingredientData;
    } else {
        ingredients = ingredientData.split(delimiter);
    }
    return ingredients
        .map(ing => ing.trim())
        .filter(ing => ing.length > 0)
        .map(ing => `<li class="list-group-item"><i class="bi bi-check2"></i> ${ing}</li>`)
        .join('');
}

// Display recipe details in a modal
function displayRecipeModal(recipe) {
    console.log("Recipe details for modal:", recipe);
    const detailsContainer = document.getElementById('recipe-details');

    // Construct meal type information:
    // If meal_type is an array, use it directly; if it's a string, split by commas.
    let mealTypes = 'Not specified';
    if (recipe.meal_type) {
        if (Array.isArray(recipe.meal_type)) {
            mealTypes = recipe.meal_type.map(type => `<span class="badge bg-success me-1 mb-1">${type.trim()}</span>`).join(' ');
        } else if (typeof recipe.meal_type === 'string') {
            mealTypes = recipe.meal_type.split(',').map(type => `<span class="badge bg-success me-1 mb-1">${type.trim()}</span>`).join(' ');
        }
    }
    console.log("Meal types to display:", mealTypes);

    // Get healthy type from either "health_type" or "Healthy_Type"
    const healthyTypes = recipe.health_type || recipe.Healthy_Type || '';
    const healthyTypesContent = healthyTypes
        ? healthyTypes.split(',').map(ht => `<span class="badge bg-info me-1 mb-1">${ht.trim()}</span>`).join(' ')
        : 'Not specified';

    const content = `
        <div class="recipe-details">
            <h3>${recipe.Name || 'Unnamed Recipe'}</h3>
            ${recipe.Description ? `
                <div class="alert alert-light">
                    ${recipe.Description}
                </div>
            ` : ''}
            <!-- Quick Recipe Info -->
            <div class="recipe-quick-info mb-4">
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">Cooking Information</h5>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item">
                                        <strong>Cooking Method:</strong> ${recipe.Cooking_Method || 'Not specified'}
                                    </li>
                                    <li class="list-group-item">
                                        <strong>Servings:</strong> ${recipe.servings_bin || 'Not specified'}
                                    </li>
                                    <li class="list-group-item">
                                        <strong>Cook Time:</strong> ${recipe.cook_time || 'Not specified'}
                                    </li>
                                    <li class="list-group-item">
                                        <strong>Cuisine Region:</strong> ${recipe.CuisineRegion || 'Not specified'}
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">Meal & Diet Information</h5>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item">
                                        <strong>Meal Types:</strong>
                                        <div class="mt-1">${mealTypes}</div>
                                    </li>
                                    <li class="list-group-item">
                                        <strong>Diet Types:</strong> 
                                        ${recipe.Diet_Types ? recipe.Diet_Types.split(',').map(type => 
                                            `<span class="badge bg-primary me-1 mb-1">${type.trim()}</span>`
                                        ).join(' ') : 'Not specified'}
                                    </li>
                                    <li class="list-group-item">
                                        <strong>Healthy Types:</strong>
                                        <div class="mt-1">
                                            ${healthyTypesContent}
                                        </div>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Nutrition Facts</h5>
                            <div class="row">
                                <div class="col-md-4">
                                    <ul class="list-group list-group-flush">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Calories:</span>
                                            <span class="badge bg-secondary">${recipe.Calories || 'N/A'}</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Protein:</span>
                                            <span class="badge bg-secondary">${recipe.ProteinContent || 'N/A'}g</span>
                                        </li>
                                    </ul>
                                </div>
                                <div class="col-md-4">
                                    <ul class="list-group list-group-flush">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Carbohydrates:</span>
                                            <span class="badge bg-secondary">${recipe.CarbohydrateContent || 'N/A'}g</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Fat:</span>
                                            <span class="badge bg-secondary">${recipe.FatContent || 'N/A'}g</span>
                                        </li>
                                    </ul>
                                </div>
                                <div class="col-md-4">
                                    <ul class="list-group list-group-flush">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Cholesterol:</span>
                                            <span class="badge bg-secondary">${recipe.CholesterolContent || 'N/A'}mg</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Sugar:</span>
                                            <span class="badge bg-secondary">${recipe.SugarContent || 'N/A'}g</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <h4 class="mt-4">Ingredients</h4>
            <div class="row">
                <div class="col-md-6">
                    <h6>Recipe Ingredients</h6>
                    <ul class="list-group">
                        ${renderIngredientList(recipe.RecipeIngredientParts, ',')}
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>USDA Ingredients</h6>
                    <ul class="list-group">
                        ${renderIngredientList(recipe.BestUsdaIngredientName, ';')}
                    </ul>
                </div>
            </div>

            <h4 class="mt-4">Instructions</h4>
            <div class="instructions">
                ${recipe.RecipeInstructions ? recipe.RecipeInstructions.split('\n').map((step, index) => `
                    <div class="alert alert-light">
                        <strong>${index + 1}.</strong> ${step.trim()}
                    </div>
                `).join('') : '<div class="alert alert-light">No instructions available</div>'}
            </div>
        </div>
    `;

    detailsContainer.innerHTML = content;
    console.log("Recipe modal content set up. Displaying modal...");
    // Display the modal using Bootstrap
    const modal = new bootstrap.Modal(document.getElementById('recipe-modal'));
    modal.show();
}

// Show toast notification
function showToast(message, type = 'info') {
    console.log(`Showing toast notification: ${message}`);
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Create toast container
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Validate the select element's value
function validateSelect(select) {
    const isValid = select.value !== '';
    select.classList.toggle('is-invalid', !isValid);
    select.classList.toggle('is-valid', isValid);
}

// Initialize tooltips when the window loads
window.addEventListener('load', () => {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
