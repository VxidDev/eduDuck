export async function GetUserPFP() {
    try {
        if (!document.getElementById('profile-button')) return;
        
        const res = await fetch("/profile/user-pfp", { method: "GET" });

        const data = await res.json();

        if (data.url && !data.error) {
            return data.url;
        }

    } catch (err) { 
        console.error(err);
    }
     
    return null;
}