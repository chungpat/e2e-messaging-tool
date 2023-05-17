var category;
// Function to fetch and display documents based on search and sort
 function fetchDocuments(searchValue, sortValue, passwordFilter, currentCategory) 
 {
    category = currentCategory;
    const url = `/documents?search=${searchValue}&sort=${sortValue}&password=${passwordFilter}&category=${currentCategory}`;
    fetch(url)
    .then(response => response.json())
    .then(data => {
        const documentList = document.getElementById('document-list');
        documentList.innerHTML = ''; // Clear the previous document list

        data.documents.forEach(async doc => {
        const documentItem = document.createElement('div');
        documentItem.classList.add('document-item');
        documentItem.dataset.date = doc.date;
        documentItem.innerHTML = `
            <h3 class="document-title">${doc.name}</h3>
            <p>Size: ${doc.size}mb</p>
            <p>Filetype: ${doc.filetype}</p>
            <p>Date Uploaded: ${doc.date}</p>
            <button onclick="promptForPasswordAndDownload('${doc.path}', '${doc.password}')">Download</button>
        `;
        documentList.appendChild(documentItem);
        });
    });
}
// Function to prompt for password and initiate download
function promptForPasswordAndDownload(documentPath, passwordProtected) {
    if (!passwordProtected) {
    downloadDocument(documentPath);
    } else {
    const password = prompt('Enter password:');
    if (password !== null) {
        const formData = new FormData();
        formData.append('document_path', documentPath);
        formData.append('password', password);

        fetch('/download', {
        method: 'POST',
        body: formData
        })
        .then(response => {
        if (response.ok) {
            response.blob().then(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = documentPath.split('/').pop();
            link.click();
            window.URL.revokeObjectURL(url);
            });
        } else {
            promptForPasswordAndDownload(documentPath, true);
        }
        });
    }
    }
}

function downloadDocument(documentPath) {
    const link = document.createElement('a');
    link.href = documentPath;
    link.download = documentPath.split('/').pop();
    link.click();
  }

// Event listener for search input
const searchInput = document.getElementById('search-input');
searchInput.addEventListener('input', (e) => {
    const searchValue = e.target.value.trim();
    const sortValue = document.getElementById('sort-select').value;
    fetchDocuments(searchValue, sortValue, '', category);
});

// Event listener for sort select
const sortSelect = document.getElementById('sort-select');
sortSelect.addEventListener('change', (e) => {
    const searchValue = document.getElementById('search-input').value.trim();
    const sortValue = e.target.value;
    fetchDocuments(searchValue, sortValue, '', category);
});

  // Event listener for password filter select
const passwordFilterSelect = document.getElementById('password-filter-select');
passwordFilterSelect.addEventListener('change', (e) => {
    const searchValue = document.getElementById('search-input').value.trim();
    const sortValue = document.getElementById('sort-select').value;
    const passwordFilter = e.target.value;
    fetchDocuments(searchValue, sortValue, passwordFilter, category);
});
