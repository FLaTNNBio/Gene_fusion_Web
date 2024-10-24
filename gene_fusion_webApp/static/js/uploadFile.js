// Funzione per adattare dinamicamente la tabella
function modifyTableDimension() {
    document.querySelector('.container-table').style.top = '50%';
}
function resetTableDimension() {
    document.querySelector('.container-table').style.top = '33%';
}

function showPanelButtons() {
    var buttonContainer = document.getElementById('buttonContainer');
    buttonContainer.style.display = 'flex';
}

function hidePanelButtons() {
    var buttonContainer = document.getElementById('buttonContainer');
    buttonContainer.style.display = 'none';
}
//---------------------------------------------------- GENES PANEL FUNCTIONS -----------------------------------------------------

document.getElementById('geneTable').addEventListener('click', function (event) {
    var targetRow = event.target.closest('tr');

      // Verifica se è stato premuto il pulsante sinistro del mouse durante il clic
    var isLeftMouseButton = event.button === 0;

    // Verifica se è stato premuto il tasto Ctrl (o Cmd su macOS) durante il clic
    var isCtrlPressed = event.ctrlKey || event.metaKey;

    // Verifica se è stato premuto il tasto Shift durante il clic
    var isShiftPressed = event.shiftKey;

    if (targetRow) {

        if (targetRow && isCtrlPressed) {
            // Evidenzia la riga selezionata
            row.classList.toggle('selected');
        }
        else if (isShiftPressed) {

            // Se è stato premuto il tasto Shift
            var rows = document.querySelectorAll('#geneTable tr');
            var currentIndex = Array.from(rows).indexOf(targetRow);

            // Seleziona tutte le righe tra l'ultima selezione e quella corrente
            for (var i = Math.min(currentIndex, lastIndex); i <= Math.max(currentIndex, lastIndex); i++) {
                rows[i].classList.add('selected');
            }
        } else if (isCtrlPressed) {
            // Evidenzia o rimuovi la selezione sulla riga con il tasto Ctrl
            targetRow.classList.toggle('selected');
        } else {
            // Evidenzia solo la riga cliccata se nessun tasto aggiuntivo è premuto
            var selectedRows = document.querySelectorAll('#geneTable tr.selected');
            for (var i = 0; i < selectedRows.length; i++) {
                selectedRows[i].classList.remove('selected');
            }
            targetRow.classList.add('selected');
        }
        // Memorizza l'indice dell'ultima riga selezionata
        lastIndex = Array.from(document.querySelectorAll('#geneTable tr')).indexOf(targetRow);

    }
});


function toggleRowSelection(row) {
    row.classList.toggle('selected');
}

// Ritorna le righe selezionate dalla tabella
function getSelectedRowsData() {
    var selectedRows = [];

    // Trova tutte le righe selezionate nella tabella
    var selectedRowsElements = document.querySelectorAll('#geneTable tbody tr.selected');

    // Itera su ogni riga selezionata e aggiungi i dati a selectedRows
    selectedRowsElements.forEach(function (row) {
        var rowData = {
            gene: row.querySelector('.geneName').textContent,
            ensg: row.querySelector('.ensgCode').textContent
        };

        selectedRows.push(rowData);
    });

    return selectedRows;
}

// Crea un pannello di geni personalizzato a partire dalle righe selezionate dalla tabella
function createCustomPanelFile() {
    var selectedData = getSelectedRowsData();

    if (selectedData.length > 0) {
        // Converti i dati in una stringa di testo
        var textData = selectedData.map(row => `${row.gene}|${row.ensg}`).join('\n');


        // Invia i dati al server
        fetch('/save-custom-panel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data: textData }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Errore durante il salvataggio del file.');
            }
            console.log('File salvato con successo.');
        })
        .catch(error => {
            console.error('Errore:', error.message);
        });
    } else {
        console.log('Nessuna riga selezionata.');
    }
}

function  populateTable(file_lines){
    lines = file_lines
    // Ottieni l'elemento del corpo della tabella
    var tbody = document.querySelector('#geneTable tbody');

    // Popola la tabella con le righe del file
    for (var j = 0; j < lines.length; j++) {
        var line = lines[j].trim();

        if (line !== '') {
            var [gene, ensg] = line.split('|');

            var row = tbody.insertRow();

            var cellIndex = row.insertCell(0); // Cella per l'indice
            var cellGene = row.insertCell(1);
            var cellEnsg = row.insertCell(2);

            cellIndex.textContent = j + 1; // L'indice parte da 1 invece che da 0
            cellIndex.classList.add('index-cell'); // Aggiungi la classe per stili aggiuntivi

            cellGene.textContent = gene;
            cellGene.classList.add('geneName', 'green-text'); // Aggiungi la classe per il colore verde

            cellEnsg.textContent = ensg;
            cellEnsg.classList.add('ensgCode', 'red-text'); // Aggiungi la classe per il colore rosso

            // Aggiungi l'evento di clic alla riga
            row.addEventListener('click', function () {
                toggleRowSelection(this);
            });
        }
    }
    modifyTableDimension()
    showPanelButtons()
    var tableContainer = document.getElementById('tableContainer');
    tableContainer.scrollTop = tableContainer.scrollHeight;
}

function resetPanel(){
   // Rimuovi il file caricato
    var fileInput = document.getElementById('fileInput');
    var fileName = document.getElementById('fileName');
    var selectedFileName = document.getElementById('selectedFileName');

    fileInput.value = ''; // Svuota il campo di input del file
    fileName.value = '';
    selectedFileName.value = '';

    // Rimuovi la selezione da tutte le righe
    var rows = document.querySelectorAll('#geneTable tbody tr');
    rows.forEach(function (row) {
        row.classList.remove('selected');
    });

    // Rimuovi le righe dalla tabella
    var tbody = document.querySelector('#geneTable tbody');
    tbody.innerHTML = '';

    resetTableDimension()
    hidePanelButtons()

    // Dopo il reset, aggiorna la pagina dopo 3 secondi (3000 millisecondi)
    setTimeout(function () {
        location.reload();
    });
}


//--------------------------------------------------------------------------------------------------------------------------------


// Controlla che il file sia corretto e contenga gen|Ensg
function validateFileContent(fileContent) {
    // Dividi il contenuto del file in righe
    var lines = fileContent.split('\n');

    // Elimina le righe vuote da lines
    lines = lines.filter(function (line) {
        return line.trim() !== '';
    });

    // Verifica il formato per ogni riga
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();

        // Utilizza una regular expression per verificare il formato desiderato
        var regex = /^[A-Za-z0-9]+\|ENSG[0-9]+\.[0-9]+$/
        if (!regex.test(line)) {
            return false;
        }
    }

    populateTable(lines);

    return true;
}

    function updateFileName(selectedFileName) {
        var fileInput = document.getElementById('fileInput');
        var selectedFileNameSpan = document.getElementById(selectedFileName);
        selectedFileNameSpan.innerText = fileInput.files[0].name;
    }

    function uploadFile(fileNameSpanId) {
        var formData = new FormData();
        var fileInput = document.getElementById('fileInput');
        var fileNameSpan = document.getElementById(fileNameSpanId);

        if (fileInput.files.length > 0) {
            var reader = new FileReader();

            reader.onload = function (event) {
                var fileContent = event.target.result;

                // Validazione del formato del file
                if (validateFileContent(fileContent)) {
                    formData.append('file', fileInput.files[0]);

                    fetch('/upload', {
                        method: 'POST',
                        body: formData
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Errore: ' + data.error);
                            } else if (data.success) {
                                alert('File caricato con successo');
                                fileNameSpan.innerText = 'Nome del file caricato: ' + fileInput.files[0].name;
                            }
                        })
                        .catch(error => {
                            console.error('Errore:', error);
                        });
                } else {
                    alert('Il formato del file non è valido. Assicurati che ogni riga abbia il formato NomeGene|ENSG+number.number');
                }
            };

            reader.readAsText(fileInput.files[0]);
        } else {
            alert('Seleziona un file prima di caricare.');
        }
    }