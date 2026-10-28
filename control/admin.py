from django.contrib import admin

#from .models.models import Led, EventoLed, ComandoLed

from .models import (
    Led,
    EventoLed,
    ComandoLed,
    Bocina,
    EventoBocina,
    ComandoBocina,
    SensorDht11,
    LecturaDht11,
)


@admin.register(Led)
class LedAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "codigo",
        "pin",
        "color",
        "estado_actual",
        "actualizado_en",
    )

    list_filter = (
        "estado_actual",
        "color",
    )

    search_fields = (
        "nombre",
        "codigo",
    )


@admin.register(EventoLed)
class EventoLedAdmin(admin.ModelAdmin):

    list_display = (
        "led",
        "estado",
        "origen",
        "fecha",
    )

    list_filter = (
        "estado",
        "origen",
        "led",
    )


@admin.register(ComandoLed)
class ComandoLedAdmin(admin.ModelAdmin):

    list_display = (
        "led",
        "estado_deseado",
        "estado",
        "creado_en",
        "procesado_en",
    )

    list_filter = (
        "estado",
        "estado_deseado",
    )