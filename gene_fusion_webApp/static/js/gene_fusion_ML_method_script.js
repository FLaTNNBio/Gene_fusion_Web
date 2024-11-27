// Funzione per mostrare la rotellina di caricamento
function showLoadingSpinner(spinnerId) {
    const spinner = document.getElementById(spinnerId);
    if (spinner) {
        spinner.style.display = 'block';  // Mostra lo spinner
    }
}

// Funzione per nascondere la rotellina di caricamento
function hideLoadingSpinner(spinnerId) {
    const spinner = document.getElementById(spinnerId);
    if (spinner) {
        spinner.style.display = 'none';  // Nascondi lo spinner
    }
}

document.getElementById('executionType').addEventListener('change', function () {
    var selectedType = this.value;
    var MML_experiment_section = document.getElementById('MML_experiment_section');
    var MGE_experiment_section= document.getElementById('MGE_experiment_section');


    // Nascondi entrambe le sezioni per iniziare
    MML_experiment_section.style.display = 'none';
    MGE_experiment_section.style.display = 'none';


    // Mostra la sezione corrispondente in base alla selezione
    if (selectedType === 'MML_experiment') {
        MML_experiment_section.style.display = 'block';
    } else if (selectedType === 'MGE_experiment') {
        MGE_experiment_section.style.display = 'block';
    }
});

document.addEventListener("DOMContentLoaded", function () {

    const MML_chimeric_fingerprint_input = document.getElementById("dataset_chimeric_fingerprint_file");
    const MML_non_chimeric_fingerprint_input = document.getElementById("dataset_non_chimeric_fingerprint_file");

    const MGE_chimeric_fingerprint_input = document.getElementById("dataset_chimeric_fingerprint_file");
    const MGE_non_chimeric_fingerprint_input = document.getElementById("dataset_non_chimeric_fingerprint_file");

    const command1Button = document.getElementById("command1");
    const command2Button = document.getElementById("command2");
    const command3Button = document.getElementById("command3");

    // Funzione per inviare i file al backend per la validazione
    function validateFiles_ML() {
        const executionType = document.getElementById("executionType").value;
        const formData = new FormData();

        // Aggiungi l'esecuzione al FormData
        formData.append("executionType", executionType);

        const MML_chimeric_fingerprint_file =  MML_chimeric_fingerprint_input.files[0]
        const MML_non_chimeric_fingerprint_file = MML_non_chimeric_fingerprint_input.files[0]

        const MGE_chimeric_fingerprint_file = MGE_chimeric_fingerprint_input.files[0]
        const MGE_non_chimeric_fingerprint_file = MGE_non_chimeric_fingerprint_input.files[0]

        // Aggiungi solo i file di Training Combinatorics Model
        if (executionType === "MLL_experiment" && MML_chimeric_fingerprint_file && MML_non_chimeric_fingerprint_file) {
            formData.append("MML_chimeric_fingerprint_file", MML_chimeric_fingerprint_file);
            formData.append("MML_non_chimeric_fingerprint_file", MML_non_chimeric_fingerprint_file);

        }else if(executionType === "MGE_experiment" && MGE_chimeric_fingerprint_file && MGE_non_chimeric_fingerprint_file){
            formData.append("MGE_chimeric_fingerprint_file", MGE_chimeric_fingerprint_file);
            formData.append("MGE_non_chimeric_fingerprint_file", MGE_non_chimeric_fingerprint_file);
        }

        // Validazione dei file di input
        fetch("/validate_files_ML", {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(data => {

                // Nascondi la rotellina di caricamento
                hideLoadingSpinner();

                document.getElementById("loadingSpinner_MML").style.display = "none";
                document.getElementById("loadingSpinner_MGE").style.display = "none";

                if (data.success) {
                    // Abilita/disabilita pulsanti in base ai file caricati
                    if (executionType === "MMl_experiment" &&  MML_chimeric_fingerprint_file && MML_non_chimeric_fingerprint_file) {
                        command1Button.disabled = false;
                        document.getElementById("fileOutput_MML").innerText = "Files are valid.";
                    }
                    if (executionType === "MGE_experiment" && MGE_chimeric_fingerprint_file && MGE_non_chimeric_fingerprint_file) {
                        command2Button.disabled = false;
                        document.getElementById("fileOutput_MGE").innerText = "Files are valid.";
                    }

                } else {
                    command1Button.disabled = true;
                    command2Button.disabled = true;

                    document.getElementById("fileOutput_MML").innerText = data.message;
                    document.getElementById("fileOutput_MGE").innerText = data.message;
                }
            })
            .catch((error) => {
                console.error("Errore durante la validazione dei file:", error);
                 document.getElementById("fileOutput_MML").innerText = "Errore durante la validazione dei file.";
                 document.getElementById("fileOutput_MGE").innerText = "Errore durante la validazione dei file.";
            });
    }

    // Event listener per validare i file al caricamento
    MML_chimeric_fingerprint_input.addEventListener("change", validateFiles_ML)
    MML_non_chimeric_fingerprint_input.addEventListener("change", validateFiles_ML)

    MGE_chimeric_fingerprint_input.addEventListener("change", validateFiles_ML)
    MGE_non_chimeric_fingerprint_input.addEventListener("change", validateFiles_ML)

    // Funzione per inviare una richiesta al backend per eseguire il comando
    function sendCommandRequest(commandId) {

        const formData = new FormData();
        formData.append("command", commandId);

        const MML_chimeric_fingerprint_file = MML_chimeric_fingerprint_input.files[0];
        const MML_non_chimeric_fingerprint_file = MML_non_chimeric_fingerprint_input.files[0];

        const MGE_chimeric_fingerprint_file = MGE_chimeric_fingerprint_input.files[0];
        const MGE_non_chimeric_fingerprint_file = MGE_non_chimeric_fingerprint_input.files[0];

        // Append file e parametri per l'esecuzione testFusion
        if (commandId === 1) { // Supponendo che 1 sia per testFusion
            if (MML_chimeric_fingerprint_file) formData.append("MML_chimeric_fingerprint_file",MML_chimeric_fingerprint_file)
            if (MML_non_chimeric_fingerprint_file) formData.append("MML_non_chimeric_fingerprint_file",MML_non_chimeric_fingerprint_file)
        }
        // Append file e parametri per l'esecuzione combinatorics
        if (commandId === 2) { // Supponendo che 2 sia per combinatorics
            if (MGE_chimeric_fingerprint_file) formData.append("MGE_chimeric_fingerprint_file",MGE_chimeric_fingerprint_file)
            if (MGE_non_chimeric_fingerprint_file) formData.append("MGE_non_chimeric_fingerprint_file",MGE_non_chimeric_fingerprint_file)
        }


        // Nascondi il link di download all'inizio della richiesta
        let downloadLink = document.getElementById("downloadLink" + commandId);
        downloadLink.style.display = "none"; // Nascondi il link di download

        // Mostra la rotellina di caricamento
        showLoadingSpinner('loadingSpinner_MML');
        showLoadingSpinner('loadingSpinner_MGE');


        // Effettua una richiesta al backend per eseguire il comando
        fetch(`/execute_command_ML/${commandId}`, {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(data => {

                if (data.success) {
                    downloadLink.href = data.download_url;
                    downloadLink.style.display = "block";  // Rendi visibile il link
                    if (commandId === 1) {
                        // Nasconde lo spinner di caricamento  testFusion
                        hideLoadingSpinner('loadingSpinner_MML');
                    }
                    // Se è il comando 2, visualizza i fusion score
                    if (commandId === 2) {
                        // Nasconde lo spinner di caricamento combinatorics
                        hideLoadingSpinner('loadingSpinner_MGE');
                    }

                } else {
                    alert("Errore durante l'esecuzione: " + data.error);
                }
                document.getElementById("command" + commandId).disabled = false;
            })
            .catch(error => {
                console.error("Errore:", error);
                alert("Si è verificato un errore durante la richiesta.");
                // Nascondi lo spinner anche in caso di errore
                if (commandId === 1) {
                    hideLoadingSpinner('loadingSpinner_MML');
                } else if (commandId === 2) {
                    hideLoadingSpinner('loadingSpinner_MGE');
                }

                document.getElementById("command" + commandId).disabled = false;
            });
    }

    // Aggiungi gli event listener ai pulsanti di comando
    command1Button.addEventListener("click", function () {
        sendCommandRequest(1);
    });

    command2Button.addEventListener("click", function () {
        sendCommandRequest(2);
    });

    command3Button.addEventListener("click", function () {
        sendCommandRequest(3);
    });

});