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
    var combinatoricsSection = document.getElementById('combinatoricsUploadSection');
    var testFusionSection = document.getElementById('testFusionUploadSection');
    var trainingCombinatoricsModel_section = document.getElementById('trainingCombinatoricsModel_section');

    // Nascondi entrambe le sezioni per iniziare
    combinatoricsSection.style.display = 'none';
    testFusionSection.style.display = 'none';
    trainingCombinatoricsModel_section.style.display = 'none';


    // Mostra la sezione corrispondente in base alla selezione
    if (selectedType === 'combinatorics') {
        combinatoricsSection.style.display = 'block';
    } else if (selectedType === 'testFusion') {
        testFusionSection.style.display = 'block';
    } else if (selectedType === 'trainingCombinatoricsModel') {
        trainingCombinatoricsModel_section.style.display = 'block';
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const chimericFileInput = document.getElementById("chimericFile");
    const nonChimericFileInput = document.getElementById("nonChimericFile");

    const chimericFileCombinatoricsInput = document.getElementById("chimericFileCombinatorics");
    const nonChimericFileCombinatoricsInput = document.getElementById("nonChimericFileCombinatorics");

    const testResultFile1Input = document.getElementById("testResultFile1");
    const testResultFile2Input = document.getElementById("testResultFile2");

    const custom_panelInput = document.getElementById("custom_panelFile");

    // Prendi i valori del range di soglia
    let thresholdMin = parseFloat(document.getElementById("thresholdMin").value);
    let thresholdMax = parseFloat(document.getElementById("thresholdMax").value);
    let thresholdStep = parseFloat(document.getElementById("thresholdStep").value);

    const command1Button = document.getElementById("command1");
    const command2Button = document.getElementById("command2");
    const command3Button = document.getElementById("command3");


    // Funzione per inviare i file al backend per la validazione
    function validateFiles() {
        showLoadingSpinner(); // Mostra la rotellina di caricamento
        const executionType = document.getElementById("executionType").value;
        const formData = new FormData();

        // Aggiungi l'esecuzione al FormData
        formData.append("executionType", executionType); // Aggiunto qui


        const chimericFile = chimericFileInput.files[0];
        const nonChimericFile = nonChimericFileInput.files[0];
        const chimericFileCombinatorics = chimericFileCombinatoricsInput.files[0];
        const nonChimericFileCombinatorics = nonChimericFileCombinatoricsInput.files[0];
        const testResultFile1 = testResultFile1Input.files[0];
        const testResultFile2 = testResultFile2Input.files[0];
        const custom_panelFile = custom_panelInput.files[0];


        if (executionType === "combinatorics") {
            // Aggiungi solo i file di Combinatorics Analysis
            if (chimericFileCombinatorics) formData.append("chimericFileCombinatorics", chimericFileCombinatorics);
            if (nonChimericFileCombinatorics) formData.append("nonChimericFileCombinatorics", nonChimericFileCombinatorics);
            if (testResultFile1) formData.append("testResultFile1", testResultFile1);
            if (testResultFile2) formData.append("testResultFile2", testResultFile2);
            if (thresholdMin) formData.append("thresholdMin", thresholdMin);
            if (thresholdMax) formData.append("thresholdMax", thresholdMax);
            if (thresholdStep) formData.append("thresholdStep", thresholdStep);
        } else if (executionType === "testFusion") {
            // Aggiungi solo i file di Test Fusion
            if (chimericFile) formData.append("chimericFile", chimericFile);
            if (nonChimericFile) formData.append("nonChimericFile", nonChimericFile);
        } else if (executionType === "trainingCombinatoricsModel") {
            // Aggiungi solo i file di Training Combinatorics Model
            if (custom_panelFile) formData.append("custom_panelFile", custom_panelFile);
        }


        // Validazione dei file di input
        fetch("/validate_files", {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                // Nascondi la rotellina di caricamento
                hideLoadingSpinner();

                document.getElementById("loadingSpinner_testFusion").style.display = "none";
                document.getElementById("loadingSpinner_combinatorics").style.display = "none";
                document.getElementById("loadingSpinner_trainingModel").style.display = "none";

                if (data.success) {
                    // Abilita/disabilita pulsanti in base ai file caricati
                    if (executionType === "testFusion" && (chimericFile && nonChimericFile)) {
                        command1Button.disabled = false;
                        document.getElementById("fileOutput_testFusion").innerText = "Files are valid.";
                    }
                    if (executionType === "combinatorics" && (chimericFileCombinatorics && nonChimericFileCombinatorics && testResultFile1 && testResultFile2)) {
                        command2Button.disabled = false;
                        document.getElementById("fileOutput_combinatorics").innerText = "Files are valid.";
                    }
                    if (executionType === "trainingCombinatoricsModel") {
                        command3Button.disabled = false;
                        document.getElementById("fileOutput_combinatoricsModel").innerText = "Files are valid.";
                    }

                } else {
                    command1Button.disabled = true;
                    command2Button.disabled = true;
                    command3Button.disabled = true;

                    document.getElementById("fileOutput_combinatorics").innerText = data.message;
                    document.getElementById("fileOutput_testFusion").innerText = data.message;
                    document.getElementById("fileOutput_combinatoricsModel").innerText = data.message;
                }
            })
            .catch((error) => {
                console.error("Errore durante la validazione dei file:", error);
                document.getElementById("fileOutput_combinatorics").innerText = "Errore durante la validazione dei file.";
                document.getElementById("fileOutput_testFusion").innerText = "Errore durante la validazione dei file.";
                document.getElementById("fileOutput_combinatoricsModel").innerText = "Errore durante la validazione dei file.";

            });
    }
    // Funzione per visualizzare i fusion score nel frontend
    function displayFusionScores(fusionScores) {
        fusionScoresOutput.innerHTML = ''; // Pulisci il contenuto precedente

        Object.keys(fusionScores).forEach(method => {
            const scoreElement = document.createElement('p');
            const scoreData = fusionScores[method];
            if (scoreData.fusion_score !== null) {
                scoreElement.textContent = `${scoreData.name}: ${scoreData.fusion_score.toFixed(2)}%`;
            } else {
                scoreElement.textContent = `${scoreData.name}: No data available`;
            }
            fusionScoresOutput.appendChild(scoreElement);
        });
    }


    // Event listeners per validare i file al caricamento
    chimericFileInput.addEventListener("change", validateFiles);
    nonChimericFileInput.addEventListener("change", validateFiles);
    chimericFileCombinatoricsInput.addEventListener("change", validateFiles);
    nonChimericFileCombinatoricsInput.addEventListener("change", validateFiles);
    testResultFile1Input.addEventListener("change", validateFiles);
    testResultFile2Input.addEventListener("change", validateFiles);
    custom_panelInput.addEventListener("change", validateFiles);

    // Funzione per inviare una richiesta al backend per eseguire il comando
    function sendCommandRequest(commandId) {
        const formData = new FormData();

        const selectModel = document.getElementById('SelectModel');  // Dropdown dei modelli
        const selectedModel = selectModel.value;


        formData.append("command", commandId);

        // Leggi i valori del range di soglia qui
        let thresholdMin = parseFloat(document.getElementById("thresholdMin").value);
        let thresholdMax = parseFloat(document.getElementById("thresholdMax").value);
        let thresholdStep = parseFloat(document.getElementById("thresholdStep").value);

        const chimericFile = chimericFileInput.files[0];
        const nonChimericFile = nonChimericFileInput.files[0];
        const chimericFileCombinatorics = chimericFileCombinatoricsInput.files[0];
        const nonChimericFileCombinatorics = nonChimericFileCombinatoricsInput.files[0];
        const testResultFile1 = testResultFile1Input.files[0];
        const testResultFile2 = testResultFile2Input.files[0];
        const custom_panelFile = custom_panelInput.files[0];


        // Append file e parametri per l'esecuzione testFusion
        if (commandId === 1) { // Supponendo che 1 sia per testFusion
            if (!selectedModel) {
                alert("Seleziona un modello prima di eseguire il comando.");
                return;
            }
            formData.append("model", selectedModel);  // Aggiunge il modello selezionato

            if (chimericFile) formData.append("chimericFile", chimericFile);
            if (nonChimericFile) formData.append("nonChimericFile", nonChimericFile);
        }
        // Append file e parametri per l'esecuzione combinatorics
        if (commandId === 2) { // Supponendo che 2 sia per combinatorics
            if (!selectedModel) {
                alert("Seleziona un modello prima di eseguire il comando.");
                return;
            }
            formData.append("model", selectedModel);  // Aggiunge il modello selezionato
            if (chimericFileCombinatorics) formData.append("chimericFileCombinatorics", chimericFileCombinatorics);
            if (nonChimericFileCombinatorics) formData.append("nonChimericFileCombinatorics", nonChimericFileCombinatorics);
            if (testResultFile1) formData.append("testResultFile1", testResultFile1);
            if (testResultFile2) formData.append("testResultFile2", testResultFile2);
        }
        if (commandId === 3){
            if (custom_panelFile) formData.append("custom_panelFile",custom_panelFile)
        }

        formData.append("thresholdMin", thresholdMin); // Assicurati di appendere i valori aggiornati
        formData.append("thresholdMax", thresholdMax);
        formData.append("thresholdStep", thresholdStep);

        // Nascondi il link di download all'inizio della richiesta
        let downloadLink = document.getElementById("downloadLink" + commandId);
        downloadLink.style.display = "none"; // Nascondi il link di download

        // Mostra la rotellina di caricamento
        showLoadingSpinner('loadingSpinner_testFusion');
        showLoadingSpinner('loadingSpinner_combinatorics');
        showLoadingSpinner('loadingSpinner_trainingModel');

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
                        hideLoadingSpinner('loadingSpinner_testFusion');
                    }
                    // Se è il comando 2, visualizza i fusion score
                    if (commandId === 2) {
                        // Nasconde lo spinner di caricamento combinatorics
                        hideLoadingSpinner('loadingSpinner_combinatorics');
                        // Mostra i fusion scores
                        displayFusionScores(data.fusion_scores);
                    }
                    if (commandId === 3){
                        showLoadingSpinner('loadingSpinner_trainingModel');
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
                    hideLoadingSpinner('loadingSpinner_testFusion');
                } else if (commandId === 2) {
                    hideLoadingSpinner('loadingSpinner_combinatorics');
                } else if (commandId === 3) {
                    showLoadingSpinner('loadingSpinner_trainingModel');
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

//Eventi per la selezione del modello
document.addEventListener('DOMContentLoaded', function () {
    // Popola il dropdown con i file
   fetch('/get_models')
    .then(response => response.json())
    .then(files => {
        const selectModel = document.getElementById('SelectModel');
        const selectModelDelete = document.getElementById('SelectModelDelete');

        // Svuota le tendine prima di popolarle (opzionale)
        selectModel.innerHTML = '';
        selectModelDelete.innerHTML = '';

        files.forEach(file => {
            // Crea un'opzione per la prima tendina
            const option1 = document.createElement('option');
            option1.value = file;
            option1.textContent = file;
            selectModel.appendChild(option1);

            // Crea un'opzione separata per la seconda tendina
            const option2 = document.createElement('option');
            option2.value = file;
            option2.textContent = file;
            selectModelDelete.appendChild(option2);
        });
    });
    // Elimina il file selezionato
    document.getElementById('deleteButton').addEventListener('click', function () {
        const selectedFile = document.getElementById('SelectModelDelete').value;
        if (selectedFile) {
            fetch('/delete_model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename: selectedFile })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message || data.error);
                location.reload(); // Ricarica la pagina per aggiornare la lista
            });
        } else {
            alert("Please select a model to delete.");
        }
    });
});