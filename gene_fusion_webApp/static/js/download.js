/*
$(document).ready(function(){
    // Qui effettui una richiesta AJAX al backend per ottenere il file
    $.ajax({
        url: 'http://127.0.0.1:5000/download_file',
        method: 'GET',
        success: function(response) {
        console.log("Risposta dal server:", response);

            if('data' in response) {
                // Dopo aver ricevuto il file dal backend, crei un oggetto Blob
                var blob = new Blob([data], {type: '.fastq'});

                // Generi un URL per il Blob
                var url = window.URL.createObjectURL(blob);

                // Imposti l'attributo href del link nascosto con l'URL creato
                $('#downloadLink').attr('href', url);

                // Imposti il nome del file (puoi estrarlo dalla risposta del backend)
                $('#downloadLink').attr('download', 'nome_del_file');

                // Simuli il click sul link per avviare il download automatico
                document.getElementById('downloadLink').click();

                // Rilasci l'URL creato dopo il download
                window.URL.revokeObjectURL(url);
            }
        },
        error: function(xhr, status, error) {
            // Gestione degli errori
            console.error(error);
        }
    });
});*/

document.addEventListener('DOMContentLoaded', function() {
    const downloadButton = document.getElementById('downloadButton');

    function checkFileStatus() {
        fetch('http://127.0.0.1:5000/check_status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ready') {
                    // Abilita il bottone di download
                    downloadButton.disabled = false;
                    downloadButton.classList.remove('btn-disabled');
                    downloadButton.classList.add('btn-enabled');

                     // Verifica se l'event listener è già presente per evitare duplicazioni
                    if (!downloadButton.classList.contains('click-enabled')) {
                        // Aggiungi una classe per segnare che l'evento click è stato aggiunto
                        downloadButton.classList.add('click-enabled');

                        // Aggiungi l'evento click al bottone di download
                        downloadButton.addEventListener('click', function downloadFile() {
                            fetch('http://127.0.0.1:5000/download_file')
                                .then(response => {
                                    if (!response.ok) {
                                        return response.json().then(error => { throw new Error(error.error); });
                                    }
                                    return response.blob();
                                })
                                .then(blob => {
                                    const url = window.URL.createObjectURL(blob);
                                    const a = document.createElement('a');
                                    a.style.display = 'none';
                                    a.href = url;
                                    a.download = 'files.zip'; // Nome del file da scaricare
                                    document.body.appendChild(a);
                                    a.click();
                                    window.URL.revokeObjectURL(url);
                                })
                                .catch(err => {
                                    console.error('Download failed:', err);
                                    alert('Download failed: ' + err.message);
                                });
                        });
                    }
                } else if (data.status === 'error') {
                    console.error('Error generating files:', data.message);
                    alert('Error generating files: ' + data.message);
                } else {
                    setTimeout(checkFileStatus, 10000);  // Controlla di nuovo tra 10 secondi
                }
            })
            .catch(err => {
                console.error('Error checking file status:', err);
                alert('Error checking file status: ' + err.message);
            });
    }

    // Controlla lo stato del file ogni 10 secondi
    setInterval(checkFileStatus, 10000);
});

document.addEventListener("DOMContentLoaded", function() {
    const validateButton = document.getElementById("validateFiles");

    // Funzione per eseguire il download automatico
    function triggerFileDownload(url) {
        const link = document.createElement('a');
        link.href = url;
        link.download = '';  // Lascia il nome del file come quello di origine
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Funzione per inviare i dati al backend e avviare il download
    validateButton.addEventListener("click", function() {
        // Simuliamo l'invio della lista di geni al backend
        const dataToSend = {
            data: "lista di geni..."
        };

        fetch("/save_custom_panel", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(dataToSend)
        })
        .then(response => response.json())
        .then(data => {
            if (data.download_url) {
                // Avvia il download automatico del file
                triggerFileDownload(data.download_url);
            } else {
                alert('Errore nel download del file');
            }
        })
        .catch(error => {
            console.error('Errore durante la validazione:', error);
        });
    });
});