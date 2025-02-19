document.querySelector('form').addEventListener('submit', function (e) {
    e.preventDefault();
    const zona = document.getElementById('zona').value;
    const metriQuadri = document.getElementById('metri-quadri').value;
    const guadagnoStimato = metriQuadri * 10; // Example calculation
    alert(`Guadagno stimato per la zona ${zona}: €${guadagnoStimato}/mese`);
});