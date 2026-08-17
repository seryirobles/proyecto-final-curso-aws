# Patrones de acceso

> **Fuente de verdad: `docs/data_model.md` §4**, que además asocia cada patrón a
> su operación concreta de DynamoDB. Esta tabla es la vista en castellano del
> catálogo, verificada contra la hoja de cálculo del propietario en su guardado
> del **2026-08-16 14:23**.
>
> **Corregido el 2026-08-16.** La versión anterior era una instantánea anterior al
> 2026-08-15 y contenía cuatro errores ya resueltos en su momento: usaba
> `idPlatoDefinitiva` (femenino) en lugar de `idPlatoDefinitivo`; daba a AP10 y
> AP12 solo `idPlato` como parámetro, con lo que ninguno de los dos podía
> localizar su ítem sin un índice; daba a AP15 y AP17 solo `idPlato` en lugar de
> `idBiblioteca, idPlato`; y añadía a AP14 los parámetros `nombrePlato` y
> `tipoAlimento`, cuando ambos filtros se resuelven en memoria. AP10 tampoco
> devuelve `idPlatoDefinitivo`.
>
> **Los formatos de las claves no van aquí** — están en `data_model.md` §2, y
> cuatro de ellos llevan una trampa documentada.

| AP | Título | Tipo | Parámetros | Devolución | Frecuencia | ¿Requiere ordenación o filtrado? |
|---|---|---|---|---|---|---|
| AP1 | Pantalla admin - Listar usuarios | Lectura | - | lista(idUsuario, nombreUsuario, tipo, isPassReseteada) | Baja | No |
| AP2 | Obtener usuario | Lectura | idUsuario | idUsuario, nombreUsuario, tipo, isPassReseteada | Baja | No |
| AP3 | Obtener usuario por nombre | Lectura | nombreUsuario | idUsuario, nombreUsuario, tipo, isPassReseteada | Baja | No |
| AP4 | Pantalla admin - Crear o editar usuario | Escritura | nombreUsuario, idUsuario, tipo, pass, isPassReseteada | idUsuario, nombreUsuario, tipo, isPassReseteada | Baja | No |
| AP5 | Pantalla admin - Eliminar usuario | Eliminación | idUsuario | - | Baja | No |
| AP6 | Login | Lectura | nombreUsuario, pass | idUsuario, tipo, isPassReseteada | Alta | No |
| AP7 | Establecer contraseña | Escritura | idUsuario, pass | - | Media | No |
| AP8 | Obtener semana | Lectura | idSemana | idSemana, lista(numeroDia, lista(numeroComida, idPlatoDefinitivo, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento))) | Alta | Sí |
| AP9 | Obtener semana + ingredientes | Lectura | idSemana | idSemana, lista(numeroDia, lista(numeroComida, idPlatoDefinitivo, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento, lista(nombreIngrediente, cantidad, unidad)))) | Media | Sí |
| AP10 | Obtener comida - Semana | Lectura | idSemana, numeroDia, numeroComida, idPlato | idSemana, numeroDia, numeroComida, idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso), añadidoPor | Alta | No |
| AP11 | Establecer/Desasignar comida definitiva | Escritura | idSemana, numeroDia, numeroComida, idPlatoDefinitivo | idSemana, numeroDia, numeroComida, idPlatoDefinitivo | Media | No |
| AP12 | Eliminar comida | Eliminación | idSemana, numeroDia, numeroComida, idPlato | - | Media | No |
| AP13 | Editar o añadir comida | Escritura | idSemana, idPlato, numeroDia, añadidoPor, numeroComida, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | idSemana, numeroDia, añadidoPor, numeroComida, idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | Media | No |
| AP14 | Obtener biblioteca | Lectura | idBiblioteca | idBiblioteca, lista(idPlato, nombrePlato, tiempo, tipoAlimento, añadidoPor) | Alta | Sí |
| AP15 | Obtener comida de la biblioteca | Lectura | idBiblioteca, idPlato | idBiblioteca, idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso), añadidoPor | Alta | No |
| AP16 | Añadir o editar comida (biblioteca) | Escritura | idBiblioteca, idPlato, nombrePlato, tipoAlimento, tiempo, numeroComensales, añadidoPor, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | idBiblioteca, idPlato, nombrePlato, tiempo, numeroComensales, tipoAlimento, añadidoPor, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso) | Media | No |
| AP17 | Eliminar comida (biblioteca) | Eliminación | idBiblioteca, idPlato | - | Media | No |
| AP18 | Obtener lista de la compra | Lectura | idLista | lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado) | Alta | No |
| AP19 | Añadir o editar elemento de lista de la compra | Escritura | idLista, idIngrediente, nombreIngrediente, cantidad, unidad, isComprado | idIngrediente, nombreIngrediente, cantidad, unidad, isComprado | Alta | No |
| AP20 | Eliminar elemento de la lista de la compra | Eliminación | idLista, idIngrediente | - | Alta | No |
| AP21 | Eliminar elementos marcados de la lista de la compra | Eliminación | idLista | lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado) | Media | Sí |
| AP22 | Obtener reglas | Lectura | idGrupoReglas | idGrupoReglas, lista(idRegla, tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato, nombrePlato) | Media | No |
| AP23 | Añadir o editar regla | Escritura | idGrupoReglas, idRegla, tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato | idRegla, tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato | Media | No |
| AP24 | Eliminar regla | Eliminación | idGrupoReglas, idRegla | - | Media | No |
| AP25 | Añadir o editar petición IA (idempotencia) | Escritura | idPeticionIA, estado, resultado, ttl | idPeticionIA | Media | No |
| AP26 | Obtener petición IA (idempotencia) | Lectura | idPeticionIA | idPeticionIA, estado, resultado, ttl | Media | No |
| AP27 | Eliminar petición IA (idempotencia) | Eliminación | idPeticionIA | - | Media | No |

## Notas

- **`nombrePlato` en AP22 no se almacena.** `DatosRegla` guarda solo `idPlato`; el
  nombre se resuelve en lectura desde la biblioteca, para que no pueda quedar
  obsoleto al renombrar una receta. Ver `data_model.md` §6.
- **Cuatro patrones hacen una segunda lectura por diseño** — AP3/AP6, AP22 y
  AP8/AP9. Todas son búsquedas por clave y ninguna necesita un índice.
  **No conviene "arreglarlas" desnormalizando.**
- **Ningún patrón requiere índices secundarios ni `Scan`.**
- `LockLista` es el único tipo de ítem sin patrón de acceso: es el mecanismo de
  serialización de `FR-SHOP-10`, no una operación de usuario.
