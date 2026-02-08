interface Message {
    role: string;
    content: string;
}

let Messages: Array<Message> = [];

export function addMessage(role: string, content: string): void {
    Messages.push({ role, content });
}

export function getHistory(): string {
    return Messages.slice(-10).map(m => `${m.role}: ${m.content}`).join("\n");
}

export function getMessages(): Array<Message> {
    return Messages;
}

export function parseInitialChat(initialChatData: string | undefined): void {
    if (initialChatData && initialChatData !== "" && initialChatData !== "null") {
        try {
            const parsedChat: Array<Message> = JSON.parse(initialChatData);
            parsedChat.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
        } catch (err) {
            console.error("Failed to parse initial DuckAI chat:", err);
        }
    }
}
