export async function GetFreeLimitUsage(FreeLimitBar , SubmitBtn) {
    SubmitBtn.disabled = true;

    const request = await fetch("/get-usage" , {
        method: "GET",
		headers: { "Content-Type": "application/json" },
    });

    const data = await request.json();

    FreeLimitBar.textContent = `${data.timesUsed}/3 free used`;

    SubmitBtn.disabled = false;
}