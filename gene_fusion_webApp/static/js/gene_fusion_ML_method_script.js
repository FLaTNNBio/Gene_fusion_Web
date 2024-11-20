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
    var dnaBert_section = document.getElementById('dnaBert_section');
    var graphTool_section= document.getElementById('graphTool_section');
    var hypergraphTool_section = document.getElementById('hypergraphTool_section');

    // Nascondi entrambe le sezioni per iniziare
    dnaBert_section.style.display = 'none';
    graphTool_section.style.display = 'none';
    hypergraphTool_section.style.display = 'none';


    // Mostra la sezione corrispondente in base alla selezione
    if (selectedType === 'dnaBert') {
        dnaBert_section.style.display = 'block';
    } else if (selectedType === 'graphTool') {
        graphTool_section.style.display = 'block';
    } else if (selectedType === 'hypergraphTool') {
        hypergraphTool_section.style.display = 'block';
    }
});

document.addEventListener("DOMContentLoaded", function () {

    const custom_panelInput = document.getElementById("custom_panelFile");

    const command1Button = document.getElementById("command1");
    const command2Button = document.getElementById("command2");
    const command3Button = document.getElementById("command3");

    // Funzione per inviare i file al backend per la validazione
    function validateFiles() {
        const executionType = document.getElementById("executionType").value;
        const formData = new FormData();

        // Aggiungi l'esecuzione al FormData
        formData.append("executionType", executionType);

        const custom_panelFile = custom_panelInput.files[0];

        // Aggiungi solo i file di Training Combinatorics Model
        if (executionType === "dnaBert" && custom_panelFile) {
            formData.append("custom_panelFile", custom_panelFile);
        }else if(executionType === "graphTool" && custom_panelFile){
            formData.append("custom_panelFile", custom_panelFile);
        }else if(executionType === "hypergraphTool" && custom_panelFile){
            formData.append("custom_panelFile", custom_panelFile);
        }

        // Validazione dei file di input
        fetch("/validate_files", {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Abilita/disabilita pulsanti in base ai file caricati
                    if (executionType === "dnaBert" && custom_panelFile) {
                        command1Button.disabled = false;
                        document.getElementById("fileOutput_dnaBert").innerText = "Files are valid.";
                    }
                    if (executionType === "graphTool" && custom_panelFile) {
                        command2Button.disabled = false;
                        document.getElementById("fileOutput_graphTool").innerText = "Files are valid.";
                    }
                    if (executionType === "hypergraphTool" && custom_panelFile) {
                        command3Button.disabled = false;
                        document.getElementById("fileOutput_hypergraphTool").innerText = "Files are valid.";
                    }

                } else {
                    command1Button.disabled = true;
                    command2Button.disabled = true;
                    command3Button.disabled = true;

                    document.getElementById("fileOutput_dnaBert").innerText = data.message;
                    document.getElementById("fileOutput_graphTool").innerText = data.message;
                    document.getElementById("fileOutput_hypergraphTool").innerText = data.message;
                }
            })
            .catch((error) => {
                console.error("Errore durante la validazione dei file:", error);
                 document.getElementById("fileOutput_dnaBert").innerText = "Errore durante la validazione dei file.";
                 document.getElementById("fileOutput_graphTool").innerText = "Errore durante la validazione dei file.";
                 document.getElementById("fileOutput_hypergraphTool").innerText = "Errore durante la validazione dei file.";
            });
    }

    // Event listener per validare i file al caricamento
    custom_panelInput.addEventListener("change", validateFiles);

    // Funzione per inviare una richiesta al backend per eseguire il comando
    function sendCommandRequest(commandId) {
        const formData = new FormData();
        formData.append("command", commandId);


        const custom_panelFile = custom_panelInput.files[0];

        // Append file e parametri per l'esecuzione testFusion
        if (commandId === 1) { // Supponendo che 1 sia per testFusion
            if (custom_panelFile) formData.append("custom_panelFile",custom_panelFile)
        }
        // Append file e parametri per l'esecuzione combinatorics
        if (commandId === 2) { // Supponendo che 2 sia per combinatorics
            if (custom_panelFile) formData.append("custom_panelFile",custom_panelFile)
        }
        if (commandId === 3){
            if (custom_panelFile) formData.append("custom_panelFile",custom_panelFile)
        }


        // Nascondi il link di download all'inizio della richiesta
        let downloadLink = document.getElementById("downloadLink" + commandId);
        downloadLink.style.display = "none"; // Nascondi il link di download

        // Mostra la rotellina di caricamento
        showLoadingSpinner('loadingSpinner_bert');
        showLoadingSpinner('loadingSpinner_graph');
        showLoadingSpinner('loadingSpinner_hypergraph');

        // Effettua una richiesta al backend per eseguire il comando
        fetch(`/execute_command/${commandId}`, {
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
                        hideLoadingSpinner('loadingSpinner_bert');
                    }
                    // Se è il comando 2, visualizza i fusion score
                    if (commandId === 2) {
                        // Nasconde lo spinner di caricamento combinatorics
                        hideLoadingSpinner('loadingSpinner_graph');
                        // Mostra i fusion scores
                        displayFusionScores(data.fusion_scores);
                    }
                    if (commandId === 3){
                        showLoadingSpinner('loadingSpinner_hypergraph');
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
                    hideLoadingSpinner('loadingSpinner_bert');
                } else if (commandId === 2) {
                    hideLoadingSpinner('loadingSpinner_graph');
                } else if (commandId === 3) {
                    showLoadingSpinner('loadingSpinner_hypergraph');
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