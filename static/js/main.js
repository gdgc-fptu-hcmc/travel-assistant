document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('travelForm');
    const resultsDiv = document.getElementById('results');
    const tripSummaryDiv = document.getElementById('tripSummary');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        submitButton.textContent = 'Planning...';
        submitButton.disabled = true;
        
        try {
            const formData = {
                departure_city: document.getElementById('departureCity').value,
                arrival_city: document.getElementById('arrivalCity').value,
                departure_date: document.getElementById('departureDate').value,
                return_date: document.getElementById('returnDate').value || null,
                budget: document.getElementById('budget').value || null,
                currency: document.getElementById('currency').value
            };
            
            const response = await fetch('/api/plan-trip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                displayResults(data);
            } else {
                throw new Error(data.message || 'Failed to plan trip');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            // Reset button state
            submitButton.textContent = originalButtonText;
            submitButton.disabled = false;
        }
    });
    
    function displayResults(data) {
        resultsDiv.style.display = 'block';
        
        // Create HTML for trip summary
        const summary = `
            <div class="table-responsive">
                <table class="table">
                    <tbody>
                        <tr>
                            <th>From:</th>
                            <td>${data.data.request.departure_city}</td>
                        </tr>
                        <tr>
                            <th>To:</th>
                            <td>${data.data.request.arrival_city}</td>
                        </tr>
                        <tr>
                            <th>Departure Date:</th>
                            <td>${data.data.request.departure_date}</td>
                        </tr>
                        ${data.data.request.return_date ? `
                        <tr>
                            <th>Return Date:</th>
                            <td>${data.data.request.return_date}</td>
                        </tr>
                        ` : ''}
                        <tr>
                            <th>Estimated Cost:</th>
                            <td>${data.data.currency} ${data.data.estimated_cost.toFixed(2)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        
        tripSummaryDiv.innerHTML = summary;
    }
}); 