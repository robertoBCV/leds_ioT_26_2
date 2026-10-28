import time

import serial

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from control.models import (
    Led,
    EventoLed,
    ComandoLed,
)


class Command(BaseCommand):
    help = (
        "Comunicación serial entre "
        "Django y Arduino Mega-UNO"
    )


    # ==================================================
    # ARGUMENTOS
    # ==================================================

    def add_arguments(self, parser):
        parser.add_argument(
            "--port",
            type=str,
            default="COM6",
            help="Puerto serial del Arduino"
        )

        parser.add_argument(
            "--baudrate",
            type=int,
            default=9600,
            help="Velocidad serial"
        )


    # ==================================================
    # EJECUCIÓN PRINCIPAL
    # ==================================================

    def handle( self,  *args, **options ):
        puerto =   options["port"]
        baudrate =  options["baudrate"]
        self.stdout.write("--------------------------------")
        self.stdout.write("Worker IoT iniciado")
        self.stdout.write(f"Puerto: {puerto}")
        self.stdout.write(f"Baudrate: {baudrate}")
        self.stdout.write("--------------------------------")
        try:
            arduino = serial.Serial(port=puerto,baudrate=baudrate, timeout=0.1)
        except serial.SerialException as error:
            self.stderr.write(self.style.ERROR(f"No se pudo abrir {puerto}"))
            self.stderr.write(str(error))
            return

        # Cuando se abre el puerto,
        # Arduino normalmente se reinicia.
        self.stdout.write("Esperando al Arduino..." )
        time.sleep(2)

        # Limpiamos cualquier basura anterior
        # que pudiera existir en el buffer.
        arduino.reset_input_buffer()
        self.stdout.write(self.style.SUCCESS("Arduino conectado correctamente.") )
        try:
            while True:
                close_old_connections()
                # ======================================
                # 1. LEER INFORMACIÓN DEL ARDUINO
                # ======================================
                self.leer_arduino(arduino)
                # ======================================
                # 2. BUSCAR COMANDOS DE LA WEB
                # ======================================
                self.enviar_comando_pendiente(arduino )
                time.sleep(0.05)
        except KeyboardInterrupt:
            self.stdout.write("\nDeteniendo worker..." )
        finally:
            if arduino.is_open:
                arduino.close()

            self.stdout.write(self.style.SUCCESS("Puerto serial cerrado.") )

    # ==================================================
    # LEER ARDUINO
    # ==================================================
    def leer_arduino(self, arduino ):
        while arduino.in_waiting > 0:
            try:
                linea = (arduino
                    .readline()
                    .decode("utf-8", errors="ignore" )
                    .strip()
                )

            except Exception as error:
                self.stderr.write(f"Error leyendo Arduino: {error}" )
                return

            if not linea:
                return

            self.stdout.write( f"Arduino -> {linea}"  )
            self.procesar_linea( linea )


    # ==================================================
    # PROCESAR RESPUESTAS
    # ==================================================

    def procesar_linea(self,  linea):
        partes = linea.split(",")
        # ==============================================
        # EVENTO
        #
        # EVENTO,ROJO,1,BOTON
        # EVENTO,VERDE,0,WEB
        # ==============================================
        if (len(partes) == 4 and partes[0] == "EVENTO" ):
            codigo = partes[1].strip()
            estado =  partes[2].strip() == "1"
            origen = partes[3].strip()
            try:
                led = Led.objects.get( codigo=codigo )
            except Led.DoesNotExist:
                self.stderr.write( f"LED desconocido: {codigo}" )
                return

            # Actualizar estado actual
            led.estado_actual =   estado
            led.save()

            # Crear registro histórico
            EventoLed.objects.create(led=led,estado=estado,origen=origen)


            self.stdout.write(
                self.style.SUCCESS(
                    f"{codigo}: "
                    f"{'ENCENDIDO' if estado else 'APAGADO'} "
                    f"({origen})"
                )
            )


            # Si vino de la web,
            # confirmamos el comando.
            if origen == "WEB":
                self.confirmar_comando( led, estado  )
            return

        # ==============================================
        # ESTADO
        #
        # ESTADO,ROJO,1
        # ==============================================
        if (len(partes) == 3  and partes[0] == "ESTADO"):
            codigo =  partes[1].strip()
            estado =  partes[2].strip() == "1"
            try:
                led =  Led.objects.get(codigo=codigo  )
            except Led.DoesNotExist:
                self.stderr.write(f"LED desconocido: {codigo}" )
                return
            led.estado_actual =  estado
            led.save()

            # También puede tratarse de la confirmación
            # de una orden cuyo estado ya coincidía.
            self.confirmar_comando(led,estado)


            self.stdout.write(
                f"Estado actualizado: "
                f"{codigo} = "
                f"{'ON' if estado else 'OFF'}"
            )
            return


        # ==============================================
        # ERROR
        # ==============================================
        if ( len(partes) >= 2 and  partes[0] == "ERROR" ):
            self.stderr.write(f"Arduino reportó: {linea}" )
            return
        self.stderr.write(f"Mensaje desconocido: {linea}" )

    # ==================================================
    # ENVIAR COMANDO PENDIENTE
    # =================================================
    def enviar_comando_pendiente( self, arduino ):
        comando = (
            ComandoLed.objects
            .filter(estado="PENDIENTE")
            .select_related("led")
            .order_by("id")
            .first()
        )

        if comando is None:
            return


        valor = (
            1
            if comando.estado_deseado
            else 0
        )


        mensaje = (
            f"{comando.led.codigo}:"
            f"{valor}\n"
        )


        try:
            arduino.write(
                mensaje.encode(
                    "utf-8"
                )
            )
            arduino.flush()


        except serial.SerialException as error:
            comando.estado =     "ERROR"
            comando.mensaje_error =   str(error)
            comando.procesado_en = timezone.now()
            comando.save()

            self.stderr.write(f"Error enviando comando: {error}" )
            return

        comando.estado =      "ENVIADO"
        comando.procesado_en =      timezone.now()
        comando.save()


        self.stdout.write(
            f"Django -> "
            f"{mensaje.strip()}"
        )

    # ==================================================
    # CONFIRMAR COMANDO
    # ==================================================
    def confirmar_comando( self, led,estado ):
        comando = (
            ComandoLed.objects
            .filter(
                led=led,
                estado_deseado=estado,
                estado="ENVIADO"
            )
            .order_by("id")
            .first()
        )


        if comando is None:
            return

        comando.estado =    "CONFIRMADO"
        comando.procesado_en =     timezone.now()
        comando.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Comando #{comando.id} "
                f"CONFIRMADO"
            )
        )