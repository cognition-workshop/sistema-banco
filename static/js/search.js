function initializeSearch() {
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase().trim();
        
        if (query.length < 2) {
            resetTableRows();
            return;
        }
        
        searchInTable(query);
    });
    
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            searchInput.value = '';
            resetTableRows();
            searchInput.blur();
        }
    });
}

function searchInTable(query) {
    const rows = document.querySelectorAll('tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(query)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    updateSearchResults(visibleCount);
}

function resetTableRows() {
    const rows = document.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.style.display = '';
    });
    
    const resultsMsg = document.getElementById('searchResults');
    if (resultsMsg) {
        resultsMsg.remove();
    }
}

function updateSearchResults(count) {
    let resultsMsg = document.getElementById('searchResults');
    
    if (!resultsMsg) {
        const table = document.querySelector('table');
        if (table) {
            resultsMsg = document.createElement('div');
            resultsMsg.id = 'searchResults';
            resultsMsg.className = 'bg-blue-50 border-l-4 border-blue-400 p-3 mb-4 text-sm';
            table.parentNode.insertBefore(resultsMsg, table);
        }
    }
    
    if (resultsMsg) {
        resultsMsg.innerHTML = `
            <i class="fas fa-search text-blue-600"></i>
            <span class="ml-2 text-blue-800">${count} resultado(s) encontrado(s)</span>
        `;
    }
}

document.addEventListener('DOMContentLoaded', initializeSearch);
