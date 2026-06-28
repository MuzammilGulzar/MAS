let mediaRecorder;
let audioChunks = [];
let recordedBlob = null;
let isRecording = false;

async function toggleRecording() {

    const button = document.getElementById("recordButton");
    const status = document.getElementById("recordStatus");

    if (!isRecording) {

        try {

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            mediaRecorder = new MediaRecorder(stream);

            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

           mediaRecorder.onstop = async () => {

           recordedBlob = new Blob(audioChunks, {
               type: "audio/webm"
            });

            status.innerHTML = "⏳ Converting speech...";

            await submitVoiceAnswer();

            status.innerHTML = "✅ Voice submitted";
            };

            mediaRecorder.start();

            isRecording = true;

            button.innerHTML = "⏹ Stop";

            button.classList.remove("bg-red-600");
            button.classList.add("bg-yellow-500");

            status.innerHTML = "🎙 Recording...";

        } catch (err) {

            console.error(err);

            alert("Unable to access microphone.");
        }

    } else {

        mediaRecorder.stop();

        isRecording = false;

        button.innerHTML = "🎤 Record";

        button.classList.remove("bg-yellow-500");
        button.classList.add("bg-red-600");

    }

}

async function uploadRecording(sessionId) {

    if (!recordedBlob) {
        alert("Please record first.");
        return;
    }

    const formData = new FormData();

    formData.append("session_id", sessionId);

    formData.append(
        "audio",
        recordedBlob,
        "answer.webm"
    );

    const response = await fetch(
        "http://127.0.0.1:8000/interview/voice-answer",
        {
            method: "POST",
            body: formData
        }
    );

    return await response.json();
}