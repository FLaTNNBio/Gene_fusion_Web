// Controlla se il parametro 'refresh' è presente nell'URL
    var urlParams = new URLSearchParams(window.location.search);
    var refresh = urlParams.get('refresh');

    // Se 'refresh' è presente, ricarica la pagina
    if (refresh) {
        window.location.reload();
    }


    document.addEventListener('DOMContentLoaded', function () {


        // Funzione per ottenere la percentuale di completamento fusim dal server
        function getCompletionPercentage_fusim() {

            $.ajax({
                url: 'http://127.0.0.1:5000/get_completion_percentage_fusim',
                type: 'GET',
                dataType: 'json',
                success: function (response) {
                    console.log("Risposta dal server:", response);

                    if ('completion_percentage_fusim' in response) {

                        // Aggiorna la barra di caricamento o fai altre operazioni con i dati ricevuti
                        var completionPercentage = response.completion_percentage_fusim;
                        var estimated_time_elapsed = response.estimated_time_elapsed_fusim
                        updateProgressBar(completionPercentage, estimated_time_elapsed, 'progressBar_fusim');

                    } else {
                        console.error("La risposta non contiene la percentuale di completamento.");
                    }
                },
                error: function (xhr, status, error) {
                    // Gestisci gli errori qui
                    console.error("Errore durante la richiesta al server:", xhr, status, error);
                }
            });
        }
        // Funzione per ottenere la percentuale di completamento fusim dal server
        function getCompletionPercentage_genDataset() {

            $.ajax({
                url: 'http://127.0.0.1:5000/get_completion_percentage_genDataset',
                type: 'GET',
                dataType: 'json',
                success: function (response) {
                    console.log("Risposta dal server:", response);

                    if ('completion_percentage_genDataset' in response) {

                        // Aggiorna la barra di caricamento o fai altre operazioni con i dati ricevuti
                        var completionPercentage = response.completion_percentage_genDataset;
                        var estimated_time_elapsed = response.estimated_time_elapsed_genDataset
                        updateProgressBar(completionPercentage, estimated_time_elapsed, 'progressBar_genDataset');

                    } else {
                        console.error("La risposta non contiene la percentuale di completamento.");
                    }
                },
                error: function (xhr, status, error) {
                    // Gestisci gli errori qui
                    console.error("Errore durante la richiesta al server:", xhr, status, error);
                }
            });
        }
    // Funzione per aggiornare la barra di avanzamento
    function updateProgressBar(percentage, estimated_time_elapsed, progressBar_name) {

        var progressBar = document.getElementById(progressBar_name);
        progressBar.style.width = percentage + '%';
        progressBar.innerHTML = percentage + '%';

        // Aggiungi una classe 'complete' quando raggiungi il 100%
        if (percentage >= 100) {

            progressBar.classList.add('complete');

        } else {
            progressBar.classList.remove('complete');
        }

        // Aggiorna il tempo stimato
        var estimatedTimeElement
        if (progressBar_name === 'progressBar_fusim')
           estimatedTimeElement = document.getElementById('estimatedTime_fusim');
        else if(progressBar_name === 'progressBar_genDataset')
            estimatedTimeElement = document.getElementById('estimatedTime_genDataset');

        estimatedTimeElement.textContent = estimated_time_elapsed;
    }

        // Chiamare la funzione per ottenere la percentuale(fusim) dal server ogni 1 secondo
        setInterval(getCompletionPercentage_fusim, 10000);
         // Chiamare la funzione per ottenere la percentuale (genDataset) dal server ogni 1 secondo
        setInterval(getCompletionPercentage_genDataset, 10000);
    });

// Aggiungi l'evento di click al pulsante di annullamento
$("#buttonCancelExec").on("click", function () {

    // Chiamata AJAX per annullare l'esecuzione
    $.ajax({
        url: 'http://localhost:5000/request_cancellation',
        type: 'POST',
        success: function (response) {
            console.log(response);
            resetProgressBar()
            resetTimeEstimated()
        },
        error: function (xhr, status, error) {
            console.error("Errore durante la richiesta al server:", xhr, status, error);
        }
    });
});

// Funzione per impostare la progress bar a una percentuale specifica
function setProgressBar(percentage, progressBar_name) {

     var progressBar = document.getElementById(progressBar_name);
     progressBar.style.width = percentage + '%';
     progressBar.innerHTML = percentage + '%';
}

// Funzione per resettare la barra di avanzamento
function resetProgressBar() {

    setProgressBar(0, 'progressBar_fusim');  // Imposta il valore iniziale
    setProgressBar(0, 'progressBar_genDataset')
    isProgressValid = false;
}
function resetTimeEstimated(){
     estimatedTimeFusim = document.getElementById('estimatedTime_fusim');
     estimatedTimeGenDataset = document.getElementById('estimatedTime_genDataset');

     estimatedTimeFusim.textContent = "--:--";
     estimatedTimeGenDataset.textContent = "--:--";

}