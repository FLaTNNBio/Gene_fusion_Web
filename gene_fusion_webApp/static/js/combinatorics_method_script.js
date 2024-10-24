document.getElementById('executionType').addEventListener('change', function () {
            var selectedType = this.value;
            var combinatoricsSection = document.getElementById('combinatoricsUploadSection');
            var testFusionSection = document.getElementById('testFusionUploadSection');

            // Nascondi entrambe le sezioni per iniziare
            combinatoricsSection.style.display = 'none';
            testFusionSection.style.display = 'none';

            // Mostra la sezione corrispondente in base alla selezione
            if (selectedType === 'combinatorics') {
                combinatoricsSection.style.display = 'block';
            } else if (selectedType === 'testFusion') {
                testFusionSection.style.display = 'block';
            }
        });
document.addEventListener("DOMContentLoaded", function () {
    const chimericFileInput = document.getElementById("chimericFile");
    const nonChimericFileInput = document.getElementById("nonChimericFile");

    const chimericFileCombinatoricsInput= document.getElementById("chimericFileCombinatorics");
    const nonChimericFileCombinatoricsInput = document.getElementById("nonChimericFileCombinatorics");

    const testResultFile1Input = document.getElementById("testResultFile1");
    const testResultFile2Input = document.getElementById("testResultFile2");

    // Prendi i valori del range di soglia
    let thresholdMin = parseFloat(document.getElementById("thresholdMin").value);
    let thresholdMax = parseFloat(document.getElementById("thresholdMax").value);
    let thresholdStep = parseFloat(document.getElementById("thresholdStep").value);

    const command1Button = document.getElementById("command1");
    const command2Button = document.getElementById("command2");
    const command3Button = document.getElementById("command3");

    // Funzione per inviare i file al backend per la validazione
    function validateFiles() {

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
        }

        fetch("/validate_files", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Abilita/disabilita pulsanti in base ai file caricati
                if (executionType === "testFusion" && (chimericFile && nonChimericFile) ){
                    command1Button.disabled = false;
                    document.getElementById("fileOutput_testFusion").innerText = "Files are valid.";
                }
                if (executionType === "combinatorics" && (chimericFileCombinatorics && nonChimericFileCombinatorics && testResultFile1 && testResultFile2)) {
                    command2Button.disabled = false;
                    document.getElementById("fileOutput_combinatorics").innerText = "Files are valid.";
                }


            } else {
                command1Button.disabled = true;
                command2Button.disabled = true;
                command3Button.disabled = true;

                document.getElementById("fileOutput_combinatorics").innerText = data.message;
                document.getElementById("fileOutput_testFusion").innerText = data.message;
            }
        })
        .catch((error) => {
            console.error("Errore durante la validazione dei file:", error);
            document.getElementById("fileOutput_combinatorics").innerText = "Errore durante la validazione dei file.";
            document.getElementById("fileOutput_testFusion").innerText = "Errore durante la validazione dei file.";

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
    nonChimericFileCombinatoricsInput.addEventListener("change",validateFiles);
    testResultFile1Input.addEventListener("change", validateFiles);
    testResultFile2Input.addEventListener("change", validateFiles);

    // Funzione per inviare una richiesta al backend per eseguire il comando
    function sendCommandRequest(commandId) {
        const formData = new FormData();
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

        // Append file e parametri per l'esecuzione testFusion
        if (commandId === 1) { // Supponendo che 1 sia per testFusion
            if (chimericFile) formData.append("chimericFile", chimericFile);
            if (nonChimericFile) formData.append("nonChimericFile", nonChimericFile);
        }
        // Append file e parametri per l'esecuzione combinatorics
        if (commandId === 2) { // Supponendo che 2 sia per combinatorics
            if (chimericFileCombinatorics) formData.append("chimericFileCombinatorics", chimericFileCombinatorics);
            if (nonChimericFileCombinatorics) formData.append("nonChimericFileCombinatorics", nonChimericFileCombinatorics);
            if (testResultFile1) formData.append("testResultFile1", testResultFile1);
            if (testResultFile2) formData.append("testResultFile2", testResultFile2);
        }


        formData.append("thresholdMin", thresholdMin); // Assicurati di appendere i valori aggiornati
        formData.append("thresholdMax", thresholdMax);
        formData.append("thresholdStep", thresholdStep);

        // Nascondi il link di download all'inizio della richiesta
        let downloadLink = document.getElementById("downloadLink" + commandId);
        downloadLink.style.display = "none"; // Nascondi il link di download

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

                // Se è il comando 2, visualizza i fusion score
                if (commandId === 2) {
                    // Mostra i fusion scores
                    displayFusionScores(data.fusion_scores);
                }

            } else {
                alert("Errore durante l'esecuzione: " + data.error);
            }
            document.getElementById("command" + commandId).disabled = false;
        })
        .catch(error => {
            console.error("Errore:", error);
            alert("Si è verificato un errore durante la richiesta.");
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
