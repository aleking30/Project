document.getElementById("formulario").addEventListener("submit", function (event) {
    // Validar que todas las preguntas estén contestadas
    var preguntas = ["p1", "p2", "p3", "p4", "p5"];
    for (var i = 0; i < preguntas.length; i++) {
        var pregunta = preguntas[i];
        var opciones = document.getElementsByName(pregunta);
        var respondida = false;
        for (var j = 0; j < opciones.length; j++) {
            if (opciones[j].checked || opciones[j].value !== "") {
                respondida = true;
                break;
            }
        }
        if (!respondida) {
            event.preventDefault(); // Detener el envío del formulario
            alert("Por favor, responde todas las preguntas antes de enviar el formulario.");
            return;
        }
    }
});