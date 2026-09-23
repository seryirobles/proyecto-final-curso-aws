"""The single backend es-ES messages module (FR-UX-03): every user-facing
string a backend package raises lives here, in UPPER_SNAKE constants — the
backend counterpart of frontend/src/messages/."""

from __future__ import annotations

PASSWORD_TOO_SHORT = "La contraseña debe tener al menos 10 caracteres."
USERNAME_ALREADY_TAKEN = "Este nombre de usuario ya está en uso."
USERNAME_RESERVED = "Este nombre de usuario está reservado y no puede utilizarse."

AI_GENERATION_INVALID_OUTPUT = "La receta generada no es válida. Puedes intentarlo de nuevo."
AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES = (
    "No hay suficientes recetas en la biblioteca para completar la semana "
    "con este modo. Añade recetas, cambia de modo o ajusta las reglas."
)
AI_GENERATION_UNAVAILABLE = (
    "La generación con IA no está disponible en este momento. Puedes intentarlo más tarde."
)
UNKNOWN_PROMPT_VERSION = (
    "La generación con IA no está disponible en este momento. Inténtalo de nuevo más tarde."
)

FORBIDDEN = "No tienes permiso para realizar esta operación."
INVALID_CREDENTIALS = "El nombre de usuario o la contraseña no son correctos."
SESSION_EXPIRED = "La sesión ha caducado. Vuelve a iniciar sesión."
SET_PASSWORD_REQUIRED = "Debes establecer una nueva contraseña antes de continuar."
SET_PASSWORD_NOT_ALLOWED = "No es necesario establecer una nueva contraseña en este momento."
ACCOUNT_NOT_FOUND = "No se ha encontrado la cuenta solicitada."
RECIPE_NOT_FOUND = "No se ha encontrado la receta solicitada."
CANDIDATE_NOT_FOUND = "No se ha encontrado la comida solicitada."
SHOPPING_ITEM_NOT_FOUND = "No se ha encontrado el elemento de la lista de la compra."
SHOPPING_LIST_LOCK_HELD = "La lista de la compra se está actualizando. Inténtalo de nuevo."
INVALID_WEEKDAY = "El día indicado no es válido."
UNKNOWN_UNIT = "La unidad indicada no está permitida."
UNKNOWN_INGREDIENT_CATEGORY = "La categoría de ingrediente indicada no está permitida."
INVALID_ISO_WEEK = "La semana indicada no es válida."
PIN_RULES_AFFECTED = "Hay reglas que fijan esta receta."
UNSATISFIABLE_RULE_SET = "Las reglas indicadas no se pueden cumplir a la vez."
INVALID_RULE_ID = "El identificador de regla indicado no es válido."
MALFORMED_REQUEST = "La solicitud no es válida."

# Issue empty-field-error-messages: a required field left blank names itself,
# instead of falling through to the value parser's own rejection.
EMPTY_NAME = "El campo Nombre no puede estar vacío."
EMPTY_CATEGORY = "El campo Categoría no puede estar vacío."
EMPTY_INGREDIENT_NAME = "El campo Nombre del ingrediente no puede estar vacío."
EMPTY_QUANTITY = "El campo Cantidad no puede estar vacío."
EMPTY_UNIT = "El campo Unidad no puede estar vacío."
EMPTY_TOOL = "El campo Utensilio no puede estar vacío."
EMPTY_PROCEDURE_STEP = "El campo Paso de la elaboración no puede estar vacío."

# Issue tiempo-estimado-numeric-minutes (G-90): a well-formed but out-of-range
# prep/cook time is rejected the same way an empty required field is.
INVALID_ESTIMATED_TIME = (
    "El campo Tiempo estimado debe ser un número entero de minutos entre 0 y 6000."
)

# Issue negative-ingredient-quantity: a well-formed but non-positive value is
# rejected the same way an empty required field is (Part H, G-91/Part AA).
INVALID_INGREDIENT_QUANTITY = "La cantidad del ingrediente debe ser mayor que cero."
INVALID_SERVINGS = "El número de comensales debe ser mayor que cero."

# Issue recipe-saved-without-required-sections (G-89, Part Y): each section
# needs at least one item.
RECIPE_WITHOUT_INGREDIENTS = "La receta debe incluir al menos un ingrediente."
RECIPE_WITHOUT_TOOLS = "La receta debe incluir al menos un utensilio."
RECIPE_WITHOUT_PROCEDURE = "La receta debe incluir al menos un paso de elaboración."

INTERNAL_ERROR = "Se ha producido un error inesperado. Inténtalo de nuevo más tarde."
GENERATION_NOT_FOUND = "No se ha encontrado la petición de generación solicitada."
ROUTE_NOT_FOUND = "El recurso solicitado no existe."
