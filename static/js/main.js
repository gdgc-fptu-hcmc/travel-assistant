document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('travelForm');
    const resultsDiv = document.getElementById('results');
    const tripSummaryDiv = document.getElementById('tripSummary');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.querySelector('button');
    
    // Generate a unique session ID
    const sessionId = 'session_' + Date.now();

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

    function addMessage(role, content, agent = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // Add agent info if available
        if (agent) {
            const agentSpan = document.createElement('span');
            agentSpan.className = 'agent-info';
            agentSpan.textContent = `[${agent}]`;
            messageDiv.appendChild(agentSpan);
        }
        
        const contentSpan = document.createElement('span');
        contentSpan.className = 'message-content';
        contentSpan.textContent = content;
        messageDiv.appendChild(contentSpan);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage('user', message);
        userInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    session_id: sessionId
                })
            });

            const data = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator();

            if (data.status === 'success') {
                addMessage('assistant', data.content, data.agent);
            } else {
                addMessage('error', data.message || 'Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('error', 'Sorry, I encountered an error. Please try again.');
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Add welcome message
    addMessage('assistant', 'Hello! I can help you with flights, hotels, places to visit, weather, and food recommendations. What would you like to know?');
}); 