document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Script loaded");

    let botType = document.body.getAttribute("data-bot-type") || window.location.pathname.split("/").pop();
    console.log("Bot Type:", botType);

    // Get elements safely
    let sendButton = document.getElementById("send-btn");
    let inputField = document.getElementById("user-input");
    let micButton = document.getElementById("mic-btn");
    let chatBox = document.getElementById("chat-box");
    let stopButton = document.getElementById("stop-btn");
    let audioPlayback = null;

    // If any element is missing, log error and stop script
    if (!sendButton || !inputField || !micButton || !chatBox || !stopButton) {
        console.error("❌ Missing elements in chat.html. Check IDs.");
        return;
    }

    function showTypingIndicator() {
        let typingDiv = document.createElement("div");
        typingDiv.id = "typing-indicator";
        typingDiv.classList.add("chat-message", "bot-message");
        typingDiv.textContent = "Bot is typing...";
        chatBox.appendChild(typingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeTypingIndicator() {
        let typingDiv = document.getElementById("typing-indicator");
        if (typingDiv) typingDiv.remove();
    }

    function sendMessage() {
        let message = inputField.value.trim();
        if (!message) {
            console.log("⚠ Empty message. Not sending.");
            return;
        }

        console.log("📤 Sending message:", message);

        // Append user message to chat
        appendMessage("user", message);
        inputField.value = "";

        // Show typing indicator
        showTypingIndicator();

        // Send message to backend
        fetch("/chat_api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, botType: botType })
        })
        .then(response => response.json())
        .then(data => {
            console.log("✅ Received bot response:", data);
            removeTypingIndicator();
            appendMessage("bot", data.response);
            if (data.audio) {
                if (audioPlayback) {
                    audioPlayback.pause();
                    audioPlayback.currentTime = 0;
                }
                audioPlayback = new Audio(data.audio);
                audioPlayback.play();
            }
        })
        .catch(error => console.error("❌ Error sending message:", error));
    }

    function appendMessage(sender, text) {
        let messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", sender === "bot" ? "bot-message" : "user-message");
        messageDiv.textContent = text;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // ✅ Fix Send Button Not Working
    sendButton.addEventListener("click", sendMessage);

    // ✅ Fix Enter Key to Send Message
    inputField.addEventListener("keypress", function (event) {
        if (event.key === "Enter") sendMessage();
    });

    // ✅ Fix Mic Button Not Working
    micButton.addEventListener("click", function () {
        console.log("🎤 Mic button clicked. Starting speech recognition.");

        let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = "en-US";  // Change to "mr-IN" for Marathi

        recognition.onstart = function () {
            console.log("🎙 Speech recognition started...");
        };

        recognition.onresult = function (event) {
            let transcript = event.results[0][0].transcript;
            console.log("📝 Speech recognized:", transcript);
            inputField.value = transcript;
            sendMessage();
        };

        recognition.onerror = function (event) {
            console.error("❌ Speech recognition error:", event.error);
        };

        recognition.start();
    });

    // ✅ Stop Button to Cancel Speech Output
    stopButton.addEventListener("click", function () {
        if (audioPlayback) {
            audioPlayback.pause();
            audioPlayback.currentTime = 0;
            console.log("⏹ Speech playback stopped.");
        }
    });
});