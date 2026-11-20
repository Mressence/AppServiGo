# ServiGo!! V3 — cambios y guía de commits

Esta entrega conserva las aplicaciones y los archivos existentes del proyecto. Los ajustes de agenda no requieren migraciones adicionales: reutilizan los modelos y migraciones V3 que ya están en el proyecto.

## Funciones conectadas

1. **Calendario público del técnico**
   - El cliente abre el perfil del profesional aprobado y entra a su calendario.
   - Los días verdes indican que queda al menos un horario disponible.
   - Las citas ocupadas se muestran en rojo y las solicitudes con horario provisional en naranja.
   - Al seleccionar una fecha se abre el formulario de solicitud con el técnico y la fecha ya seleccionados.
   - Si el cliente inicia la solicitud desde el formulario general, al seleccionar técnico y fecha se cargan dinámicamente los horarios disponibles.

2. **Reserva provisional de horario**
   - Cuando el cliente envía una solicitud con día y hora, ese bloque queda reservado provisionalmente para ese técnico.
   - El bloque se refleja en el calendario del técnico y del cliente.
   - No se ofrece a otro cliente mientras la solicitud esté pendiente de cotización/aceptación.
   - Se valida nuevamente en el servidor antes de crear la solicitud y al confirmar/programar la cita.

3. **Cotización y programación**
   - Solo el técnico individual asignado puede consultar y cotizar esa solicitud.
   - Al aceptar la cotización, si ya había una fecha y hora solicitadas, se crea automáticamente la cita.
   - Si no se había indicado fecha, el cliente puede abrir el calendario del mismo técnico desde el detalle de la solicitud y seleccionar un día y horario.
   - La selección desde el calendario lleva al formulario de programación y crea una cita real.

4. **Disponibilidad**
   - Se respetan los horarios semanales, bloqueos de disponibilidad, citas existentes y horarios provisionales solicitados.
   - Las validaciones se ejecutan en el servidor; no se confía solamente en los colores del calendario.
   - Al reprogramar se actualiza también la fecha solicitada de la solicitud para evitar que el horario anterior quede bloqueado.

5. **Cancelaciones, historial y avisos**
   - La cancelación de una solicitud pide un motivo y lo registra en el historial.
   - Las cancelaciones y cambios de cita notifican a los participantes correspondientes.
   - Las vistas de calendario muestran eventos propios del cliente/técnico, sin mostrar información privada de otros clientes.

6. **Documentación**
   - README actualizado con el flujo V3.
   - Este archivo resume las funciones y propone mensajes de commit.

## Commits sugeridos

Se pueden registrar en uno o varios commits:

- `feat: calendario interactivo de reservas por tecnico`
- `feat: reserva provisional y validacion de disponibilidad`
- `feat: programacion de citas desde el calendario`
- `fix: evitar cruces de horarios entre solicitudes y citas`
- `feat: cancelaciones con motivo e historial`
- `feat: eventos de agenda para clientes y tecnicos`
- `docs: documentar flujo completo de ServiGo V3`

## Actualización local

En el entorno virtual del proyecto:

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

No se añadieron modelos ni campos en esta corrección, por lo que no se necesita `makemigrations`. Se conservan las migraciones V3 existentes.

## Pruebas manuales recomendadas

- Configurar dos o más horarios semanales para un técnico aprobado.
- Entrar como cliente al perfil público del técnico, elegir un día y enviar una solicitud con hora.
- Comprobar que el evento provisional aparece en naranja en los calendarios del cliente y del técnico.
- Entrar como otro cliente y verificar que ese mismo bloque no aparece entre los horarios libres.
- Entrar como el técnico asignado, enviar una cotización y comprobar la notificación del cliente.
- Aceptar la cotización y comprobar que la cita se crea y aparece como ocupada.
- Probar una solicitud sin fecha, aceptar su cotización y programarla desde el calendario del técnico.
- Reprogramar y comprobar que el horario anterior queda libre.
- Cancelar con motivo y comprobar el historial y las notificaciones.

> La sintaxis Python se revisó en esta entrega. Para certificar la ejecución integral se deben correr `manage.py check`, migraciones y las pruebas funcionales en el entorno Django local, con la base de datos del proyecto.
