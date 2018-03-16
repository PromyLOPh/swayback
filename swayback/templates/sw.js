/* script config, dynamically generated */
const baseHost = "{{ baseHost }}";
const baseDomain = baseHost.split (':', 1)[0];

self.addEventListener('install', function(event) {
	console.log ('installed service worker', event);
	self.skipWaiting();
});
/* load stuff through service worker immediately? XXX: only debugging? */
self.addEventListener('activate', async function() {
    if (self.registration.navigationPreload) {
      // Enable navigation preloads!
      await self.registration.navigationPreload.enable();
    } /*event => {
  event.waitUntil(clients.claim());*/
});

self.addEventListener('fetch', function(event) {
	let origreq = event.request;
	console.log ('fetch event', origreq.url, event);
	let url = new URL (origreq.url);
	url.protocol = 'https:';
	url.port = 443;
	url.hash = '';
	if (url.hostname.endsWith ('.' + baseDomain)) {
		url.hostname = url.hostname.slice (0, url.hostname.length-('.'+baseDomain).length);
	}
	console.log ('orig url', url);
	/* should contain everything we cannot use in the actual request (i.e. url and method) */
	let body = {
		'url': url.href,
		'method': origreq.method,
		};
	let headers = {
		'Content-Type': 'application/json',
		};
	/* add a few well-known request headers */
	let origheaders = origreq.headers;
	if (origheaders.has ('accept')) {
		headers['Accept'] = origreq.headers.get ('accept');
	}
	console.log ('sending', body, headers);
	let req = new Request ('http://' + baseHost + '/raw',
			{method: 'POST', body: JSON.stringify (body), headers: headers,
			mode: 'cors'});

	event.respondWith (
		fetch(req)
		.then(function (response) {
			// response may be used only once
			// we need to save clone to put one copy in cache
			// and serve second one
			let responseClone = response.clone();
			console.log ('got resp', responseClone);
			return response;
		})
		.catch (function () {
			console.log ('nope');
		})
	);
});
