import { GetFreeLimitUsage } from "/static/Components/GetFreeLimitUsage.js"
import { GetUserPFP } from "/static/Components/GetUserPFP.js"

( async () => {
    await GetFreeLimitUsage(); // Get Current Usage Info
    const url = await GetUserPFP(); // Get User PFP

    if (url) {
        document.getElementById('user-pfp').src = url;
    }
    
})();
