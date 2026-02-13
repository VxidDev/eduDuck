export async function GetFreeLimitUsage() {
    const FreeLimitBar = document.getElementById("FreeUsageText");
    if (!FreeLimitBar)
        return;
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
        FreeLimitBar.textContent = `${data.remaining} free uses remaining today.`;
    }
    catch (err) {
        FreeLimitBar.textContent = "Error loading usage";
        console.error(err);
    }
}
//# sourceMappingURL=GetFreeLimitUsage.js.map