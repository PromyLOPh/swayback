self.addEventListener('install', function(event) {
	console.log ('installed service worker', event);
	self.skipWaiting();
});
/* load stuff through service worker immediately? XXX: only debugging? */
self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', function(event) {
	console.log ('fetch event', event.request.url, event);
	let url = new URL (event.request.url);
	url.protocol = 'https:';
	url.port = 443;
	url.hash = '';
	if (url.hostname.endsWith ('.swayback.localhost')) {
		url.hostname = url.hostname.slice (0, url.hostname.length-'.swayback.localhost'.length);
	}
	console.log ('orig url', url);
	let body = new FormData ();
	body.append ('url', url);
	body.append ('method', event.request.method);
	let req = new Request ('http://swayback.localhost:5000/raw', {method: 'POST', body: body});

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
