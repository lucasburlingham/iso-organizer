document.onload = function () {

	async function fetchAsync() {
		const response = await fetch('http://localhost:8080/files');
		return await response.json();
	}

	let files = fetchAsync();
	files.then(data => {
		files.forEach(element => {
			let file = document.createElement('li');
			file.innerHTML = element;
			document.getElementById('files').appendChild(file);
		});
	});
}