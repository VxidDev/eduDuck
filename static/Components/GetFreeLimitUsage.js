export async function GetFreeLimitUsage() {
    const FreeLimitBar = document.getElementById("FreeUsageText");

    if (!FreeLimitBar) return;

    try {
        const request = await fetch("/get-usage", {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!request.ok) {
            FreeLimitBar.textContent = "Login to see usage";
            return;
        }

        const data = await request.json();
        FreeLimitBar.textContent = `Welcome, ${window.CURRENT_USERNAME}! You have ${data.remaining} free uses today.`;

    } catch (err) {
        FreeLimitBar.textContent = "Error loading usage";
        console.error(err);
    }
}
