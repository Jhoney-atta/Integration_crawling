document.getElementById("urlForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const urlInput = document.getElementById("blogUrl").value.trim();
    const resultMessage = document.getElementById("resultMessage");
    const extractedTextDiv = document.getElementById("extractedText");
    const downloadButton = document.getElementById("downloadButton");


    resultMessage.textContent = "Processing...";
    extractedTextDiv.textContent = ""; // Clear previous results
    downloadButton.style.display = "none"; // Hide the download button initially

    try {
        const response = await fetch("http://127.0.0.1:5000/extract_text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: urlInput })
        });

        if (!response.ok) {
            const error = await response.json();
            resultMessage.textContent = `Error: ${error.error}`;
            return;
        }

        const data = await response.json();

        if (data.error) {
            resultMessage.textContent = `Error: ${data.error}`;
        } else {
            resultMessage.textContent = "Text extracted successfully!";
            extractedTextDiv.textContent = data.text; // Display the extracted text
            downloadButton.style.display = "block"; // Show the download button

            const filename = `${data.filename}.txt`.replace(/[\\/:*?"<>|]/g, ""); // Sanitize the filename

            // Remove previous event listener to prevent duplicate triggers
            const newDownloadButton = downloadButton.cloneNode(true);
            downloadButton.parentNode.replaceChild(newDownloadButton, downloadButton);
            
            // Add click event listener to download the file
            newDownloadButton.addEventListener("click", function () {
                const blob = new Blob([data.text], { type: "text/plain" });
                const downloadLink = document.createElement("a");
                downloadLink.href = URL.createObjectURL(blob);
                downloadLink.download = filename;
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                URL.revokeObjectURL(downloadLink.href); // Free up memory
            });
            
        }
    } catch (err) {
        resultMessage.textContent = `Error: ${err.message}`;
    }
});
document.addEventListener("keydown", function (event) {
    // Detect Ctrl+A
    if (event.ctrlKey && event.key === "a") {
        const activeElement = document.activeElement; // Focused element

        // Allow default behavior for the input box
        if (activeElement && activeElement.tagName === "INPUT" && activeElement.id === "blogUrl") {
            return; // Allow browser's default Ctrl+A for the input box
        }

        // Custom Ctrl+A behavior for the text content box
        const extractedTextDiv = document.getElementById("extractedText");
        if (extractedTextDiv && extractedTextDiv.textContent.trim().length > 0) {
            event.preventDefault(); // Prevent default Ctrl+A behavior for the entire page

            // Create a range and select the content of the text box
            const range = document.createRange();
            range.selectNodeContents(extractedTextDiv);

            // Remove any existing selections
            const selection = window.getSelection();
            selection.removeAllRanges();

            // Add the new range to the selection
            selection.addRange(range);
        }
    }
});
