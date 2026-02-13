let Messages = [];
export function addMessage(role, content) {
    Messages.push({ role, content });
}
export function getHistory() {
    return Messages.slice(-10).map(m => `${m.role}: ${m.content}`).join("\n");
}
export function getMessages() {
    return Messages;
}
export function parseInitialChat(initialChatData) {
    if (initialChatData && initialChatData !== "" && initialChatData !== "null") {
        try {
            const parsedChat = JSON.parse(initialChatData);
            parsedChat.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
        }
        catch (err) {
            console.error("Failed to parse initial DuckAI chat:", err);
        }
    }
}
//# sourceMappingURL=chat.js.map