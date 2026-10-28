const csrfToken =
    document.querySelector(
        "[name=csrfmiddlewaretoken]"
    ).value;


// ==========================================
// CAMBIAR LED DESDE WEB
// ==========================================

async function cambiarLed(codigo) {

    const boton =
        document.getElementById(
            `boton-${codigo}`
        );


    const estadoActual =
        boton.dataset.estado.trim() === "1";


    const nuevoEstado =
        !estadoActual;


    boton.disabled = true;

    boton.textContent =
        "Enviando...";


    try {

        const respuesta = await fetch(
            `/api/led/${codigo}/`,
            {
                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json",

                    "X-CSRFToken":
                        csrfToken
                },

                body: JSON.stringify({
                    estado: nuevoEstado
                })
            }
        );


        const datos =
            await respuesta.json();


        if (!respuesta.ok || !datos.ok) {

            throw new Error(
                datos.error ||
                "No se pudo enviar el comando."
            );
        }


        /*
        No cambiamos directamente el estado visual.

        Esperamos a que Arduino confirme y después
        /api/estado/ nos entregue el estado real.
        */

        setTimeout(
            actualizarSistema,
            250
        );


    } catch (error) {

        console.error(error);

        alert(
            "No se pudo enviar el comando."
        );


        boton.disabled = false;

        actualizarSistema();
    }
}


// ==========================================
// OBTENER ESTADO DEL SISTEMA
// ==========================================

async function actualizarSistema() {

    try {

        const respuesta = await fetch(
            "/api/estado/",
            {
                cache: "no-store"
            }
        );


        if (!respuesta.ok) {

            throw new Error(
                "No se pudo consultar el sistema."
            );
        }


        const datos =
            await respuesta.json();


        actualizarLeds(
            datos.leds
        );


        actualizarHistorial(
            datos.eventos
        );


        actualizarResumen(
            datos.leds
        );


    } catch (error) {

        console.error(
            "Error actualizando dashboard:",
            error
        );
    }
}


// ==========================================
// ACTUALIZAR LEDS
// ==========================================

function actualizarLeds(leds) {

    leds.forEach(led => {

        const boton =
            document.getElementById(
                `boton-${led.codigo}`
            );


        const badge =
            document.getElementById(
                `badge-${led.codigo}`
            );


        const bombilla =
            document.getElementById(
                `bombilla-${led.codigo}`
            );


        if (
            !boton ||
            !badge ||
            !bombilla
        ) {

            return;
        }


        boton.dataset.estado =
            led.estado ? "1" : "0";


        boton.disabled = false;


        if (led.estado) {

            badge.textContent =
                "ENCENDIDO";

            badge.classList.add(
                "badge-on"
            );

            badge.classList.remove(
                "badge-off"
            );


            bombilla.classList.add(
                "bombilla-on"
            );


            boton.textContent =
                "Apagar";

            boton.classList.add(
                "boton-apagar"
            );

            boton.classList.remove(
                "boton-encender"
            );


        } else {

            badge.textContent =
                "APAGADO";

            badge.classList.add(
                "badge-off"
            );

            badge.classList.remove(
                "badge-on"
            );


            bombilla.classList.remove(
                "bombilla-on"
            );


            boton.textContent =
                "Encender";

            boton.classList.add(
                "boton-encender"
            );

            boton.classList.remove(
                "boton-apagar"
            );
        }

    });
}


// ==========================================
// HISTORIAL
// ==========================================

function actualizarHistorial(eventos) {

    const tbody =
        document.getElementById(
            "historial"
        );


    tbody.innerHTML = "";


    if (eventos.length === 0) {

        tbody.innerHTML = `
            <tr>
                <td colspan="4">
                    Todavía no existen eventos registrados.
                </td>
            </tr>
        `;

        return;
    }


    eventos.forEach(evento => {

        const fila =
            document.createElement(
                "tr"
            );


        const estadoClase =
            evento.estado
                ? "on"
                : "off";


        const estadoTexto =
            evento.estado
                ? "ENCENDIDO"
                : "APAGADO";


        const origen =
            evento.origen === "BOTON"
                ? "BOTÓN"
                : evento.origen;


        fila.innerHTML = `

            <td>
                ${evento.fecha}
            </td>

            <td>
                ${evento.led}
            </td>

            <td>

                <span
                    class="
                        estado-tabla
                        ${estadoClase}
                    "
                >

                    ${estadoTexto}

                </span>

            </td>

            <td>

                <span class="origen">

                    ${origen}

                </span>

            </td>
        `;


        tbody.appendChild(
            fila
        );
    });
}


// ==========================================
// RESUMEN
// ==========================================

function actualizarResumen(leds) {

    const total =
        leds.length;


    const encendidos =
        leds.filter(
            led => led.estado
        ).length;


    const apagados =
        total - encendidos;


    document.getElementById(
        "total-dispositivos"
    ).textContent =
        total;


    document.getElementById(
        "total-encendidos"
    ).textContent =
        encendidos;


    document.getElementById(
        "total-apagados"
    ).textContent =
        apagados;
}


// ==========================================
// ACTUALIZACIÓN AUTOMÁTICA
// ==========================================

actualizarSistema();


setInterval(
    actualizarSistema,
    1000
);