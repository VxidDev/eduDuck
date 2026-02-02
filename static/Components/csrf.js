const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

const originalFetch = window.fetch;

window.fetch = function (url, options) {
    if (options && ['POST', 'PUT', 'DELETE'].includes(options.method?.toUpperCase())) {
        if (!options.headers) {
            options.headers = {};
        }
        options.headers['X-CSRF-Token'] = csrfToken;
    }
    return originalFetch(url, options);
};

const originalXhrOpen = XMLHttpRequest.prototype.open;
const originalXhrSend = XMLHttpRequest.prototype.send;

XMLHttpRequest.prototype.open = function (method, url, async, user, password) {
    this._method = method;
    return originalXhrOpen.apply(this, arguments);
};

XMLHttpRequest.prototype.send = function (data) {
    if (this._method && ['POST', 'PUT', 'DELETE'].includes(this._method.toUpperCase())) {
        this.setRequestHeader('X-CSRF-Token', csrfToken);
    }
    return originalXhrSend.apply(this, arguments);
};
