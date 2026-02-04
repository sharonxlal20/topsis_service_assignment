document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault(); // Stop page reload

    const messageBox = document.getElementById('messageBox');
    const submitBtn = document.getElementById('submitBtn');
    
    // Clear previous messages
    messageBox.className = 'message-box hidden';
    messageBox.innerText = '';

    // Gather Data
    const fileInput = document.getElementById('csvFile').files[0];
    const weights = document.getElementById('weights').value;
    const impacts = document.getElementById('impacts').value;
    const email = document.getElementById('email').value;

    // Basic Validation logic (HTML5 handles most, but we double check impacts)
    if (!validateImpacts(impacts)) {
        showMessage("Impacts must only contain '+' or '-' separated by commas.", "error");
        return;
    }

    // Create FormData object to send file + text data
    const formData = new FormData();
    formData.append('file', fileInput);
    formData.append('weights', weights);
    formData.append('impacts', impacts);
    formData.append('email', email);

    // UX: Disable button while loading
    submitBtn.disabled = true;
    submitBtn.innerText = "Processing...";

    try {
        // Inside script.js
        const response = await fetch('/upload', { 
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) throw new Error(result.message || "Server Error");
        showMessage(result.message, "success");

    } catch (error) {
        showMessage("Error: " + error.message, "error");
    } finally {
        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.innerText = "Submit Data";
    }
});

// Helper: Custom validation for Impacts (ensures only +, -, and , are present)
function validateImpacts(str) {
    // Removes whitespace and checks pattern
    const cleanStr = str.replace(/\s/g, ''); 
    // Regex: Start with + or -, followed by 0 or more groups of comma and + or -
    const regex = /^[+-](,[+-])*$/;
    return regex.test(cleanStr);
}

// Helper: Display message
function showMessage(msg, type) {
    const box = document.getElementById('messageBox');
    box.innerText = msg;
    box.className = `message-box ${type}`; // Apply 'error' or 'success' class
    box.classList.remove('hidden');
}