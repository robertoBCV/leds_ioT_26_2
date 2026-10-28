
import json

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Led, EventoLed, ComandoLed


def dashboard(request):
    leds = Led.objects.all().order_by("id")

    eventos = (
        EventoLed.objects
        .select_related("led")
        .all()[:20]
    )

    return render(
        request,
        "control/dashboard.html",
        {
            "leds": leds,
            "eventos": eventos,
        }
    )


def estado_sistema(request):
    leds = Led.objects.all().order_by("id")
    datos_leds = []
    for led in leds:
        datos_leds.append({
            "codigo": led.codigo,
            "nombre": led.nombre,
            "pin": led.pin,
            "color": led.color,
            "color_hex": led.color_hex,
            "estado": led.estado_actual,
        })

    eventos = (
        EventoLed.objects
        .select_related("led")
        .all()[:20]
    )

    datos_eventos = []
    for evento in eventos:
        fecha = timezone.localtime(
            evento.fecha
        )

        datos_eventos.append({
            "led": evento.led.nombre,
            "codigo": evento.led.codigo,
            "estado": evento.estado,
            "origen": evento.origen,
            "fecha": fecha.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
        })


    return JsonResponse({
        "leds": datos_leds,
        "eventos": datos_eventos,
    })


@require_POST
def controlar_led(request, codigo):

    led = get_object_or_404(
        Led,
        codigo=codigo
    )

    try:

        datos = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "ok": False,
                "error": "JSON inválido",
            },
            status=400
        )


    nuevo_estado = datos.get("estado")


    if not isinstance(
        nuevo_estado,
        bool
    ):

        return JsonResponse(
            {
                "ok": False,
                "error": "Estado inválido",
            },
            status=400
        )


    comando = ComandoLed.objects.create(
        led=led,
        estado_deseado=nuevo_estado,
        estado="PENDIENTE"
    )


    return JsonResponse({
        "ok": True,
        "comando_id": comando.id,
        "led": led.codigo,
        "estado_deseado": nuevo_estado,
    })
