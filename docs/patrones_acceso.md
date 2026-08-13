# Patrones de acceso

| AP | Título | Tipo | Parámetros | Devolución | Frecuencia | ¿Requiere ordenación o filtrado? |
|---|---|---|---|---|---|---|
| AP1 | Pantalla admin - Listar usuarios | Lectura | - | lista(idUsuario, nombreUsuario, tipo, isPassReseteada) | Baja | No |
| AP2 | Obtener usuario | Lectura | idUsuario | idUsuario, nombreUsuario, tipo, isPassReseteada | Baja | No |
| AP3 | Obtener usuario por nombre | Lectura | nombreUsuario | idUsuario, nombreUsuario, tipo, isPassReseteada | Baja | No |
| AP4 | Pantalla admin - Crear o editar usuario | Escritura | nombreUsuario, idUsuario, tipo, pass, isPassReseteada | idUsuario, nombreUsuario, tipo, isPassReseteada | Baja | No |
| AP5 | Pantalla admin - Eliminar usuario | Eliminación | idUsuario | - | Baja | No |
| AP6 | Login | Lectura | nombreUsuario, pass | idUsuario, tipo, isPassReseteada | Alta | No |
| AP7 | Establecer contraseña | Escritura | idUsuario, pass | - | Media | No |
| AP8 | Obtener semana | Lectura | idSemana | idSemana, lista(numeroDia, lista(numeroComida, idPlatoDefinitiva, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento))) | Alta | Si |
| AP9 | Obtener semana + ingredientes | Lectura | idSemana | idSemana, lista(numeroDia, lista(numeroComida, idPlatoDefinitiva, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento, lista(nombreIngrediente, cantidad, unidad)))) | Media | Si |
| AP10 | Obtener comida - Semana | Lectura | idPlato | idSemana, numeroDia, numeroComida, idPlatoDefinitiva, idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso), añadidoPor | Alta | No |
| AP11 | Establecer/Desasignar comida definitiva | Escritura | idSemana, numeroDia, numeroComida, idPlatoDefinitiva | idSemana, numeroDia, numeroComida, idPlatoDefinitiva | Media | No |
| AP12 | Eliminar comida | Eliminación | idPlato | - | Media | No |
| AP13 | Editar o añadir comida | Escritura | idSemana, idPlato, numeroDia, añadidoPor, numeroComida, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | idSemana, numeroDia, añadidoPor, numeroComida, idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | Media | No |
| AP14 | Obtener biblioteca | Lectura | idBiblioteca, nombrePlato, tipoAlimento | lista(idPlato, nombrePlato, tiempo, tipoAlimento, añadidoPor) | Alta | Sí |
| AP15 | Obtener comida de la biblioteca | Lectura | idPlato | idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso), añadidoPor | Alta | No |
| AP16 | Añadir o editar comida (biblioteca) | Escritura | idBiblioteca, idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, añadidoPor, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, añadidoPor, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | Media | No |
| AP17 | Eliminar comida (biblioteca) | Eliminación | idPlato | - | Media | No |
| AP18 | Obtener lista de la compra | Lectura | idLista | lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado) | Alta | No |
| AP19 | Añadir o editar elemento de lista de la compra | Escritura | idLista, idIngrediente, nombreIngrediente, cantidad, unidad, isComprado | idIngrediente, nombreIngrediente, cantidad, unidad, isComprado | Alta | No |
| AP20 | Eliminar elemento de la lista de la compra | Eliminación | idLista, idIngrediente | - | Alta | No |
| AP21 | Eliminar elementos marcados de la lista de la compra | Eliminación | idLista | lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado) | Media | Sí |
| AP22 | Obtener reglas | Lectura | idGrupoReglas, tipoRegla | idGrupoReglas, lista(idRegla, tipoRegla, tipoComida, cantidad, numeroDia, numeroComida, idPlato, nombrePlato) | Media | Sí |
| AP23 | Añadir o editar regla | Escritura | idRegla, tipoRegla, tipoComida, cantidad, numeroDia, numeroComida, idPlato | idRegla, tipoRegla, tipoComida, cantidad, numeroDia, numeroComida, idPlato | Media | No |
| AP24 | Eliminar regla | Eliminación | idRegla | - | Media | No |
| AP25 | Añadir o editar petición IA (idempotencia) | Escritura | requestId, status, result, ttl | requestId | Alta | No |
| AP26 | Obtener petición IA (idempotencia) | Lectura | requestId | requestId, status, result, ttl | Alta | No |
| AP27 | Eliminar petición IA (idempotencia) | Eliminación | requestId | - | Alta | No |
